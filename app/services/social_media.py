"""
Social Media Metadata Extraction Service
Extracts enhanced metadata from social media posts for archival and graphical recreation

Supports:
- Twitter/X posts (full text, author info, media, timestamps)
- Future: Facebook, Instagram, TikTok, LinkedIn, etc.
"""
import logging
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from requests_oauthlib import OAuth1

logger = logging.getLogger(__name__)


def get_twitter_oauth_credentials(db=None) -> Optional[Dict[str, str]]:
    """
    Get Twitter OAuth 1.0a credentials from database (decrypted)

    Returns:
        dict: {apiKey, apiSecret, accessToken, accessTokenSecret} if configured
        None: If not configured or disabled
    """
    if not db:
        return None

    try:
        from api_config import APIConfigManager

        # Use APIConfigManager to get decrypted values (it uses its own DB session)
        logger.info("🔍 Loading Twitter OAuth credentials from database...")
        api_config_manager = APIConfigManager()
        config = api_config_manager.load_config()

        logger.info(f"📋 Config loaded, workflows: {list(config.keys())}")

        # Navigate to twitter config
        twitter_config = config.get('promotion', {}).get('social_media', {}).get('twitter', {})
        logger.info(f"📋 Twitter config keys: {list(twitter_config.keys())}")

        # Check if enabled (can be string 'true' or boolean True)
        enabled = twitter_config.get('enabled')
        if enabled not in ['true', True]:
            logger.warning(f"⚠️ Twitter API is disabled (enabled={enabled})")
            return None

        # Get all OAuth credentials
        credentials = {
            'apiKey': twitter_config.get('apiKey'),
            'apiSecret': twitter_config.get('apiSecret'),
            'accessToken': twitter_config.get('accessToken'),
            'accessTokenSecret': twitter_config.get('accessTokenSecret')
        }

        logger.info(f"📋 Credentials present: {[k for k, v in credentials.items() if v]}")

        # Check if we have all required OAuth credentials
        if all(credentials.values()):
            logger.info("✅ Twitter OAuth 1.0a credentials found (decrypted)")
            return credentials

        logger.warning(f"⚠️ Incomplete Twitter OAuth credentials (have: {[k for k, v in credentials.items() if v]})")
        return None

    except Exception as e:
        logger.error(f"❌ Error fetching Twitter OAuth credentials: {e}", exc_info=True)
        return None


def extract_twitter_metadata(soup, url: str) -> dict:
    """
    Extract comprehensive Twitter/X metadata for graphical recreation

    Captures:
    - Full post text content
    - Author name and handle
    - Author avatar URL
    - Published date/time
    - Media URLs (images, videos)
    - Tweet ID and platform
    - Thread context if available

    NOTE: Reply extraction requires Twitter API access (not included in metadata)

    Args:
        soup: BeautifulSoup object of the page HTML
        url: Original URL of the tweet

    Returns:
        dict: Twitter-specific metadata with keys like author_handle, tweet_text, etc.
    """
    twitter_data = {}

    # Twitter Card metadata
    twitter_data['twitter_card_type'] = soup.find('meta', attrs={'name': 'twitter:card'})
    if twitter_data['twitter_card_type']:
        twitter_data['twitter_card_type'] = twitter_data['twitter_card_type'].get('content', '')

    # Author information
    twitter_creator = soup.find('meta', attrs={'name': 'twitter:creator'})
    if twitter_creator:
        twitter_data['author_handle'] = twitter_creator.get('content', '').lstrip('@')

    twitter_site = soup.find('meta', attrs={'name': 'twitter:site'})
    if twitter_site:
        twitter_data['site_handle'] = twitter_site.get('content', '').lstrip('@')

    # Author name from og:site_name or title parsing
    og_site_name = soup.find('meta', property='og:site_name')
    if og_site_name:
        twitter_data['author_name'] = og_site_name.get('content', '')

    # Tweet text content (full post text)
    twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
    if twitter_desc:
        twitter_data['tweet_text'] = twitter_desc.get('content', '')

    # Also check og:description for full text
    og_desc = soup.find('meta', property='og:description')
    if og_desc and not twitter_data.get('tweet_text'):
        twitter_data['tweet_text'] = og_desc.get('content', '')

    # Tweet title (often contains author info)
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    if twitter_title:
        title_content = twitter_title.get('content', '')
        # Parse format like "John Doe on X: tweet text"
        if ' on X: ' in title_content or ' on Twitter: ' in title_content:
            parts = re.split(r' on (?:X|Twitter): ', title_content, 1)
            if len(parts) == 2:
                twitter_data['author_name'] = parts[0]
                if not twitter_data.get('tweet_text'):
                    twitter_data['tweet_text'] = parts[1]

    # Media URLs (images, videos)
    twitter_images = []
    for i in range(5):  # Check for up to 5 images
        img_meta = soup.find('meta', attrs={'name': f'twitter:image{i if i > 0 else ""}'})
        if img_meta:
            img_url = img_meta.get('content', '')
            if img_url:
                twitter_images.append(img_url)

    if twitter_images:
        twitter_data['media_urls'] = twitter_images

    # Video metadata
    twitter_player = soup.find('meta', attrs={'name': 'twitter:player'})
    if twitter_player:
        twitter_data['video_url'] = twitter_player.get('content', '')

    twitter_player_stream = soup.find('meta', attrs={'name': 'twitter:player:stream'})
    if twitter_player_stream:
        twitter_data['video_stream_url'] = twitter_player_stream.get('content', '')

    # Published date/time
    published_time = soup.find('meta', property='article:published_time')
    if published_time:
        twitter_data['published_time'] = published_time.get('content', '')

    # Profile image (author avatar)
    twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
    if twitter_image:
        twitter_data['author_avatar'] = twitter_image.get('content', '')

    # Extract from URL pattern (e.g., twitter.com/username/status/123456)
    url_match = re.match(r'https?://(?:www\.)?(twitter\.com|x\.com)/([^/]+)/status/(\d+)', url)
    if url_match:
        twitter_data['platform'] = 'x' if url_match.group(1) == 'x.com' else 'twitter'
        twitter_data['username_from_url'] = url_match.group(2)
        twitter_data['tweet_id'] = url_match.group(3)

    # Try to extract JSON-LD structured data
    try:
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            if script.string:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Extract author info from JSON-LD
                    if 'author' in data:
                        author = data['author']
                        if isinstance(author, dict):
                            if 'name' in author:
                                twitter_data['author_name'] = author['name']
                            if 'url' in author:
                                twitter_data['author_url'] = author['url']

                    # Extract date info
                    if 'datePublished' in data:
                        twitter_data['published_time'] = data['datePublished']

                    # Extract headline/description
                    if 'headline' in data and not twitter_data.get('tweet_text'):
                        twitter_data['tweet_text'] = data['headline']

                    if 'description' in data and not twitter_data.get('tweet_text'):
                        twitter_data['tweet_text'] = data['description']
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"Could not parse JSON-LD data: {e}")

    # Clean up None values
    return {k: v for k, v in twitter_data.items() if v}


