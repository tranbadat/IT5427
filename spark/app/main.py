from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import StringType, StructField, StructType

# ==================================================
# CONFIG
# ==================================================
INPUT_DIR = "/opt/data/raw"
CHECKPOINT_DIR = "/opt/checkpoints/social_burst"

TIME_BUCKET = "1 hour"      # 5 minutes | 1 hour | 1 day
ROLLING_WINDOW = 6          # number of buckets for rolling mean/std
BURST_THRESHOLD = 2.5
MAX_FILES_PER_TRIGGER = 5
DEBUG_LOG = True  # set False after debugging

# ClickHouse
CLICKHOUSE_URL = "jdbc:clickhouse://clickhouse:8123/default"
CLICKHOUSE_DRIVER = "com.clickhouse.jdbc.ClickHouseDriver"
CLICKHOUSE_USER = "admin"
CLICKHOUSE_PASSWORD = "admin123"

TIME_SERIES_TABLE = "social_time_series"
BURST_TABLE = "social_burst_events"

# Source-specific CSV schemas (all string, cast later)
TWITTER_SCHEMA = StructType(
    [
        StructField("source", StringType(), True),
        StructField("docType", StringType(), True),
        StructField("type", StringType(), True),
        StructField("userId", StringType(), True),
        StructField("userName", StringType(), True),
        StructField("sourceId", StringType(), True),
        StructField("sourceName", StringType(), True),
        StructField("collectDate", StringType(), True),
        StructField("createDate", StringType(), True),
        StructField("postLink", StringType(), True),
        StructField("domain", StringType(), True),
        StructField("pictures", StringType(), True),
        StructField("content", StringType(), True),
        StructField("description", StringType(), True),
        StructField("tags", StringType(), True),
        StructField("title", StringType(), True),
        StructField("logoLink", StringType(), True),
        StructField("provinces", StringType(), True),
        StructField("categories", StringType(), True),
        StructField("link", StringType(), True),
        StructField("numLikes", StringType(), True),
        StructField("numDislikes", StringType(), True),
        StructField("numComments", StringType(), True),
        StructField("numShares", StringType(), True),
        StructField("numViews", StringType(), True),
        StructField("reactions", StringType(), True),
        StructField("docId", StringType(), True),
        StructField("postId", StringType(), True),
        StructField("fromCrawler", StringType(), True),
    ]
)

REDDIT_SCHEMA = StructType(
    [
        StructField("source", StringType(), True),
        StructField("docType", StringType(), True),
        StructField("type", StringType(), True),
        StructField("userId", StringType(), True),
        StructField("userName", StringType(), True),
        StructField("sourceId", StringType(), True),
        StructField("sourceName", StringType(), True),
        StructField("collectDate", StringType(), True),
        StructField("createDate", StringType(), True),
        StructField("postLink", StringType(), True),
        StructField("domain", StringType(), True),
        StructField("pictures", StringType(), True),
        StructField("title", StringType(), True),
        StructField("description", StringType(), True),
        StructField("tags", StringType(), True),
        StructField("content", StringType(), True),
        StructField("logoLink", StringType(), True),
        StructField("provinces", StringType(), True),
        StructField("categories", StringType(), True),
        StructField("link", StringType(), True),
        StructField("numLikes", StringType(), True),
        StructField("numDislikes", StringType(), True),
        StructField("numComments", StringType(), True),
        StructField("numShares", StringType(), True),
        StructField("numViews", StringType(), True),
        StructField("reactions", StringType(), True),
        StructField("docId", StringType(), True),
        StructField("postId", StringType(), True),
        StructField("fromCrawler", StringType(), True),
    ]
)

# ==================================================
# SPARK INIT
# ==================================================
def build_spark():
    return (
        SparkSession.builder
        .appName("SocialMediaEventBurstDetection")
        .getOrCreate()
    )

