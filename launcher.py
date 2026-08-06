"""
AI应用项目统一启动器 v3.0
双击 start-all.bat → 调用本脚本 → 6个服务全部启动 → 浏览器自动打开

优点：纯 Python，完全免疫 cmd.exe 中文路径/嵌套引号/编码问题
"""

import subprocess
import sys
import os
import time
import socket
import glob as _glob
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════
# 服务定义
# ═══════════════════════════════════════════════════════
SERVICES = [
    # (名称, 工作目录相对路径, 启动方式("python"|"npx"), 启动参数, 检测端口, 需要db_cleanup)
    ("P1-Backend",  r"01-RAG智能客服系统\backend",  "python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8101"], 8101, True),
    ("P1-Frontend", r"01-RAG智能客服系统\frontend", "npx",    ["vite", "--host", "0.0.0.0", "--port", "3001"], 3001, False),
    ("P2-Backend",  r"02-AI自媒体内容助手\backend",  "python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8202"], 8202, True),
    ("P2-Frontend", r"02-AI自媒体内容助手\frontend", "npx",    ["vite", "--host", "0.0.0.0", "--port", "3002"], 3002, False),
    ("P3-Backend",  r"03-AI短视频脚本工坊\backend",  "python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], 8000, True),
    ("P3-Frontend", r"03-AI短视频脚本工坊\frontend", "npx",    ["vite", "--host", "0.0.0.0", "--port", "3000"], 3000, False),
]

FRONTEND_URLS = [
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3000",
]

# ═══════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════

def print_header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}")


def is_port_open(port: int) -> bool:
    """检查 TCP 端口是否在监听"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except Exception:
        return False


def kill_port(port: int):
    """杀掉占用某端口的进程"""
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.run(
                    ["taskkill", "/f", "/pid", pid],
                    capture_output=True, timeout=10
                )
    except Exception:
        pass


def db_cleanup(project_dir: str):
    """清理 SQLite WAL/SHM 残留锁文件"""
    data_dir = os.path.join(BASE_DIR, project_dir, "data")
    if not os.path.isdir(data_dir):
        return

    # 删除 WAL/SHM 残留
    for pat in ("*.db-wal", "*.db-shm"):
        for f in _glob.glob(os.path.join(data_dir, pat)):
            for _ in range(5):
                try:
                    os.remove(f)
                    break
                except OSError:
                    time.sleep(1)

    # 清理空的 .db 文件，确保 WAL 模式
    for f in os.listdir(data_dir):
        if not f.endswith(".db"):
            continue
        fp = os.path.join(data_dir, f)
        if os.path.getsize(fp) == 0:
            os.remove(fp)
            continue
        for _ in range(5):
            try:
                conn = sqlite3.connect(fp, timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA busy_timeout=5000")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError:
                time.sleep(1)


def install_frontend_deps(project_dir: str):
    """如果没装过前端依赖，安装一次"""
    frontend_dir = os.path.join(BASE_DIR, project_dir)
    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.isdir(node_modules):
        print(f"    [?] {project_dir.split(chr(92))[0]} 首次安装前端依赖（仅一次）...")
        subprocess.run(
            ["npm", "install"],
            cwd=frontend_dir,
            capture_output=True,
            timeout=120,
        )


def start_service(name: str, workdir: str, launcher: str, args: list):
    """启动一个服务（后台进程，最小化窗口）

    在 Windows 上：
    - python 后端：用 sys.executable 确保找到正确的 Python
    - npx 前端：npx 是 .cmd 脚本，必须用 shell=True 或 cmd /c 包装
    """
    full_path = os.path.join(BASE_DIR, workdir)

    if sys.platform == "win32":
        if launcher == "python":
            cmd = [sys.executable] + args
        elif launcher == "npx":
            # npx 是 .cmd 批处理文件，CreateProcess 无法直接执行
            # 必须用 cmd /c 包装
            cmd = ["cmd", "/c", "npx"] + args
        else:
            cmd = [launcher] + args

        subprocess.Popen(
            cmd,
            cwd=full_path,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        cmd = [launcher] + args
        subprocess.Popen(
            cmd,
            cwd=full_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


# ═══════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════

def main():
    print_header("AI项目一键启动 v3.0")

    # ── Phase 1: 清理 ──────────────────────────────
    print("\n[1/4] 清理上次关机残留...")

    for _, _, _, _, port, needs_cleanup in SERVICES:
        kill_port(port)

    cleaned = set()
    for _, workdir, _, _, port, needs_cleanup in SERVICES:
        if needs_cleanup:
            # 提取项目目录名 (如 "01-RAG智能客服系统")
            proj = workdir.split(os.sep)[0]
            if proj not in cleaned:
                db_cleanup(proj)
                cleaned.add(proj)

    # 清理 __pycache__
    for root, dirs, _ in os.walk(BASE_DIR):
        for d in dirs:
            if d == "__pycache__":
                cache_path = os.path.join(root, d)
                try:
                    import shutil
                    shutil.rmtree(cache_path, ignore_errors=True)
                except Exception:
                    pass

    print("    [OK] 清理完成")

    # ── Phase 2: 前端依赖 ──────────────────────────
    print("\n[2/4] 检查前端依赖...")
    frontend_dirs = set()
    for _, workdir, _, _, _, _ in SERVICES:
        if "frontend" in workdir:
            proj = workdir.split(os.sep)[0] + os.sep + "frontend"
            if proj not in frontend_dirs:
                install_frontend_deps(proj)
                frontend_dirs.add(proj)
    print("    [OK] 依赖就绪")

    # ── Phase 3: 启动服务 ──────────────────────────
    print("\n[3/4] 启动 6 个服务...")
    for name, workdir, launcher, args, port, _ in SERVICES:
        start_service(name, workdir, launcher, args)
        print(f"    → {name} ({port})")
        time.sleep(0.3)  # 错开启动，减少瞬间负载

    # ── Phase 4: 等待就绪 ──────────────────────────
    print("\n[4/4] 等待服务就绪（最多90秒）...")
    backend_ports = [p for name, _, _, _, p, _ in SERVICES if "Backend" in name]
    max_wait = 90
    waited = 0
    while waited < max_wait:
        time.sleep(2)
        waited += 2
        ok_count = sum(1 for p in backend_ports if is_port_open(p))
        print(f"\r    等待中... {ok_count}/{len(backend_ports)} 就绪 ({waited}s)", end="")
        if ok_count == len(backend_ports):
            break

    print()

    # ── 结果 ────────────────────────────────────────
    all_ok = all(is_port_open(p) for name, _, _, _, p, _ in SERVICES if "Backend" in name)
    if all_ok:
        print_header("全部启动完成!")
        for url in FRONTEND_URLS:
            print(f"  → {url}")
        print()

        # 打开浏览器
        for url in FRONTEND_URLS:
            if sys.platform == "win32":
                os.startfile(url)  # type: ignore
            else:
                subprocess.Popen(["open", url])
            time.sleep(0.5)
    else:
        print("\n[WARN] 部分服务启动较慢，请稍后再试或查看日志")

    # ── 启动守护进程 ────────────────────────────────
    print("\n启动后台守护进程 (guardian.py)...")
    guardian_path = os.path.join(BASE_DIR, "guardian.py")
    if os.path.isfile(guardian_path):
        if sys.platform == "win32":
            subprocess.Popen(
                [sys.executable, guardian_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        print("    [OK] 守护已启动（每30秒自动检测，挂了自动恢复）")

    print("\n提示: 关闭此窗口不影响服务运行。\n")
    input("按 Enter 退出...")


if __name__ == "__main__":
    main()
