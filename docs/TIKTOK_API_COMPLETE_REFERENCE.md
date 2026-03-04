# TikTok API -- Complete Reference

**Last Updated**: 2026-02-25
**Official Docs**: https://developers.tiktok.com/
**Business API Docs**: https://business-api.tiktok.com/portal/docs
**Base URL**: `https://open.tiktokapis.com`
**oEmbed URL**: `https://www.tiktok.com/oembed`
**API Version**: v2

This is a comprehensive single-document reference for the TikTok Developer API ecosystem. It covers the official TikTok for Developers platform (consumer APIs) and the TikTok for Business API (advertising/marketing APIs).

---

## Table of Contents

1. [API Products Overview](#1-api-products-overview)
2. [Authentication](#2-authentication)
3. [Scopes and Permissions](#3-scopes-and-permissions)
4. [Login Kit](#4-login-kit)
5. [Display API -- User Info](#5-display-api--user-info)
6. [Display API -- Video List](#6-display-api--video-list)
7. [Display API -- Video Query](#7-display-api--video-query)
8. [Content Posting API -- Overview](#8-content-posting-api--overview)
9. [Content Posting API -- Query Creator Info](#9-content-posting-api--query-creator-info)
10. [Content Posting API -- Direct Post Video](#10-content-posting-api--direct-post-video)
11. [Content Posting API -- Upload Video (Media Upload)](#11-content-posting-api--upload-video-media-upload)
12. [Content Posting API -- Photo Post](#12-content-posting-api--photo-post)
13. [Content Posting API -- Status Fetch](#13-content-posting-api--status-fetch)
14. [Content Posting API -- Media Transfer Guide](#14-content-posting-api--media-transfer-guide)
15. [Share Kit](#15-share-kit)
16. [Embed Videos (oEmbed)](#16-embed-videos-oembed)
17. [Webhooks](#17-webhooks)
18. [Research API -- Overview](#18-research-api--overview)
19. [Research API -- Query Videos](#19-research-api--query-videos)
20. [Research API -- Query User Info](#20-research-api--query-user-info)
21. [Research API -- Query Video Comments](#21-research-api--query-video-comments)
22. [Research API -- User Followers](#22-research-api--user-followers)
23. [Research API -- User Following](#23-research-api--user-following)
24. [Research API -- User Liked Videos](#24-research-api--user-liked-videos)
25. [Research API -- User Pinned Videos](#25-research-api--user-pinned-videos)
26. [Research API -- User Reposted Videos](#26-research-api--user-reposted-videos)
27. [Research API -- Query Playlist Info](#27-research-api--query-playlist-info)
28. [Commercial Content API](#28-commercial-content-api)
29. [Data Portability API](#29-data-portability-api)
30. [TikTok for Business (Marketing API)](#30-tiktok-for-business-marketing-api)
31. [Data Dictionary](#31-data-dictionary)
32. [Rate Limits](#32-rate-limits)
33. [Error Codes and Handling](#33-error-codes-and-handling)
34. [Content Specifications](#34-content-specifications)
35. [Sandbox and Testing](#35-sandbox-and-testing)
36. [App Review and Audit Process](#36-app-review-and-audit-process)
37. [API Versioning and Migration](#37-api-versioning-and-migration)

---

## 1. API Products Overview

TikTok's developer platform offers the following distinct API products:

| Product | Purpose | Auth Type | Access |
|---------|---------|-----------|--------|
| **Login Kit** | OAuth 2.0 sign-in with TikTok credentials | OAuth 2.0 | Open (app review) |
| **Share Kit** | Share videos/photos from your app to TikTok | SDK (mobile) | Open (app review) |
| **Display API** | Read user profile and video data | User Access Token | Open (app review) |
| **Content Posting API** | Post videos/photos to TikTok programmatically | User Access Token | Open (app review + audit) |
| **Embed Videos** | oEmbed endpoint for embedding TikTok videos | None (public) | Open |
| **Webhooks** | Real-time event notifications | Callback URL | Open (app review) |
| **Research API** | Academic research on public TikTok data | Client Access Token | Restricted (application required) |
| **Commercial Content API** | Query ads and branded content data | Client Access Token | Restricted (application required) |
| **Data Portability API** | Transfer user data (EEA/UK only) | User Access Token | Restricted (application required) |
| **TikTok for Business (Marketing API)** | Ads Manager: campaigns, ad groups, ads, reporting | OAuth 2.0 / API Key | Business accounts |

**Developer Portal**: https://developers.tiktok.com/

---

## 2. Authentication

TikTok API v2 supports two primary authentication mechanisms:

### 2.1 OAuth 2.0 User Access Token (Authorization Code Flow)

Used for APIs that act **on behalf of a user** (Display API, Content Posting API, Data Portability API).

**Authorization Endpoint**: `https://www.tiktok.com/v2/auth/authorize/`
**Token Endpoint**: `POST https://open.tiktokapis.com/v2/oauth/token/`
**Revoke Endpoint**: `POST https://open.tiktokapis.com/v2/oauth/revoke/`

#### Step 1: Redirect User to Authorization

```
https://www.tiktok.com/v2/auth/authorize/
  ?client_key={CLIENT_KEY}
  &scope={COMMA_SEPARATED_SCOPES}
  &response_type=code
  &redirect_uri={REDIRECT_URI}
  &state={CSRF_STATE}
```

#### Step 2: Exchange Authorization Code for Access Token

```bash
curl -X POST 'https://open.tiktokapis.com/v2/oauth/token/' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_key={CLIENT_KEY}' \
  -d 'client_secret={CLIENT_SECRET}' \
  -d 'code={AUTH_CODE}' \
  -d 'grant_type=authorization_code' \
  -d 'redirect_uri={REDIRECT_URI}'
```

**PKCE Note**: Mobile/Desktop flows require `code_verifier` parameter (Proof Key for Code Exchange).

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | Bearer token for API calls |
| `expires_in` | int64 | Token lifetime: **86400 seconds (24 hours)** |
| `open_id` | string | Unique user identifier for your app |
| `scope` | string | Granted scopes (comma-separated) |
| `refresh_token` | string | Token for refreshing access |
| `refresh_expires_in` | int64 | Refresh token lifetime: **31536000 seconds (365 days)** |
| `token_type` | string | Always `"Bearer"` |

#### Step 3: Refresh Access Token

```bash
curl -X POST 'https://open.tiktokapis.com/v2/oauth/token/' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_key={CLIENT_KEY}' \
  -d 'client_secret={CLIENT_SECRET}' \
  -d 'grant_type=refresh_token' \
  -d 'refresh_token={REFRESH_TOKEN}'
```

**IMPORTANT**: The returned `refresh_token` may differ from the one sent. Always use the newly-returned refresh token for subsequent refreshes.

#### Step 4: Revoke Token

```bash
curl -X POST 'https://open.tiktokapis.com/v2/oauth/revoke/' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_key={CLIENT_KEY}' \
  -d 'client_secret={CLIENT_SECRET}' \
  -d 'token={ACCESS_TOKEN}'
```

### 2.2 Client Access Token (Client Credentials Flow)

Used for APIs that do **not** require user authorization (Research API, Commercial Content API).

```bash
curl -X POST 'https://open.tiktokapis.com/v2/oauth/token/' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_key={CLIENT_KEY}' \
  -d 'client_secret={CLIENT_SECRET}' \
  -d 'grant_type=client_credentials'
```

**Response**:

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | Client access token |
| `expires_in` | int64 | **7200 seconds (2 hours)** |
| `token_type` | string | `"Bearer"` |

### 2.3 Token Lifetimes Summary

| Token Type | Lifetime | Refresh |
|-----------|----------|---------|
| User Access Token | 24 hours (86,400s) | Via refresh_token |
| User Refresh Token | 365 days (31,536,000s) | New one issued on refresh |
| Client Access Token | 2 hours (7,200s) | Re-generate with client credentials |

### 2.4 API Keys

Managed at: https://developers.tiktok.com/ (Developer Portal)

- **Client Key** -- identifies your application
- **Client Secret** -- authenticates your application (keep secret)
- **Access Token** -- user-context or client-context bearer token
- **Redirect URI** -- registered callback URL for OAuth flow

---

## 3. Scopes and Permissions

Every TikTok API endpoint requires one or more scopes. Scopes represent permissions granted by end users. The `user.info.basic` scope is automatically added for all Login Kit apps.

### 3.1 User Scopes

| Scope | Description | Required For |
|-------|-------------|-------------|
| `user.info.basic` | Read basic profile info (open_id, avatar, display_name) | Login Kit, Display API |
| `user.info.profile` | Read extended profile (bio, is_verified, username, profile_deep_link) | Display API |
| `user.info.stats` | Read user statistics (follower_count, following_count, likes_count, video_count) | Display API |

### 3.2 Video Scopes

| Scope | Description | Required For |
|-------|-------------|-------------|
| `video.list` | Read user's public videos on TikTok | Display API |
| `video.publish` | Directly post content to user's TikTok profile | Content Posting API (Direct Post) |
| `video.upload` | Share content as draft to user's TikTok inbox | Content Posting API (Media Upload) |

### 3.3 Research Scopes

| Scope | Description | Required For |
|-------|-------------|-------------|
| `research.data.basic` | Access to TikTok public data for research | Research API |
| `research.data.u18eu` | Access to European under-18 and public data | Research API (EU) |
| `research.data.vra` | Access to provisioned data for vetted researchers | Research API (Vetted) |
| `research.adlib.basic` | Access to public commercial data for research | Commercial Content API |

### 3.4 Data Portability Scopes

| Scope | Description |
|-------|-------------|
| `portability.all.single` | One-time full data archive request |
| `portability.all.ongoing` | Ongoing full data archive requests |
| `portability.activity.single` | One-time user activity data request |
| `portability.activity.ongoing` | Ongoing user activity data requests |
| `portability.directmessages.single` | One-time direct message data request |
| `portability.directmessages.ongoing` | Ongoing direct message data requests |
| `portability.postsandprofile.single` | One-time posts/profile data request |
| `portability.postsandprofile.ongoing` | Ongoing posts/profile data requests |

### 3.5 Local Service Scopes

| Scope | Description |
|-------|-------------|
| `local.product.manage` | Create and manage product listings |
| `local.shop.manage` | Create and manage local shops |
| `local.voucher.manage` | Validate and redeem vouchers |

### 3.6 Scope Management Rules

- Developers request scopes through the Developer Portal app page
- **Applying for a scope does not grant access** -- each user must also authorize the app for specific scopes
- Users may agree to only a subset of requested scopes
- Scopes can be managed after app approval on the app settings page

---

## 4. Login Kit

**Purpose**: Allow users to sign in to your app using their TikTok credentials.

**Platforms**: iOS, Android, Desktop, Web

**Protocol**: OAuth 2.0 Authorization Code Flow

**Default Scope**: `user.info.basic` (automatically included)

### Web Integration

**Authorization URL**:
```
https://www.tiktok.com/v2/auth/authorize/
  ?client_key={CLIENT_KEY}
  &scope=user.info.basic,user.info.profile
  &response_type=code
  &redirect_uri={REDIRECT_URI}
  &state={CSRF_STATE}
```

### Mobile Integration (SDK)

The TikTok OpenSDK is available via:
- **iOS**: Swift Package Manager, CocoaPods
- **Android**: Maven repository
- **GitHub**: https://github.com/tiktok/tiktok-opensdk-ios

Login Kit and Share Kit are separate downloadable frameworks to keep integrations lightweight.

---

## 5. Display API -- User Info

### GET /v2/user/info/

Retrieves basic profile information for the authenticated user.

**URL**: `https://open.tiktokapis.com/v2/user/info/`
**Method**: GET
**Auth**: User Access Token (Bearer)
**Rate Limit**: 600 requests/minute

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated list of user fields to retrieve |

**Available Fields by Scope**:

| Field | Type | Required Scope |
|-------|------|---------------|
| `open_id` | string | `user.info.basic` |
| `union_id` | string | `user.info.basic` |
| `avatar_url` | string | `user.info.basic` |
| `avatar_url_100` | string | `user.info.basic` |
| `avatar_large_url` | string | `user.info.basic` |
| `display_name` | string | `user.info.basic` |
| `bio_description` | string | `user.info.profile` |
| `profile_deep_link` | string | `user.info.profile` |
| `is_verified` | boolean | `user.info.profile` |
| `username` | string | `user.info.profile` |
| `follower_count` | int64 | `user.info.stats` |
| `following_count` | int64 | `user.info.stats` |
| `likes_count` | int64 | `user.info.stats` |
| `video_count` | int64 | `user.info.stats` |

**Example Request**:
```bash
curl -L -X GET 'https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name,bio_description,follower_count' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Response**:
```json
{
  "data": {
    "user": {
      "open_id": "afd97af1-b87b-...",
      "union_id": "c4bbd15a-a4c3-...",
      "avatar_url": "https://...",
      "display_name": "Example User",
      "bio_description": "Creator bio text",
      "follower_count": 12500
    }
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": "20230101..."
  }
}
```

---

## 6. Display API -- Video List

### POST /v2/video/list/

Returns a paginated list of the authenticated user's public TikTok video posts, sorted by `create_time` in descending order.

**URL**: `https://open.tiktokapis.com/v2/video/list/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.list`
**Rate Limit**: 600 requests/minute

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated video fields |

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `cursor` | int64 | No | UTC Unix timestamp in milliseconds; fetches videos before this time |
| `max_count` | int32 | No | Videos per page. Default: 10, Maximum: 20 |

**Available Video Fields**: `id`, `create_time`, `cover_image_url`, `share_url`, `video_description`, `duration`, `height`, `width`, `title`, `embed_html`, `embed_link`, `like_count`, `comment_count`, `share_count`, `view_count`

**Response**:
```json
{
  "data": {
    "videos": [
      {
        "id": "7123456789012345678",
        "title": "My Video",
        "create_time": 1672531200,
        "cover_image_url": "https://...",
        "duration": 15,
        "like_count": 1500,
        "view_count": 25000
      }
    ],
    "cursor": 1672444800000,
    "has_more": true
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

**Pagination**: Pass the response `cursor` value to the next request to fetch the next page.

---

## 7. Display API -- Video Query

### POST /v2/video/query/

Query specific videos by their IDs. Verifies that videos belong to the authenticated user and returns video details. Can also be used to refresh cover image URL TTL.

**URL**: `https://open.tiktokapis.com/v2/video/query/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.list`
**Rate Limit**: 600 requests/minute

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated video fields |

**Request Body**:
```json
{
  "filters": {
    "video_ids": ["7123456789012345678", "7123456789012345679"]
  }
}
```

**Constraints**: Maximum **20 video IDs** per request.

**Available Video Fields**: `id`, `create_time`, `cover_image_url`, `share_url`, `video_description`, `duration`, `height`, `width`, `title`, `embed_html`, `embed_link`, `like_count`, `comment_count`, `share_count`, `view_count`

**Response**:
```json
{
  "data": {
    "videos": [
      {
        "id": "7123456789012345678",
        "title": "My Video",
        "video_description": "Check this out! #trending",
        "duration": 30,
        "like_count": 5000
      }
    ]
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

---

## 8. Content Posting API -- Overview

The Content Posting API enables programmatic posting of videos and photos to TikTok. It supports two posting modes:

| Mode | Scope | Description |
|------|-------|-------------|
| **Direct Post** (`DIRECT_POST`) | `video.publish` | Immediately publishes to user's TikTok profile |
| **Media Upload** (`MEDIA_UPLOAD`) | `video.upload` | Sends to user's TikTok inbox as draft; user completes posting in the TikTok app |

**CRITICAL**: All content posted by **unaudited** API clients is restricted to **private viewing mode** (`SELF_ONLY`). Your app must undergo an audit to enable public posting.

### Content Posting Workflow

```
1. POST /v2/post/publish/creator_info/query/    --> Get creator capabilities
2. POST /v2/post/publish/video/init/             --> Initialize video upload (Direct Post)
   POST /v2/post/publish/inbox/video/init/       --> Initialize video upload (Media Upload)
   POST /v2/post/publish/content/init/           --> Initialize photo post
3. PUT  {upload_url}                             --> Upload file chunks (FILE_UPLOAD only)
4. POST /v2/post/publish/status/fetch/           --> Poll for publish status
   (or use webhooks for real-time notifications)
```

### Daily Limits

- Maximum **5 pending shares** within any 24-hour period
- Maximum **20 video posts** per day via API
- Maximum **2 videos** per minute

---

## 9. Content Posting API -- Query Creator Info

### POST /v2/post/publish/creator_info/query/

**Must be called before posting** to get the target creator's current settings and capabilities.

**URL**: `https://open.tiktokapis.com/v2/post/publish/creator_info/query/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.publish`
**Rate Limit**: 20 requests/minute per user access token
**Content-Type**: `application/json; charset=UTF-8`

**Request Body**: None (authentication alone drives the query)

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `creator_avatar_url` | string | Profile image URL (2-hour TTL) |
| `creator_username` | string | Unique creator identifier |
| `creator_nickname` | string | Display name |
| `privacy_level_options` | string[] | Available privacy settings for this account |
| `comment_disabled` | boolean | True if comments set to "No one" |
| `duet_disabled` | boolean | True if private account or duets disabled |
| `stitch_disabled` | boolean | True if private account or stitches disabled |
| `max_video_post_duration_sec` | int32 | Maximum video length in seconds |

**Privacy Level Options** (varies by account type):
- `PUBLIC_TO_EVERYONE` -- visible to all users
- `MUTUAL_FOLLOW_FRIENDS` -- visible to mutual followers
- `FOLLOWER_OF_CREATOR` -- visible to followers only
- `SELF_ONLY` -- visible only to the creator

**Error Codes**:

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 200 | `ok` | Success |
| 200 | `spam_risk_too_many_posts` | Daily API post limit reached |
| 200 | `spam_risk_user_banned_from_posting` | Account posting suspended |
| 200 | `reached_active_user_cap` | Client daily quota exhausted |
| 401 | `access_token_invalid` | Token expired or invalid |
| 401 | `scope_not_authorized` | Missing `video.publish` permission |
| 429 | `rate_limit_exceeded` | Request throttled |

---

## 10. Content Posting API -- Direct Post Video

### POST /v2/post/publish/video/init/

Initialize a video upload for direct publishing to the user's TikTok profile.

**URL**: `https://open.tiktokapis.com/v2/post/publish/video/init/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.publish`
**Rate Limit**: 6 requests/minute per user access token
**Content-Type**: `application/json; charset=UTF-8`

**Request Body**:

```json
{
  "post_info": {
    "title": "My awesome video #trending",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_duet": false,
    "disable_comment": false,
    "disable_stitch": false,
    "video_cover_timestamp_ms": 1000,
    "brand_content_toggle": false,
    "brand_organic_toggle": false
  },
  "source_info": {
    "source": "FILE_UPLOAD",
    "video_size": 50000000,
    "chunk_size": 10000000,
    "total_chunk_count": 5
  }
}
```

**Post Info Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Video caption. Max **2200 UTF-16 runes**. Supports hashtags and @mentions |
| `privacy_level` | string | Yes | Must match creator's `privacy_level_options` |
| `disable_duet` | boolean | No | Disable duet for this video |
| `disable_comment` | boolean | No | Disable comments for this video |
| `disable_stitch` | boolean | No | Disable stitch for this video |
| `video_cover_timestamp_ms` | int64 | No | Timestamp in ms for cover image |
| `brand_content_toggle` | boolean | No | For paid partnerships |
| `brand_organic_toggle` | boolean | No | For creator's own business promotion |

**Source Info -- FILE_UPLOAD**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | `"FILE_UPLOAD"` |
| `video_size` | int64 | Yes | Total file size in bytes |
| `chunk_size` | int64 | Yes | Size of each upload chunk in bytes |
| `total_chunk_count` | int64 | Yes | Number of chunks = video_size / chunk_size (rounded down) |

**Source Info -- PULL_FROM_URL**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | `"PULL_FROM_URL"` |
| `video_url` | string | Yes | HTTPS URL of video. Domain must be pre-verified |

**Success Response**:
```json
{
  "data": {
    "publish_id": "v_pub_12345...",
    "upload_url": "https://open-upload.tiktokapis.com/video/?upload_id=..."
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

| Response Field | Type | Description |
|---------------|------|-------------|
| `publish_id` | string | Tracking ID (max 64 chars) |
| `upload_url` | string | Upload endpoint URL (max 256 chars, valid 1 hour). Only for FILE_UPLOAD |

**Error Codes**:

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `invalid_param` | Parameter validation failed |
| 403 | `unaudited_client_can_only_post_to_private_accounts` | Audit required for public posts |
| 403 | `privacy_level_option_mismatch` | Privacy setting not in creator's options |
| 403 | `spam_risk_user_banned_from_posting` | User posting restriction active |
| 403 | `url_ownership_unverified` | Domain not verified for PULL_FROM_URL |
| 401 | `access_token_invalid` | Token expired or invalid |
| 401 | `scope_not_authorized` | Missing `video.publish` scope |
| 429 | `rate_limit_exceeded` | Request throttled |

---

## 11. Content Posting API -- Upload Video (Media Upload)

### POST /v2/post/publish/inbox/video/init/

Initialize a video upload that is sent to the user's TikTok inbox as a draft.

**URL**: `https://open.tiktokapis.com/v2/post/publish/inbox/video/init/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.upload`
**Rate Limit**: 6 requests/minute per user access token
**Content-Type**: `application/json; charset=UTF-8`

**Request Body**: Same structure as Direct Post Video (Section 10) but uses `video.upload` scope.

**Source Info** parameters are identical to Direct Post.

**Success Response**:
```json
{
  "data": {
    "publish_id": "v_inbox_12345...",
    "upload_url": "https://open-upload.tiktokapis.com/video/?upload_id=..."
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

**Error Codes**:

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `invalid_param` | Parameter validation failed |
| 403 | `spam_risk_too_many_pending_share` | Max 5 pending shares in 24 hours |
| 403 | `url_ownership_unverified` | Domain not verified for PULL_FROM_URL |
| 401 | `access_token_invalid` | Token expired or invalid |
| 401 | `scope_not_authorized` | Missing `video.upload` scope |
| 429 | `rate_limit_exceeded` | Request throttled |

---

## 12. Content Posting API -- Photo Post

### POST /v2/post/publish/content/init/

Post photo carousels (Photo Mode) to TikTok.

**URL**: `https://open.tiktokapis.com/v2/post/publish/content/init/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.publish` (direct post) or `video.upload` (media upload)
**Rate Limit**: 6 requests/minute per user access token

**Request Body**:
```json
{
  "post_mode": "DIRECT_POST",
  "media_type": "PHOTO",
  "post_info": {
    "title": "Check out these photos!",
    "description": "Beautiful scenery from my trip #travel",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false,
    "auto_add_music": true,
    "brand_content_toggle": false,
    "brand_organic_toggle": false
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "photo_images": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "photo_cover_index": 0
  }
}
```

**Post Info Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Photo post title. Max **90 UTF-16 runes** |
| `description` | string | No | Photo post description. Max **4000 UTF-16 runes** |
| `privacy_level` | string | Yes | Must match creator's options |
| `disable_comment` | boolean | No | Disable comments (direct post only) |
| `auto_add_music` | boolean | No | Auto-add recommended music (direct post only) |
| `brand_content_toggle` | boolean | No | Paid partnership flag |
| `brand_organic_toggle` | boolean | No | Creator's business promotion flag |

**Source Info Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | `"PULL_FROM_URL"` only |
| `photo_images` | string[] | Yes | Array of image URLs (4-35 images) |
| `photo_cover_index` | int32 | No | Index of cover photo (0-based) |

**Photo Specifications**:

| Spec | Requirement |
|------|------------|
| Image count | 4 to 35 images per carousel |
| Formats | JPEG (JPG), PNG |
| Max file size per image | 20 MB |
| Total carousel size | 500 MB |
| Recommended resolution | 1080x1920 px (9:16) |
| Supported aspect ratios | 9:16, 1:1, 4:5 |

**Response**: Returns `publish_id` for status tracking.

---

## 13. Content Posting API -- Status Fetch

### POST /v2/post/publish/status/fetch/

Poll for the status of a publish action.

**URL**: `https://open.tiktokapis.com/v2/post/publish/status/fetch/`
**Method**: POST
**Auth**: User Access Token (Bearer)
**Required Scope**: `video.upload` or `video.publish`
**Rate Limit**: 30 requests/minute per user access token

**Request Body**:
```json
{
  "publish_id": "v_pub_12345..."
}
```

**Response**:
```json
{
  "data": {
    "status": "PUBLISH_COMPLETE",
    "fail_reason": "",
    "publicaly_available_post_id": [7123456789012345678],
    "uploaded_bytes": 50000000,
    "downloaded_bytes": 50000000
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

**Status Values**:

| Status | Description |
|--------|-------------|
| `PROCESSING_UPLOAD` | File upload in progress |
| `PROCESSING_DOWNLOAD` | Download from URL in progress |
| `SEND_TO_USER_INBOX` | Notification sent to creator's inbox |
| `PUBLISH_COMPLETE` | Content successfully posted |
| `FAILED` | Process failed; check `fail_reason` |

**Note**: Moderation usually finishes within 1 minute, but may take a few hours in some cases.

**Error Codes**:

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `invalid_publish_id` | Non-existent publish ID |
| 400 | `token_not_authorized_for_specified_publish_id` | Insufficient authorization |
| 401 | `access_token_invalid` | Invalid or expired token |
| 401 | `scope_not_authorized` | Missing required scopes |
| 429 | `rate_limit_exceeded` | Rate limit exceeded |

---

## 14. Content Posting API -- Media Transfer Guide

### Chunk Upload (FILE_UPLOAD)

After initializing a video upload with `source=FILE_UPLOAD`, upload the binary file to the returned `upload_url`.

**Method**: PUT
**URL**: The `upload_url` from the init response

**Headers**:

| Header | Value |
|--------|-------|
| `Content-Type` | `video/mp4`, `video/quicktime`, or `video/webm` |
| `Content-Length` | Chunk size in bytes |
| `Content-Range` | `bytes {FIRST_BYTE}-{LAST_BYTE}/{TOTAL_SIZE}` |

**Chunk Size Requirements**:

| Constraint | Value |
|-----------|-------|
| Minimum chunk size | 5 MB |
| Maximum chunk size | 64 MB |
| Final chunk maximum | 128 MB |
| Maximum number of chunks | 1,000 |
| Upload URL validity | 1 hour |
| Videos under 5 MB | Must upload as single chunk |
| Videos over 64 MB | Must upload in multiple chunks |

**Formula**: `total_chunk_count = floor(video_size / chunk_size)`

**Upload Response Codes**:

| HTTP Status | Meaning |
|------------|---------|
| 201 Created | All chunks uploaded successfully |
| 206 Partial Content | Chunk processed; more uploads pending |
| 400 Bad Request | Malformed headers or size mismatch |
| 403 Forbidden | Upload URL expired |
| 416 Range Not Satisfiable | Content-Range misalignment |

### URL Pull (PULL_FROM_URL)

For `source=PULL_FROM_URL`:

| Requirement | Detail |
|------------|--------|
| Protocol | HTTPS only |
| Redirects | Not permitted |
| Domain verification | Required via Developer Portal (DNS or URL prefix) |
| URL accessibility | Must remain accessible for 1 hour after task initiation |

**Verification Methods**:
1. **Domain Verification**: Via DNS records; covers all subdomains and paths
2. **URL Prefix Verification**: Exact `https://host/path/` matching

### Cancel Upload

**POST /v2/post/publish/cancel/**

Best-effort cancellation of ongoing downloads. Tasks nearing completion or in file processing state may not be cancellable.

---

## 15. Share Kit

**Purpose**: Let users share videos and photos from your mobile app directly to TikTok without repeated authentication.

**Platforms**: iOS, Android

**SDK**: TikTok OpenSDK (separate from Login Kit for lightweight integration)

**Capabilities**:
- Share short-form videos to TikTok
- Share photos as posts (Photo Mode)
- No repeated login required after initial authorization

**GitHub**: https://github.com/tiktok/tiktok-opensdk-ios

**Note**: Share Kit is the renamed Video Kit. It now supports sharing both videos and photos.

---

## 16. Embed Videos (oEmbed)

### GET /oembed

Public endpoint for embedding TikTok videos. No authentication required.

**URL**: `https://www.tiktok.com/oembed`
**Method**: GET
**Auth**: None
**Format**: Follows the oEmbed specification (https://oembed.com/)

**Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | The TikTok video URL to embed |

**Example Request**:
```
https://www.tiktok.com/oembed?url=https://www.tiktok.com/@scout2015/video/6718335390845095173
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | oEmbed version (`"1.0"`) |
| `type` | string | Content type (`"video"`) |
| `title` | string | Video title |
| `author_name` | string | Creator username |
| `author_url` | string | Creator profile URL |
| `width` | string | Embed width (`"100%"`) |
| `height` | string | Embed height (`"100%"`) |
| `html` | string | Complete embed HTML code |
| `thumbnail_url` | string | Video thumbnail image URL |
| `thumbnail_width` | int | Thumbnail width in pixels |
| `thumbnail_height` | int | Thumbnail height in pixels |
| `provider_name` | string | `"TikTok"` |
| `provider_url` | string | `"https://www.tiktok.com"` |

**Creator Profile Embeds**: TikTok also supports embedding creator profiles. See: https://developers.tiktok.com/doc/embed-creator-profiles

---

## 17. Webhooks

**Purpose**: Real-time event notifications via HTTPS POST callbacks, eliminating the need for API polling.

**Configuration**: Register callback URL in the TikTok Developer Portal.

### Requirements

| Requirement | Detail |
|------------|--------|
| Protocol | HTTPS only |
| Response | Must return HTTP 200 immediately |
| Delivery model | At-least-once (may receive duplicates) |
| Retry policy | Automatic retries for 72 hours with exponential backoff |
| Discard after | 72 hours if delivery remains unsuccessful |

**IMPORTANT**: Implement **idempotent event processing** to handle duplicate deliveries.

### Supported Webhook Events

| Event | Trigger | Payload Key Fields |
|-------|---------|-------------------|
| `authorization.removed` | User deauthorizes your app | `user_openid`, `content.reason` |
| `video.upload.failed` | Video Kit upload fails | `content.share_id` |
| `video.publish.completed` | Video Kit video is published | `content.share_id` |
| `portability.download.ready` | Data Portability data is ready | `content.request_id` |
| `post.publish.failed` | Content Posting API post fails | `publish_id` |
| `post.publish.complete` | Content Posting API post succeeds | `publish_id` |
| `post.publish.inbox_delivered` | Draft delivered to inbox | `publish_id` |
| `post.publish.publicly_available` | Post becomes publicly visible | `publish_id` |
| `post.publish.no_longer_publicaly_available` | Post removed from public | `publish_id` |

### Authorization Removed -- Reason Codes

| Code | Reason |
|------|--------|
| 0 | Unknown |
| 1 | User disconnects from TikTok app |
| 2 | User's account deleted |
| 3 | User's age changed |
| 4 | User's account banned |
| 5 | Developer revoke authorization |

### Example Webhook Payload

```json
{
  "client_key": "bwo2m45353a6k85",
  "event": "authorization.removed",
  "create_time": 1615338610,
  "user_openid": "act.example12345Example12345Example",
  "content": "{\"reason\": 1}"
}
```

---

## 18. Research API -- Overview

**Purpose**: Academic researchers from non-profit universities in the U.S. and Europe can study public TikTok data.

**Auth**: Client Access Token (client credentials flow)
**Required Scope**: `research.data.basic`
**Base URL**: `https://open.tiktokapis.com`

### Available Research API Endpoints

| Endpoint | URL | Description |
|----------|-----|-------------|
| Query Videos | `/v2/research/video/query/` | Search videos by conditions |
| Query User Info | `/v2/research/user/info/` | Get public user profile data |
| Query Video Comments | `/v2/research/video/comment/list/` | Get video comments |
| User Followers | `/v2/research/user/followers/` | List user's followers |
| User Following | `/v2/research/user/following/` | List user's following |
| User Liked Videos | `/v2/research/user/liked_videos/` | List user's liked videos |
| User Pinned Videos | `/v2/research/user/pinned_videos/` | List user's pinned videos |
| User Reposted Videos | `/v2/research/user/reposted_videos/` | List user's reposted videos |
| Query Playlist Info | `/v2/research/playlist/info/` | Get playlist details |

### Quotas

| Quota | Limit |
|-------|-------|
| Daily requests | 1,000 requests/day |
| Records per day | Up to 100,000 records/day |
| Records per request | Up to 100 per request |

### Eligibility

- Academic researchers at non-profit universities
- Available in the U.S. and Europe
- Application review process (typically 4 weeks)
- Apply at: https://developers.tiktok.com/products/research-api/

---

## 19. Research API -- Query Videos

### POST /v2/research/video/query/

Search for public TikTok videos using complex query filters.

**URL**: `https://open.tiktokapis.com/v2/research/video/query/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated video fields to return |

**Available Video Fields**: `id`, `video_description`, `create_time`, `region_code`, `share_count`, `view_count`, `like_count`, `comment_count`, `music_id`, `hashtag_names`, `username`, `effect_ids`, `playlist_id`, `voice_to_text`, `is_stem_verified`, `favorites_count`, `video_duration`, `hashtag_info_list`, `sticker_info_list`, `effect_info_list`, `video_mention_list`, `video_label`, `video_tag`

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | object | Yes | Contains `and`, `or`, `not` condition arrays |
| `start_date` | string | Yes | Format: `YYYYMMDD` (UTC) |
| `end_date` | string | Yes | Max 30 days after start_date |
| `max_count` | int64 | No | Default: 20, Max: 100 |
| `cursor` | int64 | No | Starting index for pagination |
| `search_id` | string | No | Resume previous search results |
| `is_random` | boolean | No | Random result ordering if true |

**Query Condition Structure**:
```json
{
  "query": {
    "and": [
      {"operation": "EQ", "field_name": "region_code", "field_values": ["US"]},
      {"operation": "IN", "field_name": "hashtag_name", "field_values": ["trending", "viral"]}
    ],
    "not": [
      {"operation": "EQ", "field_name": "username", "field_values": ["blocked_user"]}
    ]
  },
  "start_date": "20250101",
  "end_date": "20250131",
  "max_count": 50
}
```

**Query Operations**: `EQ`, `IN`, `GT`, `GTE`, `LT`, `LTE`

**Filterable Fields**:

| Field | Type | Operations | Description |
|-------|------|-----------|-------------|
| `create_date` | string | EQ, GT, GTE, LT, LTE | Format YYYYMMDD |
| `username` | string | EQ, IN | TikTok username |
| `region_code` | string | EQ, IN | Two-letter country code |
| `video_id` | int64 | EQ, IN | Video ID |
| `hashtag_name` | string | EQ, IN | Hashtag (without #) |
| `keyword` | string | EQ, IN | Keyword search in description |
| `music_id` | int64 | EQ, IN | Music/sound ID |
| `effect_id` | int64 | EQ, IN | Effect ID |
| `video_length` | string | EQ, IN | `SHORT`, `MID`, `LONG`, `EXTRA_LONG` |
| `view_count` | int64 | GT, GTE, LT, LTE | View count filter |
| `comment_count` | int64 | GT, GTE, LT, LTE | Comment count filter |

**Response**:
```json
{
  "data": {
    "videos": [...],
    "cursor": 50,
    "has_more": true,
    "search_id": "abc123..."
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

---

## 20. Research API -- Query User Info

### POST /v2/research/user/info/

Fetch public account information by TikTok username.

**URL**: `https://open.tiktokapis.com/v2/research/user/info/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated user fields |

**Request Body**:
```json
{
  "username": "joe123456"
}
```

**Available User Fields**: `display_name`, `bio_description`, `avatar_url`, `is_verified`, `follower_count`, `following_count`, `likes_count`, `video_count`, `bio_url`

**Example Request**:
```bash
curl -L 'https://open.tiktokapis.com/v2/research/user/info/?fields=display_name,bio_description,avatar_url,is_verified,follower_count,following_count,likes_count,video_count' \
  -H 'Authorization: Bearer {CLIENT_ACCESS_TOKEN}' \
  -H 'Content-Type: application/json' \
  -d '{"username": "joe123456"}'
```

**Response**:
```json
{
  "data": {
    "display_name": "Joe Smith",
    "bio_description": "Creator bio",
    "avatar_url": "https://...",
    "is_verified": false,
    "follower_count": 5000,
    "following_count": 200,
    "likes_count": 150000,
    "video_count": 45
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

---

## 21. Research API -- Query Video Comments

### POST /v2/research/video/comment/list/

Retrieve comments on a specific video. Personal information (phone numbers, emails, credit card data) is automatically redacted from comment text.

**URL**: `https://open.tiktokapis.com/v2/research/video/comment/list/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | string | Yes | Comma-separated comment fields |

**Available Comment Fields**: `id`, `video_id`, `text`, `like_count`, `reply_count`, `parent_comment_id`, `create_time`

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `video_id` | int64 | Yes | Video ID to fetch comments for |
| `max_count` | int64 | No | Default: 10, Max: 100 |
| `cursor` | int64 | No | Starting index for pagination |

**Response**:
```json
{
  "data": {
    "comments": [
      {
        "id": 123456,
        "video_id": 7123456789012345678,
        "text": "Great video!",
        "like_count": 15,
        "reply_count": 3,
        "parent_comment_id": 0,
        "create_time": 1672531200
      }
    ],
    "cursor": 10,
    "has_more": true
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": ""
  }
}
```

---

## 22. Research API -- User Followers

### POST /v2/research/user/followers/

List a user's followers.

**URL**: `https://open.tiktokapis.com/v2/research/user/followers/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Target user's username |
| `max_count` | int64 | No | Default: 20, Max: 100 |
| `cursor` | int64 | No | Unix timestamp (UTC seconds) for pagination |

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `data.user_followers` | array | List of UserInfo objects |
| `data.cursor` | int64 | Unix timestamp for next page |
| `data.has_more` | boolean | Additional followers exist |

**UserInfo Object**: `display_name` (string), `username` (string)

---

## 23. Research API -- User Following

### POST /v2/research/user/following/

List accounts a user follows.

**URL**: `https://open.tiktokapis.com/v2/research/user/following/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Target user's username |
| `max_count` | int64 | No | Default: 20, Max: 100 |
| `cursor` | int64 | No | Unix timestamp (UTC seconds) for pagination |

**Response**: Same structure as User Followers, with `data.user_following` array.

---

## 24. Research API -- User Liked Videos

### POST /v2/research/user/liked_videos/

List videos a user has liked.

**URL**: `https://open.tiktokapis.com/v2/research/user/liked_videos/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Target user's username |
| `max_count` | int64 | No | Default: 20, Max: 100 |
| `cursor` | int64 | No | Unix timestamp (UTC seconds) for pagination |

**Available Video Fields** (via `fields` query param): `id`, `create_time`, `username`, `region_code`, `video_description`, `music_id`, `like_count`, `comment_count`, `share_count`, `view_count`, `video_duration`, `hashtag_names`, `hashtag_info_list`, `sticker_info_list`, `effect_info_list`, `video_mention_list`, `video_label`, `is_stem_verified`, `favorites_count`, `video_tag`

**Response**:
```json
{
  "data": {
    "user_liked_videos": [...],
    "cursor": 1672531200,
    "has_more": true
  },
  "error": {...}
}
```

---

## 25. Research API -- User Pinned Videos

### POST /v2/research/user/pinned_videos/

List a user's pinned videos.

**URL**: `https://open.tiktokapis.com/v2/research/user/pinned_videos/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Request Body**:
```json
{
  "username": "test_username"
}
```

**Available Fields** (via `fields` query param): `id`, `like_count`, `share_count`, `view_count`, `comment_count`

**Response**:
```json
{
  "data": {
    "pinned_videos_list": [
      {
        "id": 7123456789012345678,
        "like_count": 5000,
        "share_count": 200,
        "view_count": 100000,
        "comment_count": 150
      }
    ]
  },
  "error": {...}
}
```

---

## 26. Research API -- User Reposted Videos

### POST /v2/research/user/reposted_videos/

List a user's reposted videos.

**URL**: `https://open.tiktokapis.com/v2/research/user/reposted_videos/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Request Body**:
```json
{
  "username": "test_username"
}
```

**Response**: Returns array of reposted video objects with standard video fields.

---

## 27. Research API -- Query Playlist Info

### POST /v2/research/playlist/info/

Get details about a TikTok playlist.

**URL**: `https://open.tiktokapis.com/v2/research/playlist/info/`
**Method**: POST
**Auth**: Client Access Token (Bearer)
**Required Scope**: `research.data.basic`

**Request Body**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `playlist_id` | int64 | Yes | Playlist identifier |
| `max_count` | int64 | No | Max video IDs per response |
| `cursor` | int64 | No | Pagination cursor |

**Response Fields**: `playlist_id`, `playlist_name`, `playlist_item_total`, `playlist_last_updated`, `playlist_video_ids`, `cursor`, `has_more`

---

## 28. Commercial Content API

**Purpose**: Query ads and branded commercial content data for research and transparency.

**Auth**: Client Access Token (client credentials flow)
**Required Scope**: `research.adlib.basic`
**Base URL**: `https://open.tiktokapis.com`

### Endpoints

| Endpoint | URL | Description |
|----------|-----|-------------|
| Query Ads | `POST /v2/research/adlib/ad/query/` | Search ads by keyword, advertiser, date |
| Ad Details | `POST /v2/research/adlib/ad/detail/` | Get detailed ad information |
| Ad Report | `POST /v2/research/adlib/ad/report/` | Get ad publishing report |
| Query Advertisers | `POST /v2/research/adlib/advertiser/query/` | Search advertisers |
| Commercial Content Report | `POST /v2/research/adlib/commercial_content/report/` | Branded content data |

### Query Ads Example

```bash
curl -X POST 'https://open.tiktokapis.com/v2/research/adlib/ad/query/?fields=ad,ad_group' \
  -H 'Authorization: Bearer {CLIENT_ACCESS_TOKEN}' \
  -H 'Content-Type: application/json' \
  -d '{
    "filters": {
      "ad_published_date_range": {
        "min": "20250101",
        "max": "20250131"
      },
      "country": "US"
    },
    "search_term": "example brand",
    "max_count": 50,
    "search_id": ""
  }'
```

**Response**:
```json
{
  "data": {
    "ads": [...],
    "has_more": true,
    "search_id": "abc123..."
  },
  "error": {...}
}
```

---

## 29. Data Portability API

**Purpose**: Allow TikTok users in the EEA and UK to transfer their data to your application (GDPR compliance).

**Auth**: User Access Token
**Availability**: EEA and UK users only

### Endpoints

| Endpoint | URL | Method | Description |
|----------|-----|--------|-------------|
| Add Data Request | `/v2/user/data/add/` | POST | Create a data download request |
| Download Data | `/v2/user/data/download/` | POST | Download the prepared data (ZIP) |
| Cancel Request | `/v2/user/data/cancel/` | POST | Cancel a pending request |

### Data Categories

| Scope | Data Type |
|-------|-----------|
| `portability.all.*` | Complete data archive |
| `portability.activity.*` | User activity data |
| `portability.directmessages.*` | Direct message data |
| `portability.postsandprofile.*` | Posts and profile data |

Each category has `.single` (one-time) and `.ongoing` (recurring) variants.

### Data Download Timeline

- Data typically available within seconds to hours depending on volume
- Download link valid for **4 days** after preparation
- Posts provided as `.mp4` (videos) or `.jpg` (photos) via download URLs

### Webhook Integration

Use `portability.download.ready` webhook event for real-time notification when data is ready.

---

## 30. TikTok for Business (Marketing API)

**Purpose**: Programmatic management of TikTok advertising campaigns.

**Portal**: https://business-api.tiktok.com/portal/docs
**Base URL**: `https://business-api.tiktok.com/open_api/v1.2/`

### Campaign Hierarchy

```
Advertiser Account
  +-- Campaign (sets objective)
       +-- Ad Group (targeting, placement, budget)
            +-- Ad (creative, text, CTA)
```

### Key Endpoint Categories

| Category | Example Endpoints |
|----------|------------------|
| Campaign Management | `/campaign/get/`, `/campaign/create/`, `/campaign/update/` |
| Ad Group Management | `/adgroup/get/`, `/adgroup/create/`, `/adgroup/update/` |
| Ad Management | `/ad/get/`, `/ad/create/`, `/ad/update/` |
| Reporting | `/reports/integrated/get/` |
| Creative Management | Upload and manage creative materials |
| Audience Management | Custom and lookalike audiences |

### Authentication

Business API uses its own authentication system with advertiser access tokens. See: https://business-api.tiktok.com/portal/docs

**NOTE**: The Business/Marketing API is a separate API ecosystem from the TikTok for Developers platform. It has its own documentation portal, authentication system, and endpoint structure.

---

## 31. Data Dictionary

### 31.1 User Object (Display API)

| Field | Type | Scope Required | Description |
|-------|------|---------------|-------------|
| `open_id` | string | `user.info.basic` | Unique user ID for your app |
| `union_id` | string | `user.info.basic` | Cross-app user ID |
| `avatar_url` | string | `user.info.basic` | Profile picture URL |
| `avatar_url_100` | string | `user.info.basic` | 100px avatar URL |
| `avatar_large_url` | string | `user.info.basic` | Large avatar URL |
| `display_name` | string | `user.info.basic` | User's display name |
| `bio_description` | string | `user.info.profile` | Profile bio text |
| `profile_deep_link` | string | `user.info.profile` | Deep link to TikTok profile |
| `is_verified` | boolean | `user.info.profile` | Verification badge status |
| `username` | string | `user.info.profile` | Unique username |
| `follower_count` | int64 | `user.info.stats` | Number of followers |
| `following_count` | int64 | `user.info.stats` | Number of accounts followed |
| `likes_count` | int64 | `user.info.stats` | Total likes received |
| `video_count` | int64 | `user.info.stats` | Number of public videos |

### 31.2 Video Object (Display API)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique video identifier |
| `create_time` | int64 | Unix timestamp of creation |
| `cover_image_url` | string | Video cover image URL (has TTL) |
| `share_url` | string | Shareable video URL |
| `video_description` | string | Video caption/description |
| `duration` | int32 | Video length in seconds |
| `height` | int32 | Video height in pixels |
| `width` | int32 | Video width in pixels |
| `title` | string | Video title |
| `embed_html` | string | HTML embed code |
| `embed_link` | string | Embed URL |
| `like_count` | int64 | Number of likes |
| `comment_count` | int64 | Number of comments |
| `share_count` | int64 | Number of shares |
| `view_count` | int64 | Number of views |

### 31.3 Video Object (Research API)

Includes all Display API fields plus:

| Field | Type | Description |
|-------|------|-------------|
| `region_code` | string | Two-letter country code |
| `music_id` | int64 | ID of the sound used |
| `hashtag_names` | string[] | Array of hashtag names |
| `username` | string | Creator's username |
| `effect_ids` | string[] | Array of effect IDs used |
| `playlist_id` | int64 | Playlist ID if part of a playlist |
| `voice_to_text` | string | Voice-to-text transcription |
| `is_stem_verified` | boolean | STEM content verification |
| `favorites_count` | int64 | Number of favorites/bookmarks |
| `video_duration` | int32 | Video length in seconds |
| `hashtag_info_list` | object[] | Detailed hashtag information |
| `sticker_info_list` | object[] | Sticker details |
| `effect_info_list` | object[] | Effect details |
| `video_mention_list` | object[] | Mentioned users |
| `video_label` | object | Content label information |
| `video_tag` | object | Video tag metadata |

### 31.4 Comment Object (Research API)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int64 | Unique comment identifier |
| `video_id` | int64 | Parent video ID |
| `text` | string | Comment text (PII redacted) |
| `like_count` | int64 | Number of likes |
| `reply_count` | int64 | Number of replies |
| `parent_comment_id` | int64 | Parent comment ID (0 if top-level) |
| `create_time` | int64 | Unix timestamp of creation |

### 31.5 Creator Info Object (Content Posting API)

| Field | Type | Description |
|-------|------|-------------|
| `creator_avatar_url` | string | Profile image URL (2-hour TTL) |
| `creator_username` | string | Unique creator identifier |
| `creator_nickname` | string | Display name |
| `privacy_level_options` | string[] | Available privacy settings |
| `comment_disabled` | boolean | Comments disabled status |
| `duet_disabled` | boolean | Duets disabled status |
| `stitch_disabled` | boolean | Stitches disabled status |
| `max_video_post_duration_sec` | int32 | Maximum video length allowed |

### 31.6 Error Object

All API responses include an error object:

```json
{
  "error": {
    "code": "ok",
    "message": "",
    "log_id": "20230101123456ABCDEF"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Error code string (e.g., `ok`, `access_token_invalid`) |
| `message` | string | Human-readable error description |
| `log_id` | string | Unique request ID for debugging/support |

---

## 32. Rate Limits

Rate limits are calculated on a **one-minute sliding window** unless otherwise specified.

### Display API Rate Limits

| Endpoint | Rate Limit | Window |
|----------|-----------|--------|
| `GET /v2/user/info/` | 600 requests | 1 minute |
| `POST /v2/video/list/` | 600 requests | 1 minute |
| `POST /v2/video/query/` | 600 requests | 1 minute |

### Content Posting API Rate Limits

| Endpoint | Rate Limit | Window |
|----------|-----------|--------|
| `POST /v2/post/publish/creator_info/query/` | 20 requests | 1 minute (per user token) |
| `POST /v2/post/publish/video/init/` | 6 requests | 1 minute (per user token) |
| `POST /v2/post/publish/inbox/video/init/` | 6 requests | 1 minute (per user token) |
| `POST /v2/post/publish/content/init/` | 6 requests | 1 minute (per user token) |
| `POST /v2/post/publish/status/fetch/` | 30 requests | 1 minute (per user token) |

### Content Posting -- Publishing Limits

| Limit | Value |
|-------|-------|
| Videos per minute | 2 |
| Video posts per day | 20 |
| Pending shares per 24 hours | 5 |

### Research API Rate Limits

| Quota | Limit |
|-------|-------|
| Daily requests | 1,000 requests/day |
| Records per day | 100,000 records/day |
| Max records per request | 100 |

### Rate Limit Response

When exceeded, the API returns:
- **HTTP Status**: `429`
- **Error Code**: `rate_limit_exceeded`
- **Message**: `"The API rate limit was exceeded. Please try again later."`

**Higher Limits**: Contact TikTok via their Support Page to request increased limits.

---

## 33. Error Codes and Handling

### 33.1 Standard Error Response Format

```json
{
  "error": {
    "code": "error_code_string",
    "message": "Human-readable error description",
    "log_id": "unique_request_identifier"
  }
}
```

### 33.2 Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 200 | `ok` | Request succeeded |
| 400 | `invalid_params` | One or more request fields are invalid |
| 400 | `invalid_file_upload` | Uploaded file fails to meet specifications |
| 400 | `invalid_publish_id` | Non-existent publish ID |
| 401 | `access_token_invalid` | Access token is invalid or expired |
| 401 | `scope_not_authorized` | User hasn't authorized required scopes |
| 400 | `scope_permission_missed` | Access token missing required scope fields |
| 429 | `rate_limit_exceeded` | API rate limit exceeded |
| 500 | `internal_error` | TikTok internal server error |

### 33.3 Content Posting Error Codes

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 200 | `spam_risk_too_many_posts` | Daily API post limit reached |
| 200 | `spam_risk_user_banned_from_posting` | Account posting suspended |
| 200 | `reached_active_user_cap` | Client daily user quota exhausted |
| 400 | `invalid_param` | Parameter validation failed |
| 400 | `token_not_authorized_for_specified_publish_id` | Token/publish_id mismatch |
| 403 | `unaudited_client_can_only_post_to_private_accounts` | Audit required for public posts |
| 403 | `privacy_level_option_mismatch` | Privacy setting not in creator's options |
| 403 | `spam_risk_user_banned_from_posting` | User posting restriction active |
| 403 | `spam_risk_too_many_pending_share` | Max 5 pending shares in 24 hours |
| 403 | `url_ownership_unverified` | Domain not verified for PULL_FROM_URL |

### 33.4 Login Kit / OAuth Error Codes

Errors during OAuth flow are returned as query parameters on the redirect URI:

| Error | Description |
|-------|-------------|
| `access_denied` | User denied authorization |
| `server_error` | TikTok server error |
| `temporarily_unavailable` | Service temporarily unavailable |

### 33.5 Media Upload Error Codes

| HTTP Status | Meaning |
|------------|---------|
| 201 | All chunks uploaded successfully |
| 206 | Chunk processed; more pending |
| 400 | Malformed headers or size mismatch |
| 403 | Upload URL expired |
| 416 | Content-Range misalignment |

### 33.6 Error Handling Best Practices

1. **Always check the `error.code`** field in every response
2. **Save the `log_id`** for support requests to TikTok
3. **Implement exponential backoff** for rate limit errors (429)
4. **Refresh tokens proactively** before the 24-hour expiry
5. **Handle scope errors** by re-initiating the authorization flow with required scopes

---

## 34. Content Specifications

### 34.1 Video Specifications

| Spec | Requirement |
|------|------------|
| **Recommended resolution** | 1080 x 1920 px (9:16 portrait) |
| **Primary aspect ratio** | 9:16 (vertical) |
| **Other supported ratios** | 1:1, 4:5, 16:9 |
| **Recommended format** | MP4 |
| **Supported formats** | MP4, MOV, MPEG, 3GP, AVI, WebM |
| **Recommended codec** | H.264 video, AAC audio |
| **Duration (recorded in TikTok)** | 1 second to 10 minutes |
| **Duration (uploaded)** | 1 second to 60 minutes |
| **Max file size (API)** | Determined by chunk upload limits (1000 chunks x 64MB = ~64GB theoretical max) |
| **Max file size (Android direct)** | 72 MB |
| **Max file size (iOS direct)** | 287.6 MB |
| **Max file size (ads)** | 500 MB |

### 34.2 Photo Specifications

| Spec | Requirement |
|------|------------|
| **Images per carousel** | 4 to 35 |
| **Supported formats** | JPEG (JPG), PNG |
| **Max file size per image** | 20 MB |
| **Total carousel size** | 500 MB |
| **Recommended resolution** | 1080 x 1920 px (9:16) |
| **Supported aspect ratios** | 9:16, 1:1, 4:5 |
| **Optimal count for engagement** | 5-10 slides |

### 34.3 Text Limits

| Field | Limit |
|-------|-------|
| Video title/caption (Direct Post) | 2,200 UTF-16 runes |
| Photo title | 90 UTF-16 runes |
| Photo description | 4,000 UTF-16 runes |

### 34.4 Upload Chunk Sizes

| Constraint | Value |
|-----------|-------|
| Minimum chunk | 5 MB |
| Maximum chunk | 64 MB |
| Final chunk maximum | 128 MB |
| Maximum chunks | 1,000 |
| Upload URL validity | 1 hour |

---

## 35. Sandbox and Testing

### Overview

Sandbox mode provides a restricted environment for testing integrations without submitting your app for review.

### Capabilities

| Feature | Sandbox Support |
|---------|----------------|
| Login Kit | Yes |
| Display API | Yes |
| Share Kit | Yes |
| Content Posting API (public) | **No** |
| Data Portability API | **No** |
| Webhooks | Limited |

### Limits

| Limit | Value |
|-------|-------|
| Sandboxes per app | Up to 5 |
| Test accounts per sandbox | Up to 10 |

### Creating a Sandbox

1. Log in to the TikTok Developer Portal
2. Navigate to your app settings
3. Create a new sandbox configuration
4. Add target user accounts for testing
5. Test integrations with sandbox credentials

### Key Restrictions

- Sandbox does **not** support Content Posting API for public video posting
- Sandbox does **not** support Data Portability API
- Content posted through sandbox is always private
- Sandbox credentials are separate from production credentials

---

## 36. App Review and Audit Process

### App Review

All applications must be reviewed before going live.

**App Statuses**:

| Status | Description |
|--------|-------------|
| `Draft` | App not yet submitted for review |
| `In review` | Submitted, awaiting approval |
| `Live` | Approved, integrations are active |
| `Not approved` | Rejected; feedback provided |

**Timeline**: Review takes several days to two weeks after submission.

### Requirements for Review

1. Complete developer profile
2. App description and use case
3. Privacy policy URL
4. Terms of service URL
5. UX mockups or screenshots (for new apps)
6. Redirect URI configuration

### Audit Process (Content Posting API)

**CRITICAL**: Apps using the Content Posting API must undergo a separate audit to enable public posting.

**Before Audit**:
- All posted content is restricted to `SELF_ONLY` privacy
- Users cannot see content posted by your app publicly

**Audit Requirements**:
- Demonstrate compliance with TikTok Terms of Service
- Provide reasoning for API access
- Show UX mockups of the integration
- Successfully test integration in private mode

**After Audit**:
- Content can be posted with any privacy level the creator allows
- Public posting enabled (`PUBLIC_TO_EVERYONE`)

---

## 37. API Versioning and Migration

### Current Version

TikTok API v2 is the current version, hosted at `open.tiktokapis.com`.

### v1 to v2 Migration

TikTok has migrated from API v1 to v2 with significant changes:

| Aspect | v1 | v2 |
|--------|----|----|
| Base URL | Various | `open.tiktokapis.com` |
| Auth | Custom OAuth | Industry-standard OAuth 2.0 |
| Error format | Numeric codes | Readable string codes |
| HTTP status | Mostly 200 | Proper 4xx/5xx codes |
| Scopes | Basic | Granular per-field scopes |
| Video Kit | Legacy name | Renamed to Share Kit |

### Key Migration Notes

- API v2 follows industry standards including OAuth 2.0
- Error codes are now readable strings (e.g., `access_token_invalid` instead of numeric codes)
- HTTP status codes now properly reflect error types (4xx for client errors, 5xx for server errors)
- Scopes are more granular -- `user.info.basic` alone no longer provides all user fields
- The `user.info.profile` and `user.info.stats` scopes are required for extended user data

### API Stability

- TikTok may update or deprecate endpoints
- Monitor the TikTok Developer Blog for announcements: https://developers.tiktok.com/blog
- Subscribe to developer newsletters for migration notices

---

## Quick Reference: All Endpoints

### OAuth / Token Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v2/oauth/token/` | Exchange code / refresh / client credentials |
| POST | `/v2/oauth/revoke/` | Revoke access token |

### Display API

| Method | Endpoint | Scope | Rate Limit |
|--------|----------|-------|-----------|
| GET | `/v2/user/info/` | `user.info.basic` | 600/min |
| POST | `/v2/video/list/` | `video.list` | 600/min |
| POST | `/v2/video/query/` | `video.list` | 600/min |

### Content Posting API

| Method | Endpoint | Scope | Rate Limit |
|--------|----------|-------|-----------|
| POST | `/v2/post/publish/creator_info/query/` | `video.publish` | 20/min |
| POST | `/v2/post/publish/video/init/` | `video.publish` | 6/min |
| POST | `/v2/post/publish/inbox/video/init/` | `video.upload` | 6/min |
| POST | `/v2/post/publish/content/init/` | `video.publish` / `video.upload` | 6/min |
| POST | `/v2/post/publish/status/fetch/` | `video.upload` / `video.publish` | 30/min |
| POST | `/v2/post/publish/cancel/` | `video.publish` | -- |

### Research API

| Method | Endpoint | Scope |
|--------|----------|-------|
| POST | `/v2/research/video/query/` | `research.data.basic` |
| POST | `/v2/research/user/info/` | `research.data.basic` |
| POST | `/v2/research/video/comment/list/` | `research.data.basic` |
| POST | `/v2/research/user/followers/` | `research.data.basic` |
| POST | `/v2/research/user/following/` | `research.data.basic` |
| POST | `/v2/research/user/liked_videos/` | `research.data.basic` |
| POST | `/v2/research/user/pinned_videos/` | `research.data.basic` |
| POST | `/v2/research/user/reposted_videos/` | `research.data.basic` |
| POST | `/v2/research/playlist/info/` | `research.data.basic` |

### Commercial Content API

| Method | Endpoint | Scope |
|--------|----------|-------|
| POST | `/v2/research/adlib/ad/query/` | `research.adlib.basic` |
| POST | `/v2/research/adlib/ad/detail/` | `research.adlib.basic` |
| POST | `/v2/research/adlib/ad/report/` | `research.adlib.basic` |
| POST | `/v2/research/adlib/advertiser/query/` | `research.adlib.basic` |
| POST | `/v2/research/adlib/commercial_content/report/` | `research.adlib.basic` |

### Data Portability API

| Method | Endpoint | Scope |
|--------|----------|-------|
| POST | `/v2/user/data/add/` | `portability.*` |
| POST | `/v2/user/data/download/` | `portability.*` |
| POST | `/v2/user/data/cancel/` | `portability.*` |

### Embed (Public)

| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `https://www.tiktok.com/oembed` | None |

---

## Appendix: Differences from X (Twitter) API

| Feature | TikTok API | X (Twitter) API |
|---------|-----------|----------------|
| Base URL | `open.tiktokapis.com` | `api.x.com` |
| Primary content type | Short-form video + photos | Text tweets + media |
| Auth model | OAuth 2.0 (user + client) | OAuth 2.0 + OAuth 1.0a |
| User access token lifetime | 24 hours | 2 hours |
| Refresh token lifetime | 365 days | -- (reauthorize) |
| Posting API | Content Posting API (audit required) | POST /2/tweets (scope-based) |
| Direct Messages API | **Not available** | Full DM API |
| Comments API | Read-only (Research API) | Full read/write |
| Streaming API | Not available | Filtered Stream |
| Rate limit window | 1 minute sliding | 15 minute fixed |
| Webhook events | 9 events | Extensive event types |
| Sandbox | Yes (5 sandboxes, 10 users) | No dedicated sandbox |
| Research access | Application-based (academic) | Academic Research product |

---

*Document compiled from official TikTok for Developers documentation at https://developers.tiktok.com/ and https://business-api.tiktok.com/portal/docs. For the most current information, always refer to the official documentation.*
