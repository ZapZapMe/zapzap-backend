# services/twitter_service.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from sqlalchemy import func
import tweepy
from config import settings
from fastapi import HTTPException
from models.db import Tip, User
from sqlalchemy.orm import Session

try:
    twitter_client = tweepy.Client(
        bearer_token=settings.TWITTER_ACCOUNT_BEARER_TOKEN,
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    )
    logging.info("Initialized Twitter client successfully...")
except Exception as e:
    logging.error(f"Failed to initialize Tweepy client: {e}")
    twitter_client = None


def get_user_twitter_client(access_token: str, access_token_secret: str) -> tweepy.Client:
    """
    Create a Tweepy Client for user-authenticated actions (OAuth 1.0a).
    """
    return tweepy.Client(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )


def post_reply_dynamic(tweet_id: str, reply_text: str, user: User | None):
    """
    Post a reply to a tweet using either the user's or the app's tokens.
    """
    if user and user.twitter_access_token and user.twitter_access_secret:
        logging.info(f"[post_reply_dynamic] Posting as user @{user.twitter_username}")
        user_client = get_user_twitter_client(user.twitter_access_token, user.twitter_access_secret)
        try:
            response = user_client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
            logging.info(f"[post_reply_dynamic] User tweet posted. Response: {response.data}")
            return response.data
        except tweepy.TweepyException as e:
            logging.error(f"[post_reply_dynamic] Error posting with user token: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # Fallback to app-level authentication
    logging.info("[post_reply_dynamic] Using global app-level twitter_client...")
    if not twitter_client:
        raise HTTPException(status_code=400, detail="Global Twitter client not initialized.")

    try:
        response = twitter_client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
        logging.info(f"[post_reply_dynamic] App-level tweet posted. Response: {response.data}")
        return response.data
    except tweepy.TweepyException as e:
        logging.error(f"[post_reply_dynamic] Error posting with app token: {e}")
        raise HTTPException(status_code=400, detail=str(e))




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


def post_reply_to_twitter_with_comment(db: Session, tip: Tip, user: User | None = None):
    """
    High-level function that:
      1) Builds the reply text from 'tip'
      2) Calls 'post_reply_dynamic' to decide whether to use user tokens or app tokens.
    """
    if not tip.tweet:
        logging.warning(f"Tweet {tip.tweet_id} not found. Skipping reply.")
        return

    tweet_id_str = str(tip.tweet_id)
    comment = tip.comment or "No comment"

    tweet_author_user = tip.tweet.author
    mention_text = f"@{tweet_author_user.twitter_username}" if tweet_author_user else "someone"

    reply_text = f"{mention_text}, your tip is paid by some!\n{comment}\n#ZapZap"

    # Call our new dynamic function
    response_data = post_reply_dynamic(tweet_id_str, reply_text, user)
    logging.info(f"[post_reply_to_twitter_with_comment] Response: {response_data}")


def get_avatars_for_usernames(
    usernames: List[str],
    db: Session,
) -> Dict[str, str]:
    cutoff = datetime.now() - timedelta(weeks=settings.TWITTER_AVATAR_CACHE_TTL_DAYS)
    
    # Fetch existing users from DB
    existing_users = db.query(User).filter(func.lower(User.twitter_username).in_([u.lower() for u in usernames])).all()
    user_map = {u.twitter_username: u for u in existing_users}  # Use original case as key

    # Separate who needs a refresh
    needs_refresh = [
        u.twitter_username for u in existing_users if not u.avatar_updated_at or u.avatar_updated_at < cutoff
    ]
    
    # Find any usernames not in DB yet (case-insensitive check)
    existing_usernames_lower = {u.twitter_username.lower() for u in existing_users}
    missing = [uname for uname in usernames if uname.lower() not in existing_usernames_lower]

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
    for user_obj in existing_users:
        result[user_obj.twitter_username] = user_obj.avatar_url or ""

    return result
