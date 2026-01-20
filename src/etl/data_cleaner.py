"""
Data cleaning and normalization module
"""
import re
from typing import Optional, List
from datetime import datetime

import pandas as pd
from loguru import logger
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)


class DataCleaner:
    """Clean and normalize social media data"""
    
    def __init__(self, remove_stopwords: bool = False):
        self.remove_stopwords = remove_stopwords
        try:
            self.stopwords = set(stopwords.words('english'))
        except:
            self.stopwords = set()
    
    def clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Convert to string
        text = str(text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.,!?-]', '', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def remove_emoji(self, text: str) -> str:
        """Remove emoji from text"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        if not text:
            return []
        return re.findall(r'#(\w+)', text)
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text"""
        if not text:
            return []
        return re.findall(r'@(\w+)', text)
    
    def normalize_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize URL"""
        if not url:
            return None
        
        # Remove tracking parameters
        url = re.sub(r'\?.*$', '', url)
        
        # Ensure https
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        elif not url.startswith('https://'):
            url = 'https://' + url
        
        return url.lower()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text"""
        if not text:
            return []
        
        try:
            tokens = word_tokenize(text.lower())
            
            if self.remove_stopwords:
                tokens = [t for t in tokens if t not in self.stopwords and len(t) > 2]
            
            return tokens
        except:
            # Fallback to simple split
            return text.lower().split()
    
    def clean_username(self, username: Optional[str]) -> str:
        """Clean and normalize username"""
        if not username:
            return ""
        
        # Remove @ symbol
        username = username.lstrip('@')
        
        # Remove special characters
        username = re.sub(r'[^\w\-_.]', '', username)
        
        return username.lower()
    
    def normalize_timestamp(self, timestamp: any) -> datetime:
        """Normalize timestamp to datetime"""
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            # Try parsing various formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
            ]:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
            
            # Use pandas as fallback
            try:
                return pd.to_datetime(timestamp)
            except:
                logger.warning(f"Could not parse timestamp: {timestamp}")
                return datetime.utcnow()
        
        return datetime.utcnow()
    
    def deduplicate_list(self, items: List[str]) -> List[str]:
        """Remove duplicates while preserving order"""
        seen = set()
        result = []
        for item in items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                result.append(item)
        return result
    
    def calculate_text_quality_score(self, text: str) -> float:
        """Calculate text quality score (0-1)"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Length score (prefer 50-500 chars)
        length = len(text)
        if 50 <= length <= 500:
            score += 0.3
        elif length > 20:
            score += 0.15
        
        # Has meaningful words (not just links/mentions)
        words = re.findall(r'\b\w{3,}\b', text)
        if len(words) >= 5:
            score += 0.3
        elif len(words) >= 2:
            score += 0.15
        
        # Not all caps
        if text.upper() != text:
            score += 0.2
        
        # Has punctuation (indicates proper sentences)
        if re.search(r'[.!?]', text):
            score += 0.2
        
        return min(score, 1.0)
