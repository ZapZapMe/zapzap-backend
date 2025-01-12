from datetime import datetime
from typing import List, Optional

# from models.tip import Tip
from db import Base

# from .tip import Tip
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .tip import Tip
from .tweet import Tweet


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)
    twitter_username: Mapped[str] = mapped_column(index=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    wallet_address: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_registered: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    received_tips: Mapped[List["Tip"]] = relationship(
        "Tip",
        back_populates="recipient",
        foreign_keys="[Tip.tip_receiver]",
    )
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
