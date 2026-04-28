import pytest
from app import app as flask_app
from database.db import init_db, seed_db, reset_db

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['DATABASE'] = ':memory:'
    init_db(flask_app)
    seed_db(flask_app)
    yield flask_app
    reset_db(flask_app)

@pytest.fixture
def client(app):
    return app.test_client()
