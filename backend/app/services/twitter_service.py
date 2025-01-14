# services/twitter_service.py
import logging

import tweepy
from config import settings
from fastapi import HTTPException
from models.db import Tip
from sqlalchemy.orm import Session

# We'll create a single Tweepy client for your user tokens (the account that will post tweets)
# Make sure your tokens have read/write access in the dev portal.
# The account that owns these tokens will be the one replying to tweets.

# Typically you'd store these in settings or environment variables
api_key = settings.TWITTER_CLIENT_ID
api_secret = settings.TWITTER_CLIENT_SECRET
access_token = settings.TWITTER_ACCESS_TOKEN
access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET

try:
    # Create a Tweepy Client. By default in Tweepy >=4.0, this uses OAuth1 user context.
    twitter_client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
except Exception as e:
    logging.error(f"Failed to initialize Tweepy client: {e}")
    twitter_client = None


def post_reply_with_tweepy(tweet_id: str, reply_text: str):
    """
    Use Tweepy client to post a reply.
    Return the response dict from Twitter, or raise HTTPException if it fails.
    """
    if not twitter_client:
        raise HTTPException(status_code=400, detail="Twitter client is not initialized.")

    try:
        # Use tweepy.Client.create_tweet to post a reply
        response = twitter_client.create_tweet(
            text=reply_text,
            in_reply_to_tweet_id=tweet_id,  # ensures it's a reply
        )
        logging.info(f"Posted reply to Tweet ID={tweet_id}. Twitter response: {response.data}")
        return response.data
    except tweepy.TweepyException as e:
        logging.error(f"Tweepy error while replying to Tweet ID {tweet_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


def post_reply_to_twitter_with_comment(db: Session, tip: Tip):
    """
    High-level function that:
      1) Builds the reply text from 'tip'
      2) Calls 'post_reply_with_tweepy' to post a reply.
    """
    if not tip.tweet:
        logging.warning(f"Tweet {tip.tweet_id} not found. Skipping reply.")
        return

    tweet_id_str = str(tip.tweet_id)
    comment = tip.comment or "No comment"

    tweet_author_user = tip.tweet.author
    if tweet_author_user:
        mention_text = f"@{tweet_author_user.twitter_username}"
    else:
        mention_text = "someone"

    reply_text = f"{mention_text}, your tip is paid!\n" f"{comment}\n" f"#ZapZap"

    try:
        response_data = post_reply_with_tweepy(tweet_id=tweet_id_str, reply_text=reply_text)
        logging.info(f"Posted reply to tweet {tweet_id_str} for Tip #{tip.id}. Response: {response_data}")
    except HTTPException as http_exc:
        logging.error(f"HTTP error occurred: {http_exc.detail}")
        raise
