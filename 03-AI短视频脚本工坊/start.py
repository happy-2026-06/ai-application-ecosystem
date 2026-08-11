"""项目③独立启动器 — 视界短视频工坊

被 start.bat 调用，负责清理 + 启动前后端服务。
"""
import subprocess, sys, os, time, socket, glob, sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE, "backend")
FRONTEND = os.path.join(BASE, "frontend")


def main():
    print()
    print("=" * 45)
    print("  视界短视频工坊 v2.0")
    print("  分镜脚本 + 口播话术生成")
    print("=" * 45)

    # ── Phase 1: 清理 ──────────────────────────
    print("\n[1/3] 清理残留...")

    for port in (8000, 3000):
        try:
            r = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=10
            )
            for line in r.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(["taskkill", "/f", "/pid", pid], capture_output=True)
        except Exception:
            pass

    data_dir = os.path.join(BACKEND, "data")
    if os.path.isdir(data_dir):
        for pat in ("*.db-wal", "*.db-shm"):
            for f in glob.glob(os.path.join(data_dir, pat)):
                for _ in range(5):
                    try:
                        os.remove(f)
                        break
                    except OSError:
                        time.sleep(1)
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

    for root, dirs, _ in os.walk(BACKEND):
        for d in dirs:
            if d == "__pycache__":
                try:
                    import shutil
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                except Exception:
                    pass

    print("    [OK]")

    # ── Phase 2: 前端依赖 ──────────────────────
    print("\n[2/3] 检查前端依赖...")
    nm = os.path.join(FRONTEND, "node_modules")
    if not os.path.isdir(nm):
        print("    [?] 首次安装（仅一次，之后秒开）...")
        subprocess.run(["npm", "install"], cwd=FRONTEND, capture_output=True, timeout=120)
    print("    [OK]")

    # ── Phase 3: 启动服务 ──────────────────────
    print("\n[3/3] 启动服务...")

    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND,
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("    → 后端 (8000)")

    # npx 是 .cmd 批处理，Windows 下必须用 cmd /c 包装
    if sys.platform == "win32":
        subprocess.Popen(
            ["cmd", "/c", "npx", "vite", "--host", "0.0.0.0", "--port", "3000"],
            cwd=FRONTEND,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"],
            cwd=FRONTEND,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print("    → 前端 (3000)")

    # ── 等待就绪 ────────────────────────────────
    print("\n[?] 等待后端就绪（最多90秒）...")
    for i in range(45):
        time.sleep(2)
        try:
            s = socket.socket()
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", 8000)) == 0:
                s.close()
                print()
                print("=" * 45)
                print("  启动成功!")
                print("  前端: http://127.0.0.1:3000")
                print("  后端: http://127.0.0.1:8000/docs")
                print("=" * 45)
                print()

                if sys.platform == "win32":
                    os.startfile("http://127.0.0.1:3000")
                break
            s.close()
        except Exception:
            pass
    else:
        print("\n[X] 启动超时！请查看后台窗口是否有报错。")
        return

    time.sleep(3)


if __name__ == "__main__":
    main()
