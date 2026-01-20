"""
Configuration management module
"""
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class ElasticsearchConfig(BaseSettings):
    host: str = Field(default="localhost", env="ELASTICSEARCH_HOST")
    port: int = Field(default=9200, env="ELASTICSEARCH_PORT")
    user: str = Field(default="elastic", env="ELASTICSEARCH_USER")
    password: str = Field(default="changeme", env="ELASTICSEARCH_PASSWORD")
    index_prefix: str = Field(default="social_media", env="ELASTICSEARCH_INDEX_PREFIX")

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ClickHouseConfig(BaseSettings):
    host: str = Field(default="localhost", env="CLICKHOUSE_HOST")
    port: int = Field(default=9000, env="CLICKHOUSE_PORT")
    user: str = Field(default="default", env="CLICKHOUSE_USER")
    password: str = Field(default="", env="CLICKHOUSE_PASSWORD")
    database: str = Field(default="social_analytics", env="CLICKHOUSE_DATABASE")


class PostgresConfig(BaseSettings):
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    user: str = Field(default="postgres", env="POSTGRES_USER")
    password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    db: str = Field(default="social_metadata", env="POSTGRES_DB")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisConfig(BaseSettings):
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: str = Field(default="", env="REDIS_PASSWORD")


class SparkConfig(BaseSettings):
    master: str = Field(default="local[*]", env="SPARK_MASTER")
    app_name: str = Field(default="SocialMediaAnalytics", env="SPARK_APP_NAME")
    driver_memory: str = Field(default="4g", env="SPARK_DRIVER_MEMORY")
    executor_memory: str = Field(default="4g", env="SPARK_EXECUTOR_MEMORY")


class ProcessingConfig(BaseSettings):
    batch_size: int = Field(default=1000, env="BATCH_SIZE")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    dedup_threshold: float = Field(default=0.85, env="DEDUP_THRESHOLD")
    spike_detection_threshold: float = Field(default=2.5, env="SPIKE_DETECTION_THRESHOLD")
    viral_threshold: int = Field(default=10000, env="VIRAL_THRESHOLD")
    anomaly_zscore: float = Field(default=3.0, env="ANOMALY_ZSCORE")


class PathConfig(BaseSettings):
    raw_data: Path = Field(default=Path("./data/raw"), env="RAW_DATA_PATH")
    processed_data: Path = Field(default=Path("./data/processed"), env="PROCESSED_DATA_PATH")
    output_data: Path = Field(default=Path("./data/output"), env="OUTPUT_DATA_PATH")
    sensitive_words: Path = Field(default=Path("./configs/sensitive_words.txt"), env="SENSITIVE_WORDS_PATH")
    log_file: Path = Field(default=Path("./logs/app.log"), env="LOG_FILE")


class Config(BaseSettings):
    """Main configuration class"""
    env: str = Field(default="development", env="ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Sub-configurations
    elasticsearch: ElasticsearchConfig = Field(default_factory=ElasticsearchConfig)
    clickhouse: ClickHouseConfig = Field(default_factory=ClickHouseConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    spark: SparkConfig = Field(default_factory=SparkConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    paths: PathConfig = Field(default_factory=PathConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.paths.raw_data.mkdir(parents=True, exist_ok=True)
        self.paths.processed_data.mkdir(parents=True, exist_ok=True)
        self.paths.output_data.mkdir(parents=True, exist_ok=True)
        self.paths.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()