# ==================================================
# MAIN
# ==================================================
def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    # ------------------------------------------------
    # 1. READ CSV (recursive) + file path
    # ------------------------------------------------
    base_reader = (
        spark.readStream
        .format("csv")
        .option("header", "true")
        .option("maxFilesPerTrigger", MAX_FILES_PER_TRIGGER)
    )
    twitter_stream = base_reader.schema(TWITTER_SCHEMA).load(f"{INPUT_DIR}/twitter/*.csv")
    reddit_stream = base_reader.schema(REDDIT_SCHEMA).load(f"{INPUT_DIR}/reddit/*/*.csv")
    threads_stream = base_reader.schema(TWITTER_SCHEMA).load(f"{INPUT_DIR}/threads/*.csv")
    root_stream = base_reader.schema(TWITTER_SCHEMA).load(f"{INPUT_DIR}/*.csv")

    raw = (
        twitter_stream
        .unionByName(reddit_stream, allowMissingColumns=True)
        .unionByName(threads_stream, allowMissingColumns=True)
        .unionByName(root_stream, allowMissingColumns=True)
        .withColumn("_file_path", F.input_file_name())
    )

    # ------------------------------------------------
    # 2. EXTRACT source & category FROM PATH
    # ------------------------------------------------
    df = (
        raw
        .withColumn(
            "source",
            F.regexp_extract(
                F.col("_file_path"),
                r"raw/([^/]+)/",
                1
            )
        )
        .withColumn(
            "category",
            F.when(
                F.col("source") == "reddit",
                F.regexp_extract(
                    F.col("_file_path"),
                    r"raw/reddit/([^/]+)/",
                    1
                )
            ).otherwise(F.lit(None))
        )
    )

    # ------------------------------------------------
    # 3. NORMALIZE + CLEANING
    # ------------------------------------------------
    df = (
        df
        .withColumn(
            "createDate",
            F.coalesce(
                F.to_timestamp("createDate", "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX"),
                F.to_timestamp("createDate", "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"),
                F.to_timestamp("createDate", "yyyy-MM-dd'T'HH:mm:ssXXX"),
                F.to_timestamp("createDate")
            )
        )
        .withColumn("content", F.col("content").cast("string"))
        .withColumn("sourceId", F.col("sourceId").cast("string"))
        .withColumn("userId", F.col("userId").cast("string"))

        .withColumn("numLikes", F.coalesce(F.col("numLikes").cast("long"), F.lit(0)))
        .withColumn("numComments", F.coalesce(F.col("numComments").cast("long"), F.lit(0)))
        .withColumn("numShares", F.coalesce(F.col("numShares").cast("long"), F.lit(0)))

        .withColumn(
            "interaction_score",
            F.col("numLikes")
            + 2 * F.col("numComments")
            + 3 * F.col("numShares")
        )

        .filter(F.col("content").isNotNull() & (F.length(F.col("content")) > 0))
        .filter(F.col("createDate").isNotNull())

        # dedupe by source + sourceId with watermark
        .withWatermark("createDate", "2 days")
        .dropDuplicates(["source", "sourceId"])
    )

    # ------------------------------------------------
    # 4. TIME-SERIES AGGREGATION
    # ------------------------------------------------
    ts = (
        df
        .withColumn(
            "time_bucket",
            F.window(F.col("createDate"), TIME_BUCKET)
        )
        .groupBy(
            "source",
            "category",
            "time_bucket"
        )
        .agg(
            F.count(F.lit(1)).alias("post_count"),
            F.sum("interaction_score").alias("interaction_sum")
        )
        .select(
            "source",
            "category",
            F.col("time_bucket.start").alias("bucket_start"),
            F.col("time_bucket.end").alias("bucket_end"),
            "post_count",
            "interaction_sum"
        )
    )

    # ------------------------------------------------
    # 5. FOREACH BATCH: BURST + WRITE CLICKHOUSE
    # ------------------------------------------------
    def process_batch(batch_df, batch_id):
        if batch_df.rdd.isEmpty():
            return
        if DEBUG_LOG:
            cached = batch_df.cache()
            row_count = cached.count()
            print(f"[debug] batch_id={batch_id} rows={row_count}")
            cached.show(5, truncate=False)
            try:
                stats = (
                    cached
                    .select(
                        F.min("bucket_start").alias("min_bucket_start"),
                        F.max("bucket_end").alias("max_bucket_end"),
                        F.countDistinct("source").alias("source_count"),
                        F.countDistinct("category").alias("category_count"),
                    )
                    .collect()[0]
                )
                print(
                    "[debug] batch_id={bid} range={start}..{end} sources={sc} categories={cc}".format(
                        bid=batch_id,
                        start=stats["min_bucket_start"],
                        end=stats["max_bucket_end"],
                        sc=stats["source_count"],
                        cc=stats["category_count"],
                    )
                )
            except Exception as exc:
                print(f"[debug] batch_id={batch_id} failed to compute stats: {exc}")
            cached.unpersist()

        window_spec = (
            Window
            .partitionBy("source", "category")
            .orderBy("bucket_start")
            .rowsBetween(-(ROLLING_WINDOW - 1), 0)
        )

        scored = (
            batch_df
            .withColumn("mean", F.avg("post_count").over(window_spec))
            .withColumn("std", F.stddev_pop("post_count").over(window_spec))
            .withColumn(
                "burst_score",
                F.when(F.col("std").isNull() | (F.col("std") == 0), F.lit(0.0))
                 .otherwise((F.col("post_count") - F.col("mean")) / F.col("std"))
            )
            .withColumn(
                "is_burst",
                F.col("burst_score") > F.lit(BURST_THRESHOLD)
            )
        )

        # ---------- WRITE TIME SERIES ----------
        try:
            (
                batch_df
                .select(
                    "source",
                    "category",
                    "bucket_start",
                    "bucket_end",
                    "post_count",
                    "interaction_sum"
                )
                .write
                .mode("append")
                .format("jdbc")
                .option("url", CLICKHOUSE_URL)
                .option("dbtable", TIME_SERIES_TABLE)
                .option("driver", CLICKHOUSE_DRIVER)
                .option("user", CLICKHOUSE_USER)
                .option("password", CLICKHOUSE_PASSWORD)
                .save()
            )
            if DEBUG_LOG:
                print(f"[debug] batch_id={batch_id} wrote {TIME_SERIES_TABLE}")
        except Exception as exc:
            print(f"[error] batch_id={batch_id} failed write {TIME_SERIES_TABLE}: {exc}")
            raise

        # ---------- WRITE BURST EVENTS ----------
        try:
            (
                scored
                .select(
                    "source",
                    "category",
                    "bucket_start",
                    "bucket_end",
                    "post_count",
                    "interaction_sum",
                    "mean",
                    "std",
                    "burst_score",
                    F.col("is_burst").cast("int").alias("is_burst")
                )
                .write
                .mode("append")
                .format("jdbc")
                .option("url", CLICKHOUSE_URL)
                .option("dbtable", BURST_TABLE)
                .option("driver", CLICKHOUSE_DRIVER)
                .option("user", CLICKHOUSE_USER)
                .option("password", CLICKHOUSE_PASSWORD)
                .save()
            )
            if DEBUG_LOG:
                print(f"[debug] batch_id={batch_id} wrote {BURST_TABLE}")
        except Exception as exc:
            print(f"[error] batch_id={batch_id} failed write {BURST_TABLE}: {exc}")
            raise

    # ------------------------------------------------
    # 6. START STREAM
    # ------------------------------------------------
    query = (
        ts.writeStream
        .outputMode("update")
        .option("checkpointLocation", CHECKPOINT_DIR)
        .trigger(processingTime="30 seconds")
        .foreachBatch(process_batch)
        .start()
    )

    query.awaitTermination()


# ==================================================
# ENTRY POINT
# ==================================================
if __name__ == "__main__":
    main()
