import logging
from datetime import datetime, timedelta, timezone

from config import settings
from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.db import Tip, Tweet, User
from schemas.tip import LeaderboardReceived, LeaderboardSent, TipCreate, TipInvoice, TipOut, TipSummary
from services.lightning_service import create_invoice
from services.twitter_service import get_avatars_for_usernames
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased
from utils.tweet_data_extract import extract_username_and_tweet_id
from utils.security import get_current_user

router = APIRouter(prefix="/tips", tags=["tips"])

User2 = aliased(User)


# most tipped users
@router.get("/leaderboard_received", response_model=list[LeaderboardReceived])
def get_most_tipped_users(db: Session = Depends(get_db)):
    timerange = datetime.now(timezone.utc) - timedelta(days=settings.LEADERBOARD_CALCULATION_WINDOW_DAYS)

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
            Tip.tip_sender != Tweet.tweet_author,  # Exclude self-tips
        )
        .group_by(User.twitter_username)
        .order_by(func.sum(Tip.amount_sats).desc())
        .limit(10)
        .all()
    )
    # Get the usernames from the query results
    usernames = [t.tip_recipient for t in tips]

    # Get avatars in one batch call
    avatars_map = get_avatars_for_usernames(usernames, db)

    # Build the final response
    result = []
    for t in tips:
        avatar_url = avatars_map.get(t.tip_recipient) or ""
        result.append(
            LeaderboardReceived(
                tip_recipient=t.tip_recipient,
                total_amount_sats=t.total_amount_sats,
                tip_count=t.tip_count,
                avatar_url=avatar_url,
            )
        )

    return result


# biggest tippers
@router.get("/leaderboard_sent", response_model=list[LeaderboardSent])
def get_most_active_tippers(db: Session = Depends(get_db)):
    timerange = datetime.now(timezone.utc) - timedelta(days=settings.LEADERBOARD_CALCULATION_WINDOW_DAYS)

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
        .limit(10)
        .all()
    )
    # Get the usernames from the query results
    usernames = [t.tip_sender for t in tips]

    # Get avatars in one batch call
    avatars_map = get_avatars_for_usernames(usernames, db)

    # Build the response
    result = []
    for t in tips:
        avatar_url = avatars_map.get(t.tip_sender) or ""
        result.append(
            LeaderboardSent(
                tip_sender=t.tip_sender,
                total_amount_sats=t.total_amount_sats,
                tip_count=t.tip_count,
                avatar_url=avatar_url,  # Add avatar URL to your schema if needed
            )
        )

    return result


@router.post("/", response_model=TipInvoice)
def create_tip(
    tip_data: TipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        username, tweet_id = extract_username_and_tweet_id(tip_data.tweet_url)
        tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
        if not tweet:
            logging.info(f"Tweet {tweet_id} not found. Creating new tweet.")
            receiver = db.query(User).filter(User.twitter_username == username).first()

            if not receiver:
                logging.warning(f"Receiver {username} not found in DB. Creating new user with is_registered=False.")
                receiver = User(twitter_username=username, is_registered=False)
                db.add(receiver)
                db.flush()

            else:
                if not receiver.wallet_address:
                    logging.warning(
                        f"Receiver {receiver.twitter_username} does not have a bolt12 address. Tip will be held."
                    )

            tweet = Tweet(
                id=tweet_id,
                tweet_author=receiver.id,
            )
            db.add(tweet)
            db.flush()

        payment_hash, bolt11_invoice = create_invoice(
            tip_data.amount_sats,
            f"⚡⚡ for https://x.com/{username}/status/{tweet_id}",
        )

        tip_sender_id = None

        new_tip = Tip(
            tip_sender=current_user.id,
            tweet_id=tweet_id,
            ln_payment_hash=payment_hash,
            comment=tip_data.comment,
            amount_sats=tip_data.amount_sats,
            created_at=datetime.now(timezone.utc),
        )

        db.add(new_tip)
        db.commit()
        db.refresh(new_tip)
        logging.info(f"New tip created: {new_tip.id} for tweet {tweet_id}")
        print("BOLT11: ", bolt11_invoice)

        return TipInvoice(tip_recipient=username, amount_sats=new_tip.amount_sats, bolt11_invoice=bolt11_invoice, payment_hash=payment_hash)

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


@router.get("/sent/{username}", response_model=list[TipSummary])
def get_sent_tips_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.twitter_username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")

    tips = (
        db.query(
            User.twitter_username.label("tip_sender"),
            Tip.amount_sats,
            Tip.created_at,
            Tip.tweet_id,
            Tweet.id.label("tweet_id"),
            User2.twitter_username.label("recipient"),
            Tip.comment,  # Adding comment to the query
        )
        .join(User, User.id == Tip.tip_sender)
        .join(Tweet, Tweet.id == Tip.tweet_id)
        .join(User2, User2.id == Tweet.tweet_author)
        .filter(Tip.tip_sender == user.id)
        .all()
    )

    recipient_usernames = [tip.recipient for tip in tips]
    
    avatars_map = get_avatars_for_usernames(recipient_usernames, db)

    return [
        TipSummary(
            tip_sender=tip.tip_sender,
            recipient=tip.recipient,
            amount_sats=tip.amount_sats,
            created_at=tip.created_at,
            tweet_id=tip.tweet_id,
            avatar_url=avatars_map.get(tip.recipient),
            comment=tip.comment,
            tip_type="sent",
        )
        for tip in tips
    ]


@router.get("/received/{username}", response_model=list[TipSummary])
def get_received_tips_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.twitter_username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")
    
    tips = (
        db.query(Tip)
        .join(Tweet, Tweet.id == Tip.tweet_id)
        .join(User, User.id == Tweet.tweet_author)
        .filter(Tweet.tweet_author == user.id)
        .all()
    )

    sender_usernames = [tip.sender.twitter_username for tip in tips if tip.sender is not None]
    
    avatars_map = get_avatars_for_usernames(sender_usernames, db)
    
    return [
        TipSummary(
            tip_sender=tip.sender.twitter_username if tip.sender else None,
            amount_sats=tip.amount_sats,
            created_at=tip.created_at,
            tweet_id=tip.tweet_id,
            recipient=username,
            avatar_url=avatars_map.get(tip.sender.twitter_username) if tip.sender else None,
            comment=tip.comment,
            tip_type="received",
        ) 
        for tip in tips
    ]