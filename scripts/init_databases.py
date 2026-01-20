"""
Database initialization script
"""
import sys
import time
from loguru import logger

from src.config import config
from src.storage.elasticsearch_client import ElasticsearchClient
from src.storage.clickhouse_client import ClickHouseClient


def wait_for_elasticsearch(max_retries=30, delay=2):
    """Wait for Elasticsearch to be ready"""
    logger.info("Waiting for Elasticsearch...")
    
    for i in range(max_retries):
        try:
            client = ElasticsearchClient()
            if client.client.ping():
                logger.info("Elasticsearch is ready")
                return True
        except Exception as e:
            logger.warning(f"Elasticsearch not ready (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    
    logger.error("Elasticsearch is not available")
    return False


def wait_for_clickhouse(max_retries=30, delay=2):
    """Wait for ClickHouse to be ready"""
    logger.info("Waiting for ClickHouse...")
    
    for i in range(max_retries):
        try:
            client = ClickHouseClient()
            client.client.execute("SELECT 1")
            logger.info("ClickHouse is ready")
            return True
        except Exception as e:
            logger.warning(f"ClickHouse not ready (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    
    logger.error("ClickHouse is not available")
    return False


def initialize_elasticsearch():
    """Initialize Elasticsearch indices"""
    logger.info("Initializing Elasticsearch indices...")
    
    try:
        client = ElasticsearchClient()
        client.create_indices()
        logger.info("Elasticsearch indices created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch indices: {e}")
        return False


def initialize_clickhouse():
    """Initialize ClickHouse tables"""
    logger.info("Initializing ClickHouse tables...")
    
    try:
        client = ClickHouseClient()
        client.create_tables()
        logger.info("ClickHouse tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create ClickHouse tables: {e}")
        return False


def main():
    """Main initialization function"""
    logger.info("=" * 50)
    logger.info("Database Initialization Script")
    logger.info("=" * 50)
    
    success = True
    
    # Wait for services
    if not wait_for_elasticsearch():
        success = False
    
    if not wait_for_clickhouse():
        success = False
    
    if not success:
        logger.error("Some services are not available")
        sys.exit(1)
    
    # Initialize databases
    if not initialize_elasticsearch():
        success = False
    
    if not initialize_clickhouse():
        success = False
    
    if success:
        logger.info("=" * 50)
        logger.info("Database initialization completed successfully")
        logger.info("=" * 50)
        sys.exit(0)
    else:
        logger.error("=" * 50)
        logger.error("Database initialization failed")
        logger.error("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
