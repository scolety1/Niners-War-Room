"""Framework-neutral application facade for Niners War Room."""

from src.application.contracts import CONTRACT_VERSION, contract_envelope
from src.application.desktop_facade import DesktopBackendFacade, FacadeError, FacadePayload

__all__ = (
    "CONTRACT_VERSION",
    "DesktopBackendFacade",
    "FacadeError",
    "FacadePayload",
    "contract_envelope",
)
