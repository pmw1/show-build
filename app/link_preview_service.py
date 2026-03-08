"""
Link Preview Service
Fetch OpenGraph metadata from URLs for rich link previews
Enhanced with social media-specific metadata extraction
Includes database caching to store successful fetches
"""
import requests
import re
import hashlib
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging
from services.social_media import extract_twitter_metadata, fetch_tweet_from_api, fetch_tweet_via_syndication, get_twitter_oauth_credentials

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Force INFO level for cache debugging


def get_twitter_bearer_token(db=None):
    """
    Get Twitter API bearer token from database

    Returns:
        str: Bearer token if configured and enabled, None otherwise
    """
    if not db:
        return None

    try:
        from sqlalchemy import text

        # Check if twitter is enabled
        enabled_result = db.execute(text("""
            SELECT config_value FROM api_configs
            WHERE workflow = 'promotion'
            AND category = 'social_media'
            AND service = 'twitter'
            AND config_key = 'enabled'
            AND is_enabled = true
        """)).fetchone()

        if not enabled_result or enabled_result[0] != 'true':
            return None

        # Get bearer token
        token_result = db.execute(text("""
            SELECT config_value FROM api_configs
            WHERE workflow = 'promotion'
            AND category = 'social_media'
            AND service = 'twitter'
            AND config_key = 'bearerToken'
            AND is_enabled = true
        """)).fetchone()

        if token_result and token_result[0]:
            return token_result[0]

        return None
    except Exception as e:
        logger.error(f"Error fetching Twitter bearer token: {e}")
        return None


def get_cached_preview(url: str, db) -> dict:
    """
    Get cached preview data from database if available and not expired
    Returns dict with _cached flag set to True if from cache
    """
    if not db:
        return None

    try:
        from sqlalchemy import text
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        logger.info(f"🔎 Looking for cache with hash: {url_hash[:16]}...")

        result = db.execute(text("""
            SELECT preview_data, fetched_at, expires_at
            FROM link_preview_cache
            WHERE url_hash = :url_hash
        """), {"url_hash": url_hash}).fetchone()

        logger.info(f"🔍 Cache lookup result: {'Found' if result else 'Not found'}")

        if result:
            preview_data, fetched_at, expires_at = result
            logger.info(f"📋 Retrieved: preview_data type={type(preview_data)}, expires_at={expires_at}")

            # Check if cache is expired (use timezone-aware datetime)
            from datetime import timezone
            if expires_at and datetime.now(timezone.utc) > expires_at:
                logger.info(f"⏰ Cache expired for {url}")
                return None

            logger.info(f"✅ Using cached preview for {url} (fetched {fetched_at})")
            # Add cached flag to indicate this came from cache
            # Make a copy to avoid modifying cached data
            import copy
            result = copy.deepcopy(preview_data) if isinstance(preview_data, dict) else preview_data
            if isinstance(result, dict):
                result['_cached'] = True
                result['_cached_at'] = fetched_at.isoformat() if fetched_at else None
            logger.info(f"✅ Returning cached result with {len(result)} keys")
            return result

        logger.info("🔴 Result was None, returning None")
        return None
    except Exception as e:
        logger.error(f"❗ Error reading cache: {e}", exc_info=True)
        return None


def cache_preview(url: str, preview_data: dict, db, ttl_days=30):
    """
    Cache preview data in database with optional TTL
    """
    if not db:
        return

    try:
        from sqlalchemy import text
        import json
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=ttl_days) if ttl_days else None

        # Insert or update cache (PostgreSQL will auto-convert JSON string to jsonb)
        db.execute(text("""
            INSERT INTO link_preview_cache (url, url_hash, preview_data, expires_at)
            VALUES (:url, :url_hash, CAST(:preview_data AS jsonb), :expires_at)
            ON CONFLICT (url_hash)
            DO UPDATE SET
                preview_data = CAST(:preview_data AS jsonb),
                fetched_at = now(),
                expires_at = :expires_at
        """), {
            "url": url,
            "url_hash": url_hash,
            "preview_data": json.dumps(preview_data),  # Serialize to JSON string
            "expires_at": expires_at
        })
        db.commit()
        logger.info(f"💾 Cached preview for {url}")
    except Exception as e:
        logger.error(f"Error caching preview: {e}")
        db.rollback()


