"""
④ 图库资产管家 — 高并发压力测试
=========================================
业务场景: B端数字资产管理（DAM）
核心端点: 素材上传/下载、搜索、AI标签、公开API

用法:
    locust -f tests/locustfile.py --host=http://localhost:8400
    locust -f tests/locustfile.py --host=http://localhost:8400 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html
"""

import io
import json
import os
import random
from pathlib import Path

from locust import HttpUser, between, events, tag, task

USERS_FILE = Path(__file__).parent.parent / "data" / "test_users.json"
_user_credentials = []
_user_index = 0
_admin_user = os.getenv("TEST_ADMIN_USER", "admin")
_admin_pass = os.getenv("TEST_ADMIN_PASS", "ChangeMe!2024")

# 生成 1KB 的模拟 PNG 图片数据
MOCK_IMAGE = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)


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


# ── 普通用户（~85%）──────────────────────────────────
class AssetUser(HttpUser):
    """模拟 DAM 用户：上传 → 搜索 → 浏览 → 公开搜索"""

    wait_time = between(3, 8)
    weight = 17

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None

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

    @tag("smoke", "load", "mutation")
    @task(4)
    def upload_asset(self):
        """核心：上传素材"""
        if not self.token:
            return
        MOCK_IMAGE.seek(0)
        self.client.post(
            "/api/assets/upload",
            files={"file": ("test_image.png", MOCK_IMAGE, "image/png")},
            data={"tags": "测试,压力,自动化"},
            name="POST /api/assets/upload", catch_response=True,
        )

    @tag("smoke", "load")
    @task(3)
    def list_assets(self):
        """浏览素材列表（含搜索/标签筛选）"""
        if not self.token:
            return
        params = {"page": 1, "page_size": 20}
        if random.random() > 0.5:
            params["search"] = random.choice(["产品", "海报", "banner", "logo"])
            params["tag"] = random.choice(["设计", "营销", "素材"])
        self.client.get("/api/assets/list", params=params,
                        name="GET /api/assets/list", catch_response=True)

    @tag("smoke")
    @task(1)
    def asset_stats(self):
        if not self.token:
            return
        self.client.get("/api/assets/stats", name="GET /api/assets/stats",
                        catch_response=True)

    @tag("smoke")
    @task(1)
    def popular_tags(self):
        if not self.token:
            return
        self.client.get("/api/assets/tags/popular",
                        name="GET /api/assets/tags/popular",
                        catch_response=True)

    @tag("load")
    @task(1)
    def free_stock_photos(self):
        """免费图库照片（公开接口，无需认证）"""
        self.client.get("/api/assets/free-stock-photos",
                        name="GET /api/assets/free-stock-photos",
                        catch_response=True)

    @tag("load")
    @task(1)
    def public_search(self):
        """公开搜索（无需认证）"""
        self.client.get(
            "/api/assets/public/search",
            params={"q": random.choice(["风景", "产品", "人物", "建筑"])},
            name="GET /api/assets/public/search", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def import_from_url(self):
        if not self.token:
            return
        self.client.post(
            "/api/assets/import-from-url",
            json={"url": f"https://picsum.photos/seed/{random.randint(1,9999)}/200/200.jpg"},
            name="POST /api/assets/import-from-url", catch_response=True,
        )


# ── 管理员（~15%）────────────────────────────────────
class AdminUser(HttpUser):
    wait_time = between(5, 15)
    weight = 3

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
