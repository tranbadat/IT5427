"""
Data loader for reading CSV files and converting to unified schema
"""
import csv
import json
from pathlib import Path
from typing import Generator, List, Optional
from datetime import datetime

import pandas as pd
from loguru import logger

from src.models import SocialMediaPost, SourcePlatform, DocType


class DataLoader:
    """Load and parse social media data from CSV files"""
    
    def __init__(self, data_path: Path):
        self.data_path = Path(data_path)
    
    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """Load CSV file into DataFrame"""
        try:
            df = pd.read_csv(
                file_path,
                encoding="utf-8",
                on_bad_lines="skip",
                low_memory=False
            )
            logger.info(f"Loaded {len(df)} records from {file_path.name}")
            return df
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()
    
    def parse_json_field(self, value: str) -> any:
        """Parse JSON string fields"""
        if pd.isna(value) or not value:
            return None
        
        try:
            # Handle string representation of lists/dicts
            if isinstance(value, str):
                # Remove extra quotes and escape characters
                value = value.strip()
                if value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                return json.loads(value.replace("'", '"'))
            return value
        except (json.JSONDecodeError, ValueError):
            # If parsing fails, try to evaluate as Python literal
            try:
                import ast
                return ast.literal_eval(value)
            except:
                return value
    
    def parse_list_field(self, value: str) -> List[str]:
        """Parse list fields from CSV"""
        if pd.isna(value) or not value:
            return []
        
        parsed = self.parse_json_field(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
        elif isinstance(parsed, str):
            return [parsed] if parsed else []
        return []
    
    def parse_dict_field(self, value: str) -> dict:
        """Parse dictionary fields from CSV"""
        if pd.isna(value) or not value:
            return {}
        
        parsed = self.parse_json_field(value)
        if isinstance(parsed, dict):
            return parsed
        return {}
    
    def row_to_post(self, row: pd.Series) -> Optional[SocialMediaPost]:
        """Convert DataFrame row to SocialMediaPost"""
        try:
            # Extract reactions data
            reactions = self.parse_dict_field(row.get("reactions", "{}"))
            
            # Calculate engagement metrics from reactions if not present
            num_likes = int(row.get("numLikes", 0)) or reactions.get("likes", 0)
            num_shares = int(row.get("numShares", 0)) or reactions.get("reposts", 0) + reactions.get("quotes", 0)
            
            post = SocialMediaPost(
                doc_id=str(row.get("docId", "")),
                post_id=str(row.get("postId", "")),
                source=row.get("source", "unknown"),
                source_id=str(row.get("sourceId", "")),
                
                title=row.get("title"),
                content=row.get("content"),
                description=row.get("description"),
                tags=self.parse_list_field(row.get("tags", "[]")),
                
                pictures=self.parse_list_field(row.get("pictures", "[]")),
                link=row.get("link"),
                post_link=row.get("postLink", ""),
                domain=row.get("domain"),
                
                num_likes=num_likes,
                num_dislikes=int(row.get("numDislikes", 0)),
                num_comments=int(row.get("numComments", 0)),
                num_shares=num_shares,
                num_views=int(row.get("numViews", 0)),
                reactions=reactions,
                
                user_id=str(row.get("userId", "")),
                user_name=row.get("userName", ""),
                source_name=row.get("sourceName"),
                logo_link=row.get("logoLink"),
                
                doc_type=row.get("docType", "post"),
                type=row.get("type"),
                from_crawler=row.get("fromCrawler", "unknown"),
                categories=self.parse_list_field(row.get("categories", "[]")),
                provinces=self.parse_list_field(row.get("provinces", "[]")),
                
                create_date=row.get("createDate"),
                collect_date=row.get("collectDate"),
            )
            return post
        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            logger.debug(f"Problematic row: {row.to_dict()}")
            return None
    
    def load_posts(self, file_path: Path) -> Generator[SocialMediaPost, None, None]:
        """Generator to load posts from CSV file"""
        df = self.load_csv(file_path)
        
        for idx, row in df.iterrows():
            post = self.row_to_post(row)
            if post:
                yield post
    
    def load_all_files(self, pattern: str = "posts_*.csv") -> Generator[SocialMediaPost, None, None]:
        """Load all CSV files matching pattern"""
        files = sorted(self.data_path.glob(pattern))
        logger.info(f"Found {len(files)} files to process")
        
        for file_path in files:
            logger.info(f"Processing {file_path.name}")
            yield from self.load_posts(file_path)
    
    def load_batch(self, file_paths: List[Path], batch_size: int = 1000) -> Generator[List[SocialMediaPost], None, None]:
        """Load posts in batches"""
        batch = []
        
        for file_path in file_paths:
            for post in self.load_posts(file_path):
                batch.append(post)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
        
        # Yield remaining posts
        if batch:
            yield batch
