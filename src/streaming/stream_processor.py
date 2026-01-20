"""
Real-time streaming data processor using Spark Structured Streaming
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from loguru import logger

from src.config import config


class StreamProcessor:
    """Process social media data in real-time using Spark Streaming"""
    
    def __init__(self):
        self.config = config.spark
        self.spark = self._create_spark_session()
    
    def _create_spark_session(self) -> SparkSession:
        """Create Spark session"""
        spark = SparkSession.builder \
            .appName(self.config.app_name) \
            .master(self.config.master) \
            .config("spark.driver.memory", self.config.driver_memory) \
            .config("spark.executor.memory", self.config.executor_memory) \
            .config("spark.sql.streaming.checkpointLocation", "./checkpoints") \
            .getOrCreate()
        
        logger.info(f"Created Spark session: {self.config.app_name}")
        return spark
    
    def create_schema(self) -> StructType:
        """Define schema for social media posts"""
        return StructType([
            StructField("doc_id", StringType(), False),
            StructField("post_id", StringType(), False),
            StructField("source", StringType(), False),
            StructField("content", StringType(), True),
            StructField("title", StringType(), True),
            StructField("tags", ArrayType(StringType()), True),
            StructField("num_likes", IntegerType(), True),
            StructField("num_shares", IntegerType(), True),
            StructField("num_comments", IntegerType(), True),
            StructField("num_views", IntegerType(), True),
            StructField("user_id", StringType(), True),
            StructField("user_name", StringType(), True),
            StructField("create_date", TimestampType(), False),
            StructField("collect_date", TimestampType(), False),
            StructField("engagement_score", FloatType(), True),
        ])
    
    def process_file_stream(self, input_path: str, output_path: str):
        """Process streaming CSV files"""
        schema = self.create_schema()
        
        # Read streaming data
        df = self.spark.readStream \
            .schema(schema) \
            .option("header", "true") \
            .csv(input_path)
        
        # Add processing timestamp
        df = df.withColumn("processing_time", current_timestamp())
        
        # Calculate engagement score if not present
        df = df.withColumn(
            "engagement_score",
            when(col("engagement_score").isNull(),
                 col("num_likes") * 1.0 +
                 col("num_shares") * 3.0 +
                 col("num_comments") * 2.0 +
                 col("num_views") * 0.01
            ).otherwise(col("engagement_score"))
        )
        
        # Write to console (for debugging)
        query = df.writeStream \
            .outputMode("append") \
            .format("console") \
            .option("truncate", "false") \
            .start()
        
        # Write to parquet
        parquet_query = df.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", f"{output_path}/_checkpoint") \
            .start()
        
        return query, parquet_query
    
    def aggregate_by_window(
        self,
        input_path: str,
        output_path: str,
        window_duration: str = "1 hour",
        watermark_delay: str = "10 minutes"
    ):
        """Aggregate posts by time windows"""
        schema = self.create_schema()
        
        df = self.spark.readStream \
            .schema(schema) \
            .option("header", "true") \
            .csv(input_path)
        
        # Add watermark for late data
        df = df.withWatermark("create_date", watermark_delay)
        
        # Aggregate by window
        windowed = df.groupBy(
            window(col("create_date"), window_duration),
            col("source")
        ).agg(
            count("*").alias("post_count"),
            sum("num_likes").alias("total_likes"),
            sum("num_shares").alias("total_shares"),
            sum("num_comments").alias("total_comments"),
            avg("engagement_score").alias("avg_engagement"),
            countDistinct("user_id").alias("unique_users")
        )
        
        # Write aggregated results
        query = windowed.writeStream \
            .outputMode("update") \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", f"{output_path}/_checkpoint") \
            .start()
        
        return query
    
    def detect_trending_keywords(
        self,
        input_path: str,
        output_path: str,
        window_duration: str = "5 minutes"
    ):
        """Detect trending keywords in real-time"""
        schema = self.create_schema()
        
        df = self.spark.readStream \
            .schema(schema) \
            .option("header", "true") \
            .csv(input_path)
        
        # Explode tags array
        df = df.withColumn("tag", explode(col("tags")))
        
        # Filter empty tags
        df = df.filter(col("tag") != "")
        
        # Add watermark
        df = df.withWatermark("create_date", "10 minutes")
        
        # Aggregate tags by window
        trending = df.groupBy(
            window(col("create_date"), window_duration),
            col("tag")
        ).agg(
            count("*").alias("frequency"),
            sum("engagement_score").alias("total_engagement")
        ).orderBy(col("frequency").desc())
        
        # Write results
        query = trending.writeStream \
            .outputMode("complete") \
            .format("memory") \
            .queryName("trending_keywords") \
            .start()
        
        return query
    
    def detect_viral_posts(
        self,
        input_path: str,
        output_path: str,
        engagement_threshold: int = 10000
    ):
        """Detect viral posts in real-time"""
        schema = self.create_schema()
        
        df = self.spark.readStream \
            .schema(schema) \
            .option("header", "true") \
            .csv(input_path)
        
        # Filter viral posts
        viral = df.filter(col("engagement_score") >= engagement_threshold)
        
        # Add viral flag
        viral = viral.withColumn("is_viral", lit(True))
        viral = viral.withColumn("detected_at", current_timestamp())
        
        # Write to output
        query = viral.writeStream \
            .outputMode("append") \
            .format("json") \
            .option("path", output_path) \
            .option("checkpointLocation", f"{output_path}/_checkpoint") \
            .start()
        
        return query
    
    def join_cross_platform_data(
        self,
        twitter_path: str,
        reddit_path: str,
        threads_path: str,
        output_path: str
    ):
        """Join data from multiple platforms"""
        schema = self.create_schema()
        
        # Read from multiple sources
        twitter = self.spark.readStream.schema(schema).csv(twitter_path)
        reddit = self.spark.readStream.schema(schema).csv(reddit_path)
        threads = self.spark.readStream.schema(schema).csv(threads_path)
        
        # Union all sources
        all_posts = twitter.union(reddit).union(threads)
        
        # Add processing
        all_posts = all_posts.withColumn("processing_time", current_timestamp())
        
        # Write unified stream
        query = all_posts.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", f"{output_path}/_checkpoint") \
            .partitionBy("source", "create_date") \
            .start()
        
        return query
    
    def stop(self):
        """Stop Spark session"""
        if self.spark:
            self.spark.stop()
            logger.info("Stopped Spark session")


def main():
    """Main streaming application"""
    processor = StreamProcessor()
    
    try:
        # Process file stream
        logger.info("Starting streaming processor...")
        
        input_path = str(config.paths.raw_data / "*.csv")
        output_path = str(config.paths.processed_data / "streaming")
        
        # Start streaming queries
        file_query, parquet_query = processor.process_file_stream(input_path, output_path)
        
        # Aggregate by window
        agg_output = str(config.paths.output_data / "aggregated")
        agg_query = processor.aggregate_by_window(input_path, agg_output)
        
        # Detect trending
        trending_output = str(config.paths.output_data / "trending")
        trending_query = processor.detect_trending_keywords(input_path, trending_output)
        
        # Wait for termination
        logger.info("Streaming queries started. Press Ctrl+C to stop.")
        file_query.awaitTermination()
        
    except KeyboardInterrupt:
        logger.info("Stopping streaming processor...")
    finally:
        processor.stop()


if __name__ == "__main__":
    main()
