from typing import List

# from models.tip import Tip
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

from .tip import Tip
from .user import User


class Tweet(Base):
    __tablename__ = "tweets"

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
