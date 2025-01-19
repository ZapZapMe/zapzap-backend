# from datetime import datetime, timedelta

# from db import get_db
# from fastapi import APIRouter, Depends
# from models.db import Tip, Tweet, User
# from schemas.tip import LeaderboardReceived, LeaderboardSent
# from services.twitter_service import get_avatars_for_usernames
# from sqlalchemy import func
# from sqlalchemy.orm import Session

# router = APIRouter(prefix="/tips", tags=["tips"])


# # big tippers!
# @router.get("/leaderboard_sent", response_model=list[LeaderboardSent])
# def get_most_active_tippers(db: Session = Depends(get_db)):
#     timerange = datetime.utcnow() - timedelta(days=30)

#     tips = (
#         db.query(
#             User.twitter_username.label("tip_sender"),
#             func.count(Tip.id).label("tip_count"),
#             func.sum(Tip.amount_sats).label("total_amount_sats"),
#         )
#         .join(Tip, User.id == Tip.tip_sender)
#         .filter(
#             Tip.tip_sender.is_not(None),  # Exclude anonymous tips
#             Tip.paid_in.is_(True),  # Only tips that have been paid in
#             Tip.created_at >= timerange,
#         )
#         .group_by(User.twitter_username)
#         .order_by(func.sum(Tip.amount_sats).desc())
#         .limit(10)
#         .all()
#     )
#     # Get the usernames from the query results
#     usernames = [t.tip_sender for t in tips]

#     # Get avatars in one batch call
#     avatars_map = get_avatars_for_usernames(usernames, db)

#     # Build the response
#     result = []
#     for t in tips:
#         avatar_url = avatars_map.get(t.tip_sender) or ""
#         result.append(
#             LeaderboardSent(
#                 tip_sender=t.tip_sender,
#                 total_amount_sats=t.total_amount_sats,
#                 tip_count=t.tip_count,
#                 avatar_url=avatar_url,  # Add avatar URL to your schema if needed
#             )
#         )

#     return result


# # most received tips
# @router.get("/leaderboard_received", response_model=list[LeaderboardReceived])
# def get_most_tipped_users(db: Session = Depends(get_db)):
#     timerange = datetime.utcnow() - timedelta(days=30)

#     # Label the columns to match the fields in LeaderboardReceived
#     tips = (
#         db.query(
#             User.twitter_username.label("tip_recipient"),
#             func.count(Tip.id).label("tip_count"),
#             func.sum(Tip.amount_sats).label("total_amount_sats"),
#         )
#         .join(Tweet, Tweet.id == Tip.tweet_id)
#         .join(User, User.id == Tweet.tweet_author)
#         .filter(
#             Tip.tip_sender.is_not(None),  # Exclude anonymous tips
#             Tip.paid_in.is_(True),
#             Tip.created_at >= timerange,
#             Tip.tip_sender != Tweet.tweet_author,  # Exclude tipping themselves
#         )
#         .group_by(User.twitter_username)
#         .order_by(func.sum(Tip.amount_sats).desc())
#         .limit(10)
#         .all()
#     )
#     # Get the usernames from the query results
#     usernames = [t.tip_sender for t in tips]

#     # Get avatars in one batch call
#     avatars_map = get_avatars_for_usernames(usernames, db)

#     # Build the response
#     result = []
#     for t in tips:
#         avatar_url = avatars_map.get(t.tip_sender) or ""
#         result.append(
#             LeaderboardSent(
#                 tip_recipient=t.tip_sender,
#                 total_amount_sats=t.total_amount_sats,
#                 tip_count=t.tip_count,
#                 avatar_url=avatar_url,  # Add avatar URL to your schema if needed
#             )
#         )

#     return result
