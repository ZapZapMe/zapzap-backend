from db import Base
from datetime import datetime
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import List


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    twitter_username: Mapped[str] = mapped_column(index=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    wallet_address: Mapped[str] = mapped_column(nullable=True, index=True)
    is_admin: Mapped[bool] = mapped_column(default=False)


    sent_tips: Mapped[List["Tip"]] = relationship(back_populates="tipper_user")
