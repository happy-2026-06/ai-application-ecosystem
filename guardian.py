"""
AI 项目后台守护进程 — Guardian v1.0
每30秒巡检全部6个服务，挂了自动拉起。
Windows 关机后的 WAL 锁文件自动清理。
"""

import subprocess
import time
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICES = [
    # (名称, 工作目录, 启动方式"python"|"npx", 启动参数, 检测端口, 是否需要db_cleanup)
    ("P1-Backend",  os.path.join(BASE_DIR, r"01-RAG智能客服系统\backend"),  "python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8101"], 8101, True),
    ("P1-Frontend", os.path.join(BASE_DIR, r"01-RAG智能客服系统\frontend"), "npx",    ["vite", "--host", "0.0.0.0", "--port", "3001"], 3001, False),
    ("P2-Backend",  os.path.join(BASE_DIR, r"02-AI自媒体内容助手\backend"),  "python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8202"], 8202, True),
    ("P2-Frontend", os.path.join(BASE_DIR, r"02-AI自媒体内容助手\frontend"), "npx",    ["vite", "--host", "0.0.0.0", "--port", "3002"], 3002, False),
    ("P3-Backend",  os.path.join(BASE_DIR, r"03-AI短视频脚本工坊\backend"),  "python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], 8000, True),
    ("P3-Frontend", os.path.join(BASE_DIR, r"03-AI短视频脚本工坊\frontend"), "npx",    ["vite", "--host", "0.0.0.0", "--port", "3000"], 3000, False),
]

PROJECT_DB_CLEANUP = {
    8101: r"01-RAG智能客服系统\backend\scripts\db_cleanup.py",
    8202: r"02-AI自媒体内容助手\backend\scripts\db_cleanup.py",
    8000: r"03-AI短视频脚本工坊\backend\scripts\db_cleanup.py",
}


def is_port_listening(port: int) -> bool:
    """检查端口是否在监听"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except Exception:
        return False


def run_db_cleanup(port: int):
    """清理对应项目的数据库残留"""
    script_path = PROJECT_DB_CLEANUP.get(port)
    if not script_path:
        return
    full_path = os.path.join(BASE_DIR, script_path)
    if os.path.isfile(full_path):
        try:
            subprocess.run(
                ["python", full_path],
                capture_output=True,
                timeout=15,
            )
        except Exception:
            pass


def restart_service(name: str, workdir: str, launcher: str, args: list, port: int, needs_cleanup: bool):
    """重启一个服务"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] ↻ {name} 挂了 → 自动重启…")

    if needs_cleanup:
        run_db_cleanup(port)

    # 构建命令 — npx 是 .cmd 文件，Windows 下必须用 cmd /c 包装
    if sys.platform == "win32":
        if launcher == "python":
            cmd = [sys.executable] + args
        elif launcher == "npx":
            cmd = ["cmd", "/c", "npx"] + args
        else:
            cmd = [launcher] + args
    else:
        cmd = [launcher] + args

    try:
        subprocess.Popen(
            cmd,
            cwd=workdir,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            if sys.platform == "win32"
            else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] ✗ {name} 重启失败: {e}")


def main():
    print("=" * 60)
    print(f"  Guardian v1.0  启动于 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("  守护 6 个服务，每30秒巡检一次")
    print("=" * 60)

    fail_count = {}
    consecutive_ok = 0

    while True:
        all_ok = True

        for name, workdir, launcher, args, port, needs_cleanup in SERVICES:
            if not is_port_listening(port):
                all_ok = False
                fail_count[name] = fail_count.get(name, 0) + 1

                if fail_count[name] <= 3:
                    # 前3次立即重试
                    restart_service(name, workdir, launcher, args, port, needs_cleanup)
                elif fail_count[name] % 6 == 0:
                    # 之后每3分钟重试一次（6次 × 30秒）
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] ⚠ {name} 已连续失败 {fail_count[name]} 次 ({fail_count[name]//2}分钟)，继续重试…")
                    restart_service(name, workdir, launcher, args, port, needs_cleanup)

        if all_ok:
            for k in list(fail_count.keys()):
                if fail_count.get(k, 0) > 0:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] ✓ {k} 已恢复")
            fail_count.clear()
            consecutive_ok += 1
            if consecutive_ok == 1 or consecutive_ok % 20 == 0:
                # 30秒一次太吵，每10分钟报告一次全绿
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] ✓ 全部正常 ({consecutive_ok * 30}s 无故障)")
        else:
            consecutive_ok = 0

        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n守护进程已停止。")
