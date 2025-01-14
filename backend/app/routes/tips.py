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


@router.get("/leaderboard_sent", response_model=list[LeaderboardSent])
def get_most_active_tippers(db: Session = Depends(get_db)):
    timerange = datetime.utcnow() - timedelta(days=30)

    tips = (
        db.query(
            User.twitter_username.label("username"),
            func.count(Tip.id).label("number_of_tips"),
            func.sum(Tip.amount_sats).label("sum_of_tips"),
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

    leaderboard = []
    for row in tips:
        leaderboard.append(
            {
                "username": row.username,
                "number_of_tips": row.number_of_tips,
                "sum_of_tips": row.sum_of_tips,
            }
        )

    return leaderboard


@router.post("/", response_model=TipOut)
def create_tip(
    tip_data: TipCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        username, tweet_id = extract_username_and_tweet_id(tip_data.tweet_url)

        receiver = db.query(User).filter(User.twitter_username == username).first()

        if receiver:
            if not receiver.wallet_address:
                logging.warning(
                    f"Receiver {receiver.twitter_username} does not have a bolt12 address. Tip will be held."
                )

        else:
            logging.warning(
                f"Receiver {tip_data.recipient_twitter_username} not found. Tip will be held until user registers."
            )

        payment_hash = create_invoice(
            tip_data.amount_sats,
            f"⚡⚡ for https://x.com/{tip_data.recipient_twitter_username}/status/{tip_data.tweet_id}",
        )

        new_tip = Tip(
            tipper_display_name=tip_data.tip_sender or "anonymous",
            tip_receiver=receiver.id if receiver else None,
            tweet_id=tweet_id,
            ln_payment_hash=payment_hash,
            comment=tip_data.comment,
            amount_sats=tip_data.amount_sats,
            paid_in=False,
            paid_out=False,
            created_at=datetime.utcnow(),
        )

        db.add(new_tip)
        db.commit()
        db.refresh(new_tip)
        print("Created NEW TIP!")

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
