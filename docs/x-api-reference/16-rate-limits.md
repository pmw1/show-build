# Rate Limits

All rate limits are per **15-minute window** unless noted otherwise.

## Headers

Every response includes rate limit headers:

```
x-rate-limit-limit: 900
x-rate-limit-remaining: 899
x-rate-limit-reset: 1609459200
```

| Header | Description |
|--------|-------------|
| `x-rate-limit-limit` | Max requests in window |
| `x-rate-limit-remaining` | Requests remaining |
| `x-rate-limit-reset` | Unix epoch time when window resets |

## HTTP 429 — Too Many Requests

When rate limited, the API returns HTTP 429. Wait until `x-rate-limit-reset` before retrying.

---

## Tweets Endpoints

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/tweets` (lookup) | 3,500 | 5,000 |
| `GET /2/tweets/:id` | 3,500 | 5,000 |
| `POST /2/tweets` (create) | 10,000 /24hrs | 100 /15min |
| `DELETE /2/tweets/:id` | — | 50 |
| `GET /2/tweets/search/recent` | 450 | 180 |
| `GET /2/tweets/search/all` | 300 | 1 |
| `GET /2/tweets/search/stream` | 50 (connects) | — |
| `GET /2/tweets/:id/quote_tweets` | 75 | 75 |
| `GET /2/tweets/:id/retweeted_by` | 75 | 75 |
| `GET /2/tweets/:id/retweets` | 75 | 75 |
| `GET /2/tweets/:id/liking_users` | 75 | 75 |
| `PUT /2/tweets/:id/hidden` | — | 50 |

## Users Endpoints

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/users/:id` | 300 | 900 |
| `GET /2/users` (by IDs) | 300 | 900 |
| `GET /2/users/by/username/:username` | 300 | 900 |
| `GET /2/users/by` (by usernames) | 300 | 900 |
| `GET /2/users/me` | — | 75 |
| `GET /2/users/:id/followers` | 15 | 15 |
| `GET /2/users/:id/following` | 15 | 15 |
| `POST /2/users/:id/following` (follow) | — | 50 |
| `DELETE /2/users/:id/following/:id` (unfollow) | — | 50 |
| `GET /2/users/:id/blocking` | — | 15 |
| `POST /2/users/:id/blocking` (block) | — | 50 |
| `GET /2/users/:id/muting` | — | 15 |
| `POST /2/users/:id/muting` (mute) | — | 50 |

## Timelines

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/users/:id/tweets` | 1,500 | 900 |
| `GET /2/users/:id/mentions` | 450 | 180 |
| `GET /2/users/:id/timelines/reverse_chronological` | — | 180 |

## Engagement

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `POST /2/users/:id/likes` (like) | — | 200 /24hrs |
| `DELETE /2/users/:id/likes/:id` (unlike) | — | 50 |
| `GET /2/users/:id/liked_tweets` | 75 | 75 |
| `POST /2/users/:id/retweets` (retweet) | — | 50 |
| `DELETE /2/users/:id/retweets/:id` | — | 50 |
| `GET /2/users/:id/bookmarks` | — | 180 |
| `POST /2/users/:id/bookmarks` | — | 50 |
| `DELETE /2/users/:id/bookmarks/:id` | — | 50 |

## Direct Messages

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/dm_events` | — | 300 |
| `GET /2/dm_conversations/with/:id/dm_events` | — | 300 |
| `GET /2/dm_conversations/:id/dm_events` | — | 300 |
| `POST /2/dm_conversations` | — | 200 /24hrs |
| `POST /2/dm_conversations/with/:id/messages` | — | 200 /24hrs |
| `POST /2/dm_conversations/:id/messages` | — | 200 /24hrs |

## Lists

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/lists/:id` | 75 | 75 |
| `POST /2/lists` (create) | — | 300 |
| `PUT /2/lists/:id` (update) | — | 300 |
| `DELETE /2/lists/:id` | — | 300 |
| `GET /2/lists/:id/members` | 900 | 900 |
| `POST /2/lists/:id/members` | — | 300 |
| `GET /2/lists/:id/tweets` | 900 | 900 |

## Spaces

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/spaces` | 300 | 300 |
| `GET /2/spaces/:id` | 300 | 300 |
| `GET /2/spaces/search` | 300 | 300 |

## Trends

| Endpoint | Per App /15min | Per User /15min |
|----------|---------------|-----------------|
| `GET /2/trends/by/woeid/:id` | 75 | 75 |

## Media Upload

| Endpoint | Per User /15min |
|----------|-----------------|
| `POST /2/media/upload` | 415 |
| `POST /2/media/upload/initialize` | 415 |
| `POST /2/media/upload/append` | 415 |
| `POST /2/media/upload/finalize` | 415 |

---

## Monthly Post Read Cap

| Tier | Posts/month |
|------|------------|
| Free | 0 (write only) |
| Basic | 10,000 |
| Pro | 1,000,000 |
| Enterprise | Custom |
