from datetime import datetime
from typing import List

from db import Base
from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tweet_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    tweets: Mapped[List["Tip"]] = relationship(back_populates="tweetFK", foreign_keys="[Tip.tweet_id]")
    sent_tips: Mapped[List["Tip"]] = relationship(back_populates="sender", foreign_keys="[Tip.tip_sender]")
