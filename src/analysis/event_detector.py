"""
Event detection and burst analysis module
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger

from src.models import ProcessedPost, EventDetection, SourcePlatform


class EventDetector:
    """Detect and track event bursts in social media data"""
    
    def __init__(
        self,
        window_size: int = 24,  # hours
        threshold_zscore: float = 2.5,
        min_posts: int = 50
    ):
        self.window_size = window_size
        self.threshold_zscore = threshold_zscore
        self.min_posts = min_posts
    
    def detect_volume_spikes(
        self,
        posts: List[ProcessedPost],
        time_interval: str = '1H'
    ) -> List[Dict[str, Any]]:
        """Detect spikes in posting volume"""
        if not posts:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': p.create_date,
            'engagement': p.engagement_score,
            'platform': p.source
        } for p in posts])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Resample by time interval
        volume = df.resample(time_interval).size()
        engagement = df.resample(time_interval)['engagement'].sum()
        
        # Calculate statistics
        mean_volume = volume.mean()
        std_volume = volume.std()
        
        if std_volume == 0:
            return []
        
        # Calculate z-scores
        z_scores = (volume - mean_volume) / std_volume
        
        # Find spikes
        spikes = []
        for timestamp, z_score in z_scores.items():
            if z_score >= self.threshold_zscore and volume[timestamp] >= self.min_posts:
                spikes.append({
                    'timestamp': timestamp,
                    'volume': int(volume[timestamp]),
                    'z_score': float(z_score),
                    'engagement': float(engagement[timestamp]),
                    'is_spike': True
                })
        
        return spikes
    
    def detect_keyword_bursts(
        self,
        posts: List[ProcessedPost],
        min_frequency: int = 10
    ) -> List[Dict[str, Any]]:
        """Detect bursting keywords over time"""
        # Group posts by hour
        time_buckets = defaultdict(list)
        
        for post in posts:
            hour = post.create_date.replace(minute=0, second=0, microsecond=0)
            time_buckets[hour].append(post)
        
        # Count keyword frequencies per time bucket
        keyword_counts = defaultdict(lambda: defaultdict(int))
        
        for hour, hour_posts in time_buckets.items():
            for post in hour_posts:
                for keyword in post.keywords:
                    if keyword:
                        keyword_counts[keyword][hour] += 1
        
        # Calculate burst scores
        bursts = []
        
        for keyword, hourly_counts in keyword_counts.items():
            total_freq = sum(hourly_counts.values())
            
            if total_freq < min_frequency:
                continue
            
            # Convert to time series
            times = sorted(hourly_counts.keys())
            if len(times) < 3:
                continue
            
            counts = [hourly_counts[t] for t in times]
            
            # Calculate statistics
            mean_count = np.mean(counts)
            std_count = np.std(counts)
            
            if std_count == 0:
                continue
            
            max_count = max(counts)
            max_time = times[counts.index(max_count)]
            
            # Calculate burst score
            burst_score = (max_count - mean_count) / std_count if std_count > 0 else 0
            
            if burst_score >= self.threshold_zscore:
                bursts.append({
                    'keyword': keyword,
                    'total_frequency': total_freq,
                    'peak_frequency': max_count,
                    'peak_time': max_time,
                    'burst_score': float(burst_score),
                    'duration_hours': (times[-1] - times[0]).total_seconds() / 3600
                })
        
        # Sort by burst score
        bursts.sort(key=lambda x: x['burst_score'], reverse=True)
        
        return bursts
    
    def cluster_events(
        self,
        posts: List[ProcessedPost],
        time_window: timedelta = timedelta(hours=6),
        keyword_overlap: int = 2
    ) -> List[EventDetection]:
        """Cluster posts into events based on time and keywords"""
        events = []
        
        # Sort posts by time
        sorted_posts = sorted(posts, key=lambda p: p.create_date)
        
        current_cluster = []
        current_keywords = Counter()
        
        for post in sorted_posts:
            if not current_cluster:
                # Start new cluster
                current_cluster.append(post)
                current_keywords.update(post.keywords)
                continue
            
            # Check if post belongs to current cluster
            time_diff = post.create_date - current_cluster[-1].create_date
            
            # Check keyword overlap
            post_keywords = set(post.keywords)
            cluster_top_keywords = set([kw for kw, _ in current_keywords.most_common(10)])
            overlap = len(post_keywords & cluster_top_keywords)
            
            if time_diff <= time_window and overlap >= keyword_overlap:
                # Add to current cluster
                current_cluster.append(post)
                current_keywords.update(post.keywords)
            else:
                # Save current cluster and start new one
                if len(current_cluster) >= self.min_posts:
                    event = self._create_event_from_cluster(current_cluster, current_keywords)
                    if event:
                        events.append(event)
                
                # Start new cluster
                current_cluster = [post]
                current_keywords = Counter(post.keywords)
        
        # Don't forget the last cluster
        if len(current_cluster) >= self.min_posts:
            event = self._create_event_from_cluster(current_cluster, current_keywords)
            if event:
                events.append(event)
        
        return events
    
    def _create_event_from_cluster(
        self,
        posts: List[ProcessedPost],
        keywords: Counter
    ) -> Optional[EventDetection]:
        """Create EventDetection from a cluster of posts"""
        if not posts:
            return None
        
        # Get time range
        start_time = min(p.create_date for p in posts)
        end_time = max(p.create_date for p in posts)
        
        # Find peak time (hour with most posts)
        hour_counts = Counter()
        for post in posts:
            hour = post.create_date.replace(minute=0, second=0, microsecond=0)
            hour_counts[hour] += 1
        peak_time = hour_counts.most_common(1)[0][0]
        
        # Calculate metrics
        total_engagement = sum(p.engagement_score for p in posts)
        platforms = list(set(p.source for p in posts))
        
        # Top keywords
        top_keywords = [kw for kw, _ in keywords.most_common(10)]
        
        # Top posts by engagement
        top_posts = sorted(posts, key=lambda p: p.engagement_score, reverse=True)[:10]
        top_post_ids = [p.doc_id for p in top_posts]
        
        # Calculate growth rate
        time_span = (end_time - start_time).total_seconds() / 3600  # hours
        growth_rate = len(posts) / max(time_span, 1)
        
        # Calculate z-score (simplified)
        engagements = [p.engagement_score for p in posts]
        z_score = (np.max(engagements) - np.mean(engagements)) / (np.std(engagements) + 1e-10)
        
        # Generate event ID
        import hashlib
        event_id = hashlib.md5(
            f"{start_time.isoformat()}_{'-'.join(top_keywords[:3])}".encode()
        ).hexdigest()[:16]
        
        return EventDetection(
            event_id=event_id,
            keywords=top_keywords,
            start_time=start_time,
            end_time=end_time,
            peak_time=peak_time,
            total_posts=len(posts),
            total_engagement=int(total_engagement),
            platforms=platforms,
            growth_rate=float(growth_rate),
            z_score=float(z_score),
            top_posts=top_post_ids
        )
    
    def calculate_trend_score(
        self,
        current_volume: int,
        historical_volumes: List[int],
        current_engagement: float,
        historical_engagements: List[float]
    ) -> float:
        """Calculate trend score for a topic"""
        if not historical_volumes or not historical_engagements:
            return 0.0
        
        # Volume trend
        mean_vol = np.mean(historical_volumes)
        std_vol = np.std(historical_volumes)
        volume_score = (current_volume - mean_vol) / (std_vol + 1e-10)
        
        # Engagement trend
        mean_eng = np.mean(historical_engagements)
        std_eng = np.std(historical_engagements)
        engagement_score = (current_engagement - mean_eng) / (std_eng + 1e-10)
        
        # Combined score
        trend_score = 0.6 * volume_score + 0.4 * engagement_score
        
        return float(trend_score)
    
    def detect_anomalies(
        self,
        time_series: pd.Series,
        window: int = 24,
        threshold: float = 3.0
    ) -> List[Tuple[datetime, float]]:
        """Detect anomalies in time series data"""
        anomalies = []
        
        # Calculate rolling statistics
        rolling_mean = time_series.rolling(window=window, min_periods=1).mean()
        rolling_std = time_series.rolling(window=window, min_periods=1).std()
        
        # Calculate z-scores
        z_scores = (time_series - rolling_mean) / (rolling_std + 1e-10)
        
        # Find anomalies
        for timestamp, z_score in z_scores.items():
            if abs(z_score) >= threshold:
                anomalies.append((timestamp, float(z_score)))
        
        return anomalies
