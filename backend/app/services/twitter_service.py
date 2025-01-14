from fastapi import HTTPException

import requests
from config import settings
import logging
from sqlalchemy.orm import Session
from models.db import Tip

def post_reply_to_tweet(
        tweet_id: str,
        reply_text: str,
        bearer_token: str,
):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "text": reply_text,
        "reply": {"in reply to tweet": tweet_id},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to post reply to Twitter. Reason: {str(e)}")
    

def post_reply_to_twitter_with_comment(db: Session, tip: Tip):
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

    reply_text = (
        f"{mention_text}, your tip is paid!\n"
        f"{comment}\n"
        f"#ZapZap"
    )

    bearer_token = settings.TWITTER_ACCOUNT_BEARER_TOKEN 
    try:
        response_data = post_reply_to_tweet(
            tweet_id=tweet_id_str,
            reply_text=reply_text,
            bearer_token=bearer_token,
        )
        logging.info(f"Posted reply to tweet {tweet_id_str} for Tip #{tip.id}. Response: {response_data}")
    except HTTPException as http_exc:
        logging.error(f"HTTP error occurred: {http_exc.detail}")
        raise





# if anoymous tip
#   post from @zap-zap.me acount and don't include comments
#   {reply-to tweet}  "someone anonymous has tipped you 100 sats go to https://zap-zap.me/{recipient_username} to view" 

# if logged in, post as the logged in user, include the comments 
#   post from {tip_sender}    
#   {reply-to tweet} "@username tipped you 100sats at https://zap-zap.me/{username}  {comment}"