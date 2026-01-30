"""
Main ETL pipeline orchestrator
"""
from pathlib import Path
from typing import List
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from src.config import config
from src.models import ProcessedPost
from src.etl.data_loader import DataLoader
from src.etl.data_cleaner import DataCleaner
from src.etl.deduplicator import Deduplicator
from src.analysis.text_analyzer import TextAnalyzer, EngagementCalculator
from src.analysis.event_detector import EventDetector
from src.storage.elasticsearch_client import ElasticsearchClient
from src.storage.clickhouse_client import ClickHouseClient
from src.filter_sensitive import load_terms, should_drop


class ETLPipeline:
    """Main ETL pipeline for social media data processing"""
    
    def __init__(self):
        self.config = config
        
        # Initialize components
        self.data_loader = DataLoader(config.paths.raw_data)
        self.cleaner = DataCleaner()
        self.deduplicator = Deduplicator(
            similarity_threshold=config.processing.dedup_threshold
        )
        self.text_analyzer = TextAnalyzer()
        self.engagement_calc = EngagementCalculator()
        self.event_detector = EventDetector(
            threshold_zscore=config.processing.spike_detection_threshold
        )
        
        # Initialize storage
        self.es_client = ElasticsearchClient()
        self.ch_client = ClickHouseClient()
        
        # Load sensitive words
        self.sensitive_terms = load_terms(str(config.paths.sensitive_words))
        
        logger.info("ETL Pipeline initialized")
    
    def setup_storage(self):
        """Initialize database tables and indices"""
        logger.info("Setting up storage...")
        self.es_client.create_indices()
        self.ch_client.create_tables()
        logger.info("Storage setup complete")
    
    def extract(self, pattern: str = "posts_*.csv") -> List:
        """Extract data from CSV files"""
        logger.info(f"Extracting data from {config.paths.raw_data}")
        
        posts = []
        for post in self.data_loader.load_all_files(pattern):
            posts.append(post)
        
        logger.info(f"Extracted {len(posts)} posts")
        return posts
    
    def transform(self, posts: List) -> List[ProcessedPost]:
        """Transform and enrich data"""
        logger.info("Transforming data...")
        
        processed_posts = []
        
        for post in tqdm(posts, desc="Processing posts"):
            # Convert to ProcessedPost
            processed = ProcessedPost(**post.dict())
            
            # Clean text
            cleaned_content = self.cleaner.clean_text(post.content)
            processed.cleaned_text = cleaned_content
            
            # Check for sensitive content
            text_to_check = " ".join([
                post.title or "",
                post.content or "",
                post.description or "",
                " ".join(post.tags)
            ])
            
            processed.is_sensitive = any(
                term in text_to_check.lower()
                for term in self.sensitive_terms
            )
            
            # Skip sensitive content if configured
            if processed.is_sensitive and config.env == "production":
                continue
            
            # Text analysis
            if cleaned_content:
                # Language detection
                processed.language = self.text_analyzer.detect_language(cleaned_content)
                
                # Sentiment analysis
                sentiment = self.text_analyzer.analyze_sentiment(cleaned_content)
                processed.sentiment = sentiment['label']
                
                # Extract keywords
                processed.keywords = self.text_analyzer.extract_keywords(cleaned_content)
                
                # Extract entities
                processed.entities = self.text_analyzer.extract_entities(cleaned_content)
            
            # Calculate engagement metrics
            processed.engagement_score = self.engagement_calc.calculate_engagement_score(processed)
            processed.is_viral = self.engagement_calc.is_viral(
                processed,
                threshold=config.processing.viral_threshold
            )
            
            processed_posts.append(processed)
        
        logger.info(f"Transformed {len(processed_posts)} posts")
        
        # Deduplication
        logger.info("Detecting duplicates...")
        processed_posts = self.deduplicator.mark_duplicates(processed_posts)
        
        # Filter duplicates
        unique_posts = [p for p in processed_posts if not p.is_duplicate]
        logger.info(f"Removed {len(processed_posts) - len(unique_posts)} duplicates")
        
        return unique_posts
    
    def detect_events(self, posts: List[ProcessedPost]):
        """Detect events and bursts"""
        logger.info("Detecting events...")
        
        # Detect volume spikes
        spikes = self.event_detector.detect_volume_spikes(posts)
        logger.info(f"Detected {len(spikes)} volume spikes")
        
        # Detect keyword bursts
        bursts = self.event_detector.detect_keyword_bursts(posts)
        logger.info(f"Detected {len(bursts)} keyword bursts")
        
        # Cluster into events
        events = self.event_detector.cluster_events(posts)
        logger.info(f"Detected {len(events)} events")
        
        return events, spikes, bursts
    
    def load(self, posts: List[ProcessedPost], events: List):
        """Load data into storage systems"""
        logger.info("Loading data to storage...")
        
        # Load to Elasticsearch (for search)
        batch_size = config.processing.batch_size
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            result = self.es_client.bulk_index_posts(
                batch,
                index=self.es_client.processed_index
            )
            logger.info(f"Indexed {result['indexed']} posts to Elasticsearch")
        
        # Load to ClickHouse (for analytics)
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            self.ch_client.insert_posts(batch)
        
        logger.info(f"Loaded {len(posts)} posts to storage")
        
        # Load events
        if events:
            # Index events to Elasticsearch
            for event in events:
                self.es_client.client.index(
                    index=self.es_client.events_index,
                    id=event.event_id,
                    document=event.dict()
                )
            logger.info(f"Loaded {len(events)} events")
    
    def run(self, pattern: str = "posts_*.csv"):
        """Run the complete ETL pipeline"""
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("Starting ETL Pipeline")
        logger.info("=" * 50)
        
        try:
            # Setup storage
            self.setup_storage()
            
            # Extract
            posts = self.extract(pattern)
            
            if not posts:
                logger.warning("No posts to process")
                return
            
            # Transform
            processed_posts = self.transform(posts)
            
            # Detect events
            events, spikes, bursts = self.detect_events(processed_posts)
            
            # Load
            self.load(processed_posts, events)
            
            # Report
            duration = (datetime.now() - start_time).total_seconds()
            logger.info("=" * 50)
            logger.info("ETL Pipeline Complete")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Processed: {len(processed_posts)} posts")
            logger.info(f"Events: {len(events)}")
            logger.info(f"Spikes: {len(spikes)}")
            logger.info(f"Bursts: {len(bursts)}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")
            raise


def main():
    """Main entry point"""
    # Configure logging
    logger.add(
        config.paths.log_file,
        rotation="100 MB",
        retention="30 days",
        level=config.log_level
    )
    
    # Run pipeline
    pipeline = ETLPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
