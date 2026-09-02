from app.routes.health import router as health_router
from app.routes.meta import router as meta_router
from app.routes.reports import router as reports_router
from app.routes.clusters import router as clusters_router
from app.routes.dashboard import router as dashboard_router
from app.routes.reviews import router as reviews_router
from app.routes.evaluations import router as evaluations_router

__all__ = [
    "health_router",
    "meta_router",
    "reports_router",
    "clusters_router",
    "dashboard_router",
    "reviews_router",
    "evaluations_router",
]
