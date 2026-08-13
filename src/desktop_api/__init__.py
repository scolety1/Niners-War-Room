"""Authenticated loopback HTTP adapter for the Niners War Room desktop app."""

from src.desktop_api.server import (
    BODY_LIMIT_BYTES,
    DesktopApiServer,
    create_desktop_api_server,
    validate_bind_host,
    validate_token,
)

__all__ = (
    "BODY_LIMIT_BYTES",
    "DesktopApiServer",
    "create_desktop_api_server",
    "validate_bind_host",
    "validate_token",
)
