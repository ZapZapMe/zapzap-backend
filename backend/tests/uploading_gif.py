import base64
import json
import logging
import mimetypes
from io import BytesIO

import requests
from requests_oauthlib import OAuth1

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Twitter API credentials


def upload_media_in_memory(gif_url):
    """Download a GIF and upload it to Twitter without saving to disk"""
    # Download the GIF
    logging.info(f"Downloading GIF from: {gif_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(gif_url, headers=headers, timeout=10)

    if response.status_code != 200:
        logging.error(f"Failed to download GIF: Status code {response.status_code}")
        return None

    content_type = response.headers.get("Content-Type", "image/gif")
    media_content = response.content
    media_size = len(media_content)
    logging.info(f"Downloaded {media_size} bytes of {content_type}")

    # Create OAuth1 auth object
    oauth = OAuth1(
        TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=TWITTER_ACCESS_TOKEN,
        resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )

    # INIT phase
    init_url = "https://upload.twitter.com/1.1/media/upload.json"
    init_data = {
        "command": "INIT",
        "total_bytes": media_size,
        "media_type": content_type,
        "media_category": "tweet_gif",
    }

    logging.info("INIT phase...")
    init_response = requests.post(init_url, data=init_data, auth=oauth)

    if init_response.status_code != 202:
        logging.error(f"INIT failed with status {init_response.status_code}: {init_response.text}")
        return None

    media_id = init_response.json()["media_id_string"]
    logging.info(f"Media ID: {media_id}")

    # APPEND phase
    media_io = BytesIO(media_content)
    chunk_size = 4 * 1024 * 1024  # 4MB chunks

    segment_index = 0
    bytes_sent = 0

    while bytes_sent < media_size:
        chunk = media_io.read(chunk_size)
        if not chunk:
            break

        logging.info(f"APPEND phase, segment {segment_index}, size {len(chunk)} bytes...")

        append_url = "https://upload.twitter.com/1.1/media/upload.json"
        append_data = {"command": "APPEND", "media_id": media_id, "segment_index": segment_index}

        files = {"media": chunk}

        append_response = requests.post(append_url, data=append_data, files=files, auth=oauth)

        if append_response.status_code != 204:
            logging.error(f"APPEND failed with status {append_response.status_code}: {append_response.text}")
            return None

        segment_index += 1
        bytes_sent += len(chunk)
        logging.info(f"Progress: {bytes_sent}/{media_size} bytes ({bytes_sent / media_size * 100:.1f}%)")

    # FINALIZE phase
    finalize_url = "https://upload.twitter.com/1.1/media/upload.json"
    finalize_data = {"command": "FINALIZE", "media_id": media_id}

    logging.info("FINALIZE phase...")
    finalize_response = requests.post(finalize_url, data=finalize_data, auth=oauth)

    if finalize_response.status_code not in (200, 201):
        logging.error(f"FINALIZE failed with status {finalize_response.status_code}: {finalize_response.text}")
        return None

    finalize_json = finalize_response.json()
    logging.info(f"Upload complete! Response: {json.dumps(finalize_json, indent=2)}")

    # Check if processing is needed
    if "processing_info" in finalize_json:
        processing_info = finalize_json["processing_info"]
        state = processing_info.get("state")
        logging.info(f"Media processing state: {state}")

    return media_id


def post_tweet_with_media(text, media_id):
    """Post a tweet with the uploaded media"""
    oauth = OAuth1(
        TWITTER_CONSUMER_KEY,
        client_secret=TWITTER_CONSUMER_SECRET,
        resource_owner_key=TWITTER_ACCESS_TOKEN,
        resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )

    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text, "media": {"media_ids": [media_id]}}

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, auth=oauth, headers=headers)

    if response.status_code not in (200, 201):
        logging.error(f"Tweet creation failed with status {response.status_code}: {response.text}")
        return None

    response_json = response.json()
    logging.info(f"Tweet created! Response: {json.dumps(response_json, indent=2)}")

    tweet_id = response_json["data"]["id"]
    return tweet_id


if __name__ == "__main__":
    # GIF URL from your frontend code
    gif_url = "https://media.giphy.com/media/trN9ht5RlE3Dcwavg2/giphy.gif"

    # Upload the media using in-memory approach
    media_id = upload_media_in_memory(gif_url)

    if media_id:
        # Post a tweet with the media
        tweet_text = "Testing GIF upload from URL without temp files!"
        tweet_id = post_tweet_with_media(tweet_text, media_id)

        if tweet_id:
            print(f"\nSuccess! Tweet posted with ID: {tweet_id}")
            print(f"View it at: https://twitter.com/i/status/{tweet_id}")
        else:
            print("\nFailed to post tweet.")
    else:
        print("\nFailed to upload media.")
