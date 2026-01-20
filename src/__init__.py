"""
Package initialization
"""
__version__ = "1.0.0"
__author__ = "Social Media Analytics Team"
__description__ = "Social Media Data Processing and Event Detection System"

from src.config import config
from src.models import SocialMediaPost, ProcessedPost, EventDetection

__all__ = [
    'config',
    'SocialMediaPost',
    'ProcessedPost',
    'EventDetection',
]
