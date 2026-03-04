# Authentication

## Overview

X API v2 supports three authentication methods:

### 1. OAuth 2.0 App-Only (Bearer Token)
- For accessing **public data** only
- No user context required
- Use for: tweet lookup, user lookup, search, trends

```bash
# Get Bearer Token
curl -u "$API_KEY:$API_SECRET" \
  -d "grant_type=client_credentials" \
  "https://api.x.com/oauth2/token"

# Use Bearer Token
curl "https://api.x.com/2/tweets/123456" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### 2. OAuth 2.0 Authorization Code with PKCE (User Token)
- For actions **on behalf of a user**
- Required for: posting tweets, liking, following, DMs, bookmarks
- Uses scopes to limit access

**Required Scopes by Feature:**

| Feature | Required Scopes |
|---------|----------------|
| Read tweets | `tweet.read`, `users.read` |
| Post tweets | `tweet.read`, `tweet.write`, `users.read` |
| Like/Unlike | `like.read`, `like.write`, `tweet.read`, `users.read` |
| Follow/Unfollow | `follows.read`, `follows.write`, `tweet.read`, `users.read` |
| Bookmarks | `bookmark.read`, `bookmark.write`, `tweet.read`, `users.read` |
| DMs | `dm.read`, `dm.write`, `tweet.read`, `users.read` |
| Lists | `list.read`, `list.write`, `tweet.read`, `users.read` |
| Mute | `mute.read`, `mute.write`, `tweet.read`, `users.read` |
| Block | `block.read`, `block.write`, `tweet.read`, `users.read` |
| Spaces | `space.read`, `tweet.read`, `users.read` |
| Media upload | `media.write` |

### 3. OAuth 1.0a (Legacy User Token)
- Also provides user context
- Used for media upload endpoints and legacy compatibility

## Header Format

```
Authorization: Bearer <token>
```

## API Keys

Manage keys at: https://developer.x.com/en/portal/dashboard

- **API Key** (Consumer Key) — identifies your app
- **API Secret** (Consumer Secret) — app authentication
- **Bearer Token** — app-only access token
- **Access Token + Secret** — user-specific OAuth 1.0a credentials
