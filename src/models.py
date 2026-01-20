"""
Data models and schemas
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator


class SourcePlatform(str, Enum):
    """Social media platform types"""
    TWITTER = "twitter"
    X = "x"
    THREADS = "threads"
    REDDIT = "reddit"
    UNKNOWN = "unknown"


class DocType(str, Enum):
    """Document types"""
    POST = "post"
    COMMENT = "comment"
    THREAD = "thread"
    RETWEET = "retweet"
    SHARE = "share"


class SocialMediaPost(BaseModel):
    """Unified schema for social media posts"""
    # Identifiers
    doc_id: str = Field(..., description="Unique document ID")
    post_id: str = Field(..., description="Platform-specific post ID")
    source: SourcePlatform = Field(..., description="Source platform")
    source_id: str = Field(..., description="Source-specific ID")
    
    # Content
    title: Optional[str] = Field(None, description="Post title")
    content: Optional[str] = Field(None, description="Main content")
    description: Optional[str] = Field(None, description="Additional description")
    tags: List[str] = Field(default_factory=list, description="Tags/hashtags")
    
    # Media
    pictures: List[str] = Field(default_factory=list, description="Image URLs")
    link: Optional[str] = Field(None, description="External link")
    post_link: str = Field(..., description="Link to the post")
    domain: Optional[str] = Field(None, description="Domain name")
    
    # Engagement metrics
    num_likes: int = Field(default=0, description="Number of likes")
    num_dislikes: int = Field(default=0, description="Number of dislikes")
    num_comments: int = Field(default=0, description="Number of comments")
    num_shares: int = Field(default=0, description="Number of shares")
    num_views: int = Field(default=0, description="Number of views")
    reactions: Dict[str, Any] = Field(default_factory=dict, description="Detailed reactions")
    
    # User information
    user_id: str = Field(..., description="User ID")
    user_name: str = Field(..., description="Username")
    source_name: Optional[str] = Field(None, description="Source display name")
    logo_link: Optional[str] = Field(None, description="User avatar URL")
    
    # Metadata
    doc_type: DocType = Field(default=DocType.POST, description="Document type")
    type: Optional[str] = Field(None, description="Additional type info")
    from_crawler: str = Field(..., description="Crawler identifier")
    categories: List[str] = Field(default_factory=list, description="Categories")
    provinces: List[str] = Field(default_factory=list, description="Geographic info")
    
    # Timestamps
    create_date: datetime = Field(..., description="Creation timestamp")
    collect_date: datetime = Field(..., description="Collection timestamp")
    
    # Computed fields (added during processing)
    sentiment: Optional[str] = Field(None, description="Sentiment analysis result")
    language: Optional[str] = Field(None, description="Detected language")
    is_viral: bool = Field(default=False, description="Viral post flag")
    is_sensitive: bool = Field(default=False, description="Contains sensitive content")
    engagement_score: float = Field(default=0.0, description="Computed engagement score")
    
    @validator("create_date", "collect_date", pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            # Handle various datetime formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            # If all formats fail, try pandas parser
            import pandas as pd
            return pd.to_datetime(v)
        return v
    
    @validator("source", pre=True)
    def normalize_source(cls, v):
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in ["twitter", "x"]:
                return SourcePlatform.X
            elif v_lower == "threads":
                return SourcePlatform.THREADS
            elif v_lower == "reddit":
                return SourcePlatform.REDDIT
        return v
    
    class Config:
        use_enum_values = True


class ProcessedPost(SocialMediaPost):
    """Extended model for processed posts with additional analytics"""
    # Text analysis
    cleaned_text: Optional[str] = Field(None, description="Cleaned and normalized text")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    entities: List[Dict[str, str]] = Field(default_factory=list, description="Named entities")
    
    # Duplicate detection
    is_duplicate: bool = Field(default=False, description="Duplicate flag")
    duplicate_of: Optional[str] = Field(None, description="Original post ID if duplicate")
    similarity_score: Optional[float] = Field(None, description="Similarity score")
    
    # Cross-platform tracking
    cross_platform_ids: List[str] = Field(default_factory=list, description="Related posts on other platforms")
    
    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    processing_version: str = Field(default="1.0", description="Processing pipeline version")


class EventDetection(BaseModel):
    """Event burst detection result"""
    event_id: str = Field(..., description="Event identifier")
    keywords: List[str] = Field(..., description="Event keywords")
    start_time: datetime = Field(..., description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    peak_time: datetime = Field(..., description="Peak activity time")
    
    # Metrics
    total_posts: int = Field(..., description="Total posts in event")
    total_engagement: int = Field(..., description="Total engagement")
    platforms: List[SourcePlatform] = Field(..., description="Affected platforms")
    
    # Statistics
    growth_rate: float = Field(..., description="Growth rate")
    z_score: float = Field(..., description="Statistical z-score")
    
    # Content
    top_posts: List[str] = Field(default_factory=list, description="Top post IDs")
    summary: Optional[str] = Field(None, description="Event summary")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AggregatedMetrics(BaseModel):
    """Aggregated metrics for time windows"""
    window_start: datetime
    window_end: datetime
    platform: Optional[SourcePlatform] = None
    
    # Counts
    total_posts: int = 0
    unique_users: int = 0
    
    # Engagement
    total_likes: int = 0
    total_shares: int = 0
    total_comments: int = 0
    total_views: int = 0
    
    # Averages
    avg_engagement: float = 0.0
    avg_sentiment: float = 0.0
    
    # Top items
    top_keywords: List[Dict[str, Any]] = Field(default_factory=list)
    top_users: List[Dict[str, Any]] = Field(default_factory=list)
    trending_topics: List[str] = Field(default_factory=list)
