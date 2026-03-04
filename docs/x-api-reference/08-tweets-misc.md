# Hide Replies

## PUT /2/tweets/:tweet_id/hidden — Hide/Unhide Reply

Hide or unhide a reply to a tweet authored by the authenticated user.

**URL**: `https://api.x.com/2/tweets/:tweet_id/hidden`

**Auth**: OAuth 2.0 User Token (PKCE)

### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tweet_id` | string | Yes | ID of the reply to hide/unhide |

### Request Body

```json
{
  "hidden": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `hidden` | boolean | `true` to hide, `false` to unhide |

### Example Request

```bash
curl -X PUT "https://api.x.com/2/tweets/1346889436626259968/hidden" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hidden": true}'
```

### Response

```json
{
  "data": {
    "hidden": true
  }
}
```

### Notes

- Can only hide replies to tweets you authored
- Hidden replies are still accessible but require an extra click to view
- Useful for moderating conversation threads
