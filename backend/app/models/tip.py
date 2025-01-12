from datetime import datetime
from typing import Optional

from db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .tweet import Tweet
from .user import User


class Tip(Base):
    __tablename__ = "tip"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    # Foreign keys
    tip_sender: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # null = anonymous
    # tip_receiver: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=False)

    # Fields
    ln_payment_hash: Mapped[str] = mapped_column(nullable=False, index=True)
    comment: Mapped[Optional[str]] = mapped_column(nullable=True)
    amount_sats: Mapped[int] = mapped_column(nullable=False)
    paid_in: Mapped[bool] = mapped_column(default=False)
    paid_out: Mapped[bool] = mapped_column(default=False)
    forward_payment_hash: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    # Constraints
    # __table_args__ = (ForeignKeyConstraint([tweet_id, tip_receiver], ["tweets.id", "tweets.tweet_author"]),)

    # Relationships
    sender: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[tip_sender],
        back_populates="sent_tips",
    )
    # recipient: Mapped[Optional["User"]] = relationship(
    #    "User",
    #    foreign_keys=[tip_receiver],
    #    back_populates="received_tips",
    # )
    tweet: Mapped["Tweet"] = relationship(
        "Tweet",
        foreign_keys=[tweet_id],
        back_populates="tips",
    )
