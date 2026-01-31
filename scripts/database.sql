CREATE TABLE social_time_series
(
    `source` String,
    `category` String DEFAULT '', -- Không dùng Nullable, dùng chuỗi rỗng làm mặc định
    `bucket_start` DateTime,
    `bucket_end` DateTime,
    `post_count` Int64,
    `interaction_sum` Int64
)
ENGINE = MergeTree
PARTITION BY toDate(bucket_start)
ORDER BY (source, category, bucket_start);



CREATE TABLE social_burst_events
(
    source String,
    category  String DEFAULT '',
    bucket_start DateTime,
    bucket_end DateTime,
    post_count Int64,
    interaction_sum Int64,
    mean Float64,
    std Float64,
    burst_score Float64,
    is_burst Int8
)
ENGINE = MergeTree
PARTITION BY toDate(bucket_start)
ORDER BY (source, category, bucket_start);


CREATE TABLE social_daily_summary
(
    date Date,
    source String,
    category String DEFAULT '',
    total_posts Int64,
    total_interaction Int64,
    burst_count Int64
)
ENGINE = SummingMergeTree
PARTITION BY date
ORDER BY (date, source, category);


CREATE MATERIALIZED VIEW mv_social_daily_summary
TO social_daily_summary
AS
SELECT
    toDate(bucket_start) AS date,
    source,
    category,
    sum(post_count) AS total_posts,
    sum(interaction_sum) AS total_interaction,
    sumIf(1, is_burst = 1) AS burst_count
FROM social_burst_events
GROUP BY date, source, category;


CREATE TABLE social_top_bursts
(
    date Date,
    source String,
    category String DEFAULT '',
    bucket_start DateTime,
    burst_score Decimal(18, 4), -- Lưu tối đa 4 chữ số thập phân
    post_count Int64
)
ENGINE = MergeTree
PARTITION BY date
ORDER BY (date, burst_score); -- Decimal được phép nằm trong ORDER BY


ALTER TABLE social_time_series MODIFY COLUMN post_count Int64;
ALTER TABLE social_time_series MODIFY COLUMN interaction_sum Int64;

ALTER TABLE social_burst_events MODIFY COLUMN post_count Int64;
ALTER TABLE social_burst_events MODIFY COLUMN interaction_sum Int64;
ALTER TABLE social_burst_events MODIFY COLUMN is_burst Int8;

ALTER TABLE social_daily_summary MODIFY COLUMN total_posts Int64;
ALTER TABLE social_daily_summary MODIFY COLUMN total_interaction Int64;
ALTER TABLE social_daily_summary MODIFY COLUMN burst_count Int64;

ALTER TABLE social_top_bursts MODIFY COLUMN post_count Int64;
