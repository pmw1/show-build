# X API v2 — Local Reference Guide

**Last Updated**: 2026-02-25
**Official Docs**: https://docs.x.com/x-api/introduction
**Base URL**: `https://api.x.com`

This is a locally-mirrored reference of the X (Twitter) API v2 for use in Show-Build's whiteboard/brainstorm system — specifically for fetching tweets to render as full-screen graphics.

## File Index

| File | Contents |
|------|----------|
| [01-authentication.md](01-authentication.md) | OAuth 2.0, Bearer tokens, scopes |
| [02-tweets-lookup.md](02-tweets-lookup.md) | GET tweets by ID, multiple tweets |
| [03-tweets-search.md](03-tweets-search.md) | Recent search, full-archive search, operators |
| [04-tweets-manage.md](04-tweets-manage.md) | Create, delete, edit posts |
| [05-tweets-timelines.md](05-tweets-timelines.md) | User timeline, mentions, reverse-chronological |
| [06-tweets-engagement.md](06-tweets-engagement.md) | Likes, retweets/reposts, bookmarks, quotes |
| [07-tweets-stream.md](07-tweets-stream.md) | Filtered stream, rules management |
| [08-tweets-misc.md](08-tweets-misc.md) | Hide replies |
| [09-users.md](09-users.md) | User lookup, followers, following, blocks, mutes |
| [10-spaces.md](10-spaces.md) | Space lookup, search |
| [11-direct-messages.md](11-direct-messages.md) | DM lookup, send messages, conversations |
| [12-lists.md](12-lists.md) | Create/manage lists, members, followers |
| [13-media-upload.md](13-media-upload.md) | Simple upload, chunked upload, initialize |
| [14-trends.md](14-trends.md) | Trends by WOEID |
| [15-data-dictionary.md](15-data-dictionary.md) | Tweet, User, Media, Space, List, Poll, Place objects |
| [16-rate-limits.md](16-rate-limits.md) | Rate limit reference table |
| [17-compliance.md](17-compliance.md) | Compliance streams |

## Quick Start — Fetch a Tweet by ID

```bash
curl "https://api.x.com/2/tweets/1346889436626259968?tweet.fields=created_at,author_id,public_metrics,entities&expansions=author_id,attachments.media_keys&user.fields=username,profile_image_url&media.fields=url,preview_image_url,type" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

## Access Tiers

| Tier | Cost | Post Reads/mo | Post Creates/mo | Key Limits |
|------|------|---------------|-----------------|------------|
| Free | $0 | — | 1,500 | Write-only, 1 app |
| Basic | $200/mo | 10,000 | 3,000 | 2 apps |
| Pro | $5,000/mo | 1,000,000 | 300,000 | 3 apps |
| Enterprise | Custom | Custom | Custom | Unlimited apps |

## Show-Build Integration Notes

For the whiteboard tweet card feature:
1. Use **Tweet Lookup** (`GET /2/tweets/:id`) to fetch tweet content, author, and media
2. Use **expansions** to get author profile image and media attachments in one call
3. Store the tweet data in the whiteboard card's metadata field
4. Use the stored data to render full-screen graphics later
