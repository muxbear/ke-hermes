from dotenv import load_dotenv
from fastapi import FastAPI

from server import app


def test_app_instance():
    assert isinstance(app, FastAPI)
    assert app.title == "ke-hermes"


def test_routes_registered():
    routes = [r.path for r in app.routes]
    assert "/api/chat" in routes
    assert "/api/chat/stream" in routes


def test_load_dotenv_called():
    load_dotenv()