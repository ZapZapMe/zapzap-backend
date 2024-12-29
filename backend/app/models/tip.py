from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, Integer
from db import Base
from datetime import datetime
from sqlalchemy.orm import relationship, mapped_column, Mapped
from models.user import User
from datetime import datetime

class Tip(Base):
    __tablename__ = "tip"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipper_display_name: Mapped[str] = mapped_column(nullable=False, default="anonymous")
    tipper_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    recipient_twitter_username: Mapped[str] = mapped_column(nullable=False, index=True)
    tweet_url: Mapped[str] = mapped_column(nullable=False)
    bolt11_invoice: Mapped[str] = mapped_column(nullable=False, index=True)
    ln_payment_hash: Mapped[str] = mapped_column(nullable=True, index=True)
    comment: Mapped[str] = mapped_column(nullable=True)
    amount_sats: Mapped[int] = mapped_column(nullable=False)
    paid_in: Mapped[bool] = mapped_column(default=False)
    paid_out: Mapped[bool] = mapped_column(default=False)
    forward_payment_hash: Mapped[str] = mapped_column(nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    tipper_user: Mapped["User"] = relationship(back_populates="sent_tips")
