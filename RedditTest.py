import praw
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RedditReference:
    """Reddit参考评论数据类"""
    comment: str
    score: int
    awards: int
    subreddit: str

# Reddit API 配置（建议用环境变量或你的 config_manager 管理）
REDDIT_CLIENT_ID = "9C6poNE9n_xrDPG5G5yYqQ"
REDDIT_CLIENT_SECRET = "zRnZTdiGwHr-np9Du8uX9hJVLANpUA"
REDDIT_USER_AGENT = "NewsCommentBot/1.0 by Low-Throat-2067"

def search_reddit_posts(query: str, limit: int = 5) -> List[Dict]:
    """
    Search Reddit posts related to a given query.

    Args:
        query (str): Search keyword or news headline
        limit (int): Max number of results to return

    Returns:
        List[Dict]: [{'title','url','score','subreddit'}, ...]
    """
    results: List[Dict] = []
    q = (query or "").strip()
    if len(q) < 3:
        return results  # 太短直接返回空

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    references = []

    try:
        # 用相关度排序更稳定；需要“热门”可改成 sort="hot"
        submissions = reddit.subreddit("all").search(q, sort="relevance", limit=limit)
        for submission in submissions:
            # 获取高质量评论
            submission.comments.replace_more(limit=0)  # 展开评论

            for comment in submission.comments[:5]:
                references.append(RedditReference(
                    comment=comment.body[:300],  # 限制长度
                    score=comment.score,
                    awards=len(comment.all_awardings) if hasattr(comment, 'all_awardings') else 0,
                    subreddit=submission.subreddit.display_name,
                ))
                # 取前5个评论
    except Exception as e:
        print(f"❌ Reddit search failed: {e}")

    return references


if __name__ == "__main__":
    news_title = "OpenAI releases new GPT model"
    reddit_results = search_reddit_posts(news_title, limit=3)
