# services/twitter_service.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import tweepy
from config import settings
from fastapi import HTTPException
from models.db import Tip, User
from sqlalchemy.orm import Session

try:
    twitter_client = tweepy.Client(
        bearer_token=settings.TWITTER_ACCOUNT_BEARER_TOKEN,
        consumer_key=settings.TWITTER_OAUTH2_CLIENT_ID,
        consumer_secret=settings.TWITTER_OAUTH2_CLIENT_SECRET,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    )
    logging.info("Initialized Twitter client successfully...")
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


def get_avatars_for_usernames(
    usernames: List[str],
    db: Session,
) -> Dict[str, str]:
    """
    Returns a dict of {username: avatar_url}.
    Fetches from DB if still valid (less than refresh_interval_weeks old),
    otherwise calls Twitter API and updates DB.
    """
    cutoff = datetime.now() - timedelta(weeks=settings.TWITTER_AVATAR_CACHE_TTL_DAYS)
    # Fetch existing users from DB
    existing_users = db.query(User).filter(User.twitter_username.in_(usernames)).all()
    user_map = {u.twitter_username.lower(): u for u in existing_users}

    # Separate who needs a refresh
    needs_refresh = [
        u.twitter_username for u in existing_users if not u.avatar_updated_at or u.avatar_updated_at < cutoff
    ]
    # Find any usernames not in DB yet
    missing = [uname for uname in usernames if uname.lower() not in user_map]

    to_update = list(set(needs_refresh + missing))
    result = {}

    # Fetch fresh data from Twitter for those who need it
    if to_update:
        try:
            # Up to 100 at once. Adjust as needed for larger lists.
            # user_fields must include profile_image_url for this to work
            response = twitter_client.get_users(usernames=to_update, user_fields=["profile_image_url"])
            if response.data:
                for user_data in response.data:
                    uname = user_data.username.lower()
                    avatar_url = user_data.profile_image_url
                    if uname in user_map:
                        # Update existing record
                        db_user = user_map[uname]
                    else:
                        # Create new record
                        db_user = User(twitter_username=user_data.username)
                        db.add(db_user)
                        user_map[uname] = db_user
                    db_user.avatar_url = avatar_url
                    db_user.avatar_updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            logging.error(f"Error calling Twitter API: {e}")

    # Build final result from updated DB state
    for uname, user_obj in user_map.items():
        result[uname] = user_obj.avatar_url or ""

    return {u: result.get(u.lower(), "") for u in usernames}
