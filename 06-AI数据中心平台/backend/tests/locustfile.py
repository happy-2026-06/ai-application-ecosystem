"""
⑥ 数据中枢 — 高并发压力测试
=========================================
业务场景: 数据中心平台（数据采集/清洗/标注/导出）
核心端点: 数据集CRUD、数据导入、清洗、AI标注、导出

用法:
    locust -f tests/locustfile.py --host=http://localhost:8606
    locust -f tests/locustfile.py --host=http://localhost:8606 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html
"""

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

# 模拟数据导入文本
MOCK_DATA_TEXTS = [
    "Q: 退货怎么操作？ A: 您可以进入我的订单页面，点击申请退货，填写退货原因后提交即可。",
    "Q: 什么时候发货？ A: 一般情况下付款后24小时内发货，节假日顺延，物流信息可在订单详情页查看。",
    "Q: 优惠券怎么领？ A: 您可以关注我们店铺首页的领券中心，每天有限量优惠券发放。",
    "Q: 这个产品支持分期吗？ A: 支持花呗分期和信用卡分期，3期和6期免手续费。",
]


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


# ── 数据操作员（~90%）───────────────────────────────
class DataOperatorUser(HttpUser):
    """模拟数据操作员：创建数据集 → 导入 → 清洗 → 标注 → 导出"""

    wait_time = between(3, 8)
    weight = 18

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.dataset_id = None

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
    @task(3)
    def create_dataset(self):
        """创建数据集"""
        if not self.token:
            return
        with self.client.post(
            "/api/data/datasets",
            json={"name": f"压测数据集-{random.randint(1, 99999)}",
                  "description": "自动化压测数据"},
            name="POST /api/data/datasets", catch_response=True,
        ) as r:
            if r.status_code in (200, 201):
                self.dataset_id = r.json().get("id", "")
                r.success()

    @tag("smoke", "load")
    @task(2)
    def list_datasets(self):
        if not self.token:
            return
        self.client.get("/api/data/datasets", params={"page": 1, "page_size": 20},
                        name="GET /api/data/datasets", catch_response=True)

    @tag("mutation")
    @task(2)
    def ingest_data(self):
        """数据导入"""
        if not self.token or not self.dataset_id:
            return
        texts = MOCK_DATA_TEXTS
        self.client.post(
            f"/api/data/datasets/{self.dataset_id}/ingest",
            json={"texts": texts},
            name="POST /api/data/datasets/:id/ingest", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def clean_dataset(self):
        """数据清洗"""
        if not self.token or not self.dataset_id:
            return
        self.client.post(
            f"/api/data/datasets/{self.dataset_id}/clean",
            name="POST /api/data/datasets/:id/clean", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def annotate_dataset(self):
        """AI 自动标注"""
        if not self.token or not self.dataset_id:
            return
        self.client.post(
            f"/api/data/datasets/{self.dataset_id}/annotate",
            json={"dataset_id": self.dataset_id,
                  "items": [{"text": t, "index": i}
                            for i, t in enumerate(MOCK_DATA_TEXTS)]},
            name="POST /api/data/datasets/:id/annotate", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def create_version(self):
        """创建版本快照"""
        if not self.token or not self.dataset_id:
            return
        self.client.post(
            f"/api/data/datasets/{self.dataset_id}/versions",
            json={"description": f"压测版本-{random.randint(1, 999)}"},
            name="POST /api/data/datasets/:id/versions", catch_response=True,
        )

    @tag("smoke")
    @task(1)
    def quality_report(self):
        """查看质量报告"""
        if not self.token or not self.dataset_id:
            return
        self.client.get(
            f"/api/data/datasets/{self.dataset_id}/quality",
            name="GET /api/data/datasets/:id/quality", catch_response=True,
        )

    @tag("load")
    @task(1)
    def export_for_finetune(self):
        """导出微调格式"""
        if not self.token or not self.dataset_id:
            return
        self.client.get(
            f"/api/data/datasets/{self.dataset_id}/export-for-finetune",
            name="GET /api/data/datasets/:id/export-for-finetune", catch_response=True,
        )

    @tag("smoke")
    @task(1)
    def dashboard(self):
        if not self.token:
            return
        self.client.get("/api/data/dashboard",
                        name="GET /api/data/dashboard", catch_response=True)

    @tag("mutation")
    @task(1)
    def external_ingest(self):
        """跨项目数据接收"""
        if not self.token:
            return
        self.client.post(
            "/api/data/external/ingest",
            json={"source_project": "p1-customer-service",
                  "texts": MOCK_DATA_TEXTS[:2]},
            name="POST /api/data/external/ingest", catch_response=True,
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
