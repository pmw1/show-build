"""
Whiteboard social media download endpoints: Twitter, TikTok, YouTube, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import re
import shutil
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from models_whiteboard import AssetPoolFile, AssetTag
from services.asset_id import AssetIDService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whiteboard"])


@router.post("/{identifier}/download-social-media")
async def download_social_media(
    identifier: str,
    url: str,
    tags: Optional[str] = None,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Download media from social media URLs (Twitter, YouTube, TikTok, etc.)
    For Twitter/X: Uses Twitter API v2 directly to get media URLs and download them.
    For other services: Falls back to yt-dlp if installed.
    Returns list of downloaded media files with AssetIDs.
    """
    username = current_user.get("username", "unknown")
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    is_twitter = bool(re.search(r'(twitter\.com|x\.com)', domain))

    if is_twitter:
        return await _download_twitter_media(identifier, url, tags, username, db)
    else:
        return await _download_via_ytdlp(identifier, url, tags, username, db)


async def _download_twitter_media(
    identifier: str, url: str, tags: Optional[str],
    username: str, db: Session
):
    """Download media from Twitter/X using API v2 directly."""
    import requests as http_requests

    # Extract tweet ID from URL
    url_match = re.match(
        r'https?://(?:www\.)?(twitter\.com|x\.com)/([^/]+)/status/(\d+)',
        url
    )
    if not url_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract tweet ID from URL"
        )

    tweet_id = url_match.group(3)

    # Fetch tweet data - try v2 API first, syndication as fallback
    from services.social_media import fetch_tweet_via_syndication, fetch_tweet_from_api, get_twitter_oauth_credentials
    from link_preview_service import get_twitter_bearer_token

    oauth_creds = get_twitter_oauth_credentials(db)
    bearer_token = get_twitter_bearer_token(db) if not oauth_creds else None

    tweet_data = None
    if oauth_creds or bearer_token:
        tweet_data = fetch_tweet_from_api(tweet_id, bearer_token=bearer_token, oauth_creds=oauth_creds)

    # If v2 API failed or returned error, try syndication as fallback
    if not tweet_data or (isinstance(tweet_data, dict) and tweet_data.get('_error')):
        v2_error = tweet_data  # preserve error info
        logger.info(f"v2 API failed for tweet {tweet_id}, trying syndication fallback")
        tweet_data = fetch_tweet_via_syndication(tweet_id)
        if tweet_data:
            logger.info(f"Syndication fallback succeeded for tweet {tweet_id}")

    # Handle total failure
    if not tweet_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch tweet {tweet_id} from any source"
        )

    if isinstance(tweet_data, dict) and tweet_data.get('_error'):
        # API returned an error - return it with partial status so frontend can show warning
        error_info = {k: v for k, v in tweet_data.items() if k != '_error'}
        error_info['fallback_used'] = False
        return {
            "success": False,
            "status": "error",
            "url": url,
            "tweet_id": tweet_id,
            "files_downloaded": 0,
            "assets": [],
            "error": error_info,
            "tweet_data": None,
        }

    media_objects = tweet_data.get('media_objects', [])
    if not media_objects:
        # No structured media objects, try media_urls as image fallback
        media_urls = tweet_data.get('media_urls', [])
        if media_urls:
            media_objects = [{'type': 'photo', 'url': u} for u in media_urls]

    if not media_objects:
        return {
            "success": True,
            "url": url,
            "files_downloaded": 0,
            "assets": [],
            "message": "Tweet has no downloadable media"
        }

    # Determine destination
    is_episode_wb = identifier.isdigit() and len(identifier) == 4
    if is_episode_wb:
        from core.paths import paths as path_manager
        media_dir = path_manager.get_whiteboard_media_dir(identifier)
    else:
        media_dir = Path("/mnt/sync/asset-pool")
    media_dir.mkdir(parents=True, exist_ok=True)

    asset_records = []

    for media_obj in media_objects:
        media_url = media_obj.get('url')
        if not media_url:
            continue

        media_type = media_obj.get('type', 'photo')

        # Download the file
        try:
            resp = http_requests.get(media_url, timeout=30, stream=True)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download media from {media_url}: {e}")
            continue

        # Determine extension from content-type or URL
        content_type = resp.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'mp4' in content_type or 'video' in content_type:
            ext = '.mp4'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            # Try from URL path
            from urllib.parse import urlparse as parse_url
            path = parse_url(media_url).path
            ext = Path(path).suffix or '.jpg'

        # Determine category
        if media_type in ('video', 'animated_gif'):
            media_category = 'video'
            mime = 'video/mp4'
        else:
            media_category = 'image'
            mime = content_type or f'image/{ext.lstrip(".")}'

        # Generate a registry-backed AssetID: asset_pool_files.asset_id has an
        # enforced FK to asset_id_registry, so an unregistered generate() ID
        # makes the insert below fail.
        asset_type = f"whiteboard_{media_category}"
        asset_id = AssetIDService.request_asset_id(
            db, entity_type=asset_type, reason="create", requested_by=username,
            context={"source": "twitter", "source_url": url, "tweet_id": tweet_id}
        )
        file_name = f"{asset_id}{ext}"
        dest_path = media_dir / file_name

        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(dest_path)

        if is_episode_wb:
            relative_path = f"whiteboard/{identifier}/{file_name}"
            file_url = f"/pool/{relative_path}"  # whiteboard media moved to the pool
        else:
            relative_path = str(dest_path)
            file_url = f"/asset-pool/{file_name}"

        source_context = {
            'tweet_id': tweet_id,
            'author': tweet_data.get('author_handle'),
            'author_name': tweet_data.get('author_name'),
            'tweet_text': tweet_data.get('tweet_text', '')[:500],
            'title': f"@{tweet_data.get('author_handle', 'unknown')} - {media_type}",
            'width': media_obj.get('width'),
            'height': media_obj.get('height'),
            'duration_ms': media_obj.get('duration_ms'),
        }

        asset_pool_file = AssetPoolFile(
            asset_id=asset_id,
            file_path=str(dest_path),
            original_filename=file_name,
            mime_type=mime,
            file_size=file_size,
            source='twitter',
            source_url=url,
            source_context=source_context
        )
        db.add(asset_pool_file)

        # Add tags
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            for tag in tag_list:
                db.add(AssetTag(asset_id=asset_id, tag=tag, created_by=username))

        if is_episode_wb:
            db.add(AssetTag(asset_id=asset_id, tag=f"episode:{identifier}", created_by=username))

        db.add(AssetTag(asset_id=asset_id, tag="twitter", created_by=username))
        db.commit()

        asset_records.append({
            "asset_id": asset_id,
            "file_url": file_url,
            "media_path": relative_path if is_episode_wb else None,
            "file_path": str(dest_path),
            "mime_type": mime,
            "file_size": file_size,
            "media_category": media_category,
            "original_filename": file_name,
            "source_context": source_context
        })

        logger.info(f"Downloaded Twitter {media_category} from tweet {tweet_id} as {asset_id} -> {dest_path}")

    # Also download author avatar to local cache
    local_avatar_url = None
    avatar_url = tweet_data.get('author_avatar')
    if avatar_url:
        try:
            # Get higher-res avatar (replace _normal with _400x400)
            hires_avatar = avatar_url.replace('_normal', '_400x400')
            resp = http_requests.get(hires_avatar, timeout=10)
            resp.raise_for_status()
            avatar_ext = '.jpg'
            if 'png' in resp.headers.get('content-type', ''):
                avatar_ext = '.png'
            avatar_filename = f"avatar_{tweet_data.get('author_handle', 'unknown')}{avatar_ext}"
            avatar_dest = media_dir / avatar_filename
            with open(avatar_dest, 'wb') as f:
                f.write(resp.content)
            if is_episode_wb:
                local_avatar_url = f"/pool/whiteboard/{identifier}/{avatar_filename}"
            else:
                local_avatar_url = f"/asset-pool/{avatar_filename}"
            logger.info(f"Cached author avatar for @{tweet_data.get('author_handle')} -> {avatar_dest}")
        except Exception as e:
            logger.warning(f"Failed to cache author avatar: {e}")

    # Build local media URL mapping (CDN URL -> local URL)
    local_media_urls = [a["file_url"] for a in asset_records]

    return {
        "success": True,
        "url": url,
        "tweet_id": tweet_id,
        "files_downloaded": len(asset_records),
        "assets": asset_records,
        "tweet_data": tweet_data,
        "local_avatar_url": local_avatar_url,
        "local_media_urls": local_media_urls
    }


