# Users

## User Lookup

### GET /2/users/:id — Single User by ID

**URL**: `https://api.x.com/2/users/:id`

**Auth**: Bearer Token, OAuth 2.0 User Token, or OAuth 1.0a

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (path) | Yes | User ID |
| `user.fields` | string | No | `id`, `name`, `username`, `created_at`, `description`, `entities`, `location`, `profile_image_url`, `profile_banner_url`, `protected`, `public_metrics`, `verified`, `verified_type`, `url`, `subscription_type`, `connection_status` |
| `expansions` | string | No | `pinned_tweet_id`, `most_recent_tweet_id`, `affiliation.user_id` |
| `tweet.fields` | string | No | Tweet fields for expanded tweets |

```bash
curl "https://api.x.com/2/users/2244994945\
?user.fields=created_at,description,public_metrics,profile_image_url,verified" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

**Response:**
```json
{
  "data": {
    "id": "2244994945",
    "name": "X Dev",
    "username": "XDevelopers",
    "created_at": "2013-12-14T04:35:55.000Z",
    "description": "The voice of the X Platform developer community",
    "public_metrics": {
      "followers_count": 571000,
      "following_count": 2048,
      "tweet_count": 14052,
      "listed_count": 1672
    },
    "profile_image_url": "https://pbs.twimg.com/profile_images/..._normal.jpg",
    "verified": true
  }
}
```

### GET /2/users — Multiple Users by IDs

**URL**: `https://api.x.com/2/users?ids=...`

| Param | Type | Description |
|-------|------|-------------|
| `ids` | string | Comma-separated user IDs (max 100) |

### GET /2/users/by/username/:username — Single User by Username

**URL**: `https://api.x.com/2/users/by/username/:username`

```bash
curl "https://api.x.com/2/users/by/username/XDevelopers\
?user.fields=profile_image_url,public_metrics,verified" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### GET /2/users/by — Multiple Users by Usernames

**URL**: `https://api.x.com/2/users/by?usernames=...`

| Param | Type | Description |
|-------|------|-------------|
| `usernames` | string | Comma-separated usernames (max 100) |

### GET /2/users/me — Authenticated User

**URL**: `https://api.x.com/2/users/me`

**Auth**: OAuth 2.0 User Token (scopes: `tweet.read`, `users.read`)

---

## Follows

### GET /2/users/:id/followers — Get Followers

**URL**: `https://api.x.com/2/users/:id/followers`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Range | Description |
|-------|------|-------|-------------|
| `max_results` | integer | 1-1,000 | Results per page |
| `pagination_token` | string | — | Base32 pagination token |
| `user.fields` | string | — | User fields |
| `expansions` | string | — | `affiliation.user_id`, `most_recent_tweet_id`, `pinned_tweet_id` |
| `tweet.fields` | string | — | Tweet fields for expansions |

### GET /2/users/:id/following — Get Following

**URL**: `https://api.x.com/2/users/:id/following`

**Auth**: Bearer Token, OAuth 2.0 User Token

Same parameters as followers.

### POST /2/users/:id/following — Follow User

**URL**: `https://api.x.com/2/users/:id/following`

**Auth**: OAuth 2.0 User Token (scopes: `follows.write`, `tweet.read`, `users.read`)

```json
{"target_user_id": "2244994945"}
```

**Response**: `{"data": {"following": true, "pending_follow": false}}`

### DELETE /2/users/:source_user_id/following/:target_user_id — Unfollow

**URL**: `https://api.x.com/2/users/:source_user_id/following/:target_user_id`

**Auth**: OAuth 2.0 User Token

**Response**: `{"data": {"following": false}}`

---

## Blocks

### GET /2/users/:id/blocking — Get Blocked Users

**URL**: `https://api.x.com/2/users/:id/blocking`

**Auth**: OAuth 2.0 User Token

**Access**: Pay-per-use and Enterprise

### POST /2/users/:id/blocking — Block User

**URL**: `https://api.x.com/2/users/:id/blocking`

**Auth**: OAuth 2.0 User Token

**Access**: Enterprise only

```json
{"target_user_id": "9876543210"}
```

**Response**: `{"data": {"blocking": true}}`

### DELETE /2/users/:source_user_id/blocking/:target_user_id — Unblock

**URL**: `https://api.x.com/2/users/:source_user_id/blocking/:target_user_id`

**Auth**: OAuth 2.0 User Token

**Access**: Enterprise only

---

## Mutes

### GET /2/users/:id/muting — Get Muted Users

**URL**: `https://api.x.com/2/users/:id/muting`

**Auth**: OAuth 2.0 User Token

| Param | Type | Description |
|-------|------|-------------|
| `max_results` | integer | 1-1,000 |
| `pagination_token` | string | Pagination |
| `user.fields` | string | User fields |

### POST /2/users/:id/muting — Mute User

**URL**: `https://api.x.com/2/users/:id/muting`

**Auth**: OAuth 2.0 User Token

```json
{"target_user_id": "9876543210"}
```

**Response**: `{"data": {"muting": true}}`

### DELETE /2/users/:source_user_id/muting/:target_user_id — Unmute

**URL**: `https://api.x.com/2/users/:source_user_id/muting/:target_user_id`

**Auth**: OAuth 2.0 User Token

**Response**: `{"data": {"muting": false}}`
