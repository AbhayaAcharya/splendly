import os
import tempfile
import pytest
from app import app as flask_app
from database.db import init_db, seed_db

@pytest.fixture
def app():
    _, db_path = tempfile.mkstemp(suffix='.db')
    flask_app.config['TESTING'] = True
    flask_app.config['DATABASE'] = db_path
    init_db(flask_app)
    seed_db(flask_app)
    yield flask_app
    flask_app.config.pop('DATABASE', None)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()
