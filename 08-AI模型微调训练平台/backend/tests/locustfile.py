"""
⑧ 模型定制工厂 — 高并发压力测试
=========================================
业务场景: AI模型微调训练 + Smart Proxy推理
核心端点: 微调任务管理、模型部署、Smart Proxy推理、缓存统计

用法:
    locust -f tests/locustfile.py --host=http://localhost:8808
    locust -f tests/locustfile.py --host=http://localhost:8808 \
        --users=100 --spawn-rate=10 --run-time=5m \
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

# Smart Proxy 推理问题池（电商场景）
PROXY_QUESTIONS = [
    "退货怎么操作？需要什么条件？",
    "促销活动的优惠券怎么领取？",
    "这个手机电池续航多久？",
    "有哪些支付方式？可以分期吗？",
    "包裹寄错了地址怎么办？",
    "怎么修改订单收货地址？",
    "现在有什么满减活动？",
    "保修期内屏幕碎了怎么修？",
    "怎么查询物流信息？",
    "可以指定快递公司配送吗？",
]

# 微调任务配置
TASK_CONFIGS = [
    {"name": "qwen2-7b-customer-service", "base_model": "deepseek-chat",
     "dataset_id": "客服FAQ数据集"},
    {"name": "qwen2-7b-sales-script", "base_model": "deepseek-chat",
     "dataset_id": "销售话术语料"},
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


# ── 模型使用者（~85%）───────────────────────────────
class ModelUser(HttpUser):
    """模拟外部项目用户：登录 → 查模型 → Smart Proxy推理"""

    wait_time = between(3, 8)
    weight = 17

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.model_id = None
        self._fetched_models = False

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
    def list_active_models(self):
        """查看已部署的模型（跨项目发现），同时缓存 model_id 供 proxy 用"""
        if not self.token:
            return
        with self.client.get("/api/finetune/models/active",
                             name="GET /api/finetune/models/active",
                             catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    self.model_id = data[0].get("id", "")
                r.success()

    @tag("smoke", "load", "stress")
    @task(5)
    def smart_proxy_inference(self):
        """核心：Smart Proxy 三层推理（意图路由+Few-shot+缓存）"""
        if not self.token:
            return
        # 如果还没有 model_id，先查询活跃模型
        if not self.model_id:
            with self.client.get("/api/finetune/models/active",
                                 name="GET /api/finetune/models/active",
                                 catch_response=True) as r:
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list) and data:
                        self.model_id = data[0].get("id", "")
                        r.success()
                if not self.model_id:
                    return  # 没有可用模型，跳过 proxy 调用

        question = random.choice(PROXY_QUESTIONS)
        url = f"{self.client.base_url}/api/finetune/models/{self.model_id}/proxy"
        try:
            resp = requests.post(
                url,
                json={"message": question, "stream": False},
                headers=self.client.headers,
                timeout=(10, 60),
            )
            with self.client.post(
                f"/api/finetune/models/{self.model_id}/proxy",
                json={"message": question},
                name="POST /api/finetune/models/:id/proxy",
                catch_response=True,
            ) as rec:
                if resp.status_code == 200:
                    rec.success()
                else:
                    rec.failure(f"Proxy状态码: {resp.status_code}")
        except Exception as e:
            with self.client.post(
                f"/api/finetune/models/{self.model_id}/proxy",
                json={"message": question},
                name="POST /api/finetune/models/:id/proxy",
                catch_response=True,
            ) as rec:
                rec.failure(f"异常: {str(e)[:80]}")

    @tag("smoke")
    @task(1)
    def cache_stats(self):
        """查看缓存统计"""
        if not self.token:
            return
        self.client.get("/api/finetune/models/cache-stats",
                        name="GET /api/finetune/models/cache-stats",
                        catch_response=True)

    @tag("mutation")
    @task(1)
    def clear_cache(self):
        """清除缓存"""
        if not self.token:
            return
        self.client.post("/api/finetune/models/cache-clear",
                         name="POST /api/finetune/models/cache-clear",
                         catch_response=True)

    @tag("smoke")
    @task(1)
    def dashboard(self):
        if not self.token:
            return
        self.client.get("/api/finetune/dashboard",
                        name="GET /api/finetune/dashboard", catch_response=True)


# ── 训练操作员（~15%）───────────────────────────────
class TrainingOperatorUser(HttpUser):
    """模拟训练操作员：创建任务 → 查看进度 → 部署模型"""

    wait_time = between(5, 15)
    weight = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.task_id = None

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
    @task(2)
    def create_finetune_task(self):
        """创建微调任务"""
        if not self.token:
            return
        config = random.choice(TASK_CONFIGS)
        with self.client.post(
            "/api/finetune/tasks",
            json=config,
            name="POST /api/finetune/tasks", catch_response=True,
        ) as r:
            if r.status_code in (200, 201):
                self.task_id = r.json().get("id", "")
                r.success()

    @tag("smoke", "load")
    @task(2)
    def list_finetune_tasks(self):
        if not self.token:
            return
        self.client.get("/api/finetune/tasks",
                        name="GET /api/finetune/tasks", catch_response=True)

    @tag("load")
    @task(1)
    def check_task_status(self):
        """轮询任务状态"""
        if not self.token or not self.task_id:
            return
        self.client.get(
            f"/api/finetune/tasks/{self.task_id}",
            name="GET /api/finetune/tasks/:id", catch_response=True,
        )

    @tag("load")
    @task(1)
    def list_task_models(self):
        """查看任务模型版本"""
        if not self.token or not self.task_id:
            return
        self.client.get(
            f"/api/finetune/tasks/{self.task_id}/models",
            name="GET /api/finetune/tasks/:id/models", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def deploy_model(self):
        """部署模型：先取任务下的模型版本ID，再PATCH部署"""
        if not self.token or not self.task_id:
            return
        # 部署接口需要 model_id 而不是 task_id，先查任务下的模型版本
        model_id = None
        with self.client.get(
            f"/api/finetune/tasks/{self.task_id}/models",
            name="GET /api/finetune/tasks/:id/models", catch_response=True,
        ) as r:
            if r.status_code == 200:
                models = r.json()
                if isinstance(models, list) and models:
                    model_id = models[0].get("id", "")
                    r.success()
                else:
                    r.failure(f"任务 {self.task_id} 下暂无模型版本")
            else:
                r.failure(f"获取模型列表失败: {r.status_code}")
        if not model_id:
            return
        self.client.patch(
            f"/api/finetune/models/{model_id}/deploy",
            name="PATCH /api/finetune/models/:id/deploy", catch_response=True,
        )
