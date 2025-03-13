import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

import tweepy
from config import settings
from db import SessionLocal, get_db
from models.db import ProcessedMention
from sqlalchemy.orm import Session


class TwitterMentionMonitor:
    def __init__(self):
        # Initialize client using your existing Twitter credentials
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_ACCOUNT_BEARER_TOKEN,
            consumer_key=settings.TWITTER_OAUTH2_CLIENT_ID,
            consumer_secret=settings.TWITTER_OAUTH2_CLIENT_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        )
        self.pattern = re.compile(r"@zapzapbot\s+(\d+)", re.IGNORECASE)
        self.bot_username = "zapzapbot"

    async def start_monitoring(self):
        """Start the monitoring loop that runs every 30 seconds"""
        logging.info("Starting Twitter mention monitoring")
        while True:
            try:
                await self.check_mentions()
            except Exception as e:
                logging.error(f"Error checking Twitter mentions: {e}")

            # Wait 30 seconds before checking again
            await asyncio.sleep(61)

    async def check_mentions(self):
        """Check for new mentions and process them"""
        logging.info("Checking for new Twitter mentions")

        # Get the timestamp of the most recent processed mention from the database
        db = SessionLocal()
        latest_mention = db.query(ProcessedMention).order_by(ProcessedMention.processed_at.desc()).first()
        start_time = (
            latest_mention.processed_at if latest_mention else (datetime.now(timezone.utc) - timedelta(hours=1))
        )
        db.close()

        # Query Twitter API for recent mentions
        try:
            mentions = self.client.search_recent_tweets(
                query=f"@{self.bot_username}", start_time=start_time, tweet_fields=["created_at", "author_id", "text"]
            )
        except Exception as e:
            logging.error(f"Failed to retrieve mentions: {e}")
            return

        if not mentions or not mentions.data:
            logging.info("No new mentions found")
            return

        # Process each mention
        for tweet in mentions.data:
            await self.process_mention(tweet)

    async def process_mention(self, tweet):
        """Process a single mention tweet"""
        # Check if we've already processed this tweet
        db = SessionLocal()
        try:
            existing = db.query(ProcessedMention).filter_by(tweet_id=tweet.id).first()
            if existing:
                logging.debug(f"Already processed tweet {tweet.id}")
                return

            # Look for the pattern "@zapzapbot <number>"
            match = self.pattern.search(tweet.text)
            if match:
                number = match.group(1)
                logging.info(f"Found mention with number: {number} from user {tweet.author_id}")

                # Send DM to the user
                await self.send_dm(tweet.author_id, number)

                # Mark as processed
                db.add(
                    ProcessedMention(
                        tweet_id=tweet.id, author_id=tweet.author_id, processed_at=datetime.now(timezone.utc)
                    )
                )
                db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error processing mention: {e}")
        finally:
            db.close()

    async def send_dm(self, user_id, number):
        """Send a DM to the user who mentioned the bot"""
        try:
            # Customize this message as needed
            message = f"Thanks for your mention! I see you mentioned the number {number}."

            # Send DM using Twitter API
            self.client.create_direct_message(participant_id=user_id, text=message)
            logging.info(f"Sent DM to user {user_id}")
        except Exception as e:
            logging.error(f"Failed to send DM: {e}")


mention_monitor = TwitterMentionMonitor()
