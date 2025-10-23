"""
Twitter OAuth 2.0 Router
Handles Twitter OAuth authentication and API operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import requests
import secrets
import base64
import hashlib
from datetime import datetime, timedelta
import logging

from database import get_db
from auth.utils import get_current_user
from models_twitter import TwitterOAuthToken
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twitter", tags=["twitter"])


# Pydantic models
class TwitterAuthURL(BaseModel):
    auth_url: str
    state: str


class TweetCreate(BaseModel):
    text: str
    reply_to_tweet_id: Optional[str] = None


class TweetResponse(BaseModel):
    id: str
    text: str
    created_at: str


# In-memory state storage (in production, use Redis)
oauth_states = {}


def get_twitter_config(db: Session) -> Dict[str, str]:
    """Get Twitter OAuth configuration from database"""
    from api_config import APIConfigManager

    config_manager = APIConfigManager()
    twitter_config = config_manager.get_service_config('promotion', 'social_media', 'twitter')

    config = {}
    if twitter_config and twitter_config.get('apiKey'):
        config['client_id'] = twitter_config['apiKey']
    if twitter_config and twitter_config.get('apiSecret'):
        config['client_secret'] = twitter_config['apiSecret']

    return config


def generate_code_verifier() -> str:
    """Generate a code verifier for PKCE"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    return code_verifier.rstrip('=')


def generate_code_challenge(verifier: str) -> str:
    """Generate a code challenge from verifier for PKCE"""
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('utf-8')
    return challenge.rstrip('=')


@router.get("/auth/url")
async def get_auth_url(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TwitterAuthURL:
    """
    Generate Twitter OAuth 2.0 authorization URL
    """
    try:
        logger.info("Getting Twitter config from database...")
        config = get_twitter_config(db)
        logger.info(f"Twitter config retrieved: {list(config.keys())}")

        if 'client_id' not in config:
            logger.error("Twitter OAuth not configured - missing client_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Twitter OAuth not configured. Please add Client ID in settings."
            )

        logger.info(f"Client ID found: {config['client_id'][:10]}...")

        # Generate state and PKCE parameters
        state = secrets.token_urlsafe(32)
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)

        # Store state and code_verifier for callback verification
        oauth_states[state] = {
            'user_id': current_user['id'],
            'code_verifier': code_verifier,
            'created_at': datetime.utcnow()
        }

        # Build authorization URL
        redirect_uri = "https://192.168.51.210:8091/api/twitter/callback"
        scopes = [
            'tweet.read',
            'tweet.write',
            'users.read',
            'offline.access'  # For refresh token
        ]

        auth_url = (
            f"https://twitter.com/i/oauth2/authorize"
            f"?response_type=code"
            f"&client_id={config['client_id']}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={'+'.join(scopes)}"
            f"&state={state}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )

        return TwitterAuthURL(auth_url=auth_url, state=state)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Twitter auth URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {str(e)}"
        )


