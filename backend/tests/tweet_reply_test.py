import tweepy

# User’s OAuth 2.0 Bearer token from the authorization code flow
OAUTH2_USER_BEARER_TOKEN = "aE9hSDk3WjdPS2dvWkZLV1JiVWlFX19WVkJWc2dOMk52TlBvQTNTU042UmtxOjE3Mzc0ODMyNTc4Mzc6MTowOmF0OjE"

client = tweepy.Client(
    bearer_token=OAUTH2_USER_BEARER_TOKEN
)

try:
    response = client.create_tweet(
        text="Hello from my OAuth 2.0 user token!",
        in_reply_to_tweet_id="1880978668769681829"
        # Do NOT set user_auth=True
    )
    print("Reply posted successfully:", response)
except tweepy.TweepyException as e:
    print("Error posting reply:", e)
