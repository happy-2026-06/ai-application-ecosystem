"""
RAG 知识库问答系统 — 压力测试脚本
=====================================
用法:
    locust -f tests/locustfile.py --host=http://localhost:8400
    浏览器打开 http://localhost:8089，输入用户数和增速，开始压测。

无 UI 模式:
    locust -f tests/locustfile.py --host=http://localhost:8400 \
        --users=100 --spawn-rate=10 --run-time=5m \
        --html=reports/stress-report.html
"""

import json
import os
import random
import sys
from pathlib import Path

import requests
from locust import HttpUser, between, events, task

# ── 问题池 ──────────────────────────────────────────────
# 压测时每个用户随机抽取一个问题提问
QUESTIONS = [
    # 手机类
    "小米14的屏幕参数是什么？",
    "iPhone 15的摄像头像素是多少？",
    "华为Mate 60 Pro支持卫星通信吗？",
    "推荐一款适合玩原神的手机",
    "iPhone 15和小米14哪个拍照好？",
    "三星Galaxy S24有什么新功能？",
    "OPPO Find X7的充电功率是多少？",
    "哪款手机续航最长？",
    "5000mAh以上的手机有哪些？",
    "支持无线充电的手机推荐",
    "性价比最高的手机是哪款？",
    "适合老年人的大字体手机推荐",
    "哪个品牌的手机信号最好？",
    "折叠屏手机值得买吗？",
    "手机存储空间多大够用？",
    # 笔记本类
    "5000元以内的笔记本电脑推荐",
    "联想ThinkPad适合程序员用吗？",
    "MacBook Air和华为MateBook X Pro哪个好？",
    "适合打游戏的笔记本推荐",
    "笔记本电脑i5和i7差距大吗？",
    "学生党买什么笔记本性价比高？",
    "ROG笔记本的散热怎么样？",
    "轻薄本和游戏本怎么选？",
    "华为MateBook有什么特点？",
    "小米笔记本Pro的屏幕素质如何？",
    # 耳机类
    "蓝牙耳机怎么选？",
    "索尼WH-1000XM5降噪效果怎么样？",
    "AirPods Pro和华为FreeBuds Pro哪个好？",
    "适合跑步的运动耳机推荐",
    "200元以内的蓝牙耳机推荐",
    "入耳式和半入耳式耳机有什么区别？",
    "蓝牙耳机的延迟会影响玩游戏吗？",
    "无线耳机续航时间一般多长？",
    "降噪耳机对听力有保护作用吗？",
    "Type-C接口的耳机有哪些推荐？",
    # 智能手表类
    "智能手表和手环有什么区别？",
    "Apple Watch Series 9有什么新功能？",
    "华为Watch GT系列支持eSIM吗？",
    "适合游泳佩戴的智能手表",
    "智能手表能检测睡眠质量吗？",
    "小米手环和OPPO手环哪个准？",
    # 综合对比类
    "安卓和iOS系统哪个更适合办公？",
    "国产手机和苹果手机差距大吗？",
    "OLED屏幕和LCD屏幕有什么区别？",
    "Type-C接口都有哪些设备在用？",
    "什么手机最适合拍视频？",
    "预算3000元买手机还是买平板？",
]

# ── 测试用户池 ──────────────────────────────────────────
USERS_FILE = Path(__file__).parent.parent / "data" / "test_users.json"
_user_credentials = []
_user_index = 0


def load_users():
    """加载预生成的测试用户"""
    global _user_credentials
    if USERS_FILE.exists():
        _user_credentials = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        print(f"[OK] 已加载 {len(_user_credentials)} 个测试用户")
    return _user_credentials


def next_user():
    """轮询获取下一个测试用户（避免同一账号并发登录冲突）"""
    global _user_index
    if not _user_credentials:
        load_users()
    if not _user_credentials:
        return None
    u = _user_credentials[_user_index % len(_user_credentials)]
    _user_index += 1
    return u


# ── Locust 事件钩子 ─────────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    """压测开始前检查测试用户是否就绪"""
    users = load_users()
    target = environment.parsed_options.num_users if environment.parsed_options else 100
    if len(users) < target:
        print(f"\n[WARN] 测试用户不足！需要 {target} 个，当前只有 {len(users)} 个")
        print(f"   请先运行: python scripts/generate_test_users.py")
        print(f"   或者降低并发用户数: --users={len(users)}\n")
    else:
        print(f"\n[OK] 测试用户就绪：{len(users)} 个，目标并发 {target}\n")


