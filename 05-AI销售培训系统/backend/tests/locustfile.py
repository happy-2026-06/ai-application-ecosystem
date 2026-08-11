"""
⑤ 话术对战教练 — 高并发压力测试
=========================================
业务场景: 销售培训角色扮演
核心端点: 培训会话管理、话术对战(SSE)、评分报告、客户类型

用法:
    locust -f tests/locustfile.py --host=http://localhost:8505
    locust -f tests/locustfile.py --host=http://localhost:8505 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html
"""

import json
import os
import random
from pathlib import Path

import requests
from locust import HttpUser, between, events, tag, task

# ── 销售话术问题池 ─────────────────────────────────
SALES_SCRIPTS = [
    "这款产品的价格确实比竞品高一些，但我们提供三年的免费质保服务。",
    "我理解您说预算有限，不过我们可以帮您做免费分期，首付只要20%。",
    "您提到别家差不多的产品便宜30%，其实我们用的是最新一代芯片，性能翻倍。",
    "先不急着下决定，您觉得哪个功能最吸引您？我帮您做个对比分析。",
    "这款手机虽然没有最顶尖的配置，但性价比非常高，日常使用完全足够。",
    "您说再考虑考虑，我完全理解。不如我们先加个微信，有任何问题随时问我？",
    "我不是在推销，这款产品确实能解决您之前提到的散热问题。",
]

CUSTOMER_TYPES = [
    "picky", "price", "hesitant", "expert",
]

CUSTOMER_TITLE_PREFIXES = [
    "手机促销", "笔记本对比", "保险方案", "课程推荐", "家电咨询",
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


# ── 销售学员（~90%）─────────────────────────────────
class TraineeUser(HttpUser):
    """模拟销售学员：登录 → 创建培训 → 多轮话术对战 → 获取报告"""

    wait_time = between(4, 10)
    weight = 18

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.training_id = None
        self.round_count = 0

    def _random_context(self):
        return random.choice(CUSTOMER_TITLE_PREFIXES) + "产品介绍"

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

    @tag("smoke")
    @task(1)
    def get_customer_types(self):
        """查看可用客户类型"""
        if not self.token:
            return
        self.client.get("/api/training/customer-types",
                        name="GET /api/training/customer-types",
                        catch_response=True)

    @tag("smoke", "load", "mutation")
    @task(3)
    def create_training(self):
        """创建训练会话"""
        if not self.token:
            return
        customer_type = random.choice(CUSTOMER_TYPES)
        with self.client.post(
            "/api/training/sessions",
            json={"title": f"压测-{random.randint(1, 9999)}",
                  "customer_type": customer_type,
                  "product_context": self._random_context()},
            name="POST /api/training/sessions", catch_response=True,
        ) as r:
            if r.status_code == 201:
                self.training_id = r.json().get("id", "")
                self.round_count = 0
                r.success()

    @tag("smoke", "load", "stress")
    @task(5)
    def practice_respond(self):
        """核心：话术对战（SSE 流式评分）"""
        if not self.token:
            return
        if not self.training_id:
            # 尝试创建
            with self.client.post(
                "/api/training/sessions",
                json={"title": f"压测-{random.randint(1, 9999)}",
                      "customer_type": random.choice(CUSTOMER_TYPES),
                      "product_context": self._random_context()},
                name="POST /api/training/sessions", catch_response=True,
            ) as r:
                if r.status_code == 201:
                    self.training_id = r.json().get("id", "")
                    self.round_count = 0

        if not self.training_id:
            return

        script = random.choice(SALES_SCRIPTS)
        url = f"{self.client.base_url}/api/training/sessions/{self.training_id}/respond"
        try:
            resp = requests.post(
                url, json={"response": script},
                headers=self.client.headers, stream=True, timeout=(10, 180),
            )
            if resp.status_code == 200:
                for line in resp.iter_lines(decode_unicode=True):
                    if line and "data: [DONE]" in line:
                        break
            with self.client.post(
                "/api/training/sessions/{id}/respond",
                json={"response": script},
                params={"id": self.training_id},
                name="POST /api/training/sessions/:id/respond (SSE)",
                catch_response=True,
            ) as rec:
                if resp.status_code == 200:
                    rec.success()
                else:
                    rec.failure(f"状态码: {resp.status_code}")
            self.round_count += 1
        except Exception:
            pass  # 训练会话可能已结束

    @tag("smoke")
    @task(1)
    def view_rounds(self):
        if not self.token or not self.training_id:
            return
        self.client.get(
            f"/api/training/sessions/{self.training_id}/rounds",
            name="GET /api/training/sessions/:id/rounds", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def end_training_and_report(self):
        """结束训练并获取报告"""
        if not self.token or not self.training_id:
            return
        self.client.post(
            f"/api/training/sessions/{self.training_id}/end",
            name="POST /api/training/sessions/:id/end", catch_response=True,
        )
        self.client.get(
            f"/api/training/sessions/{self.training_id}/report",
            name="GET /api/training/sessions/:id/report", catch_response=True,
        )
        self.training_id = None

    @tag("smoke", "load")
    @task(1)
    def list_sessions(self):
        if not self.token:
            return
        self.client.get("/api/training/sessions",
                        name="GET /api/training/sessions", catch_response=True)


# ── 管理员（~10%）────────────────────────────────────
class AdminUser(HttpUser):
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
