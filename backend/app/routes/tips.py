import logging
from datetime import datetime, timedelta

from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.db import Tip, User
from schemas.tip import (
    LeaderboardReceived,
    LeaderboardSent,
    TipCreate,
    TipOut,
)
from services.lightning_service import create_invoice
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from utils.tweet_data_extract import extract_username_and_tweet_id

router = APIRouter(prefix="/tips", tags=["tips"])


@router.get("/leaderboard_received", response_model=list[LeaderboardReceived])
def get_most_tipped_users(db: Session = Depends(get_db)):
    timerange = datetime.utcnow() - timedelta(days=30)

    tips = (
        db.query(
            User.twitter_username.label("tip_recipient"),
            func.sum(Tip.amount_sats).label("total_amount_sats"),
            func.count(Tip.id).label("tip_count"),
        )
        .join(User, User.id == Tip.tip_recipient)
        .filter(Tip.paid_in.is_(True), Tip.created_at >= timerange)
        .group_by(User.twitter_username)
        .order_by(desc("total_amount_sats"))
        .limit(10)
        .all()
    )

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
            Tip.tipper_display_name,
            func.sum(Tip.amount_sats).label("total_amount_sats"),
            func.count(Tip.id).label("tip_count"),
        )
        .filter(Tip.paid_in.is_(True), Tip.created_at >= timerange, Tip.tipper_display_name != "anonymous")
        .group_by(Tip.tipper_display_name)
        .order_by(desc("total_amount_sats"))
        .limit(10)
        .all()
    )

    # Convert the query result to a list of LeaderboardSent
    result = [
        LeaderboardSent(
            tipper_display_name=tip.tipper_display_name,
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

        receiver = db.query(User).filter(User.twitter_username == username)

        if receiver:
            if not receiver.wallet_address:
                logging.warning(
                    f"Receiver {receiver.recipient_twitter_username} does not have a bolt12 address. Tip will be held."
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
            recipient_twitter_username=tip_data.tip_recipient,
            tweet_id=tip_data.tweet_id,
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


# @router.put("/{tip_id}", response_model=TipOut)
# def update_tip_status(
#     tip_id: int,
#     tip_data: TipUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     tip = db.query(Tip).filter(Tip.id == tip_id).first()
#     if not tip:
#         raise HTTPException(status_code=404, detail="Tip not found.")

#     if tip.tipper_user_id != current_user.id:
#         raise HTTPException(
#             status_code=403, detail="You can only update your own tips."
#         )

#     tip.comment = tip_data.comment
#     db.commit()
#     db.refresh(tip)
#     return tip
