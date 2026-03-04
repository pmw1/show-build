# Direct Messages

**Data Window**: Events from up to **30 days ago** are available.

---

## DM Lookup

### GET /2/dm_events — All DM Events

**URL**: `https://api.x.com/2/dm_events`

**Auth**: OAuth 2.0 User Token (scopes: `dm.read`, `tweet.read`, `users.read`)

| Param | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `max_results` | integer | 100 | 1-100 | Results per page |
| `pagination_token` | string | — | — | Base32, min 16 chars |
| `event_types` | array | all | — | `MessageCreate`, `ParticipantsJoin`, `ParticipantsLeave` |
| `dm_event.fields` | string | — | — | `attachments`, `created_at`, `dm_conversation_id`, `entities`, `event_type`, `id`, `participant_ids`, `referenced_tweets`, `sender_id`, `text` |
| `expansions` | string | — | — | `attachments.media_keys`, `participant_ids`, `referenced_tweets.id`, `sender_id` |
| `media.fields` | string | — | — | Standard media fields |
| `user.fields` | string | — | — | Standard user fields |
| `tweet.fields` | string | — | — | Standard tweet fields |

### Example Response

```json
{
  "data": [
    {
      "id": "1580705921830768643",
      "event_type": "MessageCreate",
      "text": "Hello!",
      "sender_id": "2244994945",
      "dm_conversation_id": "1580705921830768640",
      "created_at": "2022-10-13T22:28:10.000Z"
    }
  ],
  "meta": {
    "result_count": 1,
    "next_token": "...",
    "previous_token": "..."
  }
}
```

### GET /2/dm_conversations/with/:participant_id/dm_events — 1-to-1 DMs

**URL**: `https://api.x.com/2/dm_conversations/with/:participant_id/dm_events`

**Auth**: OAuth 2.0 User Token

Same query parameters as above. Returns events from a specific 1-to-1 conversation.

### GET /2/dm_conversations/:dm_conversation_id/dm_events — Conversation DMs

**URL**: `https://api.x.com/2/dm_conversations/:dm_conversation_id/dm_events`

**Auth**: OAuth 2.0 User Token

Same query parameters as above. Returns events from any conversation by ID.

---

## DM Management (Send Messages)

### POST /2/dm_conversations — Create New Group Conversation

**URL**: `https://api.x.com/2/dm_conversations`

**Auth**: OAuth 2.0 User Token (scopes: `dm.write`, `dm.read`)

```json
{
  "conversation_type": "Group",
  "participant_ids": ["2244994945", "6253282"],
  "message": {
    "text": "Welcome to the group!"
  }
}
```

**Response:**
```json
{
  "data": {
    "dm_conversation_id": "1580705921830768640",
    "dm_event_id": "1580705921830768643"
  }
}
```

### POST /2/dm_conversations/with/:participant_id/messages — Send 1-to-1 DM

**URL**: `https://api.x.com/2/dm_conversations/with/:participant_id/messages`

**Auth**: OAuth 2.0 User Token

```json
{
  "text": "Hello!",
  "attachments": [{"media_id": "1455952740635586573"}]
}
```

**Response:**
```json
{
  "data": {
    "dm_conversation_id": "1580705921830768640",
    "dm_event_id": "1580705921830768643"
  }
}
```

### POST /2/dm_conversations/:dm_conversation_id/messages — Send to Existing Conversation

**URL**: `https://api.x.com/2/dm_conversations/:dm_conversation_id/messages`

**Auth**: OAuth 2.0 User Token

Same request body as above.

### DELETE /2/dm_events/:id — Delete a DM Event

**URL**: `https://api.x.com/2/dm_events/:id`

**Auth**: OAuth 2.0 User Token

**Response**: `{"data": {"deleted": true}}`

---

## DM Event Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Event identifier |
| `event_type` | string | `MessageCreate`, `ParticipantsJoin`, `ParticipantsLeave` |
| `text` | string | Message content |
| `sender_id` | string | User ID of sender |
| `dm_conversation_id` | string | Conversation identifier |
| `created_at` | string | ISO 8601 timestamp |
| `attachments` | object | Card IDs and media keys |
| `entities` | object | Hashtags, mentions, cashtags, URLs |
| `participant_ids` | array | For join/leave events |
| `referenced_tweets` | array | Tweet IDs referenced |
