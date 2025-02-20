import tweepy

# User’s OAuth 2.0 Bearer token from the authorization code flow
OAUTH2_USER_BEARER_TOKEN = "Your OAuth 2.0 Bearer token"

client = tweepy.Client(bearer_token=OAUTH2_USER_BEARER_TOKEN)

try:
    response = client.create_tweet(
        text="Hello from my OAuth 2.0 user token!",
        in_reply_to_tweet_id="your tweet id",
        # Do NOT set user_auth=True
    )
    print("Reply posted successfully:", response)
except tweepy.TweepyException as e:
    print("Error posting reply:", e)
