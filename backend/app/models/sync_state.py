from db import Base
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    last_timestamp: Mapped[int] = mapped_column(nullable=False, default=0)
