"""
Test configuration and fixtures
"""
import pytest
from datetime import datetime
from src.models import SocialMediaPost, SourcePlatform


@pytest.fixture
def sample_post():
    """Create a sample post for testing"""
    return SocialMediaPost(
        doc_id="test123",
        post_id="post123",
        source=SourcePlatform.THREADS,
        source_id="source123",
        title="Sample Post Title",
        content="This is sample post content for testing purposes.",
        description="Sample description",
        tags=["test", "sample", "python"],
        pictures=["http://example.com/image.jpg"],
        link="http://example.com",
        post_link="http://threads.net/post/123",
        domain="threads.net",
        num_likes=100,
        num_dislikes=5,
        num_comments=20,
        num_shares=15,
        num_views=1000,
        reactions={"likes": 100, "reposts": 15},
        user_id="user123",
        user_name="testuser",
        source_name="Test User",
        logo_link="http://example.com/avatar.jpg",
        doc_type="post",
        from_crawler="test_crawler",
        categories=["technology"],
        provinces=[],
        create_date=datetime(2026, 1, 20, 10, 0, 0),
        collect_date=datetime(2026, 1, 20, 11, 0, 0)
    )


@pytest.fixture
def sample_posts_batch(sample_post):
    """Create a batch of sample posts"""
    posts = []
    for i in range(10):
        post = sample_post.copy(deep=True)
        post.doc_id = f"test{i}"
        post.post_id = f"post{i}"
        post.num_likes = 100 * (i + 1)
        posts.append(post)
    return posts
