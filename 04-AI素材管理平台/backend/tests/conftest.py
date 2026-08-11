"""Pytest fixtures: test database + HTTP client."""
import os, sys, pytest, asyncio, shutil
from httpx import AsyncClient, ASGITransport

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/_test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "false"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.session import init_db, AsyncSessionLocal
from app.services.auth_service import seed_admin_user


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """Async HTTP test client with fresh DB for each test."""
    # Ensure data dir exists (CI may not have it)
    test_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "_test.db")
    os.makedirs(os.path.dirname(test_db), exist_ok=True)
    # Delete old test DB to ensure clean state
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_admin_user(db)
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # Cleanup: dispose engine and delete test DB
    from app.db.session import engine
    await engine.dispose()
    test_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "_test.db")
    if os.path.exists(test_db):
        try: os.remove(test_db)
    
    # Ensure data dir exists (CI may not have it)
    os.makedirs(os.path.dirname(test_db), exist_ok=True)
        except: pass


@pytest.fixture
async def admin_token(client):
    resp = await client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
async def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
