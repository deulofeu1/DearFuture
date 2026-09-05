from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, build_engine, get_db
from app.main import create_app


@pytest.fixture
def db(tmp_path) -> Generator[Session, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db: Session, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("app.graph.plan_with_model", lambda _question, _check_at: None)
    application = create_app(initialize_database=False)

    def override_db():
        yield db

    application.dependency_overrides[get_db] = override_db
    with TestClient(application) as test_client:
        yield test_client
