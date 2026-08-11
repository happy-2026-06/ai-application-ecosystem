"""
② 灵笔内容引擎 — 高并发压力测试
=========================================
业务场景: 自媒体内容创作助手
核心端点: 内容生成(SSE)、会话管理、管理后台

用法:
    locust -f tests/locustfile.py --host=http://localhost:8202
    locust -f tests/locustfile.py --host=http://localhost:8202 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html
"""

import json
import os
import random
from pathlib import Path

import requests
from locust import HttpUser, between, events, tag, task

# ── 自媒体内容创作问题池 ──────────────────────────
CONTENT_QUESTIONS = [
    # 小红书
    "写一篇小红书爆款美妆文案，推荐口红",
    "生成一个小红书穿搭ootd笔记",
    "小红书标题怎么写吸引人？关于护肤",
    "写一段小红书探店文案，咖啡馆",
    "帮我写小红书配图文案，旅行打卡",
    # 抖音/短视频
    "写一个抖音短视频脚本，剧情反转类",
    "帮我写口播文案，关于职场干货",
    "怎么起一个抖音爆款标题？",
    "写一个美食类短视频的分镜脚本",
    "帮我生成一段带货直播话术",
    # 公众号
    "写一篇公众号文章：如何提升工作效率",
    "公众号文章开头怎么写吸引人？",
    "帮我写一个公众号推文标题合集",
    "写一篇行业分析文章的框架",
    # 知乎/B站
    "写一个知乎高赞回答：程序员如何自学AI",
    "帮我写B站视频简介文案",
    "科技类B站视频脚本怎么写？",
    # 电商文案
    "写一段淘宝详情页产品描述",
    "帮我写京东商品标题优化文案",
    "写一段直播带货的秒杀话术",
    # SEO/营销
    "怎么写SEO友好的文章？",
    "帮我写品牌故事文案",
    "怎么把长文章改写成短视频脚本？",
]

USERS_FILE = Path(__file__).parent.parent / "data" / "test_users.json"
_user_credentials = []
_user_index = 0
_admin_user = os.getenv("TEST_ADMIN_USER", "admin")
_admin_pass = os.getenv("TEST_ADMIN_PASS", "ChangeMe!2024")


def load_users():
    global _user_credentials
    if USERS_FILE.exists():
        _user_credentials = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        print(f"[OK] 已加载 {len(_user_credentials)} 个测试用户")
    return _user_credentials


def next_user():
    global _user_index
    if not _user_credentials:
        load_users()
    if not _user_credentials:
        return None
    u = _user_credentials[_user_index % len(_user_credentials)]
    _user_index += 1
    return u


@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    users = load_users()
    target = (environment.parsed_options.num_users if environment.parsed_options and environment.parsed_options.num_users is not None else 100)
    if len(users) < target:
        print(f"\n[WARN] 测试用户不足！需要 {target} 个，当前只有 {len(users)} 个")


@events.quitting.add_listener
def on_test_quitting(environment, **_kwargs):
    stats = environment.stats.total
    if stats.num_requests > 0:
        fail_rate = stats.num_failures / stats.num_requests * 100
        print(f"\n[压测结束] 总请求: {stats.num_requests}, 失败率: {fail_rate:.1f}%")
        print(f"  P50: {stats.get_response_time_percentile(0.5):.0f}ms  "
              f"P95: {stats.get_response_time_percentile(0.95):.0f}ms  "
              f"P99: {stats.get_response_time_percentile(0.99):.0f}ms")
        if fail_rate > 5:
            environment.process_exit_code = 1


