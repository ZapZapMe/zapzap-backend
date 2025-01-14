import logging
from datetime import datetime, timedelta

from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.db import Tip, Tweet, User
from schemas.tip import (
    LeaderboardReceived,
    LeaderboardSent,
    TipCreate,
    TipOut,
)
from services.lightning_service import create_invoice
from sqlalchemy import func
from sqlalchemy.orm import Session
from utils.tweet_data_extract import extract_username_and_tweet_id
from utils.security import get_current_user

router = APIRouter(prefix="/tips", tags=["tips"])


@router.get("/leaderboard_received", response_model=list[LeaderboardReceived])
def get_most_tipped_users(db: Session = Depends(get_db)):
    timerange = datetime.utcnow() - timedelta(days=30)

    # Label the columns to match the fields in LeaderboardReceived
    tips = (
        db.query(
            User.twitter_username.label("tip_recipient"),
            func.count(Tip.id).label("tip_count"),
            func.sum(Tip.amount_sats).label("total_amount_sats"),
        )
        .join(Tweet, Tweet.id == Tip.tweet_id)
        .join(User, User.id == Tweet.tweet_author)
        .filter(
            Tip.tip_sender.is_not(None),  # Exclude anonymous tips
            Tip.paid_in.is_(True),
            Tip.created_at >= timerange,
            Tip.tip_sender != Tweet.tweet_author,  # Exclude tipping themselves
        )
        .group_by(User.twitter_username)
        .order_by(func.sum(Tip.amount_sats).desc())
        .limit(10)
        .all()
    )
    print("TIPS: ", tips)

    # Build the response using the matching field names
    result = [
        LeaderboardReceived(
            tip_recipient=tip.tip_recipient,
            total_amount_sats=tip.total_amount_sats,
            tip_count=tip.tip_count,
        )
        for tip in tips
    ]

    return result


# most sent
@router.get("/leaderboard_sent", response_model=list[LeaderboardSent])
def get_most_active_tippers(db: Session = Depends(get_db)):
    timerange = datetime.utcnow() - timedelta(days=30)

    tips = (
        db.query(
            User.twitter_username.label("tip_sender"),
            func.count(Tip.id).label("tip_count"),
            func.sum(Tip.amount_sats).label("total_amount_sats"),
        )
        .join(Tip, User.id == Tip.tip_sender)
        .filter(
            Tip.tip_sender.is_not(None),  # Exclude anonymous tips
            Tip.paid_in.is_(True),  # Only tips that have been paid in
            Tip.created_at >= timerange,
        )
        .group_by(User.twitter_username)
        .order_by(func.sum(Tip.amount_sats).desc())
        .all()
    )
    print("TIPS: ", tips)
    result = [
        LeaderboardSent(
            tip_sender=tip.tip_sender,
            total_amount_sats=tip.total_amount_sats,
            tip_count=tip.tip_count,
        )
        for tip in tips
    ]

    return result


@router.post("/", response_model=TipOut)
def create_tip(
    tip_data: TipCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        username, tweet_id = extract_username_and_tweet_id(tip_data.tweet_url)
        tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
        if not tweet:
            logging.info(f"Tweet {tweet_id} not found. Creating new tweet.")
            receiver = db.query(User).filter(User.twitter_username == username).first()

            if receiver:
                if not receiver.wallet_address:
                    logging.warning(
                        f"Receiver {receiver.twitter_username} does not have a bolt12 address. Tip will be held."
                    )

            else:
                logging.warning(
                    f"Receiver {username} not found. Tip will be held until user registers."
                )
            tweet_author_id = receiver.id if receiver else None

            tweet = Tweet(
                id=tweet_id,
                tweet_author=tweet_author_id,
            )
            db.add(tweet)
            db.flush()

        payment_hash, bolt11_invoice = create_invoice(
            tip_data.amount_sats,
            f"⚡⚡ for https://x.com/{username}/status/{tweet_id}",
        )

        tip_sender_id = None


        new_tip = Tip(
            tip_sender=tip_sender_id,
            tweet_id=tweet_id,
            ln_payment_hash=payment_hash,
            comment=tip_data.comment,
            amount_sats=tip_data.amount_sats,
            created_at=datetime.utcnow(),
        )
        

        db.add(new_tip)
        db.commit()
        db.refresh(new_tip)
        print("BOLT11: ", bolt11_invoice)

        return new_tip

    except HTTPException as http_exc:
        logging.error(f"HTTP error occurred: {http_exc.detail}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create tip. Reason: {str(e)}")


@router.get("/", response_model=list[TipOut])
def list_tips(db: Session = Depends(get_db)):
    return db.query(Tip).all()


@router.get("/{tip_id}", response_model=TipOut)
def get_tip(tip_id: int, db: Session = Depends(get_db)):
    tip = db.query(Tip).filter(Tip.id == tip_id).first()
    if not tip:
        raise HTTPException(status_code=404, detail="Tip not found.")
    return tip

