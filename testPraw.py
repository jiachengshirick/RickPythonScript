import praw

# 既不传 client_id，也不传 client_secret
reddit = praw.Reddit()
print("配置加载成功，当前 user_agent:", reddit.user_agent)