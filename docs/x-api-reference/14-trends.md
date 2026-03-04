# Trends

## GET /2/trends/by/woeid/:id — Trends by Location

**URL**: `https://api.x.com/2/trends/by/woeid/:id`

**Auth**: Bearer Token

### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Yahoo! Where On Earth ID (WOEID) |

### Common WOEID Values

| Location | WOEID |
|----------|-------|
| Worldwide | 1 |
| United States | 23424977 |
| United Kingdom | 23424975 |
| Japan | 23424856 |
| Canada | 23424775 |
| Australia | 23424748 |
| Germany | 23424829 |
| France | 23424819 |
| India | 23424848 |
| Brazil | 23424768 |
| New York | 2459115 |
| Los Angeles | 2442047 |
| London | 44418 |
| Tokyo | 1118370 |
| San Francisco | 2487956 |
| Chicago | 2379574 |

### Example Request

```bash
curl "https://api.x.com/2/trends/by/woeid/1" \
  -H "Authorization: Bearer $BEARER_TOKEN"
```

### Example Response

```json
{
  "data": [
    {
      "trend_name": "#AI",
      "tweet_count": 250000
    },
    {
      "trend_name": "Breaking News",
      "tweet_count": 180000
    },
    {
      "trend_name": "#Bitcoin",
      "tweet_count": 95000
    }
  ]
}
```

---

## Personalized Trends (Enterprise)

### GET /2/users/:id/trends — Personalized Trends

**URL**: `https://api.x.com/2/users/:id/trends`

**Auth**: OAuth 2.0 User Token

**Access**: Enterprise only

Returns trends personalized to the authenticated user's interests and network.
