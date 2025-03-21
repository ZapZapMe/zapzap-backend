

import logging
import tweepy

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Twitter API credentials


def post_simple_tweet(tweet_text):
    """Post a simple text tweet using Twitter API v2"""
    try:
        # Set up Twitter API v2 client
        client = tweepy.Client(
            consumer_key=GIFBOT_CONSUMER_KEY,
            consumer_secret=GIFBOT_CONSUMER_SECRET,
            access_token=GIFBOT_ACCESS_TOKEN,
            access_token_secret=GIFBOT_ACCESS_TOKEN_SECRET
        )
        
        # Post the tweet
        response = client.create_tweet(text=tweet_text)
        
        if response and hasattr(response, 'data') and 'id' in response.data:
            tweet_id = response.data['id']
            logging.info(f"Tweet posted successfully! ID: {tweet_id}")
            
            # Use v1.1 API just to get the username for creating the URL
            auth = tweepy.OAuth1UserHandler(
                GIFBOT_CONSUMER_KEY,
            GIFBOT_CONSUMER_SECRET,
            GIFBOT_ACCESS_TOKEN,
            GIFBOT_ACCESS_TOKEN_SECRET
            )
            api_v1 = tweepy.API(auth)
            user_info = api_v1.verify_credentials()
            
            tweet_url = f"https://twitter.com/{user_info.screen_name}/status/{tweet_id}"
            return tweet_url
        else:
            logging.error(f"Failed to post tweet. Response: {response}")
            return None
            
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test with a simple tweet
    tweet_text = "This is a test tweet posted via the Twitter API at " + \
                 "timestamp: " + str(import time; time.time()) + \
                 " #testing #twitterapi"
    
    result = post_simple_tweet(tweet_text)
    
    if result:
        print(f"\nSuccess! Tweet posted: {result}")
    else:
        print("\nFailed to post tweet.")