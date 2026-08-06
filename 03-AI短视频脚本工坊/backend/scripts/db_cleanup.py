"""Clean up SQLite WAL/SHM lock files left by abnormal shutdown.

Windows 强制关机/断电后，SQLite WAL 模式的 .db-wal 和 .db-shm 文件会残留在磁盘上。
本脚本在启动时删除这些残留文件，然后确保数据库保持 WAL 模式。
"""
import os
import glob as _glob
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def cleanup():
    if not os.path.isdir(DATA_DIR):
        return

    # Step 1: 删除残留的 WAL/SHM 锁文件
    for pat in ("*.db-wal", "*.db-shm"):
        for f in _glob.glob(os.path.join(DATA_DIR, pat)):
            for _ in range(5):
                try:
                    os.remove(f)
                    break
                except OSError:
                    time.sleep(1)

    # Step 2: 遍历所有 .db 文件，确保 WAL 模式 + 修复损坏
    for f in os.listdir(DATA_DIR):
        if not f.endswith(".db"):
            continue
        fp = os.path.join(DATA_DIR, f)

        # 删除空文件
        if os.path.getsize(fp) == 0:
            os.remove(fp)
            continue

        for _ in range(5):
            try:
                conn = sqlite3.connect(fp, timeout=10)
                # ⚠️ 保持 WAL 模式（不切 DELETE！）
                # WAL 提供更好的读写并发性能
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA busy_timeout=5000")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError:
                time.sleep(1)


if __name__ == "__main__":
    cleanup()
    print("OK")
