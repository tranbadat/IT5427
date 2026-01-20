"""
FastAPI REST API for social media analytics
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.config import config
from src.storage.elasticsearch_client import ElasticsearchClient
from src.storage.clickhouse_client import ClickHouseClient
from src.models import SocialMediaPost, EventDetection, AggregatedMetrics


# API Models
class SearchRequest(BaseModel):
    query: Optional[str] = None
    platform: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100


class StatsResponse(BaseModel):
    total_posts: int
    unique_users: int
    total_likes: int
    total_shares: int
    total_comments: int
    avg_engagement: float
    platforms: Dict[str, int]


# Create FastAPI app
app = FastAPI(
    title="Social Media Analytics API",
    description="API for social media data analysis and event detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
es_client = None
ch_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup"""
    global es_client, ch_client
    es_client = ElasticsearchClient()
    ch_client = ClickHouseClient()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Social Media Analytics API",
        "version": "1.0.0",
        "endpoints": [
            "/search",
            "/stats",
            "/trending",
            "/viral",
            "/events",
            "/timeseries",
            "/users/top"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "elasticsearch": es_client is not None,
        "clickhouse": ch_client is not None
    }


@app.post("/search")
async def search_posts(request: SearchRequest):
    """Search social media posts"""
    try:
        result = es_client.search_posts(
            query=request.query,
            platform=request.platform,
            start_date=request.start_date,
            end_date=request.end_date,
            size=request.limit
        )
        
        return {
            "total": result['hits']['total']['value'],
            "posts": [hit['_source'] for hit in result['hits']['hits']]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get overall statistics"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        stats = ch_client.get_statistics(start_date, end_date)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trending/keywords")
async def get_trending_keywords(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(20, le=100)
):
    """Get trending keywords"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(hours=24)
        if not end_date:
            end_date = datetime.now()
        
        keywords = es_client.get_trending_keywords(start_date, end_date, size=limit)
        
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trending/tags")
async def get_trending_tags(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get trending tags from ClickHouse"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(hours=24)
        if not end_date:
            end_date = datetime.now()
        
        tags = ch_client.get_trending_tags(start_date, end_date, limit)
        
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/viral")
async def get_viral_posts(
    threshold: int = Query(10000, ge=1000),
    start_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=100)
):
    """Get viral posts"""
    try:
        viral_posts = es_client.get_viral_posts(
            threshold=threshold,
            start_date=start_date,
            size=limit
        )
        
        return {"viral_posts": viral_posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/spikes")
async def get_activity_spikes(
    window_hours: int = Query(24, ge=1, le=168),
    threshold: float = Query(2.5, ge=1.0)
):
    """Detect activity spikes"""
    try:
        spikes = ch_client.detect_spikes(
            window_hours=window_hours,
            threshold=threshold
        )
        
        return {"spikes": spikes.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/timeseries")
async def get_time_series(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    platform: Optional[str] = Query(None),
    interval: str = Query("1 HOUR", regex="^(1 HOUR|1 DAY|1 WEEK)$")
):
    """Get time series data"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        df = ch_client.query_time_series(
            start_date=start_date,
            end_date=end_date,
            platform=platform,
            interval=interval
        )
        
        return {"data": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/top")
async def get_top_users(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get top users by engagement"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        df = ch_client.get_top_users(
            start_date=start_date,
            end_date=end_date,
            platform=platform,
            limit=limit
        )
        
        return {"users": df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/aggregate")
async def get_aggregated_data(
    interval: str = Query("1h", regex="^(1h|6h|1d)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get aggregated metrics by time interval"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        data = es_client.aggregate_by_time(
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
        
        return {"aggregations": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_api()