def fetch_tweet_from_api(tweet_id: str, bearer_token: str = None, oauth_creds: Dict[str, str] = None) -> Optional[dict]:
    """
    Fetch comprehensive tweet data from Twitter API v2

    Args:
        tweet_id: Tweet ID to fetch
        bearer_token: Twitter API Bearer Token (App-only auth, lower rate limits)
        oauth_creds: OAuth 1.0a credentials dict with keys: apiKey, apiSecret, accessToken, accessTokenSecret
                     (User context auth, better rate limits)

    Returns:
        dict: Enhanced tweet metadata including author, text, media, metrics
        None: If API request fails
    """
    try:
        logger.info(f"🔄 Attempting to fetch tweet {tweet_id} from Twitter API")

        # Tweet fields we want to retrieve
        tweet_fields = [
            'id', 'text', 'author_id', 'created_at', 'conversation_id',
            'public_metrics', 'entities', 'attachments', 'referenced_tweets'
        ]

        # User fields for author info
        user_fields = [
            'id', 'name', 'username', 'profile_image_url', 'verified',
            'description', 'public_metrics'
        ]

        # Media fields for images/videos
        media_fields = [
            'media_key', 'type', 'url', 'preview_image_url',
            'width', 'height', 'duration_ms', 'public_metrics'
        ]

        # Build API request
        url = f'https://api.twitter.com/2/tweets/{tweet_id}'
        params = {
            'tweet.fields': ','.join(tweet_fields),
            'expansions': 'author_id,attachments.media_keys,referenced_tweets.id',
            'user.fields': ','.join(user_fields),
            'media.fields': ','.join(media_fields)
        }

        logger.debug(f"🌐 Making request to: {url}")
        logger.debug(f"📋 Params: {params}")

        # Use fresh session to avoid connection pooling issues
        session = requests.Session()

        # Choose authentication method
        if oauth_creds and all(k in oauth_creds for k in ['apiKey', 'apiSecret', 'accessToken', 'accessTokenSecret']):
            # OAuth 1.0a (User Context) - Better rate limits
            logger.info("🔐 Using OAuth 1.0a authentication (better rate limits)")
            auth = OAuth1(
                oauth_creds['apiKey'],
                oauth_creds['apiSecret'],
                oauth_creds['accessToken'],
                oauth_creds['accessTokenSecret']
            )
            response = session.get(url, auth=auth, params=params, timeout=10)
        elif bearer_token:
            # Bearer token (App-only) - Lower rate limits
            logger.info("🔑 Using Bearer Token authentication (limited rate limits)")
            headers = {'Authorization': f'Bearer {bearer_token}', 'Content-Type': 'application/json'}
            response = session.get(url, headers=headers, params=params, timeout=10)
        else:
            logger.error("❌ No authentication credentials provided")
            return None

        logger.info(f"📡 Twitter API response: HTTP {response.status_code}")

        # Log rate limit info
        rate_headers = {k: v for k, v in response.headers.items() if 'rate-limit' in k.lower()}
        if rate_headers:
            logger.info(f"📊 Rate Limits: {rate_headers}")

        logger.debug(f"📄 Response headers: {dict(response.headers)}")

        response.raise_for_status()

        data = response.json()
        logger.debug(f"✅ Received data keys: {list(data.keys())}")

        if 'data' not in data:
            logger.warning(f"⚠️ No tweet data found for ID: {tweet_id}, response: {data}")
            return None

        tweet = data['data']
        includes = data.get('includes', {})

        # Build comprehensive metadata
        metadata = {
            'tweet_id': tweet['id'],
            'tweet_text': tweet['text'],
            'published_time': tweet['created_at'],
            'conversation_id': tweet.get('conversation_id'),
            'platform': 'x'
        }

        # Add public metrics (likes, retweets, replies)
        if 'public_metrics' in tweet:
            metrics = tweet['public_metrics']
            metadata['likes'] = metrics.get('like_count', 0)
            metadata['retweets'] = metrics.get('retweet_count', 0)
            metadata['replies'] = metrics.get('reply_count', 0)
            metadata['quotes'] = metrics.get('quote_count', 0)

        # Add author information
        users = {user['id']: user for user in includes.get('users', [])}
        if tweet.get('author_id') and tweet['author_id'] in users:
            author = users[tweet['author_id']]
            metadata['author_name'] = author['name']
            metadata['author_handle'] = author['username']
            metadata['author_avatar'] = author.get('profile_image_url', '')
            metadata['author_verified'] = author.get('verified', False)
            metadata['author_bio'] = author.get('description', '')

            if 'public_metrics' in author:
                metadata['author_followers'] = author['public_metrics'].get('followers_count', 0)
                metadata['author_following'] = author['public_metrics'].get('following_count', 0)

        # Add media URLs
        media = {m['media_key']: m for m in includes.get('media', [])}
        if 'attachments' in tweet and 'media_keys' in tweet['attachments']:
            media_urls = []
            for media_key in tweet['attachments']['media_keys']:
                if media_key in media:
                    media_obj = media[media_key]
                    if media_obj['type'] == 'photo':
                        media_urls.append(media_obj.get('url', ''))
                    elif media_obj['type'] == 'video':
                        # Use preview image for videos
                        preview = media_obj.get('preview_image_url', '')
                        if preview:
                            media_urls.append(preview)

            if media_urls:
                metadata['media_urls'] = media_urls

        # Add referenced tweets (quote tweets, replies)
        if 'referenced_tweets' in tweet:
            metadata['referenced_tweets'] = tweet['referenced_tweets']

        # Add entities (hashtags, mentions, URLs)
        if 'entities' in tweet:
            metadata['entities'] = tweet['entities']

        logger.info(f"Successfully fetched tweet {tweet_id} from API")
        return metadata

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error(f"❌ Twitter API authentication failed: Invalid bearer token")
        elif e.response.status_code == 404:
            logger.warning(f"⚠️ Tweet {tweet_id} not found or not accessible")
        elif e.response.status_code == 429:
            logger.error(f"🚫 Twitter API rate limit: {e.response.status_code}")
            logger.error(f"📋 Response headers: {dict(e.response.headers)}")
            logger.error(f"📄 Response body: {e.response.text}")
            # Check if we have rate limit reset info
            if 'x-rate-limit-reset' in e.response.headers:
                import datetime
                reset_time = datetime.datetime.fromtimestamp(int(e.response.headers['x-rate-limit-reset']))
                logger.error(f"⏰ Rate limit resets at: {reset_time}")
            if 'x-rate-limit-remaining' in e.response.headers:
                logger.error(f"🔢 Remaining requests: {e.response.headers['x-rate-limit-remaining']}")
        else:
            logger.error(f"❌ Twitter API error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Twitter API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching tweet from API: {e}")
        return None


def extract_facebook_metadata(soup, url: str) -> dict:
    """
    Extract Facebook post metadata (future implementation)
    """
    # Placeholder for future Facebook support
    return {}


def extract_instagram_metadata(soup, url: str) -> dict:
    """
    Extract Instagram post metadata (future implementation)
    """
    # Placeholder for future Instagram support
    return {}


def extract_linkedin_metadata(soup, url: str) -> dict:
    """
    Extract LinkedIn post metadata (future implementation)
    """
    # Placeholder for future LinkedIn support
    return {}


def extract_tiktok_metadata(soup, url: str) -> dict:
    """
    Extract TikTok post metadata (future implementation)
    """
    # Placeholder for future TikTok support
    return {}
