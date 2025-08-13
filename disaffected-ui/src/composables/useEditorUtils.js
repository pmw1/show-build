import { themeColorMap } from '@/utils/themeColorMap'

export function useEditorUtils() {
  
  // Error handling utility
  const handleError = (context, error, fallback = null) => {
    console.warn(`[ContentEditor:${context}]`, error)
    return fallback
  }

  // Safe property accessor utility
  const safeGet = (obj, path, fallback = null) => {
    try {
      return path.split('.').reduce((current, key) => current?.[key], obj) ?? fallback
    } catch {
      return fallback
    }
  }

  // Theme and styling utilities
  const resolveTypeClass = (type) => {
    const colorMapping = themeColorMap[type] || themeColorMap.unknown
    return `type-${type.toLowerCase()}-bg`
  }

  const getItemTypeColor = (type) => {
    // Updated color mapping to match database values
    const colorMap = {
      opening: 'green',
      segment: 'info',      // Updated to match database  
      ad: 'primary',        // Updated to match database
      interview: 'purple',
      music: 'teal',
      cta: 'accent',        // Updated to match database
      closing: 'indigo',
      outro: 'brown',
      story: 'info',        // Updated to match database
      commercial: 'primary', // Updated to match database
      weather: 'cyan',
      sports: 'green',
      feature: 'purple',
      breaking: 'red',
      live: 'pink',
      package: 'indigo',
      vo: 'deep-orange',
      vosot: 'amber',
      reader: 'brown',
      tease: 'lime',
      tag: 'grey'
    }
    return colorMap[type] || 'grey'
  }

  const getTextColorForItem = (type) => {
    const colorMapping = themeColorMap[type] || themeColorMap.unknown
    return colorMapping.textColor || 'inherit'
  }

  // Duration formatting
  const formatDuration = (duration) => {
    if (!duration) return '0:00'
    if (typeof duration === 'string' && duration.includes(':')) {
      return duration
    }
    // Handle numeric duration (assuming seconds)
    if (typeof duration === 'number') {
      const minutes = Math.floor(duration / 60)
      const seconds = duration % 60
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }
    return duration.toString()
  }

  // Mode utilities
  const getModeIcon = (mode) => {
    const icons = {
      script: 'mdi-script-text',
      scratch: 'mdi-pencil',
      metadata: 'mdi-cog'
    }
    return icons[mode] || 'mdi-script-text'
  }

  // Content processing
  const insertCueAtCursor = (content, cueMarkdown, cursorPosition = null) => {
    try {
      if (cursorPosition !== null) {
        const before = content.substring(0, cursorPosition)
        const after = content.substring(cursorPosition)
        return before + '\n\n' + cueMarkdown + '\n\n' + after
      } else {
        return content + '\n\n' + cueMarkdown + '\n\n'
      }
    } catch (error) {
      handleError('insertCueAtCursor', error)
      return content + '\n\n' + cueMarkdown + '\n\n'
    }
  }

  const generateCueMarkdown = (cueData) => {
    const { type, slug, description, duration } = cueData
    
    let markdown = `### ${type.toUpperCase()}: ${slug}\n`
    markdown += `**Duration:** ${duration || 'TBD'}\n\n`
    markdown += `${description}\n`
    
    // Add type-specific fields
    if (type === 'sot' && cueData.sourceFile) {
      markdown += `\n**Source:** ${cueData.sourceFile}`
      if (cueData.timecode) {
        markdown += ` @ ${cueData.timecode}`
      }
    } else if (type === 'vo' && cueData.script) {
      markdown += `\n**Script:**\n${cueData.script}`
    } else if (type === 'fsq' && cueData.quoteText) {
      markdown += `\n> ${cueData.quoteText}`
      if (cueData.attribution) {
        markdown += `\n> — ${cueData.attribution}`
      }
    } else if (type === 'nat' && cueData.location) {
      markdown += `\n**Location:** ${cueData.location}`
      if (cueData.ambientType) {
        markdown += ` (${cueData.ambientType})`
      }
    } else if (type === 'pkg') {
      if (cueData.reporter) {
        markdown += `\n**Reporter:** ${cueData.reporter}`
      }
      if (cueData.pkgDuration) {
        markdown += `\n**Package Duration:** ${cueData.pkgDuration}`
      }
      if (cueData.notes) {
        markdown += `\n**Notes:** ${cueData.notes}`
      }
    }
    
    return markdown
  }

  // Asset handling
  const handleAssetDrop = (event, currentContent, updateContentCallback) => {
    try {
      event.preventDefault()
      const files = Array.from(event.dataTransfer.files)
      
      files.forEach(file => {
        if (file.type.startsWith('image/')) {
          const reader = new FileReader()
          reader.onload = (e) => {
            const markdown = `![${file.name}](${e.target.result})\n\n`
            updateContentCallback(currentContent + markdown)
          }
          reader.readAsDataURL(file)
        } else {
          const markdown = `[${file.name}](path/to/${file.name})\n\n`
          updateContentCallback(currentContent + markdown)
        }
      })
    } catch (error) {
      handleError('handleAssetDrop', error)
    }
  }

  // Validation rules
  const titleRules = [
    v => !!v || 'Title is required',
    v => (v && v.length >= 3) || 'Title must be at least 3 characters'
  ]

  const slugRules = [
    v => !!v || 'Slug is required',
    v => (v && v.length >= 3) || 'Slug must be at least 3 characters',
    v => /^[a-z0-9-_]+$/.test(v) || 'Slug must be lowercase with only letters, numbers, hyphens, and underscores'
  ]

  const durationRules = [
    v => !v || /^\d{1,2}:\d{2}(:\d{2})?$/.test(v) || 'Duration must be in MM:SS or HH:MM:SS format'
  ]

  const linkRules = [
    v => !v || /^https?:\/\/.+/.test(v) || 'Link must be a valid URL starting with http:// or https://'
  ]

  // Constants
  const productionStatuses = [
    { title: 'Draft', value: 'draft' },
    { title: 'Approved', value: 'approved' },
    { title: 'Production', value: 'production' },
    { title: 'Completed', value: 'completed' }
  ]

  const itemTypes = [
    'story',
    'commercial',
    'weather',
    'sports',
    'feature',
    'breaking',
    'live',
    'package',
    'vo',
    'vosot',
    'reader',
    'tease',
    'tag'
  ]

  const rundownItemTypes = [
    { title: 'Opening', value: 'opening' },
    { title: 'Segment', value: 'segment' },
    { title: 'Commercial Break', value: 'ad' },
    { title: 'Interview', value: 'interview' },
    { title: 'Music', value: 'music' },
    { title: 'Call to Action', value: 'cta' },
    { title: 'Closing', value: 'closing' },
    { title: 'Outro', value: 'outro' }
  ]

  // Placeholders
  const scriptPlaceholder = `Start writing your script here...

Use the cue buttons above to insert broadcast elements:
• GFX - Graphics and lower thirds
• FSQ - Full screen quotes  
• SOT - Sound on tape/video clips
• VO - Voice over segments
• NAT - Natural sound
• PKG - Pre-produced packages`

  const scratchPlaceholder = `Use this space for brainstorming, notes, and rough drafts...

• Drag and drop assets here
• Experiment with ideas
• Keep track of research
• Draft story outlines`

  return {
    // Utilities
    handleError,
    safeGet,
    resolveTypeClass,
    getItemTypeColor,
    getTextColorForItem,
    formatDuration,
    getModeIcon,
    insertCueAtCursor,
    generateCueMarkdown,
    handleAssetDrop,
    
    // Validation
    titleRules,
    slugRules,
    durationRules,
    linkRules,
    
    // Constants
    productionStatuses,
    itemTypes,
    rundownItemTypes,
    scriptPlaceholder,
    scratchPlaceholder
  }
}