# ── 普通用户（约占 95%）─────────────────────────────────
class RAGUser(HttpUser):
    """模拟普通用户：登录 → 查看会话 → 提问获取AI回复"""

    wait_time = between(3, 8)  # 模拟阅读/打字间隔
    weight = 19  # 权重 95%

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.session_id = None

    def on_start(self):
        """登录获取 JWT Token"""
        creds = next_user()
        if creds is None:
            print("[ERROR] 无可用测试用户，跳过")
            return

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
            else:
                # 用户可能不存在，尝试注册
                reg = self.client.post(
                    "/api/auth/register",
                    json={
                        "username": creds["username"],
                        "password": creds["password"],
                        "display_name": creds["username"],
                    },
                    name="POST /api/auth/register",
                )
                if reg.status_code in (201, 409):
                    # 注册成功或已存在，重试登录
                    r2 = self.client.post(
                        "/api/auth/login",
                        json={"username": creds["username"], "password": creds["password"]},
                        name="POST /api/auth/login",
                    )
                    if r2.status_code == 200:
                        self.token = r2.json().get("access_token", "")
                        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                        r.success()
                    else:
                        r.failure(f"登录失败: {r2.status_code}")
                else:
                    r.failure(f"注册+登录均失败: {r.status_code}")

    @task(5)
    def ask_question(self):
        """核心场景：提问并获取流式AI回复"""
        if not self.token:
            return

        # 如果没有会话，先创建一个
        if not self.session_id:
            with self.client.post(
                "/api/chat/sessions",
                json={"title": "压测会话"},
                name="POST /api/chat/sessions",
                catch_response=True,
            ) as r:
                if r.status_code == 201:
                    self.session_id = r.json().get("id", "")
                    r.success()
                else:
                    r.failure(f"创建会话失败: {r.status_code}")
                    return

        # 随机选一个问题
        question = random.choice(QUESTIONS)

        # SSE 流式请求 — 手动处理以测量完整响应时间
        url = f"{self.client.base_url}/api/chat/ask?session_id={self.session_id}"
        try:
            resp = requests.post(
                url,
                json={"question": question},
                headers=self.client.headers,
                stream=True,
                timeout=(10, 120),  # (connect, read)
            )
            if resp.status_code == 200:
                # 读取 SSE 流直到结束
                for line in resp.iter_lines(decode_unicode=True):
                    if line and line.startswith("data: [DONE]"):
                        break
            # 记录结果
            with self.client.post(
                "/api/chat/ask",
                json={"question": question},
                params={"session_id": self.session_id},
                name="POST /api/chat/ask (SSE)",
                catch_response=True,
            ) as r:
                if resp.status_code == 200:
                    r.success()
                else:
                    r.failure(f"状态码: {resp.status_code}")
        except Exception as e:
            with self.client.post(
                "/api/chat/ask",
                json={"question": question},
                params={"session_id": self.session_id},
                name="POST /api/chat/ask (SSE)",
                catch_response=True,
            ) as r:
                r.failure(f"异常: {str(e)[:80]}")

    @task(2)
    def list_sessions(self):
        """查看会话列表"""
        if not self.token:
            return
        with self.client.get(
            "/api/chat/sessions",
            name="GET /api/chat/sessions",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"{r.status_code}")

    @task(1)
    def create_session(self):
        """创建新会话"""
        if not self.token:
            return
        with self.client.post(
            "/api/chat/sessions",
            json={"title": f"会话-{random.randint(1,1000)}"},
            name="POST /api/chat/sessions",
            catch_response=True,
        ) as r:
            if r.status_code == 201:
                # 可选：替换当前会话
                self.session_id = r.json().get("id", self.session_id)
                r.success()
            else:
                r.failure(f"{r.status_code}")


# ── 管理员用户（约占 5%）─────────────────────────────────
class AdminUser(HttpUser):
    """模拟管理员：登录 → 查看仪表盘 → 浏览知识库"""

    wait_time = between(5, 15)
    weight = 1  # 权重 5%

    def on_start(self):
        with self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "123456"},
            name="POST /api/auth/login (Admin)",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                self.token = r.json().get("access_token", "")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                r.success()
            else:
                r.failure(f"管理员登录失败: {r.status_code}")

    @task(3)
    def view_dashboard(self):
        """查看管理仪表盘"""
        with self.client.get(
            "/api/admin/dashboard",
            name="GET /api/admin/dashboard",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"{r.status_code}")

    @task(2)
    def view_documents(self):
        """查看知识库文档列表"""
        with self.client.get(
            "/api/kb/documents",
            name="GET /api/kb/documents",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"{r.status_code}")

    @task(1)
    def view_users(self):
        """查看用户列表"""
        with self.client.get(
            "/api/admin/users",
            name="GET /api/admin/users",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"{r.status_code}")