async def _download_via_ytdlp(
    identifier: str, url: str, tags: Optional[str],
    username: str, db: Session
):
    """Download media via yt-dlp for non-Twitter services (TikTok, YouTube, etc.).
    Returns rich metadata for local caching, matching Twitter download pattern."""
    import subprocess
    import tempfile
    import json
    import requests as http_requests

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Detect service for metadata enrichment
    service = 'generic'
    if 'tiktok.com' in domain:
        service = 'tiktok'
    elif 'youtube.com' in domain or 'youtu.be' in domain:
        service = 'youtube'
    elif 'instagram.com' in domain:
        service = 'instagram'
    elif 'rumble.com' in domain:
        service = 'rumble'
    elif 'soundcloud.com' in domain:
        service = 'soundcloud'

    # For TikTok: fetch oEmbed metadata first (fast, no auth, no rate limits)
    oembed_data = None
    if service == 'tiktok':
        try:
            oembed_resp = http_requests.get(
                f'https://www.tiktok.com/oembed?url={url}',
                timeout=10
            )
            if oembed_resp.status_code == 200:
                oembed_data = oembed_resp.json()
                logger.info(f"TikTok oEmbed: '{oembed_data.get('title', '')[:50]}' by {oembed_data.get('author_name')}")
        except Exception as e:
            logger.warning(f"TikTok oEmbed fetch failed: {e}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_template = str(temp_path / "%(id)s.%(ext)s")

        yt_dlp_cmd = [
            "python", "-m", "yt_dlp",
            "--write-info-json",
            "--write-thumbnail",
            "-o", output_template,
            url
        ]

        try:
            result = subprocess.run(
                yt_dlp_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                logger.error(f"yt-dlp failed: {result.stderr}")
                return {
                    "success": False,
                    "url": url,
                    "service": service,
                    "error": {
                        "service": service,
                        "status_code": 500,
                        "message": "Download failed",
                        "endpoint": "yt-dlp",
                        "detail": result.stderr[:300] if result.stderr else "Unknown yt-dlp error",
                        "fallback_used": False
                    }
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "url": url,
                "service": service,
                "error": {
                    "service": service,
                    "status_code": 408,
                    "message": "Download timed out",
                    "endpoint": "yt-dlp",
                    "detail": "Download timed out after 120 seconds",
                    "fallback_used": False
                }
            }
        except FileNotFoundError:
            return {
                "success": False,
                "url": url,
                "service": service,
                "error": {
                    "service": service,
                    "status_code": 500,
                    "message": "yt-dlp not installed",
                    "endpoint": "yt-dlp",
                    "detail": "yt-dlp is not installed on the server",
                    "fallback_used": False
                }
            }

        downloaded_files = []
        info_json = None

        for file_path in temp_path.iterdir():
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    info_json = json.load(f)
            elif file_path.suffix not in ['.json', '.part']:
                downloaded_files.append(file_path)

        if not downloaded_files:
            return {
                "success": False,
                "url": url,
                "service": service,
                "error": {
                    "service": service,
                    "status_code": 404,
                    "message": "No media files found",
                    "endpoint": "yt-dlp",
                    "detail": "yt-dlp completed but no media files were downloaded",
                    "fallback_used": False
                }
            }

        # Determine destination directory
        is_episode_wb = identifier.isdigit() and len(identifier) == 4
        if is_episode_wb:
            from core.paths import paths as path_manager
            media_dir = path_manager.get_whiteboard_media_dir(identifier)
        else:
            media_dir = Path("/mnt/sync/asset-pool")
        media_dir.mkdir(parents=True, exist_ok=True)

        asset_records = []

        for file_path in downloaded_files:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            if mime_type.startswith('video/'):
                media_category = 'video'
            elif mime_type.startswith('audio/'):
                media_category = 'audio'
            elif mime_type.startswith('image/'):
                media_category = 'image'
            else:
                media_category = 'document'

            # Registry-backed AssetID — see FK note in _download_twitter_media.
            asset_type = f"whiteboard_{media_category}"
            asset_id = AssetIDService.request_asset_id(
                db, entity_type=asset_type, reason="create", requested_by=username,
                context={"source": service, "source_url": url}
            )

            file_ext = file_path.suffix
            file_name = f"{asset_id}{file_ext}"
            dest_path = media_dir / file_name

            if is_episode_wb:
                relative_path = f"whiteboard/{identifier}/{file_name}"
                file_url = f"/pool/{relative_path}"  # whiteboard media moved to the pool
            else:
                relative_path = str(dest_path)
                file_url = f"/asset-pool/{file_name}"

            shutil.copy2(file_path, dest_path)
            file_size = os.path.getsize(dest_path)

            source_context = {}
            if info_json:
                source_context = {
                    'title': info_json.get('title'),
                    'uploader': info_json.get('uploader'),
                    'upload_date': info_json.get('upload_date'),
                    'description': info_json.get('description'),
                    'duration': info_json.get('duration'),
                    'view_count': info_json.get('view_count')
                }

            asset_pool_file = AssetPoolFile(
                asset_id=asset_id,
                file_path=str(dest_path),
                original_filename=file_path.name,
                mime_type=mime_type,
                file_size=file_size,
                source=service,
                source_url=url,
                source_context=source_context
            )
            db.add(asset_pool_file)

            if tags:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                for tag in tag_list:
                    db.add(AssetTag(asset_id=asset_id, tag=tag, created_by=username))

            if is_episode_wb:
                db.add(AssetTag(asset_id=asset_id, tag=f"episode:{identifier}", created_by=username))

            db.add(AssetTag(asset_id=asset_id, tag=service, created_by=username))
            db.commit()

            asset_records.append({
                "asset_id": asset_id,
                "file_url": file_url,
                "media_path": relative_path if is_episode_wb else None,
                "file_path": str(dest_path),
                "mime_type": mime_type,
                "file_size": file_size,
                "media_category": media_category,
                "original_filename": file_path.name,
                "source_context": source_context
            })

            logger.info(f"Downloaded {media_category} from {url} as {asset_id} -> {dest_path}")

        # Build rich content_data from yt-dlp info.json (mirrors tweet_data structure)
        content_data = None
        local_avatar_url = None
        local_thumbnail_url = None

        if info_json:
            content_data = {
                'platform': service,
                'post_id': info_json.get('id'),
                'post_text': info_json.get('description') or info_json.get('title', ''),
                'author_name': info_json.get('uploader') or info_json.get('creator'),
                'author_handle': info_json.get('uploader_id') or info_json.get('channel_id'),
                'author_url': info_json.get('uploader_url') or info_json.get('channel_url'),
                'published_time': info_json.get('upload_date'),
                'duration': info_json.get('duration'),
                'duration_string': info_json.get('duration_string'),
                'title': info_json.get('title'),
                'webpage_url': info_json.get('webpage_url'),
            }

            # Engagement metrics (varies by platform)
            if info_json.get('view_count') is not None:
                content_data['views'] = info_json.get('view_count')
            if info_json.get('like_count') is not None:
                content_data['likes'] = info_json.get('like_count')
            if info_json.get('comment_count') is not None:
                content_data['comments'] = info_json.get('comment_count')
            if info_json.get('repost_count') is not None:
                content_data['reposts'] = info_json.get('repost_count')

            # TikTok-specific fields
            if service == 'tiktok':
                content_data['track'] = info_json.get('track')
                content_data['artist'] = info_json.get('artist')
                # TikTok hashtags from description
                desc = info_json.get('description', '')
                hashtags = re.findall(r'#(\w+)', desc)
                if hashtags:
                    content_data['hashtags'] = hashtags

                # Enrich with oEmbed data (more reliable author info)
                if oembed_data:
                    content_data['author_name'] = oembed_data.get('author_name') or content_data.get('author_name')
                    content_data['author_url'] = oembed_data.get('author_url') or content_data.get('author_url')
                    # Extract handle from author_url (https://www.tiktok.com/@handle)
                    author_url = oembed_data.get('author_url', '')
                    if '/@' in author_url:
                        content_data['author_handle'] = author_url.split('/@')[-1].rstrip('/')
                    content_data['oembed_title'] = oembed_data.get('title')
                    content_data['embed_html'] = oembed_data.get('html')

            # Download and cache avatar/thumbnail locally
            thumbnail_url = info_json.get('thumbnail')
            # TikTok oEmbed thumbnail is often better quality
            if oembed_data and oembed_data.get('thumbnail_url'):
                thumbnail_url = oembed_data.get('thumbnail_url')

            # Cache thumbnail
            if thumbnail_url:
                try:
                    resp = http_requests.get(thumbnail_url, timeout=10)
                    resp.raise_for_status()
                    thumb_ext = '.jpg'
                    if 'png' in resp.headers.get('content-type', ''):
                        thumb_ext = '.png'
                    elif 'webp' in resp.headers.get('content-type', ''):
                        thumb_ext = '.webp'
                    post_id = info_json.get('id', 'unknown')
                    thumb_filename = f"thumb_{service}_{post_id}{thumb_ext}"
                    thumb_dest = media_dir / thumb_filename
                    with open(thumb_dest, 'wb') as f:
                        f.write(resp.content)
                    if is_episode_wb:
                        local_thumbnail_url = f"/pool/whiteboard/{identifier}/{thumb_filename}"
                    else:
                        local_thumbnail_url = f"/asset-pool/{thumb_filename}"
                    content_data['thumbnail_url'] = local_thumbnail_url
                    logger.info(f"Cached {service} thumbnail -> {thumb_dest}")
                except Exception as e:
                    logger.warning(f"Failed to cache thumbnail: {e}")
                    content_data['thumbnail_url'] = thumbnail_url

        local_media_urls = [a["file_url"] for a in asset_records]

        return {
            "success": True,
            "url": url,
            "service": service,
            "files_downloaded": len(asset_records),
            "assets": asset_records,
            "content_data": content_data,
            "local_avatar_url": local_avatar_url,
            "local_thumbnail_url": local_thumbnail_url,
            "local_media_urls": local_media_urls
        }
