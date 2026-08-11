"""
① 智能客服助手 — 高并发压力测试
=========================================
业务场景: 电商客服 RAG 问答
核心端点: ask(SSE流式)、知识库上传/检索、转人工、管理后台

用法:
    locust -f tests/locustfile.py --host=http://localhost:8101
    浏览器打开 http://localhost:8089

无 UI 模式:
    locust -f tests/locustfile.py --host=http://localhost:8101 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html

标签筛选:
    locust -f tests/locustfile.py --host=http://localhost:8101 --tags smoke
    locust -f tests/locustfile.py --host=http://localhost:8101 --tags load
"""

import json
import os
import random
from pathlib import Path

import requests
from locust import HttpUser, between, constant, events, tag, task

# ── 电商客服问题池 ────────────────────────────────
ECOMMERCE_QUESTIONS = [
    # 退货退款
    "我买的衣服不合适怎么退货？", "退货流程需要多长时间？", "退款什么时候到账？",
    "七天无理由退货怎么申请？", "退货包运费吗？", "换货和退货有什么区别？",
    "已经拆封的商品还能退吗？", "海外购商品怎么退货？", "退货需要原包装吗？",
    "退款是退到原支付方式吗？",
    # 促销活动
    "现在有什么优惠活动？", "双十一活动什么时候开始？", "优惠券怎么领取？",
    "满减活动可以叠加使用吗？", "新用户有什么优惠？", "会员积分怎么兑换？",
    "限时秒杀商品能退货吗？", "拼团活动怎么参与？",
    # 物流配送
    "什么时候能发货？", "可以指定快递公司吗？", "怎么查询物流信息？",
    "偏远地区包邮吗？", "加急配送要加多少钱？", "快递丢了怎么办？",
    "周末送货吗？", "可以修改收货地址吗？",
    # 产品参数
    "这个手机电池容量多大？", "这款电脑有多重？", "衣服是什么面料的？",
    "这个产品有什么颜色可选？", "保质期是多久？", "最大功率是多少？",
    "支持5G网络吗？", "多大尺寸的？",
    # 售后服务
    "保修期是多久？", "可以延长保修吗？", "屏幕碎了怎么修？",
    "售后电话是多少？", "配件丢了能单买吗？",
    # 订单管理
    "怎么取消订单？", "订单可以修改吗？", "如何查看历史订单？",
    "发票怎么开具？", "订单超时未支付会自动取消吗？",
    # 账户问题
    "怎么修改密码？", "账号被冻结了怎么办？", "如何注销账号？",
    "手机号变更了怎么修改？", "为什么登录不了？",
    # 支付问题
    "支持哪些支付方式？", "可以分期付款吗？", "支付失败怎么办？",
    "信用卡支付有手续费吗？", "可以用支付宝吗？",
]

# ── 测试用户池 ────────────────────────────────────
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
    target = (environment.parsed_options.num_users
              if environment.parsed_options and environment.parsed_options.num_users is not None
              else 100)
    if len(users) < target:
        print(f"\n[WARN] 测试用户不足！需要 {target} 个，当前只有 {len(users)} 个")
        print(f"   请先运行: python scripts/generate_test_users.py")
    else:
        print(f"\n[OK] 测试用户就绪：{len(users)} 个，目标并发 {target}\n")


@events.quitting.add_listener
def on_test_quitting(environment, **_kwargs):
    """压测结束后检查失败率，超过 5% 返回非零退出码"""
    stats = environment.stats.total
    if stats.num_requests > 0:
        fail_rate = stats.num_failures / stats.num_requests * 100
        print(f"\n[压测结束] 总请求: {stats.num_requests}, 失败率: {fail_rate:.1f}%")
        print(f"  P50: {stats.get_response_time_percentile(0.5):.0f}ms")
        print(f"  P95: {stats.get_response_time_percentile(0.95):.0f}ms")
        print(f"  P99: {stats.get_response_time_percentile(0.99):.0f}ms")
        if fail_rate > 5:
            print(f"\n[FAIL] 失败率 {fail_rate:.1f}% 超过 5% 阈值！")
            environment.process_exit_code = 1


