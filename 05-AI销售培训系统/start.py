"""项目⑤ 话术对战教练 — 本地启动脚本"""
import os
import sys
import subprocess
import time
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def check_port(port: int) -> bool:
    """Check if a port is already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def kill_port(port: int):
    """Kill process occupying a port (Windows only)."""
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in parts:
                pid = parts[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True,
                              capture_output=True)
                print(f"  [清理] 端口 {port} 已释放 (PID {pid})")
    except Exception:
        pass


def main():
    os.chdir(BASE_DIR)
    print("=" * 48)
    print("  项目⑤ — 话术对战教练")
    print(f"  后端: http://localhost:8505")
    print(f"  前端: http://localhost:3005")
    print("=" * 48)

    # Check dependencies
    backend_dir = os.path.join(BASE_DIR, "backend")
    frontend_dir = os.path.join(BASE_DIR, "frontend")

    if not os.path.isdir(backend_dir):
        print("[ERROR] backend 目录不存在！")
        sys.exit(1)
    if not os.path.isdir(frontend_dir):
        print("[ERROR] frontend 目录不存在！")
        sys.exit(1)

    # Clean ports
    print("\n[1/4] 清理端口...")
    kill_port(8505)
    kill_port(3005)

    # Clean SQLite WAL files
    try:
        data_dir = os.path.join(backend_dir, "data")
        if os.path.isdir(data_dir):
            for f in os.listdir(data_dir):
                if f.endswith(("-wal", "-shm")):
                    os.remove(os.path.join(data_dir, f))
                    print(f"  [清理] DB残留文件: {f}")
    except Exception:
        pass

    # Start backend
    print("\n[2/4] 启动后端 (端口 8505)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8505", "--reload"],
        cwd=backend_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )

    time.sleep(3)

    # Start frontend
    print("\n[3/4] 启动前端 (端口 3005)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )

    print("\n[4/4] ✅ 项目⑤启动完成！")
    print(f"  后端 API 文档: http://localhost:8505/api/docs")
    print(f"  前端页面:      http://localhost:3005")
    print(f"\n  Demo 账号: admin / ChangeMe!2024")
    print("  按 Ctrl+C 退出...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[关闭] 正在停止服务...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("[OK] 服务已停止")


if __name__ == "__main__":
    main()
