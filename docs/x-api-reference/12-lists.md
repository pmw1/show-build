# Lists

## List Management

### POST /2/lists — Create List

**URL**: `https://api.x.com/2/lists`

**Auth**: OAuth 2.0 User Token (scopes: `list.read`, `list.write`, `tweet.read`, `users.read`)

```json
{
  "name": "Tech News",
  "description": "Top tech accounts",
  "private": false
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | 1-25 characters |
| `description` | string | No | 0-100 characters |
| `private` | boolean | No | Default: `false` |

**Response:**
```json
{
  "data": {
    "id": "1441162269824405510",
    "name": "Tech News"
  }
}
```

### PUT /2/lists/:id — Update List

**URL**: `https://api.x.com/2/lists/:id`

**Auth**: OAuth 2.0 User Token

```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "private": true
}
```

**Response:** `{"data": {"updated": true}}`

### DELETE /2/lists/:id — Delete List

**URL**: `https://api.x.com/2/lists/:id`

**Auth**: OAuth 2.0 User Token

**Response:** `{"data": {"deleted": true}}`

---

## List Lookup

### GET /2/lists/:id — Get List by ID

**URL**: `https://api.x.com/2/lists/:id`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Description |
|-------|------|-------------|
| `list.fields` | string | `created_at`, `description`, `follower_count`, `member_count`, `owner_id`, `private` |
| `expansions` | string | `owner_id` |
| `user.fields` | string | Standard user fields |

### GET /2/users/:id/owned_lists — User's Lists

**URL**: `https://api.x.com/2/users/:id/owned_lists`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Range |
|-------|------|-------|
| `max_results` | integer | 1-100 |
| `pagination_token` | string | — |

---

## List Members

### GET /2/lists/:id/members — Get List Members

**URL**: `https://api.x.com/2/lists/:id/members`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Range |
|-------|------|-------|
| `max_results` | integer | 1-100 |
| `pagination_token` | string | — |
| `user.fields` | string | Standard user fields |
| `expansions` | string | `pinned_tweet_id` |

### POST /2/lists/:id/members — Add Member

**URL**: `https://api.x.com/2/lists/:id/members`

**Auth**: OAuth 2.0 User Token

```json
{"user_id": "2244994945"}
```

**Response:** `{"data": {"is_member": true}}`

### DELETE /2/lists/:id/members/:user_id — Remove Member

**URL**: `https://api.x.com/2/lists/:id/members/:user_id`

**Auth**: OAuth 2.0 User Token

**Response:** `{"data": {"is_member": false}}`

---

## List Followers

### GET /2/lists/:id/followers — Get List Followers

**URL**: `https://api.x.com/2/lists/:id/followers`

**Auth**: Bearer Token, OAuth 2.0 User Token

Same pagination parameters as members.

### POST /2/users/:id/followed_lists — Follow a List

**URL**: `https://api.x.com/2/users/:id/followed_lists`

**Auth**: OAuth 2.0 User Token

```json
{"list_id": "1441162269824405510"}
```

**Response:** `{"data": {"following": true}}`

### DELETE /2/users/:id/followed_lists/:list_id — Unfollow List

**URL**: `https://api.x.com/2/users/:id/followed_lists/:list_id`

**Response:** `{"data": {"following": false}}`

---

## List Tweets

### GET /2/lists/:id/tweets — Get Tweets from a List

**URL**: `https://api.x.com/2/lists/:id/tweets`

**Auth**: Bearer Token, OAuth 2.0 User Token

| Param | Type | Range | Description |
|-------|------|-------|-------------|
| `max_results` | integer | 1-100 | Results per page |
| `pagination_token` | string | — | Pagination |
| `tweet.fields` | string | — | Standard tweet fields |
| `expansions` | string | — | Standard expansions |
| `user.fields` | string | — | Standard user fields |
| `media.fields` | string | — | Standard media fields |

---

## List Memberships

### GET /2/users/:id/list_memberships — Lists User Belongs To

**URL**: `https://api.x.com/2/users/:id/list_memberships`

**Auth**: Bearer Token, OAuth 2.0 User Token

Same pagination and field parameters.

---

## List Pinning

### POST /2/users/:id/pinned_lists — Pin a List

**URL**: `https://api.x.com/2/users/:id/pinned_lists`

```json
{"list_id": "1441162269824405510"}
```

### DELETE /2/users/:id/pinned_lists/:list_id — Unpin a List

**URL**: `https://api.x.com/2/users/:id/pinned_lists/:list_id`

### GET /2/users/:id/pinned_lists — Get Pinned Lists

**URL**: `https://api.x.com/2/users/:id/pinned_lists`