@router.post("/manual-callback")
async def manual_oauth_callback(
    code: str,
    state: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manual OAuth callback - user pastes authorization code manually
    (No external callback URL needed - works behind firewall)
    """
    try:
        # Verify state
        if state not in oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter. Please start authorization again."
            )

        state_data = oauth_states[state]
        code_verifier = state_data['code_verifier']

        # Clean up state
        del oauth_states[state]

        # Get Twitter config
        config = get_twitter_config(db)

        # Exchange code for access token
        token_url = "https://api.twitter.com/2/oauth2/token"
        # Use out-of-band redirect for manual flow
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

        # Prepare client credentials
        client_auth = base64.b64encode(
            f"{config['client_id']}:{config['client_secret']}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {client_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }

        response = requests.post(token_url, headers=headers, data=data, timeout=10)
        response.raise_for_status()

        token_data = response.json()

        # Get user info from Twitter
        user_info = get_twitter_user_info(token_data['access_token'])

        # Calculate expiration time
        expires_at = None
        if 'expires_in' in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

        # Store or update token in database
        existing_token = db.query(TwitterOAuthToken).filter(
            TwitterOAuthToken.user_id == current_user['user_id']
        ).first()

        if existing_token:
            existing_token.access_token = token_data['access_token']
            existing_token.refresh_token = token_data.get('refresh_token')
            existing_token.expires_at = expires_at
            existing_token.scope = token_data.get('scope')
            existing_token.twitter_user_id = user_info.get('id')
            existing_token.twitter_username = user_info.get('username')
            existing_token.twitter_name = user_info.get('name')
            existing_token.updated_at = datetime.utcnow()
        else:
            new_token = TwitterOAuthToken(
                user_id=current_user['user_id'],
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at,
                scope=token_data.get('scope'),
                twitter_user_id=user_info.get('id'),
                twitter_username=user_info.get('username'),
                twitter_name=user_info.get('name')
            )
            db.add(new_token)

        db.commit()

        return {
            'success': True,
            'message': 'Twitter account connected successfully',
            'username': user_info.get('username'),
            'name': user_info.get('name')
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter OAuth error: {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Twitter OAuth failed: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth 2.0 callback from Twitter (for public-facing URLs)
    """
    try:
        # Verify state
        if state not in oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )

        state_data = oauth_states[state]
        user_id = state_data['user_id']
        code_verifier = state_data['code_verifier']

        # Clean up state
        del oauth_states[state]

        # Get Twitter config
        config = get_twitter_config(db)

        # Exchange code for access token
        token_url = "https://api.twitter.com/2/oauth2/token"
        redirect_uri = "https://192.168.51.210:8091/api/twitter/callback"

        # Prepare client credentials
        client_auth = base64.b64encode(
            f"{config['client_id']}:{config['client_secret']}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {client_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }

        response = requests.post(token_url, headers=headers, data=data, timeout=10)
        response.raise_for_status()

        token_data = response.json()

        # Get user info from Twitter
        user_info = get_twitter_user_info(token_data['access_token'])

        # Calculate expiration time
        expires_at = None
        if 'expires_in' in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

        # Store or update token in database
        existing_token = db.query(TwitterOAuthToken).filter(
            TwitterOAuthToken.user_id == user_id
        ).first()

        if existing_token:
            existing_token.access_token = token_data['access_token']
            existing_token.refresh_token = token_data.get('refresh_token')
            existing_token.expires_at = expires_at
            existing_token.scope = token_data.get('scope')
            existing_token.twitter_user_id = user_info.get('id')
            existing_token.twitter_username = user_info.get('username')
            existing_token.twitter_name = user_info.get('name')
            existing_token.updated_at = datetime.utcnow()
        else:
            new_token = TwitterOAuthToken(
                user_id=user_id,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at,
                scope=token_data.get('scope'),
                twitter_user_id=user_info.get('id'),
                twitter_username=user_info.get('username'),
                twitter_name=user_info.get('name')
            )
            db.add(new_token)

        db.commit()

        # Redirect to frontend settings page
        return RedirectResponse(url="/settings?tab=api-access&twitter=connected")

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter OAuth error: {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Twitter OAuth failed: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


def get_twitter_user_info(access_token: str) -> Dict[str, Any]:
    """Get Twitter user info using access token"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(
            'https://api.twitter.com/2/users/me',
            headers=headers,
            params={'user.fields': 'id,name,username'},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        return data.get('data', {})

    except Exception as e:
        logger.error(f"Error fetching Twitter user info: {e}")
        return {}


def get_user_token(user_id: int, db: Session) -> Optional[TwitterOAuthToken]:
    """Get user's Twitter OAuth token from database"""
    token = db.query(TwitterOAuthToken).filter(
        TwitterOAuthToken.user_id == user_id
    ).first()

    if not token:
        return None

    # Check if token is expired
    if token.expires_at and token.expires_at < datetime.utcnow():
        # Try to refresh token
        if token.refresh_token:
            refreshed_token = refresh_access_token(token, db)
            if refreshed_token:
                return refreshed_token
        return None

    return token


def refresh_access_token(token: TwitterOAuthToken, db: Session) -> Optional[TwitterOAuthToken]:
    """Refresh an expired access token"""
    try:
        config = get_twitter_config(db)

        client_auth = base64.b64encode(
            f"{config['client_id']}:{config['client_secret']}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {client_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': token.refresh_token
        }

        response = requests.post(
            'https://api.twitter.com/2/oauth2/token',
            headers=headers,
            data=data,
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()

        # Update token
        token.access_token = token_data['access_token']
        if 'refresh_token' in token_data:
            token.refresh_token = token_data['refresh_token']
        if 'expires_in' in token_data:
            token.expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        token.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(token)

        logger.info(f"Refreshed Twitter token for user {token.user_id}")
        return token

    except Exception as e:
        logger.error(f"Error refreshing Twitter token: {e}")
        return None


@router.get("/status")
async def get_connection_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has connected their Twitter account"""
    token = get_user_token(current_user['user_id'], db)

    if token:
        return {
            'connected': True,
            'username': token.twitter_username,
            'name': token.twitter_name,
            'expires_at': token.expires_at.isoformat() if token.expires_at else None
        }

    return {'connected': False}


@router.delete("/disconnect")
async def disconnect_twitter(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect Twitter account"""
    token = db.query(TwitterOAuthToken).filter(
        TwitterOAuthToken.user_id == current_user['user_id']
    ).first()

    if token:
        db.delete(token)
        db.commit()
        return {'success': True, 'message': 'Twitter account disconnected'}

    return {'success': False, 'message': 'No Twitter account connected'}


@router.post("/tweet")
async def post_tweet(
    tweet: TweetCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TweetResponse:
    """Post a tweet"""
    try:
        token = get_user_token(current_user['user_id'], db)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Twitter account not connected"
            )

        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {'text': tweet.text}
        if tweet.reply_to_tweet_id:
            payload['reply'] = {'in_reply_to_tweet_id': tweet.reply_to_tweet_id}

        response = requests.post(
            'https://api.twitter.com/2/tweets',
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        tweet_data = data['data']

        return TweetResponse(
            id=tweet_data['id'],
            text=tweet_data['text'],
            created_at=datetime.utcnow().isoformat()
        )

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter API error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Twitter API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error posting tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/timeline")
async def get_user_timeline(
    max_results: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's home timeline"""
    try:
        token = get_user_token(current_user['user_id'], db)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Twitter account not connected"
            )

        headers = {
            'Authorization': f'Bearer {token.access_token}'
        }

        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,public_metrics,author_id',
            'expansions': 'author_id',
            'user.fields': 'name,username,profile_image_url'
        }

        response = requests.get(
            f'https://api.twitter.com/2/users/{token.twitter_user_id}/tweets',
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter API error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Twitter API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/tweet/{tweet_id}")
async def delete_tweet(
    tweet_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a tweet"""
    try:
        token = get_user_token(current_user['user_id'], db)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Twitter account not connected"
            )

        headers = {
            'Authorization': f'Bearer {token.access_token}'
        }

        response = requests.delete(
            f'https://api.twitter.com/2/tweets/{tweet_id}',
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        return {'success': True, 'message': 'Tweet deleted'}

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter API error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Twitter API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error deleting tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{username}")
async def get_user_info(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a Twitter user"""
    try:
        token = get_user_token(current_user['user_id'], db)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Twitter account not connected"
            )

        headers = {
            'Authorization': f'Bearer {token.access_token}'
        }

        params = {
            'user.fields': 'id,name,username,created_at,description,location,profile_image_url,public_metrics,verified,url'
        }

        response = requests.get(
            f'https://api.twitter.com/2/users/by/username/{username}',
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter API error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Twitter API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tweet/{tweet_id}/media")
async def download_tweet_media(
    tweet_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get media URLs from a tweet for downloading
    Returns direct URLs to photos and videos
    """
    try:
        token = get_user_token(current_user['user_id'], db)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Twitter account not connected"
            )

        headers = {
            'Authorization': f'Bearer {token.access_token}'
        }

        params = {
            'expansions': 'attachments.media_keys',
            'media.fields': 'media_key,type,url,preview_image_url,width,height,duration_ms,variants'
        }

        response = requests.get(
            f'https://api.twitter.com/2/tweets/{tweet_id}',
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        media_items = []

        if 'includes' in data and 'media' in data['includes']:
            for media in data['includes']['media']:
                media_info = {
                    'media_key': media.get('media_key'),
                    'type': media.get('type'),
                    'width': media.get('width'),
                    'height': media.get('height')
                }

                if media['type'] == 'photo':
                    media_info['url'] = media.get('url')
                    media_info['download_url'] = media.get('url')

                elif media['type'] == 'video' or media['type'] == 'animated_gif':
                    media_info['preview_url'] = media.get('preview_image_url')
                    media_info['duration_ms'] = media.get('duration_ms')

                    # Get highest quality video variant
                    if 'variants' in media:
                        variants = media['variants']
                        # Filter for mp4 variants
                        mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']

                        if mp4_variants:
                            # Sort by bitrate (highest first)
                            mp4_variants.sort(key=lambda x: x.get('bit_rate', 0), reverse=True)
                            media_info['download_url'] = mp4_variants[0]['url']
                            media_info['bitrate'] = mp4_variants[0].get('bit_rate')
                            media_info['all_variants'] = mp4_variants

                media_items.append(media_info)

        return {
            'tweet_id': tweet_id,
            'media_count': len(media_items),
            'media': media_items
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"Twitter API error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Twitter API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error fetching media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/media/download")
async def download_media_file(
    url: str,
    filename: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Download media file from Twitter URL to Show-Build server
    """
    try:
        import os
        from pathlib import Path

        # Download the media
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Determine filename
        if not filename:
            filename = url.split('/')[-1].split('?')[0]
            if not filename:
                filename = f"twitter_media_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Save to shared media directory
        media_dir = Path('/shared_media/twitter')
        media_dir.mkdir(parents=True, exist_ok=True)

        filepath = media_dir / filename

        # Write file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = filepath.stat().st_size

        return {
            'success': True,
            'filename': filename,
            'filepath': str(filepath),
            'size_bytes': file_size,
            'message': f'Media downloaded successfully: {filename}'
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"Error downloading media: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download media: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error saving media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
