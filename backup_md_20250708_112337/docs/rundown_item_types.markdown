# Rundown Item Types and Element Cues

## Overview
The Disaffected Production Suite organizes episode content into **rundown item types** and **cue types** within the **element cue class**. Rundown item types are stored as individual Markdown files with YAML frontmatter, forming the structural backbone of episodes. Cue types in the element cue class are custom code blocks embedded within these scripts to instruct directors or AI directors to trigger specific elements (e.g., graphics, quotes, video/audio clips) at precise moments during production. Additional cue types (e.g., director notes, camera to take) are planned for future classes.

Current rundown item types include: `ad`, `cta`, `promo`, `segment`, `trans`.  
Current cue types in the element cue class include: `GFX`, `FSQ`, `SOT`, `VO`, `NAT`, `PKG`.

## Rundown Item Types
### Advertisement (ad)
- **Purpose**: Commercial breaks or sponsor messages.
- **Fields**:
  - `id`: Auto-generated (`ad_YYYYMMDD_###`)
  - `slug`: URL-safe identifier (required)
  - `type`: `ad` (required)
  - `duration`: Time in `MM:SS` or `HH:MM:SS` (required)
  - `customer_name`: Advertiser name (required)
  - `sponsor`: Sponsor organization (optional)
- **Example**:
  ```yaml
  ---
  id: ad_20250708_001
  slug: coffee-shop-ad
  type: ad
  duration: 00:30
  customer_name: Hometown Coffee Co.
  sponsor: Main Street Business Alliance
  ---
  # Hometown Coffee Ad
  Visit Hometown Coffee Co. for locally roasted beans!
  ```

### Call to Action (cta)
- **Purpose**: Audience engagement prompts (e.g., subscriptions, social media).
- **Fields**:
  - `id`: Auto-generated
  - `slug`: URL-safe identifier (required)
  - `type`: `cta` (required)
  - `duration`: Time (required)
  - `title`: Brief title (required)
  - `link`: Target URL (optional)
  - `priority`: `high`, `medium`, `low` (optional)
  - `message`: Action text (required)
- **Example**:
  ```yaml
  ---
  id: cta_20250708_001
  slug: newsletter-signup
  type: cta
  duration: 00:15
  title: Newsletter Signup
  link: https://disaffected.tv/newsletter
  priority: high
  message: Subscribe for exclusive content!
  ---
  # Join Our Newsletter
  Subscribe at disaffected.tv/newsletter.
  ```

### Promo (promo)
- **Purpose**: Promote upcoming shows or events.
- **Fields**:
  - `id`: Auto-generated
  - `slug`: URL-safe identifier (required)
  - `type`: `promo` (required)
  - `duration`: Time (required)
  - `title`: Promo title (required)
  - `description`: Promo description (required)
  - `start_date`, `end_date`: Promotion period (optional)
  - `priority`: Priority level (optional)
  - `sponsor`: Sponsor name (optional)
- **Example**:
  ```yaml
  ---
  id: promo_20250708_001
  slug: tech-series
  type: promo
  duration: 00:45
  title: Tech Dissected Series
  description: Monthly deep-dive into tech trends
  start_date: 2025-07-15
  end_date: 2025-08-15
  priority: high
  sponsor: ''
  ---
  # Tech Dissected
  Premier