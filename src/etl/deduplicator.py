"""
Deduplication module for detecting duplicate and near-duplicate posts
"""
import hashlib
from typing import List, Tuple, Set, Dict
from collections import defaultdict

from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.models import SocialMediaPost, ProcessedPost


class Deduplicator:
    """Detect and handle duplicate posts"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.seen_hashes: Set[str] = set()
        self.content_index: Dict[str, str] = {}  # hash -> doc_id
    
    def compute_hash(self, text: str) -> str:
        """Compute hash of normalized text"""
        # Normalize text for hashing
        normalized = ''.join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def compute_content_hash(self, post: SocialMediaPost) -> str:
        """Compute hash based on post content"""
        content_parts = [
            post.content or "",
            post.title or "",
            post.description or "",
        ]
        combined = " ".join(content_parts)
        return self.compute_hash(combined)
    
    def is_exact_duplicate(self, post: SocialMediaPost) -> Tuple[bool, str]:
        """Check if post is an exact duplicate"""
        content_hash = self.compute_content_hash(post)
        
        if content_hash in self.seen_hashes:
            # Find original post ID
            original_id = self.content_index.get(content_hash, "")
            return True, original_id
        
        # Register this post
        self.seen_hashes.add(content_hash)
        self.content_index[content_hash] = post.doc_id
        return False, ""
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts"""
        try:
            # Create TF-IDF vectors
            vectors = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except:
            # Fallback to simple comparison
            set1 = set(text1.lower().split())
            set2 = set(text2.lower().split())
            if not set1 or not set2:
                return 0.0
            jaccard = len(set1 & set2) / len(set1 | set2)
            return jaccard
    
    def find_near_duplicates_batch(self, posts: List[SocialMediaPost]) -> List[Tuple[int, int, float]]:
        """Find near-duplicate pairs in a batch of posts"""
        if len(posts) < 2:
            return []
        
        # Extract text content
        texts = []
        for post in posts:
            content_parts = [
                post.content or "",
                post.title or "",
                post.description or "",
            ]
            texts.append(" ".join(content_parts))
        
        # Compute TF-IDF matrix
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Compute pairwise similarities
            similarities = cosine_similarity(tfidf_matrix)
            
            # Find pairs above threshold
            duplicates = []
            n = len(posts)
            for i in range(n):
                for j in range(i + 1, n):
                    if similarities[i, j] >= self.similarity_threshold:
                        duplicates.append((i, j, similarities[i, j]))
            
            return duplicates
        except Exception as e:
            logger.error(f"Error computing similarities: {e}")
            return []
    
    def detect_cross_platform_duplicates(self, posts: List[SocialMediaPost]) -> Dict[str, List[str]]:
        """Detect posts shared across platforms"""
        # Group by content hash
        content_groups = defaultdict(list)
        
        for post in posts:
            content_hash = self.compute_content_hash(post)
            content_groups[content_hash].append(post)
        
        # Find groups with multiple platforms
        cross_platform = {}
        for content_hash, group in content_groups.items():
            if len(group) > 1:
                platforms = set(p.source for p in group)
                if len(platforms) > 1:
                    # This content appeared on multiple platforms
                    doc_ids = [p.doc_id for p in group]
                    cross_platform[content_hash] = doc_ids
        
        return cross_platform
    
    def mark_duplicates(self, posts: List[ProcessedPost]) -> List[ProcessedPost]:
        """Mark duplicate posts in a batch"""
        if not posts:
            return posts
        
        # Find near-duplicates
        duplicates = self.find_near_duplicates_batch(posts)
        
        # Create set of duplicate indices (keep first occurrence)
        duplicate_indices = set()
        duplicate_map = {}  # index -> (original_index, score)
        
        for i, j, score in duplicates:
            if j not in duplicate_map:
                duplicate_map[j] = (i, score)
                duplicate_indices.add(j)
        
        # Mark duplicates
        for idx in duplicate_indices:
            original_idx, similarity = duplicate_map[idx]
            posts[idx].is_duplicate = True
            posts[idx].duplicate_of = posts[original_idx].doc_id
            posts[idx].similarity_score = similarity
        
        # Detect cross-platform
        cross_platform = self.detect_cross_platform_duplicates(posts)
        for doc_ids in cross_platform.values():
            for post in posts:
                if post.doc_id in doc_ids:
                    post.cross_platform_ids = [
                        did for did in doc_ids if did != post.doc_id
                    ]
        
        return posts
    
    def filter_duplicates(self, posts: List[ProcessedPost], keep_first: bool = True) -> List[ProcessedPost]:
        """Filter out duplicate posts"""
        if keep_first:
            return [p for p in posts if not p.is_duplicate]
        else:
            # Keep the one with highest engagement
            unique_groups = defaultdict(list)
            for post in posts:
                key = post.duplicate_of if post.is_duplicate else post.doc_id
                unique_groups[key].append(post)
            
            result = []
            for group in unique_groups.values():
                # Sort by engagement score and keep best
                best = max(group, key=lambda p: p.engagement_score)
                result.append(best)
            
            return result
