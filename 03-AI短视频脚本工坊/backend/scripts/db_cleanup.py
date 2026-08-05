"""Clean up SQLite WAL/SHM lock files left by abnormal shutdown."""
import os
import glob as _glob
import sqlite3
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def cleanup():
    if not os.path.isdir(DATA_DIR):
        return
    for pat in ("*.db-wal", "*.db-shm"):
        for f in _glob.glob(os.path.join(DATA_DIR, pat)):
            for _ in range(5):
                try:
                    os.remove(f)
                    break
                except OSError:
                    time.sleep(1)
    for f in os.listdir(DATA_DIR):
        if not f.endswith(".db"):
            continue
        fp = os.path.join(DATA_DIR, f)
        if os.path.getsize(fp) == 0:
            os.remove(fp)
            continue
        for _ in range(5):
            try:
                conn = sqlite3.connect(fp, timeout=10)
                conn.execute("PRAGMA journal_mode=DELETE")
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError:
                time.sleep(1)

if __name__ == "__main__":
    cleanup()
    print("OK")
