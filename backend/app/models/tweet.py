from datetime import datetime
from typing import List
# from models.tip import Tip
from db import Base
from sqlalchemy import (
    ForeignKey,
    BigInteger
)
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
    tweet_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    tips: Mapped[List["Tip"]] = relationship("Tip", back_populates="tweet", foreign_keys="[Tip.tweet_id]")
