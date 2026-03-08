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


def fetch_tweet_via_syndication(tweet_id: str) -> Optional[dict]:
    """
    Fetch tweet data via X's syndication API (used by embed widgets).
    Free, no authentication required, returns rich metadata.

    Returns:
        dict: Tweet metadata matching our standard format, or None on failure
    """
    try:
        logger.info(f"🔄 Fetching tweet {tweet_id} via syndication API")
        response = requests.get(
            'https://cdn.syndication.twimg.com/tweet-result',
            params={'id': tweet_id, 'token': 'x'},
            timeout=10
        )

        if response.status_code != 200:
            logger.warning(f"Syndication API returned {response.status_code} for tweet {tweet_id}")
            return None

        data = response.json()

        if data.get('__typename') == 'TweetTombstone':
            logger.warning(f"Tweet {tweet_id} is tombstoned (deleted/suspended)")
            return None

        user = data.get('user', {})
        metadata = {
            'tweet_id': data.get('id_str', tweet_id),
            'tweet_text': data.get('text', ''),
            'published_time': data.get('created_at', ''),
            'platform': 'x',
            'likes': data.get('favorite_count', 0),
            'retweets': data.get('retweet_count', 0),
            'author_name': user.get('name', ''),
            'author_handle': user.get('screen_name', ''),
            'author_avatar': user.get('profile_image_url_https', ''),
            'author_verified': user.get('verified', False) or user.get('is_blue_verified', False),
        }

        # Extract media
        media_details = data.get('mediaDetails', [])
        media_urls = []
        media_objects = []

        for m in media_details:
            media_type = m.get('type', 'photo')
            if media_type == 'photo':
                photo_url = m.get('media_url_https', '')
                if photo_url:
                    media_urls.append(photo_url)
                    orig = m.get('original_info', {})
                    media_objects.append({
                        'type': 'photo',
                        'url': photo_url,
                        'width': orig.get('width'),
                        'height': orig.get('height'),
                    })
            elif media_type in ('video', 'animated_gif'):
                preview = m.get('media_url_https', '')
                if preview:
                    media_urls.append(preview)
                video_info = m.get('video_info', {})
                variants = video_info.get('variants', [])
                mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                if mp4_variants:
                    best = max(mp4_variants, key=lambda v: v.get('bitrate', 0))
                    media_objects.append({
                        'type': media_type,
                        'url': best['url'],
                        'preview_url': preview,
                        'width': m.get('original_info', {}).get('width'),
                        'height': m.get('original_info', {}).get('height'),
                        'duration_ms': video_info.get('duration_millis'),
                        'bit_rate': best.get('bitrate'),
                    })
                elif preview:
                    media_objects.append({
                        'type': media_type,
                        'url': preview,
                        'preview_url': preview,
                    })

        if media_urls:
            metadata['media_urls'] = media_urls
        if media_objects:
            metadata['media_objects'] = media_objects

        # Entities
        entities = data.get('entities', {})
        if entities:
            metadata['entities'] = entities

        logger.info(f"✅ Fetched tweet {tweet_id} via syndication: @{metadata['author_handle']}, {len(media_objects)} media")
        return metadata

    except Exception as e:
        logger.error(f"Syndication API error for tweet {tweet_id}: {e}")
        return None


