/**
 * useCueTranslation.js
 *
 * Maps whiteboard items to cue insertion options and builds
 * modal prefill data for each extraction choice.
 */

/**
 * Determine the social platform from a whiteboard item
 */
function detectPlatform(item) {
  const sm = item.social_metadata || {}
  if (sm.platform === 'x' || sm.platform === 'twitter') return 'twitter'
  if (sm.platform === 'tiktok') return 'tiktok'
  if (item.url) {
    if (item.url.includes('x.com') || item.url.includes('twitter.com')) return 'twitter'
    if (item.url.includes('tiktok.com')) return 'tiktok'
  }
  return null
}

/**
 * Check if a whiteboard item has media (images/video)
 */
function hasMedia(item) {
  const sm = item.social_metadata || {}
  const mediaUrls = sm.media_urls || []
  const mediaObjects = sm.media_objects || []
  return mediaUrls.length > 0 || mediaObjects.length > 0 || item.media_url
}

/**
 * Get extraction options for a whiteboard item.
 * Returns array of { key, label, icon, cueType, children? }
 */
export function getExtractionOptions(item) {
  const type = item.item_type
  const platform = detectPlatform(item)
  const options = []

  if (type === 'link' && platform === 'twitter') {
    options.push({
      key: 'xpost',
      label: 'X (Tweet) Post',
      icon: 'mdi-twitter',
      cueType: 'GFX',
      gfxSubtype: 'xpost'
    })
    if (hasMedia(item)) {
      options.push({
        key: 'media-from-post',
        label: 'Media from Post',
        icon: 'mdi-image-multiple',
        children: [
          { key: 'media-img', label: 'As IMG', icon: 'mdi-image', cueType: 'IMG' },
          { key: 'media-sot', label: 'As SOT', icon: 'mdi-video', cueType: 'SOT' },
          { key: 'media-vo', label: 'As VO', icon: 'mdi-microphone', cueType: 'VO' },
          { key: 'media-nat', label: 'As NAT', icon: 'mdi-volume-high', cueType: 'NAT' }
        ]
      })
    }
  } else if (type === 'link' && platform === 'tiktok') {
    options.push({
      key: 'tiktok-video',
      label: 'Video from TikTok',
      icon: 'mdi-video',
      cueType: 'SOT'
    })
  } else if (type === 'image') {
    // Single option — no menu needed
    options.push({
      key: 'image',
      label: 'Image',
      icon: 'mdi-image',
      cueType: 'IMG'
    })
  } else if (type === 'video') {
    options.push({
      key: 'video',
      label: 'Video',
      icon: 'mdi-video',
      cueType: 'SOT'
    })
  } else if (type === 'text') {
    options.push({
      key: 'fsq',
      label: 'Full Screen Quote',
      icon: 'mdi-format-quote-close',
      cueType: 'FSQ'
    })
    options.push({
      key: 'script-paragraph',
      label: 'Script Paragraph',
      icon: 'mdi-text',
      cueType: 'PARAGRAPH'
    })
  } else if (type === 'link') {
    // Generic link (no social platform)
    options.push({
      key: 'link-gfx',
      label: 'Link Card (GFX)',
      icon: 'mdi-card-text',
      cueType: 'GFX',
      gfxSubtype: 'fullscreen-text'
    })
  }

  return options
}

/**
 * Build modal prefill data from a whiteboard item and chosen option.
 */
export function buildModalPrefill(item, option) {
  const sm = item.social_metadata || {}

  switch (option.key) {
    case 'xpost':
      return {
        type: 'gfx-xpost',
        socialMetadata: sm,
        url: item.url
      }

    case 'media-img': {
      const mediaUrl = (sm.media_urls && sm.media_urls[0]) || item.media_url
      return {
        type: 'img',
        mediaUrl,
        assetId: item.asset_id,
        caption: sm.tweet_text || item.caption || ''
      }
    }

    case 'media-sot':
    case 'media-vo':
    case 'media-nat':
    case 'tiktok-video':
    case 'video': {
      const mediaUrl = (sm.media_urls && sm.media_urls[0]) || item.media_url || item.url
      return {
        type: option.cueType.toLowerCase(),
        mediaUrl,
        title: sm.author_handle ? `@${sm.author_handle}` : item.title || ''
      }
    }

    case 'image':
      return {
        type: 'img',
        mediaUrl: item.media_url,
        assetId: item.asset_id,
        caption: item.caption || item.title || ''
      }

    case 'fsq':
      return {
        type: 'fsq',
        quote: item.text_content || '',
        attribution: ''
      }

    case 'script-paragraph':
      return {
        type: 'paragraph',
        text: item.text_content || ''
      }

    case 'link-gfx':
      return {
        type: 'gfx-link',
        title: item.title || item.preview_title || '',
        body: item.url || '',
        description: item.preview_description || ''
      }

    default:
      return { type: 'unknown' }
  }
}