# ── 创作者用户（~90%）───────────────────────────────
class CreatorUser(HttpUser):
    """模拟自媒体创作者：登录 → 内容生成 → 管理会话"""

    wait_time = between(4, 10)
    weight = 18

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.session_id = None

    def on_start(self):
        creds = next_user()
        if creds is None:
            return
        with self.client.post(
            "/api/auth/login",
            json={"username": creds["username"], "password": creds["password"]},
            name="POST /api/auth/login", catch_response=True,
        ) as r:
            if r.status_code == 200:
                self.token = r.json().get("access_token", "")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                r.success()
            elif r.status_code == 500:
                # SQLite并发锁 —— 等一会重试
                import time; time.sleep(0.3)
                r2 = self.client.post(
                    "/api/auth/login",
                    json={"username": creds["username"], "password": creds["password"]},
                    name="POST /api/auth/login", catch_response=True,
                )
                if r2.status_code == 200:
                    self.token = r2.json().get("access_token", "")
                    self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                    r.success()
                else:
                    self._reg(creds, r)
            else:
                self._reg(creds, r)

    def _reg(self, creds, original_response):
        self.client.post(
            "/api/auth/register",
            json={"username": creds["username"], "password": creds["password"],
                  "display_name": creds["username"]},
            name="POST /api/auth/register",
        )
        r2 = self.client.post(
            "/api/auth/login",
            json={"username": creds["username"], "password": creds["password"]},
            name="POST /api/auth/login",
        )
        if r2.status_code == 200:
            self.token = r2.json().get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            original_response.success()
        else:
            original_response.failure(f"登录失败: {r2.status_code}")

    @tag("smoke", "load", "stress")
    @task(6)
    def generate_content(self):
        """核心：AI 内容生成（SSE 流式）"""
        if not self.token:
            return
        if not self.session_id:
            with self.client.post(
                "/api/chat/sessions", json={"title": "内容创作"},
                name="POST /api/chat/sessions", catch_response=True,
            ) as r:
                if r.status_code == 201:
                    self.session_id = r.json().get("id", "")
                    r.success()
                else:
                    r.failure(f"创建会话失败: {r.status_code}")
                    return

        question = random.choice(CONTENT_QUESTIONS)
        url = f"{self.client.base_url}/api/chat/ask?session_id={self.session_id}"
        try:
            resp = requests.post(
                url, json={"question": question},
                headers=self.client.headers, stream=True, timeout=(10, 180),
            )
            if resp.status_code == 200:
                for line in resp.iter_lines(decode_unicode=True):
                    if line and "data: [DONE]" in line:
                        break
            with self.client.post(
                f"/api/chat/ask?session_id={self.session_id}",
                json={"question": question},
                name="POST /api/chat/ask (SSE)", catch_response=True,
            ) as rec:
                if resp.status_code == 200:
                    rec.success()
                else:
                    rec.failure(f"状态码: {resp.status_code}")
        except Exception as e:
            with self.client.post(
                f"/api/chat/ask?session_id={self.session_id}",
                json={"question": question},
                name="POST /api/chat/ask (SSE)", catch_response=True,
            ) as rec:
                rec.failure(f"SSE异常: {str(e)[:80]}")

    @tag("smoke", "load")
    @task(2)
    def list_sessions(self):
        if not self.token:
            return
        self.client.get("/api/chat/sessions", name="GET /api/chat/sessions",
                        catch_response=True)

    @tag("mutation")
    @task(1)
    def create_session(self):
        if not self.token:
            return
        with self.client.post(
            "/api/chat/sessions", json={"title": f"创作-{random.randint(1, 999)}"},
            name="POST /api/chat/sessions", catch_response=True,
        ) as r:
            if r.status_code == 201:
                self.session_id = r.json().get("id", self.session_id)
                r.success()

    @tag("mutation")
    @task(1)
    def send_feedback(self):
        if not self.token or not self.session_id:
            return
        self.client.post(
            "/api/chat/feedback",
            json={"session_id": self.session_id, "rating": random.choice([4, 5])},
            name="POST /api/chat/feedback", catch_response=True,
        )

    @tag("smoke")
    @task(1)
    def get_me(self):
        if not self.token:
            return
        self.client.get("/api/auth/me", name="GET /api/auth/me", catch_response=True)


# ── 管理员（~10%）────────────────────────────────────
class AdminUser(HttpUser):
    """管理员：仪表盘 + 用户管理"""

    wait_time = between(5, 15)
    weight = 2

    def on_start(self):
        r = self.client.post(
            "/api/auth/login",
            json={"username": _admin_user, "password": _admin_pass},
            name="POST /api/auth/login (Admin)", catch_response=True,
        )
        if r.status_code == 200:
            self.token = r.json().get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @tag("smoke", "load")
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/admin/dashboard", name="GET /api/admin/dashboard",
                        catch_response=True)

    @tag("smoke")
    @task(2)
    def view_users(self):
        self.client.get("/api/admin/users", name="GET /api/admin/users",
                        catch_response=True)