def fetch_tweet_from_api(tweet_id: str, bearer_token: str = None, oauth_creds: Dict[str, str] = None) -> Optional[dict]:
    """
    Fetch comprehensive tweet data from Twitter API v2
    NOTE: Falls back to syndication API first (free, no auth). V2 API is attempted only if syndication fails.

    Args:
        tweet_id: Tweet ID to fetch
        bearer_token: Twitter API Bearer Token (App-only auth, lower rate limits)
        oauth_creds: OAuth 1.0a credentials dict with keys: apiKey, apiSecret, accessToken, accessTokenSecret
                     (User context auth, better rate limits)

    Returns:
        dict: Enhanced tweet metadata including author, text, media, metrics
        None/error dict: If API request fails
    """
    try:
        logger.info(f"🔄 Attempting to fetch tweet {tweet_id} from X API v2")

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
            'width', 'height', 'duration_ms', 'public_metrics',
            'variants', 'alt_text'
        ]

        # Build API request
        url = f'https://api.x.com/2/tweets/{tweet_id}'
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

        # Add media URLs and structured media objects
        media = {m['media_key']: m for m in includes.get('media', [])}
        if 'attachments' in tweet and 'media_keys' in tweet['attachments']:
            media_urls = []
            media_objects = []  # Structured media info for download
            for media_key in tweet['attachments']['media_keys']:
                if media_key in media:
                    media_obj = media[media_key]
                    if media_obj['type'] == 'photo':
                        photo_url = media_obj.get('url', '')
                        if photo_url:
                            media_urls.append(photo_url)
                            media_objects.append({
                                'type': 'photo',
                                'url': photo_url,
                                'width': media_obj.get('width'),
                                'height': media_obj.get('height'),
                                'alt_text': media_obj.get('alt_text')
                            })
                    elif media_obj['type'] in ('video', 'animated_gif'):
                        preview = media_obj.get('preview_image_url', '')
                        if preview:
                            media_urls.append(preview)
                        # Extract best video variant (highest bitrate mp4)
                        variants = media_obj.get('variants', [])
                        mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                        if mp4_variants:
                            best = max(mp4_variants, key=lambda v: v.get('bit_rate', 0))
                            media_objects.append({
                                'type': media_obj['type'],
                                'url': best['url'],
                                'preview_url': preview,
                                'width': media_obj.get('width'),
                                'height': media_obj.get('height'),
                                'duration_ms': media_obj.get('duration_ms'),
                                'bit_rate': best.get('bit_rate')
                            })
                        elif preview:
                            media_objects.append({
                                'type': media_obj['type'],
                                'url': preview,
                                'preview_url': preview,
                                'width': media_obj.get('width'),
                                'height': media_obj.get('height'),
                                'duration_ms': media_obj.get('duration_ms')
                            })

            if media_urls:
                metadata['media_urls'] = media_urls
            if media_objects:
                metadata['media_objects'] = media_objects

        # Add referenced tweets (quote tweets, replies)
        if 'referenced_tweets' in tweet:
            metadata['referenced_tweets'] = tweet['referenced_tweets']

        # Add entities (hashtags, mentions, URLs)
        if 'entities' in tweet:
            metadata['entities'] = tweet['entities']

        logger.info(f"Successfully fetched tweet {tweet_id} from API")
        return metadata

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 0
        response_text = e.response.text if e.response is not None else str(e)
        error_info = {
            '_error': True,
            'service': 'twitter',
            'status_code': status_code,
            'endpoint': f'https://api.x.com/2/tweets/{tweet_id}',
            'detail': response_text[:500],
        }
        if status_code == 401:
            error_info['message'] = 'Authentication failed - invalid credentials'
            logger.error(f"❌ Twitter API authentication failed: Invalid bearer token")
        elif status_code == 404:
            error_info['message'] = 'Tweet not found or not accessible'
            logger.warning(f"⚠️ Tweet {tweet_id} not found or not accessible")
        elif status_code == 429:
            error_info['message'] = 'Rate limit exceeded'
            logger.error(f"🚫 Twitter API rate limit: {status_code}")
            logger.error(f"📋 Response headers: {dict(e.response.headers)}")
            logger.error(f"📄 Response body: {response_text}")
            if 'x-rate-limit-reset' in e.response.headers:
                import datetime
                reset_time = datetime.datetime.fromtimestamp(int(e.response.headers['x-rate-limit-reset']))
                logger.error(f"⏰ Rate limit resets at: {reset_time}")
                error_info['rate_limit_reset'] = reset_time.isoformat()
        else:
            error_info['message'] = f'HTTP {status_code} - {response_text[:200]}'
            logger.error(f"❌ Twitter API error: {status_code} - {response_text}")
        return error_info
    except requests.exceptions.RequestException as e:
        logger.error(f"Twitter API request failed: {e}")
        return {
            '_error': True,
            'service': 'twitter',
            'status_code': 0,
            'message': f'Connection error: {str(e)}',
            'endpoint': f'https://api.x.com/2/tweets/{tweet_id}',
            'detail': str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching tweet from API: {e}")
        return {
            '_error': True,
            'service': 'twitter',
            'status_code': 0,
            'message': f'Unexpected error: {str(e)}',
            'endpoint': f'https://api.x.com/2/tweets/{tweet_id}',
            'detail': str(e),
        }


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
    Extract TikTok post metadata from HTML meta tags and oEmbed.
    """
    tiktok_data = {'platform': 'tiktok'}

    # OG metadata
    og_title = soup.find('meta', property='og:title')
    if og_title:
        tiktok_data['title'] = og_title.get('content', '')

    og_desc = soup.find('meta', property='og:description')
    if og_desc:
        tiktok_data['post_text'] = og_desc.get('content', '')

    og_image = soup.find('meta', property='og:image')
    if og_image:
        tiktok_data['thumbnail_url'] = og_image.get('content', '')

    # Author from URL pattern (tiktok.com/@username/video/id)
    url_match = re.match(r'https?://(?:www\.)?tiktok\.com/@([^/]+)/video/(\d+)', url)
    if url_match:
        tiktok_data['author_handle'] = url_match.group(1)
        tiktok_data['post_id'] = url_match.group(2)

    # Try oEmbed (fast, no auth)
    try:
        oembed_resp = requests.get(
            f'https://www.tiktok.com/oembed?url={url}',
            timeout=5
        )
        if oembed_resp.status_code == 200:
            oembed = oembed_resp.json()
            tiktok_data['author_name'] = oembed.get('author_name', tiktok_data.get('author_handle'))
            tiktok_data['author_url'] = oembed.get('author_url')
            if oembed.get('thumbnail_url'):
                tiktok_data['thumbnail_url'] = oembed['thumbnail_url']
            if oembed.get('title'):
                tiktok_data['post_text'] = oembed['title']
    except Exception as e:
        logger.debug(f"TikTok oEmbed failed: {e}")

    return {k: v for k, v in tiktok_data.items() if v}
