# Compliance

Compliance endpoints provide streams of events about deleted/withheld content. Primarily for Enterprise users who need to keep local data stores in sync.

---

## Batch Compliance

### POST /2/compliance/jobs — Create Compliance Job

**URL**: `https://api.x.com/2/compliance/jobs`

**Auth**: Bearer Token

**Access**: Enterprise

```json
{
  "type": "tweets",
  "name": "my-compliance-job"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `tweets` or `users` |
| `name` | string | Optional job name |
| `resumable` | boolean | Allow resume on failure |

### GET /2/compliance/jobs — List Compliance Jobs

**URL**: `https://api.x.com/2/compliance/jobs`

| Param | Type | Description |
|-------|------|-------------|
| `type` | string | Filter by `tweets` or `users` |
| `status` | string | Filter by `created`, `in_progress`, `complete`, `expired`, `failed` |

### GET /2/compliance/jobs/:id — Get Job Status

**URL**: `https://api.x.com/2/compliance/jobs/:id`

---

## Compliance Streams (Enterprise)

Real-time streams of compliance events.

### GET /2/tweets/compliance/stream — Tweet Compliance Stream

**URL**: `https://api.x.com/2/tweets/compliance/stream`

**Auth**: Bearer Token

**Access**: Enterprise only

Streams events for: tweet deletes, tweet withholds, tweet edits, user protects, user suspends, user deletes, user scrub_geo.

### GET /2/users/compliance/stream — User Compliance Stream

**URL**: `https://api.x.com/2/users/compliance/stream`

**Auth**: Bearer Token

**Access**: Enterprise only

### Likes Compliance Stream

**URL**: `https://api.x.com/2/likes/compliance/stream`

**Auth**: Bearer Token

**Access**: Enterprise only

Streams like/unlike events for compliance purposes.

---

## Event Types

| Event | Description |
|-------|-------------|
| `tweet_delete` | Tweet was deleted by author |
| `tweet_withheld` | Tweet withheld in specific countries |
| `tweet_edit` | Tweet was edited |
| `user_delete` | User account deleted |
| `user_suspend` | User account suspended |
| `user_protect` | User switched to protected |
| `user_unprotect` | User switched to public |
| `user_withheld` | User withheld in specific countries |
| `scrub_geo` | User removed geo data |
| `like_delete` | Like was removed |
