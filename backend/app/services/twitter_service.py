import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import tweepy
from config import settings
from fastapi import HTTPException
from models.db import Tip, User
from sqlalchemy import func
from sqlalchemy.orm import Session

# Module-level client initialization
twitter_client = tweepy.Client(
    consumer_key=settings.TWITTER_CONSUMER_KEY,
    consumer_secret=settings.TWITTER_CONSUMER_SECRET,
    access_token=settings.TWITTER_ACCESS_TOKEN,
    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
)


def post_tweet(tweet_id: str, text: str):
    try:
        response = twitter_client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
        return response.data
    except tweepy.TweepyException as e:
        error_msg = f"Twitter API error: {e}"
        logging.error(error_msg)
        raise HTTPException(status_code=502, detail=error_msg)


def update_user_avatars(db: Session, usernames: List[str]) -> None:
    try:
        for i in range(0, len(usernames), 100):
            batch = usernames[i : i + 100]
            response = twitter_client.get_users(usernames=batch, user_fields=["profile_image_url"])

            if not response.data:
                continue

            for user_data in response.data:
                db.merge(
                    User(
                        twitter_username=user_data.username.lower(),
                        avatar_url=user_data.profile_image_url,
                        avatar_updated_at=datetime.now(timezone.utc),
                    )
                )
        db.commit()
    except tweepy.TooManyRequests:
        logging.warning("Twitter rate limit reached")
    except Exception as e:
        logging.error(f"Twitter API error: {e}")


def get_avatars_for_usernames(usernames: List[str], db: Session) -> Dict[str, str]:
    cutoff = datetime.now() - timedelta(weeks=settings.TWITTER_AVATAR_CACHE_TTL_DAYS)

    existing_users = db.query(User).filter(func.lower(User.twitter_username).in_([u.lower() for u in usernames])).all()

    to_update = {
        u.twitter_username for u in existing_users if not u.avatar_updated_at or u.avatar_updated_at < cutoff
    } | {u for u in usernames if u.lower() not in {eu.twitter_username.lower() for eu in existing_users}}

    if to_update:
        update_user_avatars(db, list(to_update))
        existing_users = (
            db.query(User).filter(func.lower(User.twitter_username).in_([u.lower() for u in usernames])).all()
        )

    return {u.twitter_username: u.avatar_url or "" for u in existing_users}


def post_reply_to_twitter_with_comment(db: Session, tip: Tip) -> None:
    if not tip.tweet:
        logging.warning(f"Tweet {tip.tweet_id} not found. Skipping reply.")
        return

    comment = tip.comment or ""
    tipper_username = f"@{tip.sender.twitter_username}" if tip.sender else "Anonymous"
    recipient = tip.tweet.author.twitter_username

    # Base reply text
    reply_text = f"⚡{comment}⚡ {tipper_username} zapped you {tip.amount_sats} sats"

    # Add zap-zap.me link only if the receiver has NO wallet address
    if not tip.tweet.author.wallet_address:
        reply_text += f" zap-zap.me/{recipient}"

    try:
        response = post_tweet(str(tip.tweet_id), reply_text)
        tip.reply_tweet_id = response["id"]
        db.commit()
        logging.info(f"Posted reply to tweet {tip.tweet_id} for Tip #{tip.id}. Response: {response}")
    except HTTPException as e:
        logging.error(f"HTTP error occurred: {e.detail}")
        raise
