from sqlalchemy.orm import Session
from models.sync_state import SyncState
from datetime import datetime

def get_last_sync_state(db: Session) -> datetime:
    row = db.query(SyncState).filter(SyncState.id == 1).first()
    if not row:
        return 0
    return row.last_timestamp

def set_last_sync_timestamp(db: Session, new_ts: datetime):
    row = db.query(SyncState).filter(SyncState.id==1).first()
    if not row:
        row = SyncState(id=1, last_timestamp=new_ts)
        db.add(row)
    else:
        row.last_timestamp = new_ts
    db.commit()