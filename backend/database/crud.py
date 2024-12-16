from sqlalchemy.orm import session
from app.db.models import User


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.twitter_username == username).first()

def create_user(db: Session, username: str):
    user = User(twitter_username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# https://github.com/rustyrussell/bolt12address/blob/master/python/test_bolt12address.py
def update_bolt12_address(db: Session, username: str, bolt12_address: str):
    user = get_user_by_username(db, username)
    if user:
        user.bolt12_address = bolt12_address
        db.commit()
        db.refresh(user)
        return user
    return None

