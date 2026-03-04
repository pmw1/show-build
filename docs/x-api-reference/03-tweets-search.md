# Tweets Search

## GET /2/tweets/search/recent — Recent Search

Search tweets from the **last 7 days**.

**URL**: `https://api.x.com/2/tweets/search/recent`

**Auth**: Bearer Token, OAuth 2.0 User Token

**Access**: All tiers (Free, Basic, Pro, Enterprise)

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query (max 512 chars; 4,096 for Enterprise) |
| `max_results` | integer | No | 10-100 per request (default 10) |
| `next_token` | string | No | Pagination token from previous response |
| `since_id` | string | No | Minimum tweet ID (exclusive) |
| `until_id` | string | No | Maximum tweet ID (exclusive) |
| `start_time` | string | No | ISO 8601 earliest timestamp |
| `end_time` | string | No | ISO 8601 latest timestamp |
| `sort_order` | string | No | `recency` or `relevancy` |
| `tweet.fields` | string | No | Standard tweet fields |
| `expansions` | string | No | Standard expansions |
| `user.fields` | string | No | Standard user fields |
| `media.fields` | string | No | Standard media fields |
| `place.fields` | string | No | Standard place fields |
| `poll.fields` | string | No | Standard poll fields |

### Example Request

```bash
curl "https://api.x.com/2/tweets/search/recent\
?query=(AI OR %22artificial intelligence%22) lang:en -is:retweet has:images\
&max_results=10\
&tweet.fields=created_at,author_id,public_metrics,entities\
&expansions=author_id,attachments.media_keys\
&user.fields=username,profile_image_url\
&media.fields=url,type,preview_image_url" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Example Response

```json
{
  "data": [
    {
      "id": "1346889436626259968",
      "text": "Amazing new AI research...",
      "author_id": "2244994945",
      "created_at": "2021-01-06T18:40:40.000Z",
      "public_metrics": {
        "retweet_count": 11,
        "reply_count": 2,
        "like_count": 45
      }
    }
  ],
  "includes": {
    "users": [...],
    "media": [...]
  },
  "meta": {
    "newest_id": "1346889436626259968",
    "oldest_id": "1346889436626259960",
    "result_count": 10,
    "next_token": "b26v89c19zqg8o3fpza01xsqx6k8u0awx2lah14s00000"
  }
}
```

---

## GET /2/tweets/search/all — Full-Archive Search

Search the **complete tweet archive** back to 2006.

**URL**: `https://api.x.com/2/tweets/search/all`

**Auth**: Bearer Token, OAuth 2.0 User Token

**Access**: Pro ($5k/mo) and Enterprise only

### Query Parameters

Same as recent search, plus:

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Max 1,024 chars (4,096 Enterprise) |
| `max_results` | integer | 10-500 per request |

---

## Search Query Operators

### Keyword Operators

| Operator | Example | Description |
|----------|---------|-------------|
| keyword | `AI` | Matches keyword in tweet text |
| "exact phrase" | `"artificial intelligence"` | Exact phrase match |
| `#hashtag` | `#AI` | Matches hashtag |
| `@mention` | `@elonmusk` | Matches mention |
| `-keyword` | `-spam` | Exclude keyword |
| `OR` | `AI OR ML` | Match either term |

### User Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `from:` | `from:elonmusk` | Posts by user |
| `to:` | `to:elonmusk` | Replies to user |
| `retweets_of:` | `retweets_of:elonmusk` | Retweets of user's posts |

### Content Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `has:images` | `AI has:images` | Posts with images |
| `has:videos` | `AI has:videos` | Posts with videos |
| `has:media` | `AI has:media` | Posts with any media |
| `has:links` | `AI has:links` | Posts with URLs |
| `has:mentions` | `AI has:mentions` | Posts with @mentions |
| `has:hashtags` | `AI has:hashtags` | Posts with hashtags |
| `url:` | `url:github.com` | Posts linking to domain |
| `has:geo` | `news has:geo` | Posts with geo data |

### Filter Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `is:retweet` | `-is:retweet` | Include/exclude retweets |
| `is:reply` | `-is:reply` | Include/exclude replies |
| `is:quote` | `is:quote` | Only quote tweets |
| `is:verified` | `is:verified` | Only verified users |
| `lang:` | `lang:en` | Language filter (BCP 47) |
| `conversation_id:` | `conversation_id:123` | All replies in thread |
| `context:` | `context:10.799022225751871488` | Entity/topic context |
| `entity:` | `entity:"Bitcoin"` | Named entity |
| `place:` | `place:"New York"` | Geo place name |
| `place_country:` | `place_country:US` | Country code |

### Example Queries

```
# Tech news with images, no retweets
(AI OR "machine learning" OR "deep learning") has:images -is:retweet lang:en

# Specific user's original posts
from:elonmusk -is:retweet -is:reply

# Posts about a topic with engagement
#Bitcoin has:links is:verified

# Conversation thread
conversation_id:1346889436626259968
```

### Rate Limits

| Endpoint | Per App (15 min) | Per User (15 min) |
|----------|-----------------|-------------------|
| Recent search | 450 | 180 |
| Full-archive search | 300 | 1 |
