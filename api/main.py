import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from clickhouse_driver import Client

APP_NAME = "Social Analytics API"


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


CLICKHOUSE_HOST = _env("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(_env("CLICKHOUSE_PORT", "9000"))
CLICKHOUSE_USER = _env("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = _env("CLICKHOUSE_PASSWORD", "admin123")
CLICKHOUSE_DATABASE = _env("CLICKHOUSE_DATABASE", "default")

DEFAULT_LIMIT = 500
MAX_LIMIT = 5000


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {value}") from exc


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date: {value}") from exc


def _clean_category(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if value.strip() == "" or value.strip().lower() == "null":
        return None
    return value


def _category_filter(category_raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if category_raw is None:
        return None
    cleaned = _clean_category(category_raw)
    if cleaned is None:
        return {"sql": "category IS NULL", "params": {}}
    return {"sql": "category = %(category)s", "params": {"category": cleaned}}


def _limit(value: int) -> int:
    return max(1, min(value, MAX_LIMIT))


client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)

app = FastAPI(title=APP_NAME)

# Allow local frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    try:
        client.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ClickHouse error: {exc}") from exc
    return {"status": "ok"}


@app.get("/time-series")
def time_series(
    source: Optional[str] = None,
    category: Optional[str] = None,
    start: Optional[str] = Query(None, description="ISO datetime"),
    end: Optional[str] = Query(None, description="ISO datetime"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    order: str = Query("asc", pattern="^(asc|desc)$"),
) -> List[Dict[str, Any]]:
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)

    conditions = []
    params: Dict[str, Any] = {}
    if source:
        conditions.append("source = %(source)s")
        params["source"] = source
    category_filter = _category_filter(category)
    if category_filter:
        conditions.append(category_filter["sql"])
        params.update(category_filter["params"])
    if start_dt:
        conditions.append("bucket_start >= %(start)s")
        params["start"] = start_dt
    if end_dt:
        conditions.append("bucket_start <= %(end)s")
        params["end"] = end_dt

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order_sql = "ASC" if order == "asc" else "DESC"

    sql = f"""
        SELECT
            source,
            category,
            bucket_start,
            bucket_end,
            post_count,
            interaction_sum
        FROM social_time_series
        {where}
        ORDER BY bucket_start {order_sql}
        LIMIT %(limit)s
    """
    params["limit"] = _limit(limit)

    rows = client.execute(sql, params)
    cols = ["source", "category", "bucket_start", "bucket_end", "post_count", "interaction_sum"]
    return [dict(zip(cols, row)) for row in rows]


@app.get("/burst-events")
def burst_events(
    source: Optional[str] = None,
    category: Optional[str] = None,
    start: Optional[str] = Query(None, description="ISO datetime"),
    end: Optional[str] = Query(None, description="ISO datetime"),
    is_burst: Optional[bool] = None,
    min_score: Optional[float] = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> List[Dict[str, Any]]:
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)

    conditions = []
    params: Dict[str, Any] = {}
    if source:
        conditions.append("source = %(source)s")
        params["source"] = source
    category_filter = _category_filter(category)
    if category_filter:
        conditions.append(category_filter["sql"])
        params.update(category_filter["params"])
    if start_dt:
        conditions.append("bucket_start >= %(start)s")
        params["start"] = start_dt
    if end_dt:
        conditions.append("bucket_start <= %(end)s")
        params["end"] = end_dt
    if is_burst is not None:
        conditions.append("is_burst = %(is_burst)s")
        params["is_burst"] = 1 if is_burst else 0
    if min_score is not None:
        conditions.append("burst_score >= %(min_score)s")
        params["min_score"] = min_score

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order_sql = "ASC" if order == "asc" else "DESC"

    sql = f"""
        SELECT
            source,
            category,
            bucket_start,
            bucket_end,
            post_count,
            interaction_sum,
            mean,
            std,
            burst_score,
            is_burst
        FROM social_burst_events
        {where}
        ORDER BY bucket_start {order_sql}
        LIMIT %(limit)s
    """
    params["limit"] = _limit(limit)

    rows = client.execute(sql, params)
    cols = [
        "source",
        "category",
        "bucket_start",
        "bucket_end",
        "post_count",
        "interaction_sum",
        "mean",
        "std",
        "burst_score",
        "is_burst",
    ]
    return [dict(zip(cols, row)) for row in rows]


@app.get("/daily-summary")
def daily_summary(
    source: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> List[Dict[str, Any]]:
    start_date = _parse_date(date_from)
    end_date = _parse_date(date_to)

    conditions = []
    params: Dict[str, Any] = {}
    if source:
        conditions.append("source = %(source)s")
        params["source"] = source
    category_filter = _category_filter(category)
    if category_filter:
        conditions.append(category_filter["sql"])
        params.update(category_filter["params"])
    if start_date:
        conditions.append("date >= %(start_date)s")
        params["start_date"] = start_date
    if end_date:
        conditions.append("date <= %(end_date)s")
        params["end_date"] = end_date

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT
            date,
            source,
            category,
            total_posts,
            total_interaction,
            burst_count
        FROM social_daily_summary
        {where}
        ORDER BY date DESC
        LIMIT %(limit)s
    """
    params["limit"] = _limit(limit)

    rows = client.execute(sql, params)
    cols = [
        "date",
        "source",
        "category",
        "total_posts",
        "total_interaction",
        "burst_count",
    ]
    return [dict(zip(cols, row)) for row in rows]


@app.get("/top-bursts")
def top_bursts(
    day: Optional[str] = Query(None, description="YYYY-MM-DD"),
    source: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=MAX_LIMIT),
) -> List[Dict[str, Any]]:
    day_value = _parse_date(day) if day else None

    conditions = []
    params: Dict[str, Any] = {}
    if day_value:
        conditions.append("date = %(day)s")
        params["day"] = day_value
    if source:
        conditions.append("source = %(source)s")
        params["source"] = source
    category_filter = _category_filter(category)
    if category_filter:
        conditions.append(category_filter["sql"])
        params.update(category_filter["params"])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT
            date,
            source,
            category,
            bucket_start,
            burst_score,
            post_count
        FROM social_top_bursts
        {where}
        ORDER BY burst_score DESC
        LIMIT %(limit)s
    """
    params["limit"] = _limit(limit)

    rows = client.execute(sql, params)
    cols = ["date", "source", "category", "bucket_start", "burst_score", "post_count"]
    return [dict(zip(cols, row)) for row in rows]


@app.exception_handler(Exception)
def unhandled_exception_handler(_, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})
