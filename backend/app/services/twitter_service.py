import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import tweepy
from config import settings
from fastapi import HTTPException
from models.db import Tip, User
from sqlalchemy import func
from sqlalchemy.orm import Session


async def verify_twitter_credentials():
    request_id = str(uuid.uuid4())
    logging.info(f"[{request_id}] Verifying Twitter credentials")

    # First, let's check if we even have a token
    if not settings.TWITTER_ACCOUNT_BEARER_TOKEN:
        logging.error(f"[{request_id}] Bearer token is missing")
        raise ValueError("Missing Twitter bearer token")

    # Log the first few characters of the token (safely)
    token_preview = (
        "..." + settings.TWITTER_ACCOUNT_BEARER_TOKEN[-10:] if settings.TWITTER_ACCOUNT_BEARER_TOKEN else "None"
    )
    logging.info(f"[{request_id}] Bearer token ends with: {token_preview}")

    try:
        logging.info(f"[{request_id}] Attempting to test bearer token...")
        response = read_client.get_user(username="twitter")
        if response and response.data:
            logging.info(f"[{request_id}] Successfully verified bearer token")
            return True
    except tweepy.errors.Unauthorized as e:
        logging.error(f"[{request_id}] Authorization failed with bearer token: {str(e)}")
        raise ValueError("Invalid Twitter bearer token - unauthorized")
    except Exception as e:
        logging.error(f"[{request_id}] Unexpected error testing bearer token: {str(e)}")
        raise ValueError(f"Error verifying Twitter bearer token: {str(e)}")


read_client = tweepy.Client(
    bearer_token=settings.TWITTER_ACCOUNT_BEARER_TOKEN,
)


write_client = tweepy.Client(
    consumer_key=settings.TWITTER_CONSUMER_KEY,
    consumer_secret=settings.TWITTER_CONSUMER_SECRET,
    access_token=settings.TWITTER_ACCESS_TOKEN,
    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
)


