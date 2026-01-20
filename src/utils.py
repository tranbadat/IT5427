"""
Utility functions and helpers
"""
import json
import hashlib
from typing import Any, Dict, List
from datetime import datetime
import pandas as pd


def format_number(num: int) -> str:
    """Format number with K, M, B suffixes"""
    if num < 1000:
        return str(num)
    elif num < 1_000_000:
        return f"{num/1000:.1f}K"
    elif num < 1_000_000_000:
        return f"{num/1_000_000:.1f}M"
    else:
        return f"{num/1_000_000_000:.1f}B"


def generate_id(text: str) -> str:
    """Generate unique ID from text"""
    return hashlib.md5(text.encode()).hexdigest()


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safe division avoiding ZeroDivisionError"""
    try:
        return a / b if b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def parse_datetime_flexible(dt: Any) -> datetime:
    """Parse datetime from various formats"""
    if isinstance(dt, datetime):
        return dt
    
    if isinstance(dt, str):
        # Try pandas parser
        try:
            return pd.to_datetime(dt).to_pydatetime()
        except:
            pass
    
    return datetime.now()


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def save_json(data: Any, filepath: str, indent: int = 2):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)


def load_json(filepath: str) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


class ProgressTracker:
    """Track processing progress"""
    
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = datetime.now()
    
    def update(self, count: int = 1):
        """Update progress"""
        self.current += count
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.current / elapsed if elapsed > 0 else 0
        
        print(f"\r{self.desc}: {self.current}/{self.total} ({percentage:.1f}%) - {rate:.1f} items/s", end='')
    
    def finish(self):
        """Finish progress tracking"""
        print()  # New line