def fetch_link_preview(url: str, db=None) -> dict:
    """
    Fetch OpenGraph metadata from a URL
    Returns dict with title, description, image, and domain
    Enhanced with Twitter/X-specific metadata when applicable
    Uses database caching to avoid re-fetching
    """
    # Check cache first
    if db:
        logger.info(f"🔍 Checking cache for {url}")
        cached = get_cached_preview(url, db)
        if cached:
            logger.info(f"📦 Returning cached data for {url}")
            return cached
        logger.info(f"❌ No cache found for {url}, fetching fresh")

    try:
        # Check if this is a Twitter media URL (pbs.twimg.com)
        parsed = urlparse(url)
        is_twitter_media = parsed.netloc in ['pbs.twimg.com', 'video.twimg.com']

        if is_twitter_media:
            # Handle direct Twitter media URLs
            logger.info(f"Detected Twitter media URL: {url}")
            og_data = {
                'title': 'Twitter Media',
                'description': 'Direct media link from Twitter/X',
                'image': url if '/img/' in url or url.endswith(('.jpg', '.jpeg', '.png', '.webp')) else '',
                'domain': 'pbs.twimg.com',
                'favicon': 'https://abs.twimg.com/favicons/twitter.3.ico',
                'x_media_type': 'video' if 'amplify_video' in url or 'tweet_video' in url else 'image',
                'x_is_direct_media': True
            }

            # Try to extract higher quality video thumbnail
            if 'amplify_video_thumb' in url and 'format=jpg' in url:
                # Convert to higher quality by changing size parameter
                og_data['image'] = url.replace('name=small', 'name=large').replace('name=medium', 'name=large')
                og_data['x_video_thumbnail'] = og_data['image']

            # Cache and return
            if db and og_data:
                cache_preview(url, og_data, db, ttl_days=30)
            return og_data

        # Add timeout and user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if this is a Twitter/X URL
        is_twitter = parsed.netloc in ['twitter.com', 'x.com', 'www.twitter.com', 'www.x.com']

        # Extract OpenGraph metadata
        og_data = {}

        # Title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            og_data['title'] = og_title.get('content', '')
        else:
            # Fallback to <title> tag
            title_tag = soup.find('title')
            og_data['title'] = title_tag.string if title_tag else ''

        # Description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            og_data['description'] = og_desc.get('content', '')
        else:
            # Fallback to meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            og_data['description'] = meta_desc.get('content', '') if meta_desc else ''

        # Image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content', '')
            # Make absolute URL if relative
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(url, image_url)
            og_data['image'] = image_url
        else:
            og_data['image'] = ''

        # Domain
        og_data['domain'] = parsed.netloc

        # Favicon
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
        if favicon:
            favicon_url = favicon.get('href', '')
            if favicon_url and not favicon_url.startswith('http'):
                favicon_url = urljoin(url, favicon_url)
            og_data['favicon'] = favicon_url
        else:
            # Default favicon location
            og_data['favicon'] = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

        # If Twitter/X, extract enhanced metadata
        if is_twitter:
            tweet_id_match = re.search(r'/status/(\d+)', url)

            if tweet_id_match:
                tweet_id = tweet_id_match.group(1)

                # Try v2 API first with credentials
                oauth_creds = get_twitter_oauth_credentials(db)
                bearer_token = get_twitter_bearer_token(db) if not oauth_creds else None
                twitter_metadata = None

                if oauth_creds or bearer_token:
                    api_metadata = fetch_tweet_from_api(tweet_id, bearer_token=bearer_token, oauth_creds=oauth_creds)
                    if api_metadata and not api_metadata.get('_error'):
                        twitter_metadata = api_metadata
                        logger.info(f"Fetched X preview via v2 API for {url}: @{api_metadata.get('author_handle', 'unknown')}")

                # v2 failed or no credentials — try syndication fallback
                if not twitter_metadata:
                    syndication_result = fetch_tweet_via_syndication(tweet_id)
                    if syndication_result:
                        twitter_metadata = syndication_result
                        logger.info(f"Fetched X preview via syndication for {url}: @{syndication_result.get('author_handle', 'unknown')}")

                # Both APIs failed — fall back to scraping
                if not twitter_metadata:
                    twitter_metadata = extract_twitter_metadata(soup, url)
                    logger.info(f"All X APIs failed, using scraped data for {url}")
            else:
                twitter_metadata = extract_twitter_metadata(soup, url)

            # Merge Twitter data into og_data with 'x_' prefix
            for key, value in twitter_metadata.items():
                og_data[f'x_{key}'] = value

            if not bearer_token or not tweet_id_match:
                logger.info(f"Fetched X/Twitter preview (scraped) for {url}: {og_data.get('title', 'No title')} by @{twitter_metadata.get('author_handle', 'unknown')}")
        else:
            logger.info(f"Fetched preview for {url}: {og_data.get('title', 'No title')}")

        # Cache the successful result
        if db and og_data and 'error' not in og_data:
            cache_preview(url, og_data, db, ttl_days=30)

        return og_data

    except requests.Timeout:
        logger.error(f"Timeout fetching preview for {url}")
        return {'error': 'Request timeout'}
    except requests.RequestException as e:
        logger.error(f"Error fetching preview for {url}: {e}")
        return {'error': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error fetching preview for {url}: {e}")
        return {'error': str(e)}