# ── 客服用户（~90%）────────────────────────────────
class CustomerUser(HttpUser):
    """模拟电商客户：浏览会话 → 提问 → 反馈"""

    wait_time = between(3, 8)
    weight = 18

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.session_id = None

    def on_start(self):
        creds = next_user()
        if creds is None:
            return
        self._login_with_retry(creds)

    def _login_with_retry(self, creds, max_retries=3):
        """带重试的登录——SQLite 高并发下偶发 500，重试即可恢复"""
        for attempt in range(max_retries):
            with self.client.post(
                "/api/auth/login",
                json={"username": creds["username"], "password": creds["password"]},
                name="POST /api/auth/login",
                catch_response=True,
            ) as r:
                if r.status_code == 200:
                    self.token = r.json().get("access_token", "")
                    self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                    r.success()
                    return True
                elif r.status_code == 500 and attempt < max_retries - 1:
                    import time; time.sleep(0.5 * (attempt + 1))  # 递增延迟
                    continue
                else:
                    # 注册后重试登录
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
                        r.success()
                        return True
                    r.failure(f"登录失败(重试{attempt+1}次): {r2.status_code}")
                    return False

    @tag("smoke", "load", "stress")
    @task(6)
    def ask_question(self):
        """核心：电商问题 RAG 问答（SSE 流式）"""
        if not self.token:
            return
        if not self.session_id:
            with self.client.post(
                "/api/chat/sessions", json={"title": "客服咨询"},
                name="POST /api/chat/sessions", catch_response=True,
            ) as r:
                if r.status_code == 201:
                    self.session_id = r.json().get("id", "")
                    r.success()
                else:
                    r.failure(f"创建会话失败: {r.status_code}")
                    return

        question = random.choice(ECOMMERCE_QUESTIONS)
        url = f"{self.client.base_url}/api/chat/ask?session_id={self.session_id}"
        try:
            resp = requests.post(
                url, json={"question": question},
                headers=self.client.headers, stream=True,
                timeout=(10, 120),
            )
            if resp.status_code == 200:
                for line in resp.iter_lines(decode_unicode=True):
                    if line and line.startswith("data: [DONE]"):
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
    def send_feedback(self):
        """提交回答反馈"""
        if not self.token or not self.session_id:
            return
        self.client.post(
            "/api/chat/feedback",
            json={"session_id": self.session_id, "rating": random.choice([4, 5]),
                  "comment": "回答很准确"},
            name="POST /api/chat/feedback", catch_response=True,
        )

    @tag("mutation")
    @task(1)
    def escalate(self):
        """转人工客服"""
        if not self.token or not self.session_id:
            return
        self.client.post(
            "/api/chat/escalate",
            json={"session_id": self.session_id, "reason": "需要人工处理退货"},
            name="POST /api/chat/escalate", catch_response=True,
        )


# ── 管理员用户（~10%）──────────────────────────────
class AdminUser(HttpUser):
    """模拟管理员：仪表盘 → 知识库管理 → 文档上传"""

    wait_time = between(5, 15)
    weight = 2

    def on_start(self):
        with self.client.post(
            "/api/auth/login",
            json={"username": _admin_user, "password": _admin_pass},
            name="POST /api/auth/login (Admin)", catch_response=True,
        ) as r:
            if r.status_code == 200:
                self.token = r.json().get("access_token", "")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                r.success()
            else:
                r.failure(f"管理员登录失败: {r.status_code}")

    @tag("smoke", "load")
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/admin/dashboard", name="GET /api/admin/dashboard",
                        catch_response=True)

    @tag("smoke", "load")
    @task(2)
    def view_documents(self):
        self.client.get("/api/kb/documents", name="GET /api/kb/documents",
                        catch_response=True)

    @tag("smoke")
    @task(1)
    def kb_stats(self):
        self.client.get("/api/kb/stats", name="GET /api/kb/stats",
                        catch_response=True)

    @tag("mutation")
    @task(1)
    def view_users(self):
        self.client.get("/api/admin/users", name="GET /api/admin/users",
                        catch_response=True)


# ── 突刺压测用户 ──────────────────────────────────
class SpikeUser(HttpUser):
    """模拟突发流量：每秒发一个请求（固定间隔压测）"""

    wait_time = constant(1)
    weight = 0  # 默认不启用，用 --tags spike 单独跑

    def on_start(self):
        creds = next_user()
        if creds is None:
            return
        r = self.client.post(
            "/api/auth/login",
            json={"username": creds["username"], "password": creds["password"]},
            name="POST /api/auth/login", catch_response=True,
        )
        if r.status_code == 200:
            self.token = r.json().get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @tag("spike")
    @task
    def rapid_ask(self):
        if not hasattr(self, "token") or not self.token:
            return
        question = random.choice(ECOMMERCE_QUESTIONS[:10])  # 前10个高频问题
        self.client.post(
            "/api/chat/ask", json={"question": question},
            params={"session_id": "spike-test"},
            name="POST /api/chat/ask (Spike)", catch_response=True,
        )
