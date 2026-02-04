import os
import requests
import tweepy
import pandas as pd
import json
from datetime import datetime

class SocialFeedManager:
    def __init__(self, sources_file="social_sources.json"):
        self.sources_file = sources_file
        self.sources = self._load_sources()
        self.twitter_client = self._init_twitter()

    def _load_sources(self):
        if os.path.exists(self.sources_file):
            with open(self.sources_file, "r") as f:
                return json.load(f)
        return {"reddit": [], "twitter_users": [], "twitter_lists": []}

    def save_sources(self):
        with open(self.sources_file, "w") as f:
            json.dump(self.sources, f, indent=4)

    def add_source(self, source_type, identifier):
        if source_type in self.sources:
            if identifier not in self.sources[source_type]:
                self.sources[source_type].append(identifier)
                self.save_sources()
                return True
        return False

    def remove_source(self, source_type, identifier):
        if source_type in self.sources:
            if identifier in self.sources[source_type]:
                self.sources[source_type].remove(identifier)
                self.save_sources()
                return True
        return False

    def get_sources(self):
        return self.sources

    def _init_twitter(self):
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if bearer_token:
            return tweepy.Client(bearer_token=bearer_token)
        return None

    def _fetch_reddit(self, subreddit, limit=5):
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                posts = []
                for child in data['data']['children']:
                    post = child['data']
                    timestamp = datetime.fromtimestamp(post['created_utc'])
                    posts.append({
                        "source": "Reddit",
                        "source_name": f"r/{subreddit}",
                        "author": post['author'],
                        "text": post['title'] + "\n" + post.get('selftext', '')[:200], # Title + truncated body
                        "url": f"https://reddit.com{post['permalink']}",
                        "created_at": timestamp
                    })
                return posts
        except Exception as e:
            print(f"Error fetching Reddit r/{subreddit}: {e}")
        return []

    def _fetch_twitter_user(self, username, limit=5):
        if not self.twitter_client:
            return []
        try:
            user = self.twitter_client.get_user(username=username)
            if user.data:
                user_id = user.data.id
                tweets = self.twitter_client.get_users_tweets(id=user_id, max_results=limit, tweet_fields=['created_at', 'text'])
                posts = []
                if tweets.data:
                    for tweet in tweets.data:
                        posts.append({
                            "source": "Twitter",
                            "source_name": f"@{username}",
                            "author": username,
                            "text": tweet.text,
                            "url": f"https://twitter.com/{username}/status/{tweet.id}",
                            "created_at": tweet.created_at.replace(tzinfo=None) # naive datetime for sorting
                        })
                return posts
        except Exception as e:
            print(f"Error fetching Twitter user {username}: {e}")
        return []

    def _fetch_twitter_list(self, list_id, limit=5):
        if not self.twitter_client:
            return []
        try:
            tweets = self.twitter_client.get_list_tweets(id=list_id, max_results=limit, tweet_fields=['created_at', 'text', 'author_id'], expansions=['author_id'])
            
            # Map author IDs to usernames
            users = {u.id: u.username for u in tweets.includes['users']} if tweets.includes else {}
            
            posts = []
            if tweets.data:
                for tweet in tweets.data:
                    author_username = users.get(tweet.author_id, "unknown")
                    posts.append({
                        "source": "Twitter List",
                        "source_name": f"List {list_id}",
                        "author": author_username,
                        "text": tweet.text,
                        "url": f"https://twitter.com/{author_username}/status/{tweet.id}",
                        "created_at": tweet.created_at.replace(tzinfo=None)
                    })
            return posts
        except Exception as e:
            print(f"Error fetching Twitter List {list_id}: {e}")
        return []

    def get_feed(self):
        all_posts = []
        
        # Fetch Reddit
        for sub in self.sources.get("reddit", []):
            all_posts.extend(self._fetch_reddit(sub))
            
        # Fetch Twitter Users
        for user in self.sources.get("twitter_users", []):
            all_posts.extend(self._fetch_twitter_user(user))
            
        # Fetch Twitter Lists
        for lst in self.sources.get("twitter_lists", []):
            all_posts.extend(self._fetch_twitter_list(lst))
            
        # Sort by date (newest first)
        all_posts.sort(key=lambda x: x['created_at'], reverse=True)
        return all_posts
