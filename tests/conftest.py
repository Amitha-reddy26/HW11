import subprocess
import time
import logging
import os
from typing import Generator, Dict, List
from contextlib import contextmanager

import pytest
import requests
from faker import Faker
from playwright.sync_api import sync_playwright, Browser, Page
from sqlalchemy.orm import Session

from app.database import Base, get_engine, get_sessionmaker
from app.models.user import User
from app.config import settings
from app.database_init import init_db, drop_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(12345)

logger.info(f"Using database URL: {settings.DATABASE_URL}")

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)


def create_fake_user() -> Dict[str, str]:
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12)
    }


@contextmanager
def managed_db_session():
    session = TestingSessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def wait_for_server(url: str, timeout: int = 30) -> bool:
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False


class ServerStartupError(Exception):
    pass


# ------------------------------------------------------
# FIX: Run python main.py from PROJECT ROOT, not /tests/
# ------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_test_database(request):
    logger.info("Setting up test database...")
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    init_db()
    logger.info("Database initialized.")
    yield
    if request.config.getoption("--preserve-db"):
        logger.info("Skipping DB cleanup (preserve-db).")
    else:
        drop_db()
        logger.info("Dropped test database tables.")


@pytest.fixture(scope="session")
def fastapi_server():
    server_url = "http://127.0.0.1:8000/"
    logger.info("Starting test server...")

    # FIX: Determine project root (one level above /tests)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        process = subprocess.Popen(
            ["python", "main.py"],
            cwd=project_root,            # ⭐ critical fix
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if not wait_for_server(server_url):
            raise ServerStartupError("Failed to start test server")

        logger.info("Test server started successfully.")
        yield

    finally:
        logger.info("Terminating test server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            logger.info("Test server terminated.")
        except subprocess.TimeoutExpired:
            logger.warning("Force killing test server.")
            process.kill()


@pytest.fixture
def db_session(request) -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        if not request.config.getoption("--preserve-db"):
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        session.close()


@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    return create_fake_user()


@pytest.fixture
def test_user(db_session: Session) -> User:
    data = create_fake_user()
    user = User(**data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_users(db_session: Session, request) -> List[User]:
    num = getattr(request, "param", 5)
    users = []
    for _ in range(num):
        data = create_fake_user()
        user = User(**data)
        users.append(user)
        db_session.add(user)
    db_session.commit()
    return users


@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser_context: Browser):
    context = browser_context.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()


def pytest_addoption(parser):
    parser.addoption("--preserve-db", action="store_true", default=False)
    parser.addoption("--run-slow", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip)
