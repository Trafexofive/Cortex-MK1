"""Container orchestrator API routes."""

from .tools import router as tools_router
from .relics import router as relics_router
from .stats import router as stats_router
from .cleanup import router as cleanup_router

__all__ = [
    "tools_router",
    "relics_router",
    "stats_router",
    "cleanup_router"
]
