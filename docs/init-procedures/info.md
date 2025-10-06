---
id: 0
episode_number: {auto-generated: highest episode + 1}
type: sunday_show
airdate: {auto-calculated next Sunday from highest episode}
title: 
subtitle: 
slug: 
description:  
duration: 00:00:00:00
guest: 
tags:
omnystudio_program_id: 6960f124-9e8a-4716-a88c-acfe00399fd7
omnystudio_category: podcast
omnystudio_visibility: public
omnystudio_publish_status: 
omnystudio_publish_datetime: 
youtube_category_id: 22
youtube_privacy_status: private
youtube_title: 
youtube_description: 
youtube_tags: 
youtube_default_language: en
youtube_playlist_id: PLZO_3Z8QjnOXrRe8CIpNJG2WqaijeZ0gC
social_hashtags: 
twitter_thread: true
instagram_reel: true
facebook_post: true
explicit: false
content_warnings: 
age_rating: general
publish_status: 
schedule_datetime: 
visibility: public
recording_date: 
producer: |
  Kevin Hurley
host: Joshua Slocum
editor: |-
  Joshua Slocum
  Kevin Hurley
notes: 
server_messages: |
  Messages from Whisper server
---

# Episode Info.md Frontmatter Reference

This document serves as the reference template for `info.md` frontmatter fields that must be initialized when creating new episodes in the Show-Build system.

## Frontmatter Fields Explanation

### Core Episode Fields

**`id`**: Internal identifier
- **Format**: Integer
- **Initial Value**: `0` (placeholder, updated by system)

**`episode_number`**: Sequential episode number
- **Format**: Integer (no leading zeros in YAML)
- **Example**: `235`
- **Auto-Generation**: Scans episodes folder for highest existing episode number, adds 1

**`type`**: Episode type/category
- **Format**: String value indicating show type
- **Example**: `sunday_show`
- **Initial Value**: `sunday_show` (default for regular episodes)

**`airdate`**: Scheduled air date for the episode
- **Format**: `YYYY-MM-DD` (ISO date format)
- **Example**: `2025-08-24`
- **Auto-Generation**: For `sunday_show` type, calculates next Sunday after highest episode's airdate

### Content Fields

**`title`**: Episode title
- **Format**: String
- **Initial Value**: Empty (to be filled during content development)

**`subtitle`**: Episode subtitle/theme
- **Format**: String
- **Initial Value**: Empty (to be filled during content development)

**`slug`**: URL-friendly identifier
- **Format**: Lowercase, hyphen-separated string
- **Initial Value**: Empty (typically derived from title)

**`description`**: Full episode description
- **Format**: String (may be AI generated)
- **Initial Value**: Empty

**`duration`**: Episode duration
- **Format**: `HH:MM:SS:MS` (hours:minutes:seconds:milliseconds)
- **Example**: `01:00:00:00`
- **Initial Value**: `00:00:00:00`
- **Note**: Same format as `total_runtime` field - should be consistent across all duration fields

**`guest`**: Guest name(s)
- **Format**: String
- **Initial Value**: Empty

**`tags`**: Episode tags/categories
- **Format**: YAML list
- **Example**: `[clusterb, intro, welcome]`
- **Initial Value**: Empty

### Omny Studio (Podcast) Distribution

**`omnystudio_program_id`**: Omny Studio program identifier
- **Format**: UUID string
- **Example**: `6960f124-9e8a-4716-a88c-acfe00399fd7`
- **Initial Value**: Empty (configured per show)

**`omnystudio_category`**: Podcast category
- **Format**: String
- **Default Value**: `podcast`

**`omnystudio_visibility`**: Podcast visibility setting
- **Format**: String enum
- **Default Value**: `public`

**`omnystudio_publish_status`**: Publication status on Omny
- **Format**: String enum
- **Initial Value**: Empty (set during publication)

**`omnystudio_publish_datetime`**: Scheduled publish time
- **Format**: `MM/DD/YYYY HH:MM:SS`
- **Initial Value**: Empty

### YouTube Distribution

**`youtube_category_id`**: YouTube category identifier
- **Format**: Integer
- **Default Value**: `22` (People & Blogs)

**`youtube_privacy_status`**: Video privacy setting
- **Format**: String enum (`private`, `public`, `unlisted`)
- **Default Value**: `private`

**`youtube_title`**: YouTube video title
- **Format**: String
- **Initial Value**: Empty (typically matches episode title)

**`youtube_description`**: YouTube video description
- **Format**: String
- **Initial Value**: Empty

**`youtube_tags`**: YouTube video tags
- **Format**: String (comma-separated)
- **Initial Value**: Empty

**`youtube_default_language`**: Default language code
- **Format**: String (ISO language code)
- **Default Value**: `en`

**`youtube_playlist_id`**: YouTube playlist identifier
- **Format**: YouTube playlist ID string
- **Initial Value**: Empty

### Social Media Settings

**`social_hashtags`**: Hashtags for social media posts
- **Format**: String
- **Initial Value**: Empty

**`twitter_thread`**: Enable Twitter thread creation
- **Format**: Boolean
- **Default Value**: `true`

**`instagram_reel`**: Enable Instagram reel creation
- **Format**: Boolean
- **Default Value**: `true`

**`facebook_post`**: Enable Facebook post creation
- **Format**: Boolean
- **Default Value**: `true`

### Content Classification

**`explicit`**: Contains explicit content
- **Format**: Boolean
- **Default Value**: `false`

**`content_warnings`**: Content warning descriptions
- **Format**: String
- **Example**: `Discussion of racism and sensitive social topics`
- **Initial Value**: Empty

**`age_rating`**: Content age rating
- **Format**: String enum
- **Default Value**: `general`

### Publication Management

