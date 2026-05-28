import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

from agent import (
    run_daily_analysis,
    get_latest_digest,
    get_all_digests,
    get_performance_records,
    DailyDigest,
    PerformanceRecord,
)
from agent.orchestrator import update_performance_outcomes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schedule daily run
    run_hour = int(os.getenv("DAILY_RUN_HOUR", 7))
    run_minute = int(os.getenv("DAILY_RUN_MINUTE", 0))
    scheduler.add_job(
        run_daily_analysis,
        CronTrigger(hour=run_hour, minute=run_minute),
        id="daily_analysis",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — daily run at {run_hour:02d}:{run_minute:02d} UTC")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="RobiAgent API",
    description="AI-powered daily trade intelligence for Robinhood users",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "RobiAgent",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/digest/latest", response_model=DailyDigest)
def latest_digest():
    """Get today's (or most recent) daily digest."""
    digest = get_latest_digest()
    if not digest:
        raise HTTPException(status_code=404, detail="No digest available yet. Run /api/run to generate one.")
    return digest


@app.get("/api/digest/history", response_model=list[DailyDigest])
def digest_history():
    """Get all historical digests."""
    return get_all_digests()


@app.get("/api/performance", response_model=list[PerformanceRecord])
def performance():
    """Get all performance records with live outcome tracking."""
    update_performance_outcomes()
    return get_performance_records()


@app.post("/api/run")
def trigger_run(background_tasks: BackgroundTasks):
    """Manually trigger a full agent analysis run."""
    background_tasks.add_task(run_daily_analysis)
    return {
        "status": "started",
        "message": "Analysis running in background. Check /api/digest/latest in ~60 seconds.",
        "triggered_at": datetime.utcnow().isoformat(),
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "next_run": str(scheduler.get_job("daily_analysis").next_run_time) if scheduler.get_job("daily_analysis") else None,
    }
