from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.tip import Tip
from schemas.tip import TipUpdate, TipCreate, TipOut
from utils.security import get_current_user
from services.lightning_service import create_invoice, get_balance
from models.user import User
import logging

router = APIRouter(prefix="/tips", tags=["tips"])


@router.post("/", response_model=TipOut)
def create_tip(
    anonymous_user_id: int,
    tip_data: TipCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        bolt11, payment_hash, tip_fee = create_invoice(
            tip_data.amount_sats,
            f"Tip from anonymous - {tip_data.comment}",
        )

        new_tip = Tip(
            tipper_user_id=anonymous_user_id,
            recipient_twitter_username=tip_data.recipient_twitter_username,
            tweet_url=str(tip_data.tweet_url),
            bolt11_invoice=bolt11,
            ln_payment_hash=payment_hash,
            comment=tip_data.comment,
            amount_sats=tip_data.amount_sats - tip_fee,
            paid=False,
        )

        db.add(new_tip)
        db.commit()
        db.refresh(new_tip)

        return new_tip

    except Exception as e:
        logging.error(f"Error creating tip: {e}")
        raise HTTPException(status_code=400, detail="Failed to craete tip.")


@router.get("/", response_model=TipOut)
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