def add_rate_limit_tracking(response) -> None:
    """Log rate limit information from Twitter API response headers"""
    try:
        # Extract rate limit info from response headers if available
        if hasattr(response, "response") and response.response:
            headers = response.response.headers
            try:
                reset_timestamp = int(headers.get("x-rate-limit-reset", "0"))
                reset_time = datetime.fromtimestamp(reset_timestamp, timezone.utc)
                logging.info(
                    f"Rate Limits: "
                    f"Limit={headers.get('x-rate-limit-limit', 'N/A')}, "
                    f"Remaining={headers.get('x-rate-limit-remaining', 'N/A')}, "
                    f"Reset={reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            except (ValueError, TypeError):
                logging.debug("Could not parse rate limit headers")
    except Exception as e:
        logging.debug(f"Rate limit tracking error: {str(e)}")


def update_user_avatars(db: Session, usernames: List[str]) -> None:
    request_id = str(uuid.uuid4())
    logging.info(f"[{request_id}] Starting avatar update for usernames: {usernames}")

    try:
        for i in range(0, len(usernames), 100):
            batch = usernames[i : i + 100]
            response = read_client.get_users(usernames=batch, user_fields=["profile_image_url"])

            # Log full response details
            logging.info(f"[{request_id}] Twitter API Response: {response}")
            if response.data:
                for user in response.data:
                    logging.info(
                        f"[{request_id}] User data received: username={user.username}, "
                        f"avatar_url={user.profile_image_url}"
                    )

            # Log rate limit details from headers
            if hasattr(response, "response") and response.response:
                headers = response.response.headers
                logging.info(f"[{request_id}] Rate Limit Headers: {dict(headers)}")

            if not response.data:
                logging.warning(f"[{request_id}] No user data returned for batch: {batch}")
                continue

            for user_data in response.data:
                try:
                    existing_user = (
                        db.query(User).filter(func.lower(User.twitter_username) == user_data.username.lower()).first()
                    )

                    # Log what we're doing with each user
                    if existing_user:
                        logging.info(f"[{request_id}] Updating existing user {user_data.username}")
                        logging.info(f"[{request_id}] Old avatar: {existing_user.avatar_url}")
                        logging.info(f"[{request_id}] New avatar: {user_data.profile_image_url}")
                        existing_user.avatar_url = user_data.profile_image_url
                        existing_user.avatar_updated_at = datetime.now(timezone.utc)
                    else:
                        logging.info(f"[{request_id}] Creating new user {user_data.username}")
                        db.add(
                            User(
                                twitter_username=user_data.username.lower(),
                                avatar_url=user_data.profile_image_url,
                                avatar_updated_at=datetime.now(timezone.utc),
                            )
                        )

                except Exception as e:
                    logging.error(f"[{request_id}] Error processing user {user_data.username}: {str(e)}")
                    logging.error(f"[{request_id}] Full user data: {user_data}")
                    db.rollback()
                    continue

            db.commit()

    except tweepy.TooManyRequests as e:
        headers = e.response.headers
        logging.error(f"[{request_id}] Rate limit exceeded. Headers: {dict(headers)}")
        reset_time = datetime.fromtimestamp(int(headers["x-rate-limit-reset"]), timezone.utc)
        logging.error(f"[{request_id}] Rate limit resets at: {reset_time}")
    except Exception as e:
        logging.error(f"[{request_id}] Twitter API error: {e}")
        db.rollback()


def post_tweet(tweet_id: str, text: str):
    try:
        response = write_client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
        # Add rate limit tracking for write operations
        add_rate_limit_tracking(response)
        return response.data
    except tweepy.TweepyException as e:
        error_msg = f"Twitter API error: {e}"
        logging.error(error_msg)
        raise HTTPException(status_code=502, detail=error_msg)


def get_avatars_for_usernames(usernames: List[str], db: Session) -> Dict[str, str]:
    request_id = str(uuid.uuid4())

    try:
        existing_users = (
            db.query(User).filter(func.lower(User.twitter_username).in_([u.lower() for u in usernames])).all()
        )

        try:
            cache_ttl_days = int(settings.TWITTER_AVATAR_CACHE_TTL_DAYS)
        except (ValueError, TypeError):
            logging.warning(
                f"[{request_id}] Invalid TWITTER_AVATAR_CACHE_TTL_DAYS value, using default: {cache_ttl_days}"
            )

        cutoff = datetime.now(timezone.utc) - timedelta(days=cache_ttl_days)

        existing_users = (
            db.query(User).filter(func.lower(User.twitter_username).in_([u.lower() for u in usernames])).all()
        )

        to_update = set()
        for username in usernames:
            try:
                user = next((u for u in existing_users if u.twitter_username.lower() == username.lower()), None)
                if not user:
                    to_update.add(username)
                    continue

                if not user.avatar_updated_at:
                    to_update.add(username)
                    continue

                # Ensure avatar_updated_at is timezone aware
                try:
                    updated_at = user.avatar_updated_at
                    if updated_at.tzinfo is None:
                        updated_at = updated_at.replace(tzinfo=timezone.utc)
                    if updated_at < cutoff:
                        to_update.add(username)
                except (AttributeError, TypeError) as e:
                    logging.error(f"[{request_id}] Error processing timestamp for user {username}: {str(e)}")
                    to_update.add(username)  # Update on error to be safe

            except Exception as e:
                logging.error(f"[{request_id}] Error processing user {username}: {str(e)}")
                continue

        if to_update:
            try:
                logging.info(f"[{request_id}] Updating avatars for {len(to_update)} users")
                update_user_avatars(db, list(to_update))
                # Refresh the query in a new transaction
                db.rollback()  # Clear any pending transaction
                existing_users = (
                    db.query(User).filter(func.lower(User.twitter_username).in_([u.lower() for u in usernames])).all()
                )
            except Exception as e:
                logging.error(f"[{request_id}] Error during avatar update: {str(e)}")

        result = {u.twitter_username: u.avatar_url or "" for u in existing_users}
        return result

    except Exception as e:
        logging.error(f"[{request_id}] Error: {str(e)}")
        return {username: "" for username in usernames}


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
