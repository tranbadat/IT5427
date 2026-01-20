# Sample test file
import pytest
from src.models import SocialMediaPost, SourcePlatform
from src.etl.data_cleaner import DataCleaner
from src.analysis.text_analyzer import EngagementCalculator
from datetime import datetime


def test_data_cleaner():
    """Test data cleaning functionality"""
    cleaner = DataCleaner()
    
    # Test text cleaning
    dirty_text = "Check out this link: http://example.com   Multiple  spaces!"
    clean_text = cleaner.clean_text(dirty_text)
    assert "http://" not in clean_text
    assert "  " not in clean_text
    
    # Test hashtag extraction
    text_with_tags = "This is #awesome and #cool"
    tags = cleaner.extract_hashtags(text_with_tags)
    assert "awesome" in tags
    assert "cool" in tags


def test_engagement_calculator():
    """Test engagement score calculation"""
    calc = EngagementCalculator()
    
    # Create mock post
    post = SocialMediaPost(
        doc_id="test1",
        post_id="test1",
        source=SourcePlatform.THREADS,
        source_id="test1",
        content="Test post",
        post_link="http://test.com",
        user_id="user1",
        user_name="testuser",
        create_date=datetime.now(),
        collect_date=datetime.now(),
        num_likes=100,
        num_shares=10,
        num_comments=5,
        from_crawler="test"
    )
    
    score = calc.calculate_engagement_score(post)
    # Score should be: 100*1 + 10*3 + 5*2 = 140
    assert score == 140.0


def test_viral_detection():
    """Test viral post detection"""
    calc = EngagementCalculator()
    
    # Viral post
    viral_post = SocialMediaPost(
        doc_id="viral1",
        post_id="viral1",
        source=SourcePlatform.THREADS,
        source_id="viral1",
        content="Viral content",
        post_link="http://test.com",
        user_id="user1",
        user_name="testuser",
        create_date=datetime.now(),
        collect_date=datetime.now(),
        num_likes=50000,
        num_shares=5000,
        num_comments=1000,
        from_crawler="test"
    )
    
    assert calc.is_viral(viral_post, threshold=10000) == True
    
    # Non-viral post
    normal_post = SocialMediaPost(
        doc_id="normal1",
        post_id="normal1",
        source=SourcePlatform.THREADS,
        source_id="normal1",
        content="Normal content",
        post_link="http://test.com",
        user_id="user1",
        user_name="testuser",
        create_date=datetime.now(),
        collect_date=datetime.now(),
        num_likes=100,
        num_shares=10,
        num_comments=5,
        from_crawler="test"
    )
    
    assert calc.is_viral(normal_post, threshold=10000) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
