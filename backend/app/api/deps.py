"""Shared objects the routes need, read from app.state (set up in app.main)."""

from fastapi import Request

from app.tinyfish import WebClient


def get_web(request: Request) -> WebClient:
    return request.app.state.web
