"""
ClickHouse storage module for OLAP analytics
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from clickhouse_driver import Client
from loguru import logger
import pandas as pd

from src.config import config
from src.models import ProcessedPost, AggregatedMetrics


class ClickHouseClient:
    """ClickHouse client for storing and querying analytics data"""
    
    def __init__(self):
        self.config = config.clickhouse
        self.client = Client(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database
        )
        logger.info(f"Connected to ClickHouse at {self.config.host}:{self.config.port}")
    
    def create_tables(self):
        """Create ClickHouse tables"""
        # Posts table with partitioning by date
        create_posts_table = """
        CREATE TABLE IF NOT EXISTS posts (
            doc_id String,
            post_id String,
            source String,
            source_id String,
            
            title String,
            content String,
            description String,
            tags Array(String),
            
            num_likes UInt32,
            num_dislikes UInt32,
            num_comments UInt32,
            num_shares UInt32,
            num_views UInt32,
            
            user_id String,
            user_name String,
            
            create_date DateTime,
            collect_date DateTime,
            
            sentiment String,
            language String,
            is_viral UInt8,
            is_sensitive UInt8,
            engagement_score Float32,
            
            date Date DEFAULT toDate(create_date)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (source, date, doc_id)
        SETTINGS index_granularity = 8192
        """
        
        # Aggregated metrics table
        create_metrics_table = """
        CREATE TABLE IF NOT EXISTS metrics_hourly (
            window_start DateTime,
            window_end DateTime,
            platform String,
            
            total_posts UInt32,
            unique_users UInt32,
            
            total_likes UInt64,
            total_shares UInt64,
            total_comments UInt64,
            total_views UInt64,
            
            avg_engagement Float32,
            max_engagement Float32,
            
            date Date DEFAULT toDate(window_start)
        ) ENGINE = SummingMergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (platform, window_start)
        SETTINGS index_granularity = 8192
        """
        
        # Events table
        create_events_table = """
        CREATE TABLE IF NOT EXISTS events (
            event_id String,
            keywords Array(String),
            start_time DateTime,
            end_time DateTime,
            peak_time DateTime,
            
            total_posts UInt32,
            total_engagement UInt64,
            platforms Array(String),
            
            growth_rate Float32,
            z_score Float32,
            
            created_at DateTime DEFAULT now(),
            date Date DEFAULT toDate(start_time)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (date, event_id)
        SETTINGS index_granularity = 8192
        """
        
        # User analytics table
        create_users_table = """
        CREATE TABLE IF NOT EXISTS user_analytics (
            user_id String,
            user_name String,
            platform String,
            
            total_posts UInt32,
            total_likes UInt64,
            total_shares UInt64,
            total_comments UInt64,
            
            avg_engagement Float32,
            last_post_date DateTime,
            
            date Date DEFAULT toDate(last_post_date)
        ) ENGINE = ReplacingMergeTree(last_post_date)
        PARTITION BY toYYYYMM(date)
        ORDER BY (platform, user_id)
        SETTINGS index_granularity = 8192
        """
        
        tables = [
            create_posts_table,
            create_metrics_table,
            create_events_table,
            create_users_table
        ]
        
        for sql in tables:
            self.client.execute(sql)
            logger.info("Created ClickHouse table")
    
    def insert_posts(self, posts: List[ProcessedPost]):
        """Insert posts into ClickHouse"""
        if not posts:
            return
        
        data = []
        for post in posts:
            data.append({
                'doc_id': post.doc_id,
                'post_id': post.post_id,
                'source': post.source,
                'source_id': post.source_id,
                'title': post.title or '',
                'content': post.content or '',
                'description': post.description or '',
                'tags': post.tags,
                'num_likes': post.num_likes,
                'num_dislikes': post.num_dislikes,
                'num_comments': post.num_comments,
                'num_shares': post.num_shares,
                'num_views': post.num_views,
                'user_id': post.user_id,
                'user_name': post.user_name,
                'create_date': post.create_date,
                'collect_date': post.collect_date,
                'sentiment': post.sentiment or '',
                'language': post.language or '',
                'is_viral': 1 if post.is_viral else 0,
                'is_sensitive': 1 if post.is_sensitive else 0,
                'engagement_score': post.engagement_score,
            })
        
        self.client.execute(
            'INSERT INTO posts VALUES',
            data
        )
        logger.info(f"Inserted {len(data)} posts into ClickHouse")
    
    def query_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        platform: Optional[str] = None,
        interval: str = '1 HOUR'
    ) -> pd.DataFrame:
        """Query time series data"""
        query = f"""
        SELECT
            toStartOfInterval(create_date, INTERVAL {interval}) as time_bucket,
            source as platform,
            count() as post_count,
            sum(num_likes) as total_likes,
            sum(num_shares) as total_shares,
            sum(num_comments) as total_comments,
            avg(engagement_score) as avg_engagement
        FROM posts
        WHERE create_date >= %(start_date)s AND create_date <= %(end_date)s
        """
        
        if platform:
            query += " AND source = %(platform)s"
        
        query += """
        GROUP BY time_bucket, platform
        ORDER BY time_bucket
        """
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        if platform:
            params['platform'] = platform
        
        df = self.client.query_dataframe(query, params)
        return df
    
    def get_top_users(
        self,
        start_date: datetime,
        end_date: datetime,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Get top users by engagement"""
        query = """
        SELECT
            user_id,
            user_name,
            source as platform,
            count() as post_count,
            sum(num_likes) as total_likes,
            sum(num_shares) as total_shares,
            sum(engagement_score) as total_engagement
        FROM posts
        WHERE create_date >= %(start_date)s AND create_date <= %(end_date)s
        """
        
        if platform:
            query += " AND source = %(platform)s"
        
        query += f"""
        GROUP BY user_id, user_name, platform
        ORDER BY total_engagement DESC
        LIMIT {limit}
        """
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        if platform:
            params['platform'] = platform
        
        df = self.client.query_dataframe(query, params)
        return df
    
    def get_trending_tags(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get trending tags"""
        query = f"""
        SELECT
            tag,
            count() as frequency,
            sum(engagement_score) as total_engagement
        FROM posts
        ARRAY JOIN tags as tag
        WHERE create_date >= %(start_date)s AND create_date <= %(end_date)s
            AND tag != ''
        GROUP BY tag
        ORDER BY frequency DESC
        LIMIT {limit}
        """
        
        result = self.client.execute(
            query,
            {'start_date': start_date, 'end_date': end_date}
        )
        
        return [
            {'tag': row[0], 'frequency': row[1], 'engagement': row[2]}
            for row in result
        ]
    
    def detect_spikes(
        self,
        window_hours: int = 24,
        threshold: float = 2.5
    ) -> pd.DataFrame:
        """Detect activity spikes"""
        query = f"""
        WITH hourly_counts AS (
            SELECT
                toStartOfHour(create_date) as hour,
                source,
                count() as count
            FROM posts
            WHERE create_date >= now() - INTERVAL {window_hours} HOUR
            GROUP BY hour, source
        ),
        stats AS (
            SELECT
                source,
                avg(count) as mean,
                stddevPop(count) as stddev
            FROM hourly_counts
            GROUP BY source
        )
        SELECT
            h.hour,
            h.source,
            h.count,
            s.mean,
            s.stddev,
            (h.count - s.mean) / s.stddev as z_score
        FROM hourly_counts h
        JOIN stats s ON h.source = s.source
        WHERE (h.count - s.mean) / s.stddev > {threshold}
        ORDER BY z_score DESC
        """
        
        df = self.client.query_dataframe(query)
        return df
    
    def get_statistics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get overall statistics"""
        query = """
        SELECT
            count() as total_posts,
            uniq(user_id) as unique_users,
            sum(num_likes) as total_likes,
            sum(num_shares) as total_shares,
            sum(num_comments) as total_comments,
            avg(engagement_score) as avg_engagement,
            max(engagement_score) as max_engagement
        FROM posts
        WHERE create_date >= %(start_date)s AND create_date <= %(end_date)s
        """
        
        result = self.client.execute(
            query,
            {'start_date': start_date, 'end_date': end_date}
        )
        
        row = result[0]
        return {
            'total_posts': row[0],
            'unique_users': row[1],
            'total_likes': row[2],
            'total_shares': row[3],
            'total_comments': row[4],
            'avg_engagement': row[5],
            'max_engagement': row[6]
        }
