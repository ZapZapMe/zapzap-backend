# # filepath: /backend/tests/test_leaderboard.py
# from datetime import datetime

# import pytest
# from app.models.db import Tip, Tweet, User


# @pytest.fixture
# def test_users(db_session):
#     # Create test users
#     users = [
#         User(
#             twitter_username="user1",
#             avatar_url="https://example.com/avatar1.jpg",
#             created_at=datetime.utcnow(),
#             is_registered=True,
#         ),
#         User(
#             twitter_username="user2",
#             avatar_url="https://example.com/avatar2.jpg",
#             created_at=datetime.utcnow(),
#             is_registered=True,
#         ),
#         User(
#             twitter_username="user3",
#             avatar_url="https://example.com/avatar3.jpg",
#             created_at=datetime.utcnow(),
#             is_registered=True,
#         ),
#     ]

#     # Add users to database
#     for user in users:
#         db_session.add(user)
#     db_session.commit()

#     # Return users for use in tests
#     return users


# def test_leaderboard_endpoint(client, test_users, db_session):
#     """
#     Test the /tips/leaderboard_received endpoint.
#     """
#     # Create a tweet
#     tweet = Tweet(id=123456, tweet_author=test_users[0].id)
#     db_session.add(tweet)
#     db_session.commit()

#     # Create tips
#     tip = Tip(
#         tip_sender=test_users[1].id,
#         tweet_id=tweet.id,
#         ln_payment_hash="somehash",
#         amount_sats=100,
#         paid_in=True,
#         paid_out=True,
#         created_at=datetime.utcnow(),
#     )
#     db_session.add(tip)
#     db_session.commit()

#     response = client.get("/tips/leaderboard_received")
#     assert response.status_code == 200

#     data = response.json()
#     assert isinstance(data, list)
#     assert len(data) >= 1
#     assert data[0]["tip_recipient"] == "user1"
#     assert data[0]["total_amount_sats"] == 100
#     assert data[0]["tip_count"] == 1
