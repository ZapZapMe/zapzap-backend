from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.tip import Tip
from schemas.tip import TipUpdate, TipCreate, TipOut
from utils.security import get_current_user
from services.lightning_service import create_invoice, get_balance
from models.user import User
import logging
from datetime import datetime
router = APIRouter(prefix="/tips", tags=["tips"])


@router.post("/", response_model=TipOut)
def create_tip(
    tip_data: TipCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    try:
        receiver = db.query(User).filter(User.twitter_username == tip_data.recipient_twitter_username.lstrip("@")).first()
        if receiver and not receiver.has_account:
            logging.warning(f"Receiver @{receiver.twitter_username} exists but has not completed account setup.")

        if not receiver:
            receiver = User(
                twitter_username=tip_data.recipient_twitter_username.lstrip("@"),
                has_account=False
            )
            db.add(receiver)
            db.commit()
            db.refresh(receiver)
            logging.info(f"Created placeholder user for @{receiver.twitter_username}")
        
        if not receiver.bolt12_address:
            logging.warning(f"Receiver @{receiver.twitter_username} does not have a BOLT12 address. Payments will be held in the account.")
            print(f"Receiver @{receiver.twitter_username} does not have a BOLT12 address. Payments will be held in the account.")
        
        bolt11, payment_hash, tip_fee = create_invoice(
            tip_data.amount_sats,
            f"Tip from anonymous - {tip_data.comment}",
        )

        new_tip = Tip(
            tipper_display_name=tip_data.tipper_display_name or "anonymous",
            recipient_twitter_username=tip_data.recipient_twitter_username,
            tweet_url=tip_data.tweet_url,
            bolt11_invoice=bolt11,
            ln_payment_hash=payment_hash,
            comment=tip_data.comment,
            amount_sats=tip_data.amount_sats - tip_fee,
            paid_in=False,
            paid_out=False,
            created_at=datetime.utcnow(),
        )

        db.add(new_tip)
        db.commit()
        db.refresh(new_tip)

        return new_tip

    except HTTPException as http_exc:
        logging.error(f"HTTP error occurred: {http_exc.detail}")
        print(f"HTTP error occurred: {http_exc.detail}")
        raise
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
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
