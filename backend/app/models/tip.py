from datetime import datetime

from db import Base
from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.tweet import Tweet
from models.user import User


class Tip(Base):
    __tablename__ = "tip"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    #Forein keys
    tip_sender: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)  # null = anonymous
    tip_recipient: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=False)


    ln_payment_hash: Mapped[str] = mapped_column(nullable=False, index=True)
    comment: Mapped[str] = mapped_column(nullable=True)
    amount_sats: Mapped[int] = mapped_column(nullable=False)
    paid_in: Mapped[bool] = mapped_column(default=False)
    paid_out: Mapped[bool] = mapped_column(default=False)
    forward_payment_hash: Mapped[str] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    sender: Mapped["User"] = relationship("User", foreign_keys=[tip_sender], back_populates="sent_tips")
    recipient: Mapped["User"] = relationship("User", foreign_keys=[tip_recipient], back_populates="received_tips")
    tweet: Mapped["Tweet"] = relationship("Tweet", foreign_keys=[tweet_id], back_populates="tips")
