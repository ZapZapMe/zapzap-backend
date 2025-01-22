from datetime import datetime, timezone
from typing import List, Optional

from db import Base
from sqlalchemy import (
    BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), index=True)
    twitter_username: Mapped[str] = mapped_column(index=True, unique=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    twitter_access_token: Mapped[Optional[str]] = mapped_column(nullable=True)
    twitter_access_secret: Mapped[Optional[str]] = mapped_column(nullable=True)
    avatar_updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    wallet_address: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_registered: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    sent_tips: Mapped[List["Tip"]] = relationship(
        "Tip",
        back_populates="sender",
        foreign_keys="[Tip.tip_sender]",
    )
    authored_tweets: Mapped[List["Tweet"]] = relationship(
        "Tweet",
        back_populates="author",
        foreign_keys="[Tweet.tweet_author]",
    )


class Tip(Base):
    __tablename__ = "tip"
    __table_args__ = {}

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    # Foreign keys
    tip_sender: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # null = anonymous
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=False)

    # Fields
    ln_payment_hash: Mapped[str] = mapped_column(nullable=False, index=True)
    comment: Mapped[Optional[str]] = mapped_column(nullable=True)
    amount_sats: Mapped[int] = mapped_column(nullable=False)
    paid_in: Mapped[bool] = mapped_column(default=False)
    paid_out: Mapped[bool] = mapped_column(default=False)
    forward_payment_hash: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), index=True)

    # Relationships
    sender: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[tip_sender],
        back_populates="sent_tips",
    )
    tweet: Mapped["Tweet"] = relationship(
        "Tweet",
        foreign_keys=[tweet_id],
        back_populates="tips",
    )


class Tweet(Base):
    __tablename__ = "tweets"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True, index=True, unique=True)
    tweet_author: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    tips: Mapped[List["Tip"]] = relationship(
        "Tip",
        back_populates="tweet",
        foreign_keys="[Tip.tweet_id]",
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="authored_tweets",
        foreign_keys=[tweet_author],
    )
