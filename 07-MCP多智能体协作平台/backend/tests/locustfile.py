"""
⑦ 智能运营引擎 — 高并发压力测试
=========================================
业务场景: 多Agent协作调度（流水线/并行/投票/辩论四种模式）
核心端点: Agent管理、任务创建/执行(SSE)、仪表盘

⚠ 注意：此项目的 SSE 任务执行可能耗时 10-60 秒（多Agent调用LLM），
   压测时需适当调高 timeout 和降低并发数。

用法:
    locust -f tests/locustfile.py --host=http://localhost:8707
    locust -f tests/locustfile.py --host=http://localhost:8707 \
        --users=50 --spawn-rate=5 --run-time=5m \
        --html=reports/stress-report.html
"""

import json
import os
import random
from pathlib import Path

import requests
from locust import HttpUser, between, events, tag, task

USERS_FILE = Path(__file__).parent.parent / "data" / "test_users.json"
_user_credentials = []
_user_index = 0
_admin_user = os.getenv("TEST_ADMIN_USER", "admin")
_admin_pass = os.getenv("TEST_ADMIN_PASS", "ChangeMe!2024")

TASK_MODES = ["pipeline", "parallel", "vote", "debate"]

TASK_DESCRIPTIONS = [
    "分析当前电商市场的三大趋势并给出应对策略",
    "写一篇关于618大促的商品推广文案",
    "比较iPhone 16和华为Mate 70的优劣势",
    "制定一个新品发布的完整营销方案",
    "分析用户投诉数据，找出最关键的产品问题",
    "预测今年双十一的消费热点",
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


# ── 任务创建者（~90%）───────────────────────────────
class TaskCreatorUser(HttpUser):
    """模拟用户：登录 → 查看Agent → 创建任务(SSE流式) → 查看结果 → 删除"""

    wait_time = between(5, 15)  # 较长间隔，因为SSE任务耗时久
    weight = 18

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.created_task_ids = []

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

    @tag("smoke")
    @task(1)
    def list_agents(self):
        """查看Agent列表"""
        if not self.token:
            return
        self.client.get("/api/agent/agents", name="GET /api/agent/agents",
                        catch_response=True)

    @tag("smoke", "load", "stress")
    @task(3)
    def create_task_stream(self):
        """核心：SSE流式任务执行（多Agent编排）"""
        if not self.token:
            return
        mode = random.choice(TASK_MODES)
        description = random.choice(TASK_DESCRIPTIONS)
        # 使用SSE端点
        url = f"{self.client.base_url}/api/agent/tasks/stream"
        try:
            resp = requests.post(
                url,
                json={
                    "title": f"压测-{random.randint(1, 9999)}",
                    "description": description,
                    "mode": mode,
                },
                headers=self.client.headers,
                stream=True,
                timeout=(10, 120),  # 多Agent执行可能很慢
            )
            task_id = None
            if resp.status_code in (200, 201):
                for line in resp.iter_lines(decode_unicode=True):
                    if line and "task_id" in line.lower():
                        try:
                            data = json.loads(line.replace("data: ", ""))
                            task_id = data.get("task_id", "")
                            if task_id:
                                self.created_task_ids.append(task_id)
                        except (json.JSONDecodeError, AttributeError):
                            pass
                    if line and "data: [DONE]" in line:
                        break
            with self.client.post(
                "/api/agent/tasks/stream",
                json={"title": "压测", "description": description, "mode": mode},
                name="POST /api/agent/tasks/stream (SSE)", catch_response=True,
            ) as rec:
                if resp.status_code in (200, 201):
                    rec.success()
                else:
                    rec.failure(f"状态码: {resp.status_code}")
        except Exception as e:
            with self.client.post(
                "/api/agent/tasks/stream",
                json={"title": "压测", "description": description, "mode": mode},
                name="POST /api/agent/tasks/stream (SSE)", catch_response=True,
            ) as rec:
                rec.failure(f"SSE异常: {str(e)[:80]}")

    @tag("smoke", "load")
    @task(2)
    def list_tasks(self):
        if not self.token:
            return
        self.client.get("/api/agent/tasks", name="GET /api/agent/tasks",
                        catch_response=True)

    @tag("smoke")
    @task(1)
    def dashboard(self):
        if not self.token:
            return
        self.client.get("/api/agent/dashboard",
                        name="GET /api/agent/dashboard", catch_response=True)

    @tag("mutation")
    @task(1)
    def delete_task(self):
        """删除任务（清理测试数据）"""
        if not self.token or not self.created_task_ids:
            return
        task_id = self.created_task_ids.pop(0)
        self.client.delete(
            f"/api/agent/tasks/{task_id}",
            name="DELETE /api/agent/tasks/:id", catch_response=True,
        )

    @tag("smoke")
    @task(1)
    def get_me(self):
        if not self.token:
            return
        self.client.get("/api/auth/me", name="GET /api/auth/me", catch_response=True)

    @tag("load")
    @task(1)
    def sync_create_task(self):
        """同步创建任务（非流式，快速测试）"""
        if not self.token:
            return
        mode = random.choice(TASK_MODES)
        description = random.choice(TASK_DESCRIPTIONS)
        self.client.post(
            "/api/agent/tasks",
            json={
                "title": f"快速任务-{random.randint(1, 9999)}",
                "description": description,
                "mode": mode,
            },
            name="POST /api/agent/tasks (sync)", catch_response=True,
        )


# ── 管理员（~10%，含seed初始化）───────────────────
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

    @tag("smoke")
    @task(1)
    def seed_agents(self):
        """初始化默认Agent（幂等）"""
        self.client.post("/api/agent/agents/seed",
                         name="POST /api/agent/agents/seed", catch_response=True)

    @tag("smoke", "load")
    @task(2)
    def view_dashboard(self):
        self.client.get("/api/admin/dashboard", name="GET /api/admin/dashboard",
                        catch_response=True)

    @tag("smoke")
    @task(1)
    def view_users(self):
        self.client.get("/api/admin/users", name="GET /api/admin/users",
                        catch_response=True)