**`publish_status`**: Overall publication status
- **Format**: String enum
- **Initial Value**: Empty (set during publication workflow)

**`schedule_datetime`**: Scheduled publication time
- **Format**: Datetime string
- **Initial Value**: Empty

**`visibility`**: Content visibility setting
- **Format**: String enum
- **Default Value**: `public`

**`recording_date`**: Date episode was recorded
- **Format**: Date string
- **Initial Value**: Empty

### Production Credits

**`producer`**: Episode producer name(s)
- **Format**: String or multi-line YAML
- **Example**: `Kevin Hurley`
- **Initial Value**: Empty

**`host`**: Episode host name(s)
- **Format**: String
- **Example**: `Joshua Slocum`
- **Initial Value**: Empty

**`editor`**: Episode editor name(s)
- **Format**: String or multi-line YAML
- **Example**: `Joshua Slocum\nKevin Hurley`
- **Initial Value**: Empty

### Internal Fields

**`notes`**: Internal production notes
- **Format**: String
- **Initial Value**: Empty

**`server_messages`**: Messages from processing servers
- **Format**: Multi-line string
- **Example**: `Messages from Whisper server`
- **Initial Value**: Empty

## Auto-Generation Logic for Sunday Shows

For episodes with `type: sunday_show`, the system automatically generates episode numbers and airdates:

### Episode Number Auto-Generation
1. **Scan** all existing episodes in the episodes folder
2. **Extract** episode numbers from directory names and/or database records  
3. **Calculate** `max(existing_episode_numbers) + 1`
4. **Assign** as the new episode number

### Airdate Auto-Generation
1. **Find** the highest existing episode number
2. **Retrieve** its airdate from `info.md` or database
3. **Calculate** the next Sunday after that airdate
4. **Assign** as the new episode's airdate

**Example:**
- Latest episode: `0237` with airdate `2025-08-24` (Sunday)
- New episode: `0238` with airdate `2025-08-31` (next Sunday)

## Usage in Episode Creation

When the `POST /episodes/create` API endpoint is called for a `sunday_show`, the episode scaffolding service:

1. **Auto-generates** episode number (highest + 1)
2. **Auto-calculates** airdate (next Sunday from latest episode)
3. **Generates** AssetID from backend API
4. **Creates** episode directory structure  
5. **Creates** `info.md` file with auto-populated fields
6. **Leaves** content fields (title, subtitle, etc.) empty for user input

## Implementation Requirements

For the auto-generation logic to work properly, the episode scaffolding service must:

### Episode Number Generation
1. **Scan episodes folder** for all existing episode directories (e.g., `/episodes/0237/`)
2. **Extract episode numbers** from directory names using regex parsing
3. **Query database** for additional episode records (backup/validation)
4. **Calculate maximum** existing episode number
5. **Add 1** to get the next sequential episode number
6. **Handle edge case** when no episodes exist (start with episode 1)

### Airdate Generation  
1. **Identify highest episode number** from scanning results
2. **Read `info.md`** from that episode's directory to get airdate
3. **Parse airdate** in `YYYY-MM-DD` format
4. **Calculate next Sunday** using date arithmetic:
   - Convert airdate to date object
   - Add days until `day_of_week == Sunday` (typically +7 days for weekly show)
   - Handle month/year boundary crossings
5. **Format result** as `YYYY-MM-DD` for YAML compatibility
6. **Handle edge case** when no episodes exist (use current date's next Sunday)

### Date Calculation Logic
```python
# Pseudocode for next Sunday calculation
def get_next_sunday(last_episode_date):
    # Parse the last episode's airdate
    last_date = datetime.strptime(last_episode_date, '%Y-%m-%d')
    
    # Calculate days until next Sunday (0=Monday, 6=Sunday)
    days_ahead = 6 - last_date.weekday()  # Sunday is 6
    if days_ahead <= 0:  # Last episode was on Sunday
        days_ahead += 7   # Move to next Sunday
    
    next_sunday = last_date + timedelta(days=days_ahead)
    return next_sunday.strftime('%Y-%m-%d')
```

### Error Handling
- **No episodes exist**: Use current date's next Sunday as starting point
- **Malformed airdates**: Log error and use current date's next Sunday
- **File system access errors**: Fall back to manual input requirements
- **Database inconsistencies**: Prefer file system data over database records

### Validation
- **Verify episode number uniqueness** before finalizing
- **Confirm airdate is actually a Sunday** before assignment
- **Check for reasonable date ranges** (not too far in past/future)
- **Validate directory creation permissions** before proceeding

## Integration with Show-Build Tools

These frontmatter fields are read and utilized by:

- **Duration Calculator**: Updates `total_runtime` field
- **Script Renderer**: Uses metadata for script headers and formatting
- **Media Collector**: References episode information for organization
- **Asset Management**: Uses `AssetID` for tracking and relationships
- **Frontend UI**: Displays episode information and status
- **Episode Scaffolding**: Auto-generates episode numbers and airdates

## Field Update Workflow

**During Episode Creation**:
- `AssetID`, `episode_number`, `slug` → Set from API request/auto-generation
- `title`, `subtitle`, `airdate` → Set from `episode_metadata` or defaults
- `type`, `guest`, `tags` → Set from request or remain at defaults
- `status` → Always starts as `draft`
- `total_runtime` → Remains `00:00:00:00` until content is added

**During Content Development**:
- `title`, `subtitle` → Updated as content is refined
- `guest` → Added when guest segments are created
- `tags` → Added for categorization and search

**During Production Preparation**:
- `status` → Changed from `draft` to `production`
- `total_runtime` → Updated by duration calculator
- `airdate` → Finalized for scheduling

**Post-Production**:
- `status` → Updated to `completed` or `archived`

---

*This reference document ensures consistent `info.md` initialization across all Show-Build episode creation methods.*
