import requests
from io import BytesIO
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_gif_download(url):
    logging.info(f"Attempting to download GIF from {url}")
    
    try:
        # Add a User-Agent header to avoid potential blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Content Type: {response.headers.get('Content-Type')}")
        logging.info(f"Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Try to save the file locally to verify it's valid
            file_name = url.split('/')[-1]
            with open(f"downloaded_{file_name}", "wb") as f:
                f.write(response.content)
                
            logging.info(f"Successfully saved to downloaded_{file_name}")
            
            # Further test by loading into BytesIO
            media_file = BytesIO(response.content)
            byte_count = len(media_file.getvalue())
            logging.info(f"Successfully loaded into BytesIO. Size: {byte_count} bytes")
            
            return True
        else:
            logging.error(f"Failed to download GIF: Status code {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error downloading GIF: {str(e)}")
        return False

if __name__ == "__main__":
    # Test URLs
    urls = [
        "https://media.tenor.com/xzjlrhYq_xcAAAAC/lightning-bolt-thunder.gif",
        "https://media.giphy.com/media/3oEjHUMoOiviYNcVe8/giphy.gif",
        "https://upload.wikimedia.org/wikipedia/commons/7/78/GRACE_globe_animation.gif",
        "https://i.imgur.com/XYZ123.gif"  # Example of a non-existent URL for testing error handling
    ]
    
    print("\n" + "="*50)
    print("GIF DOWNLOAD TEST")
    print("="*50 + "\n")
    
    for url in urls:
        print("\n" + "-"*50)
        result = test_gif_download(url)
        print(f"Test result for {url}: {'SUCCESS' if result else 'FAILED'}")
        print("-"*50 + "\n")
    
    # Allow testing a custom URL
    if len(sys.argv) > 1:
        custom_url = sys.argv[1]
        print("\n" + "-"*50)
        print(f"Testing custom URL: {custom_url}")
        result = test_gif_download(custom_url)
        print(f"Test result: {'SUCCESS' if result else 'FAILED'}")
        print("-"*50 + "\n")