"""
③ 视界短视频工坊 — 高并发压力测试
=========================================
业务场景: AI短视频脚本创作 + TTS配音 + 字幕导出
核心端点: 分镜脚本生成(SSE)、TTS语音合成、字幕导出

用法:
    locust -f tests/locustfile.py --host=http://localhost:8000
    locust -f tests/locustfile.py --host=http://localhost:8000 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html
"""

import json
import os
import random
from pathlib import Path

import requests
from locust import HttpUser, between, events, tag, task

# ── 短视频创作问题池 ──────────────────────────────
VIDEO_QUESTIONS = [
    "帮我写一个30秒美食短视频分镜脚本",
    "60秒产品测评视频脚本怎么分镜？",
    "帮我写一个Vlog开头脚本",
    "给美妆视频写一个分镜拍摄方案",
    "写一个反转剧情的15秒短视频脚本",
    "帮我写一段60秒带货口播话术",
    "写一段职场干货口播文案",
    "帮我写情感类口播的开场白",
    "写一段科技产品开箱口播稿",
    "帮我写一个搞笑段子的视频脚本",
    "写一个教程类视频的拍摄脚本",
    "产品促销短视频的创意脚本",
    "帮我写探店视频的拍摄脚本",
    "写一个短剧第一集的剧本大纲",
    "帮我写B站视频的标题和描述",
    "给产品视频写一个吸引人的封面文案",
]

# TTS 文本样本
TTS_TEXTS = [
    "大家好，欢迎来到我的频道，今天给大家分享一个超级实用的护肤技巧。",
    "在数字化时代，人工智能正在改变我们的生活方式和工作模式。",
    "这道菜的做法其实非常简单，只需要三步就能完成。",
    "今天收到了一个新产品的样品，让我们一起来开箱测评一下。",
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


# ── 视频创作者（~90%）───────────────────────────────
class VideoCreatorUser(HttpUser):
    """模拟短视频创作者：登录 → 脚本创作 → TTS → 字幕导出"""

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
    @task(5)
    def generate_script(self):
        """核心：分镜脚本生成（SSE 流式）"""
        if not self.token:
            return
        if not self.session_id:
            with self.client.post(
                "/api/chat/sessions", json={"title": "脚本创作"},
                name="POST /api/chat/sessions", catch_response=True,
            ) as r:
                if r.status_code == 201:
                    self.session_id = r.json().get("id", "")
                    r.success()
                else:
                    r.failure(f"创建会话失败: {r.status_code}")
                    return

        question = random.choice(VIDEO_QUESTIONS)
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

    @tag("load", "mutation")
    @task(2)
    def tts_synthesis(self):
        """TTS 语音合成"""
        if not self.token:
            return
        text = random.choice(TTS_TEXTS)
        self.client.post(
            "/api/generation/tts",
            json={"text": text, "voice": "zh-CN-XiaoxiaoNeural"},
            name="POST /api/generation/tts", catch_response=True,
        )

    @tag("smoke")
    @task(1)
    def get_tts_voices(self):
        if not self.token:
            return
        self.client.get("/api/generation/tts/voices",
                        name="GET /api/generation/tts/voices",
                        catch_response=True)

    @tag("mutation")
    @task(1)
    def export_subtitles(self):
        if not self.token:
            return
        self.client.post(
            "/api/generation/subtitles",
            json={"text": "测试字幕内容" * 5, "format": "srt"},
            name="POST /api/generation/subtitles", catch_response=True,
        )

    @tag("smoke", "load")
    @task(1)
    def list_sessions(self):
        if not self.token:
            return
        self.client.get("/api/chat/sessions", name="GET /api/chat/sessions",
                        catch_response=True)

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
