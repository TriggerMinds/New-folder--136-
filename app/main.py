import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.logging_config import configure_logging
import app.connectors  # noqa: F401 - registreert connector types
from app.database.base import Base
from app.database.session import engine
from app.api.health import router as health_router
from app.api.claims import router as claims_router
from app.api.observations import router as observations_router
from app.api.sources import router as sources_router
from app.api.audit import router as audit_router
from app.api.web import router as web_router
from app.api.country_packs import router as country_packs_router
from app.api.source_runs import router as source_runs_router
from app.api.scheduler_api import router as scheduler_router
from app.scheduler.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await start_scheduler()
    yield
    await stop_scheduler()
    await engine.dispose()


app = FastAPI(
    title="EU Leak Discovery",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

from jinja2 import Environment, FileSystemLoader
jinja_env = Environment(loader=FileSystemLoader("app/templates"), auto_reload=False)
templates = Jinja2Templates(env=jinja_env)
app.state.templates = templates

app.include_router(health_router)
app.include_router(claims_router)
app.include_router(observations_router)
app.include_router(sources_router)
app.include_router(audit_router)
app.include_router(web_router)
app.include_router(country_packs_router)
app.include_router(source_runs_router)
app.include_router(scheduler_router)
