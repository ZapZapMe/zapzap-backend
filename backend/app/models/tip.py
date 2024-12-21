from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from db import Base
from datetime import datetime
from sqlalchemy.orm import relationship, mapped_column, Mapped


class Tip(Base):
    __tablename__ = "tip"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipper_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    recipient_twitter_username: Mapped[str] = mapped_column(nullable=False, index=True)
    tweet_url: Mapped[str] = mapped_column(nullable=False)
    bolt11_invoice: Mapped[str] = mapped_column(nullable=False, index=True)
    ln_payment_hash: Mapped[str] = mapped_column(nullable=True, index=True)
    comment: Mapped[str] = mapped_column(nullable=True)
    amount_sats: Mapped[int] = mapped_column(nullable=False)
    paid: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    tipper_user: Mapped["User"] = relationship(back_populates="sent_tips")
