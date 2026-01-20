"""
Elasticsearch integration module
"""
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime, timedelta

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError
from loguru import logger

from src.config import config
from src.models import SocialMediaPost, ProcessedPost, AggregatedMetrics


class ElasticsearchClient:
    """Elasticsearch client for indexing and searching social media data"""
    
    def __init__(self):
        self.config = config.elasticsearch
        self.client = Elasticsearch(
            [self.config.url],
            basic_auth=(self.config.user, self.config.password) if self.config.user else None,
            verify_certs=False,
            request_timeout=30
        )
        self.index_prefix = self.config.index_prefix
        
        # Index names
        self.posts_index = f"{self.index_prefix}_posts"
        self.processed_index = f"{self.index_prefix}_processed"
        self.events_index = f"{self.index_prefix}_events"
        self.metrics_index = f"{self.index_prefix}_metrics"
        
        logger.info(f"Connected to Elasticsearch at {self.config.url}")
    
    def create_indices(self):
        """Create all necessary indices with mappings"""
        # Posts index mapping
        posts_mapping = {
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "post_id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "source_id": {"type": "keyword"},
                    
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "tags": {"type": "keyword"},
                    
                    "pictures": {"type": "keyword"},
                    "link": {"type": "keyword"},
                    "post_link": {"type": "keyword"},
                    "domain": {"type": "keyword"},
                    
                    "num_likes": {"type": "integer"},
                    "num_dislikes": {"type": "integer"},
                    "num_comments": {"type": "integer"},
                    "num_shares": {"type": "integer"},
                    "num_views": {"type": "integer"},
                    "reactions": {"type": "object", "enabled": True},
                    
                    "user_id": {"type": "keyword"},
                    "user_name": {"type": "keyword"},
                    "source_name": {"type": "text"},
                    
                    "doc_type": {"type": "keyword"},
                    "from_crawler": {"type": "keyword"},
                    "categories": {"type": "keyword"},
                    "provinces": {"type": "keyword"},
                    
                    "create_date": {"type": "date"},
                    "collect_date": {"type": "date"},
                    
                    "sentiment": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "is_viral": {"type": "boolean"},
                    "is_sensitive": {"type": "boolean"},
                    "engagement_score": {"type": "float"},
                }
            },
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "refresh_interval": "5s"
            }
        }
        
        # Processed posts index (extends posts)
        processed_mapping = {
            "mappings": {
                "properties": {
                    **posts_mapping["mappings"]["properties"],
                    "cleaned_text": {"type": "text", "analyzer": "standard"},
                    "keywords": {"type": "keyword"},
                    "entities": {"type": "nested"},
                    "is_duplicate": {"type": "boolean"},
                    "duplicate_of": {"type": "keyword"},
                    "similarity_score": {"type": "float"},
                    "cross_platform_ids": {"type": "keyword"},
                    "processed_at": {"type": "date"},
                    "processing_version": {"type": "keyword"},
                }
            },
            "settings": posts_mapping["settings"]
        }
        
        # Events index
        events_mapping = {
            "mappings": {
                "properties": {
                    "event_id": {"type": "keyword"},
                    "keywords": {"type": "keyword"},
                    "start_time": {"type": "date"},
                    "end_time": {"type": "date"},
                    "peak_time": {"type": "date"},
                    
                    "total_posts": {"type": "integer"},
                    "total_engagement": {"type": "integer"},
                    "platforms": {"type": "keyword"},
                    
                    "growth_rate": {"type": "float"},
                    "z_score": {"type": "float"},
                    
                    "top_posts": {"type": "keyword"},
                    "summary": {"type": "text"},
                    "created_at": {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            }
        }
        
        # Metrics index
        metrics_mapping = {
            "mappings": {
                "properties": {
                    "window_start": {"type": "date"},
                    "window_end": {"type": "date"},
                    "platform": {"type": "keyword"},
                    
                    "total_posts": {"type": "integer"},
                    "unique_users": {"type": "integer"},
                    
                    "total_likes": {"type": "long"},
                    "total_shares": {"type": "long"},
                    "total_comments": {"type": "long"},
                    "total_views": {"type": "long"},
                    
                    "avg_engagement": {"type": "float"},
                    "avg_sentiment": {"type": "float"},
                    
                    "top_keywords": {"type": "nested"},
                    "top_users": {"type": "nested"},
                    "trending_topics": {"type": "keyword"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            }
        }
        
        # Create indices
        indices = [
            (self.posts_index, posts_mapping),
            (self.processed_index, processed_mapping),
            (self.events_index, events_mapping),
            (self.metrics_index, metrics_mapping),
        ]
        
        for index_name, mapping in indices:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created index: {index_name}")
            else:
                logger.info(f"Index already exists: {index_name}")
    
    def index_post(self, post: SocialMediaPost, index: Optional[str] = None):
        """Index a single post"""
        if index is None:
            index = self.posts_index
        
        doc = post.dict()
        # Convert datetime to ISO format
        for field in ['create_date', 'collect_date', 'processed_at']:
            if field in doc and doc[field]:
                doc[field] = doc[field].isoformat()
        
        self.client.index(
            index=index,
            id=post.doc_id,
            document=doc
        )
    
    def bulk_index_posts(self, posts: List[SocialMediaPost], index: Optional[str] = None) -> Dict[str, int]:
        """Bulk index multiple posts"""
        if index is None:
            index = self.posts_index
        
        actions = []
        for post in posts:
            doc = post.dict()
            # Convert datetime to ISO format
            for field in ['create_date', 'collect_date', 'processed_at']:
                if field in doc and doc[field]:
                    doc[field] = doc[field].isoformat()
            
            actions.append({
                "_index": index,
                "_id": post.doc_id,
                "_source": doc
            })
        
        if not actions:
            return {"indexed": 0, "errors": 0}
        
        success, errors = helpers.bulk(
            self.client,
            actions,
            stats_only=False,
            raise_on_error=False
        )
        
        logger.info(f"Bulk indexed {success} documents to {index}")
        if errors:
            logger.warning(f"Bulk index errors: {len(errors)}")
        
        return {"indexed": success, "errors": len(errors) if errors else 0}
    
    def search_posts(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        platform: Optional[str] = None,
        size: int = 100,
        from_: int = 0,
        index: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search posts with various filters"""
        if index is None:
            index = self.processed_index
        
        # Build query
        must_clauses = []
        
        if query:
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content^2", "description", "tags"],
                    "type": "best_fields"
                }
            })
        
        if start_date or end_date:
            date_range = {}
            if start_date:
                date_range["gte"] = start_date.isoformat()
            if end_date:
                date_range["lte"] = end_date.isoformat()
            must_clauses.append({
                "range": {"create_date": date_range}
            })
        
        if platform:
            must_clauses.append({
                "term": {"source": platform}
            })
        
        if filters:
            for field, value in filters.items():
                must_clauses.append({
                    "term": {field: value}
                })
        
        search_query = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}]
                }
            },
            "size": size,
            "from": from_,
            "sort": [{"create_date": {"order": "desc"}}]
        }
        
        result = self.client.search(index=index, body=search_query)
        return result
    
    def get_trending_keywords(
        self,
        start_date: datetime,
        end_date: datetime,
        size: int = 20
    ) -> List[Dict[str, Any]]:
        """Get trending keywords for a time period"""
        query = {
            "query": {
                "range": {
                    "create_date": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            },
            "aggs": {
                "trending_tags": {
                    "terms": {
                        "field": "tags",
                        "size": size
                    }
                }
            },
            "size": 0
        }
        
        result = self.client.search(index=self.processed_index, body=query)
        buckets = result['aggregations']['trending_tags']['buckets']
        
        return [{"keyword": b['key'], "count": b['doc_count']} for b in buckets]
    
    def get_viral_posts(
        self,
        threshold: int = 10000,
        start_date: Optional[datetime] = None,
        size: int = 50
    ) -> List[Dict[str, Any]]:
        """Get viral posts based on engagement threshold"""
        must_clauses = [
            {"term": {"is_viral": True}}
        ]
        
        if start_date:
            must_clauses.append({
                "range": {
                    "create_date": {"gte": start_date.isoformat()}
                }
            })
        
        query = {
            "query": {"bool": {"must": must_clauses}},
            "size": size,
            "sort": [{"engagement_score": {"order": "desc"}}]
        }
        
        result = self.client.search(index=self.processed_index, body=query)
        return [hit['_source'] for hit in result['hits']['hits']]
    
    def aggregate_by_time(
        self,
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate posts by time intervals"""
        query = {
            "query": {"match_all": {}},
            "aggs": {
                "posts_over_time": {
                    "date_histogram": {
                        "field": "create_date",
                        "fixed_interval": interval,
                        "min_doc_count": 0
                    },
                    "aggs": {
                        "total_engagement": {
                            "sum": {"field": "engagement_score"}
                        },
                        "avg_sentiment": {
                            "avg": {"field": "engagement_score"}
                        }
                    }
                }
            },
            "size": 0
        }
        
        if start_date or end_date:
            date_range = {}
            if start_date:
                date_range["gte"] = start_date.isoformat()
            if end_date:
                date_range["lte"] = end_date.isoformat()
            query["query"] = {
                "range": {"create_date": date_range}
            }
        
        result = self.client.search(index=self.processed_index, body=query)
        buckets = result['aggregations']['posts_over_time']['buckets']
        
        return [{
            "timestamp": b['key_as_string'],
            "count": b['doc_count'],
            "total_engagement": b['total_engagement']['value'],
            "avg_sentiment": b['avg_sentiment']['value']
        } for b in buckets]
    
    def delete_index(self, index: str):
        """Delete an index"""
        try:
            self.client.indices.delete(index=index)
            logger.info(f"Deleted index: {index}")
        except NotFoundError:
            logger.warning(f"Index not found: {index}")
