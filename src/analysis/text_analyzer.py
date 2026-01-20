"""
Text analysis and NLP module
"""
from typing import List, Tuple, Dict, Any, Optional
import re

from loguru import logger
import spacy
from textblob import TextBlob
from langdetect import detect, LangDetectException

from src.models import ProcessedPost


class TextAnalyzer:
    """Natural language processing and text analysis"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Spacy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect text language"""
        if not text or len(text) < 10:
            return None
        
        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return None
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob"""
        if not text:
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'label': 'neutral'
            }
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Classify sentiment
        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'label': label
        }
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords using TF-IDF and NER"""
        if not text or not self.nlp:
            return []
        
        doc = self.nlp(text)
        
        # Extract noun phrases and named entities
        keywords = set()
        
        # Named entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'PRODUCT']:
                keywords.add(ent.text.lower())
        
        # Noun chunks
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Max 3 words
                keywords.add(chunk.text.lower())
        
        # Important single tokens
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                if len(token.text) > 3:
                    keywords.add(token.text.lower())
        
        return list(keywords)[:top_n]
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities"""
        if not text or not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return entities
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """Calculate readability metrics"""
        if not text:
            return {'flesch_reading_ease': 0.0, 'avg_word_length': 0.0}
        
        # Count sentences, words, syllables
        sentences = text.count('.') + text.count('!') + text.count('?')
        sentences = max(sentences, 1)
        
        words = len(text.split())
        if words == 0:
            return {'flesch_reading_ease': 0.0, 'avg_word_length': 0.0}
        
        # Approximate syllable count
        syllables = sum(self._count_syllables(word) for word in text.split())
        
        # Flesch Reading Ease
        flesch = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        flesch = max(0, min(100, flesch))  # Clamp to 0-100
        
        avg_word_length = sum(len(word) for word in text.split()) / words
        
        return {
            'flesch_reading_ease': flesch,
            'avg_word_length': avg_word_length
        }
    
    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count for a word"""
        word = word.lower()
        syllables = 0
        vowels = 'aeiouy'
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllables += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            syllables -= 1
        
        # Ensure at least one syllable
        return max(syllables, 1)
    
    def detect_topics(self, texts: List[str], n_topics: int = 5) -> List[Dict[str, Any]]:
        """Detect topics from multiple texts (simplified version)"""
        # This is a simplified version. For production, use LDA or other topic modeling
        from collections import Counter
        
        all_keywords = []
        for text in texts:
            keywords = self.extract_keywords(text)
            all_keywords.extend(keywords)
        
        # Count keyword frequencies
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(n_topics * 3)
        
        # Group into topics (simplified)
        topics = []
        for i in range(0, min(len(top_keywords), n_topics * 3), 3):
            topic_keywords = [kw for kw, _ in top_keywords[i:i+3]]
            if topic_keywords:
                topics.append({
                    'keywords': topic_keywords,
                    'weight': sum(count for _, count in top_keywords[i:i+3])
                })
        
        return topics[:n_topics]


class EngagementCalculator:
    """Calculate engagement scores and metrics"""
    
    @staticmethod
    def calculate_engagement_score(post: ProcessedPost) -> float:
        """Calculate weighted engagement score"""
        # Weights for different engagement types
        weights = {
            'likes': 1.0,
            'shares': 3.0,  # Shares are more valuable
            'comments': 2.0,
            'views': 0.01,  # Views are less valuable
        }
        
        score = (
            post.num_likes * weights['likes'] +
            post.num_shares * weights['shares'] +
            post.num_comments * weights['comments'] +
            post.num_views * weights['views']
        )
        
        return float(score)
    
    @staticmethod
    def calculate_virality_score(post: ProcessedPost) -> float:
        """Calculate virality score (0-100)"""
        # Normalize engagement by followers/platform average
        engagement = EngagementCalculator.calculate_engagement_score(post)
        
        # Simple logarithmic scale
        import math
        if engagement <= 0:
            return 0.0
        
        # Scale: 100 likes = 10, 1000 likes = 30, 10000 = 50, 100000 = 70
        virality = 10 * math.log10(engagement + 1)
        return min(virality, 100.0)
    
    @staticmethod
    def calculate_velocity(post: ProcessedPost, current_time: Any) -> float:
        """Calculate engagement velocity (engagement per hour)"""
        from datetime import datetime
        
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time)
        
        time_diff = (current_time - post.create_date).total_seconds() / 3600  # hours
        if time_diff <= 0:
            return 0.0
        
        engagement = EngagementCalculator.calculate_engagement_score(post)
        return engagement / time_diff
    
    @staticmethod
    def is_viral(post: ProcessedPost, threshold: int = 10000) -> bool:
        """Determine if post is viral based on engagement"""
        total_engagement = (
            post.num_likes +
            post.num_shares * 2 +
            post.num_comments * 1.5
        )
        return total_engagement >= threshold
