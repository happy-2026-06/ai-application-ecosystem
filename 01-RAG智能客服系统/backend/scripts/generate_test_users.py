"""
生成压力测试用户
=================
用法: python scripts/generate_test_users.py [--count 100]

输出: data/test_users.json（Locust 压测脚本自动读取）
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

# 确保能找到项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE = "http://localhost:8101/api"
PASSWORD = "test123456"
OUTPUT = Path(__file__).parent.parent / "data" / "test_users.json"


async def generate(count: int = 100):
    """通过 API 批量注册测试用户"""
    users = []
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        for i in range(1, count + 1):
            username = f"testuser_{i:04d}"
            display_name = f"压测用户{i}"

            # 先注册
            try:
                r = await client.post("/auth/register", json={
                    "username": username,
                    "password": PASSWORD,
                    "display_name": display_name,
                })
                if r.status_code in (201, 409):  # 201=新建, 409=已存在
                    users.append({"username": username, "password": PASSWORD})
                    status = "新建" if r.status_code == 201 else "已存在"
                    print(f"  [{i:3d}/{count}] {username}  {status}")
                else:
                    print(f"  [{i:3d}/{count}] {username}  失败 (HTTP {r.status_code})")
            except httpx.ConnectError:
                print("\n❌ 无法连接后端，请先启动: python -m uvicorn app.main:app --port 8101")
                return
            except Exception as e:
                print(f"  [{i:3d}/{count}] {username}  错误: {e}")

    # 写入 JSON
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] 已生成 {len(users)} 个测试用户 -> {OUTPUT}")


if __name__ == "__main__":
    count = 100
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--count" and i + 1 < len(sys.argv):
                count = int(sys.argv[i + 1])
    print(f"正在生成 {count} 个测试用户...\n")
    asyncio.run(generate(count))
