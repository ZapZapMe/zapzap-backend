from urllib.parse import urlparse

# https://x.com/imaginator/status/1874344824528375898
# https://x.com/imaginator/status/1874344824528375898/photo/1
def extract_username_and_tweet_id(tweet_url: str):
    parsed_url = urlparse(tweet_url)
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) >= 3 and path_parts[1] == "status":
        username = path_parts[0]
        tweet_id = int(path_parts[2])
        return username, tweet_id
    else:
        raise ValueError("Invalid tweet URL")

