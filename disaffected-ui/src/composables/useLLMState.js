/**
 * useLLMState.js - Universal LLM State Management Framework
 *
 * Centralized system for tracking, visualizing, and managing all LLM operations
 * across the entire Show-Build application.
 *
 * Scope Levels:
 * - field: Individual form fields (textarea, input)
 * - card: Component cards (cue cards, item cards)
 * - item: Rundown items, segments, episodes
 * - asset: Media assets, images, videos
 * - segment: Script segments, content blocks
 * - rundown: Entire rundown operations
 * - episode: Episode-level operations
 * - user: User-specific operations
 * - system: System-wide operations
 *
 * Operation Types (examples, not exhaustive):
 * - analyzing: Analysis operations
 * - generating: Content generation
 * - modifying: Content modification
 * - extracting: Entity/data extraction
 * - composing: Content composition
 * - refactoring: Content refactoring
 * - splitting: Quote/content splitting
 * - normalizing: Text normalization
 * - validating: Validation operations
 */

import { computed, reactive } from 'vue'
import { useUserPrefs } from './useUserPrefs'

// Global state shared across all component instances
const activeOperations = reactive(new Map())
const notifications = reactive([])
const dismissedNotificationIds = reactive(new Set())
let notificationIdCounter = 0
let operationIdCounter = 0

// NOTE (2026-06-04): the old backend persistence endpoints /api/llm/operations
// and /api/llm/notifications (llm_state_router) were REMOVED — they were an
// orphaned design whose `llm_notifications` table schema no longer matched the
// model, so every call 500'd. LLM operation/notification state is now purely
// in-memory for the session, with localStorage as a soft restore + per-user
// prefs as the source of truth for DISMISSED notification IDs (both still work).

// Load persisted state (dismissed IDs from prefs/localStorage; ops/notifs from
// the localStorage fallback). No backend calls.
async function loadPersistedState() {
  try {
    // Load dismissed notification IDs: per-user pref wins; legacy localStorage fallback.
    const userPrefs = useUserPrefs()
    const savedDismissedFromPrefs = userPrefs.get('notifications.dismissed', null)
    if (Array.isArray(savedDismissedFromPrefs) && savedDismissedFromPrefs.length > 0) {
      savedDismissedFromPrefs.forEach(id => dismissedNotificationIds.add(id))
      console.log(`♻️ Loaded ${savedDismissedFromPrefs.length} dismissed notification IDs from user prefs`)
    } else {
      const savedDismissed = localStorage.getItem('llm-dismissed-notifications')
      if (savedDismissed) {
        const dismissedIds = JSON.parse(savedDismissed)
        dismissedIds.forEach(id => dismissedNotificationIds.add(id))
        console.log(`♻️ Loaded ${dismissedIds.length} dismissed notification IDs from legacy localStorage`)
      }
    }

    // Restore operations/notifications from localStorage (the only persistence now).
    loadFromLocalStorageFallback()
  } catch (error) {
    console.warn('Failed to load persisted LLM state:', error.message)
  }
}

// Fallback to localStorage if database unavailable
function loadFromLocalStorageFallback() {
  try {
    const savedOps = localStorage.getItem('llm-operations-fallback')
    if (savedOps) {
      const ops = JSON.parse(savedOps)
      ops.forEach(op => activeOperations.set(op.id, op))
      console.log(`♻️ Restored ${ops.length} operations from localStorage fallback`)
    }

    const savedNotifs = localStorage.getItem('llm-notifications-fallback')
    if (savedNotifs) {
      const notifs = JSON.parse(savedNotifs)
      // Only restore notifications that haven't been dismissed
      const activeNotifs = notifs.filter(n => !n.dismissed && !dismissedNotificationIds.has(n.id))
      notifications.push(...activeNotifs)
      console.log(`♻️ Restored ${activeNotifs.length} active notifications from localStorage (${notifs.length - activeNotifs.length} dismissed)`)
    }
  } catch (error) {
    console.error('localStorage fallback failed:', error)
  }
}

// Save state (localStorage for ops/notifs; per-user prefs for dismissed IDs).
// No backend calls — the old /api/llm/* persistence endpoints were removed.
async function savePersistedState() {
  try {
    const persistentOps = Array.from(activeOperations.values())
      .filter(op => op.persistent)
    const recentNotifs = notifications.slice(-50)

    localStorage.setItem('llm-operations-fallback', JSON.stringify(persistentOps))
    localStorage.setItem('llm-notifications-fallback', JSON.stringify(recentNotifs))
    const dismissedArray = Array.from(dismissedNotificationIds)
    localStorage.setItem('llm-dismissed-notifications', JSON.stringify(dismissedArray))
    // Source of truth for dismissed IDs is per-user prefs.
    useUserPrefs().set('notifications.dismissed', dismissedArray)
  } catch (error) {
    console.warn('Failed to save LLM state:', error.message)
  }
}

// Auto-save on changes (debounced)
let saveTimeout
function scheduleSave() {
  clearTimeout(saveTimeout)
  saveTimeout = setTimeout(savePersistedState, 1000)
}

// Load state on module initialization
loadPersistedState()

export function useLLMState() {

  /**
   * Priority levels for notifications
   */
  const PRIORITY = {
    CRITICAL: 'critical',  // User action required immediately
    HIGH: 'high',          // Important but not blocking
    NORMAL: 'normal',      // Standard notifications
    LOW: 'low'             // Can be filtered out
  }

  /**
   * Visual feedback states
   */
  const STATE = {
    ANALYZING: 'analyzing',    // Purple - AI is thinking
    GENERATING: 'generating',  // Blue - AI is creating content
    MODIFYING: 'modifying',    // Orange - AI is changing content
    APPROVED: 'approved',      // Green - AI approved/completed successfully
    REJECTED: 'rejected',      // Red - AI rejected/failed
    PENDING: 'pending'         // Yellow - Awaiting user decision
  }

  /**
   * Visual feedback configuration by scope
   */
  const scopeVisuals = {
    field: {
      borderWidth: '7px',
      borderStyle: 'solid',
      borderRadius: '0',
      animation: 'none'
    },
    card: {
      borderWidth: '3px',
      borderStyle: 'solid',
      borderRadius: '0',
      animation: 'none'
    },
    item: {
      borderWidth: '7px',
      borderStyle: 'solid',
      borderRadius: '0',
      animation: 'throb 1.5s ease-in-out infinite'
    },
    asset: {
      borderWidth: '5px',
      borderStyle: 'dashed',
      borderRadius: '0',
      animation: 'pulse 2s ease-in-out infinite'
    },
    segment: {
      borderWidth: '4px',
      borderStyle: 'solid',
      borderRadius: '0',
      animation: 'throb 1.5s ease-in-out infinite'
    },
    rundown: {
      borderWidth: '8px',
      borderStyle: 'double',
      borderRadius: '0',
      animation: 'pulse 2s ease-in-out infinite'
    },
    episode: {
      borderWidth: '6px',
      borderStyle: 'solid',
      borderRadius: '0',
      animation: 'pulse 2s ease-in-out infinite'
    },
    user: {
      borderWidth: '3px',
      borderStyle: 'solid',
      borderRadius: '0',
      animation: 'none'
    },
    system: {
      borderWidth: '10px',
      borderStyle: 'double',
      borderRadius: '0',
      animation: 'pulse 3s ease-in-out infinite'
    }
  }

  /**
   * State color mapping
   */
  const stateColors = {
    [STATE.ANALYZING]: '#9C27B0',    // Purple
    [STATE.GENERATING]: '#2196F3',   // Blue
    [STATE.MODIFYING]: '#FF9800',    // Orange
    [STATE.APPROVED]: '#4CAF50',     // Green
    [STATE.REJECTED]: '#F44336',     // Red
    [STATE.PENDING]: '#FFC107'       // Yellow
  }

  /**
   * Start an LLM operation
   * @param {string} scope - Scope level (field, card, item, etc.)
   * @param {string} targetId - Unique identifier for the target element
   * @param {string} operation - Operation type (analyzing, generating, etc.)
   * @param {object} options - Additional options
   * @returns {string} operationId - Unique ID for this operation
   */
  function startOperation(scope, targetId, operation, options = {}) {
    const operationId = `llm-op-${++operationIdCounter}`

    const op = {
      id: operationId,
      scope,
      targetId,
      operation,
      state: options.state || STATE.ANALYZING,
      model: options.model || 'Unknown',
      startTime: Date.now(),
      message: options.message || `AI is ${operation}...`,
      metadata: options.metadata || {},
      priority: options.priority || PRIORITY.NORMAL,
      persistent: options.persistent || false  // Survives navigation
    }

    activeOperations.set(operationId, op)

    console.log(`🤖 LLM Operation Started: ${operationId}`, {
      scope,
      targetId,
      operation,
      state: op.state
    })

    // Schedule persistence save
    scheduleSave()

    // Add notification if requested with better context
    if (options.notify !== false) {
      const scopeContext = {
        field: 'field',
        card: 'card',
        item: 'rundown item',
        asset: 'asset',
        segment: 'segment',
        rundown: 'rundown',
        episode: 'episode',
        user: 'user profile',
        system: 'system'
      }

      const operationGerund = {
        analyzing: 'analyzing',
        generating: 'generating',
        modifying: 'modifying',
        extracting: 'extracting',
        composing: 'composing',
        refactoring: 'refactoring',
        splitting: 'splitting',
        normalizing: 'normalizing',
        validating: 'validating'
      }

      const scopeName = scopeContext[scope] || scope
      const gerund = operationGerund[operation] || operation

      // Enhanced start notification with context
      const contextDetails = []
      if (options.metadata?.component) contextDetails.push(`in ${options.metadata.component}`)
      if (options.metadata?.location) contextDetails.push(options.metadata.location)
      if (options.metadata?.fieldName) contextDetails.push(`(${options.metadata.fieldName})`)

      const contextStr = contextDetails.length > 0 ? ` ${contextDetails.join(' ')}` : ''

      const defaultTitle = options.notificationTitle || `AI ${gerund} ${scopeName}${contextStr}`
      const defaultMessage = options.message || `AI is ${gerund} ${scopeName}...`

      addNotification({
        title: defaultTitle,
        message: defaultMessage,
        priority: op.priority,
        operationId,
        type: 'operation-start',
        metadata: options.metadata
      })
    }

    return operationId
  }

  /**
   * Update an operation's state
   */
  function updateOperation(operationId, updates) {
    const op = activeOperations.get(operationId)
    if (!op) {
      console.warn(`Operation ${operationId} not found`)
      return
    }

    Object.assign(op, updates)

    console.log(`🔄 LLM Operation Updated: ${operationId}`, updates)
  }

  /**
   * Stop an LLM operation
   * @param {string} operationId - Operation ID to stop
   * @param {object} result - Optional result data
   */
  function stopOperation(operationId, result = {}) {
    const op = activeOperations.get(operationId)
    if (!op) {
      console.warn(`Operation ${operationId} not found`)
      return
    }

    const duration = Date.now() - op.startTime

    console.log(`✅ LLM Operation Completed: ${operationId}`, {
      operation: op.operation,
      duration: `${duration}ms`,
      result
    })

    // Add completion notification with better context
    if (result.notify !== false) {
      // Build contextual notification message
      const scopeContext = {
        field: 'field',
        card: 'card',
        item: 'rundown item',
        asset: 'asset',
        segment: 'segment',
        rundown: 'rundown',
        episode: 'episode',
        user: 'user profile',
        system: 'system'
      }

      const operationVerb = {
        analyzing: 'analyzed',
        generating: 'generated',
        modifying: 'modified',
        extracting: 'extracted',
        composing: 'composed',
        refactoring: 'refactored',
        splitting: 'split',
        normalizing: 'normalized',
        validating: 'validated'
      }

      const scopeName = scopeContext[op.scope] || op.scope
      const verb = operationVerb[op.operation] || op.operation

      // Enhanced notification with context metadata
      const contextDetails = []
      if (op.metadata?.component) contextDetails.push(`in ${op.metadata.component}`)
      if (op.metadata?.location) contextDetails.push(op.metadata.location)
      if (op.metadata?.fieldName) contextDetails.push(`(${op.metadata.fieldName})`)

      const contextStr = contextDetails.length > 0 ? ` ${contextDetails.join(' ')}` : ''

      const defaultTitle = result.notificationTitle || `AI ${verb} ${scopeName}${contextStr}`

      // Build detailed message
      let defaultMessage = result.message || `Successfully ${verb} ${scopeName} in ${(duration / 1000).toFixed(1)}s`

      // Add result summary if provided
      if (result.summary) {
        defaultMessage += ` - ${result.summary}`
      }

      // Add action required flag if waiting for user
      if (result.actionRequired) {
        defaultMessage += ' ⏸️ Action required'
      }

      addNotification({
        title: defaultTitle,
        message: defaultMessage,
        priority: result.priority || op.priority,
        operationId,
        type: 'operation-complete',
        success: result.success !== false,
        actionRequired: result.actionRequired || false,
        metadata: op.metadata
      })
    }

    activeOperations.delete(operationId)
  }

  /**
   * Fail an LLM operation
   */
  function failOperation(operationId, error) {
    const op = activeOperations.get(operationId)
    if (!op) {
      console.warn(`Operation ${operationId} not found`)
      return
    }

    const duration = Date.now() - op.startTime

    console.error(`❌ LLM Operation Failed: ${operationId}`, {
      operation: op.operation,
      duration: `${duration}ms`,
      error: error.message || error
    })

    // Add error notification with context
    const scopeContext = {
      field: 'field',
      card: 'card',
      item: 'rundown item',
      asset: 'asset',
      segment: 'segment',
      rundown: 'rundown',
      episode: 'episode',
      user: 'user profile',
      system: 'system'
    }

    const operationGerund = {
      analyzing: 'analyzing',
      generating: 'generating',
      modifying: 'modifying',
      extracting: 'extracting',
      composing: 'composing',
      refactoring: 'refactoring',
      splitting: 'splitting',
      normalizing: 'normalizing',
      validating: 'validating'
    }

    const scopeName = scopeContext[op.scope] || op.scope
    const gerund = operationGerund[op.operation] || op.operation

    addNotification({
      title: `AI failed ${gerund} ${scopeName}`,
      message: error.message || `Failed to ${op.operation} ${scopeName}`,
      priority: PRIORITY.HIGH,
      operationId,
      type: 'operation-error',
      success: false,
      error
    })

    activeOperations.delete(operationId)
  }

  /**
   * Wrapper for async LLM operations with automatic state management
   * @param {string} scope - Scope level
   * @param {string} targetId - Target element ID
   * @param {string} operation - Operation type
   * @param {Function} llmFunction - Async function to execute
   * @param {object} options - Additional options
   * @returns {Promise} Result of the LLM operation
   */
  async function withLLM(scope, targetId, operation, llmFunction, options = {}) {
    console.log('🎯 withLLM called:', { scope, targetId, operation, options })
    const operationId = startOperation(scope, targetId, operation, options)
    console.log('🆔 Operation ID created:', operationId)

    try {
      console.log('▶️ Executing LLM function...')
      const result = await llmFunction()
      console.log('✅ LLM function completed, result:', result)

      // Build enhanced result info
      const resultInfo = {
        success: true,
        message: options.successMessage,
        ...options.onSuccess
      }

      // Extract summary from result if available
      if (result && typeof result === 'object') {
        if (result.action === 'split' && result.count) {
          resultInfo.summary = `Recommends ${result.count}-part split`
          resultInfo.actionRequired = true
        } else if (result.action === 'approved') {
          resultInfo.summary = 'Quote fits on single screen'
        } else if (result.action === 'decoded') {
          resultInfo.summary = 'Stripped surrounding quotes'
        } else if (result.action === 'normalized') {
          resultInfo.summary = 'Normalized nested quotes'
        } else if (result.wordCount) {
          resultInfo.summary = `Generated ${result.wordCount} words`
        }
      }

      stopOperation(operationId, resultInfo)
      return result
    } catch (error) {
      console.error('❌ LLM function threw error:', error)
      failOperation(operationId, error)

      // Re-throw if not silenced
      if (options.silent !== true) {
        throw error
      }
      return null
    }
  }

  /**
   * Get active operations for a specific target
   */
  function getOperationsForTarget(scope, targetId) {
    return Array.from(activeOperations.values())
      .filter(op => op.scope === scope && op.targetId === targetId)
  }

  /**
   * Check if target has active operations
   */
  function isTargetActive(scope, targetId) {
    return getOperationsForTarget(scope, targetId).length > 0
  }

  /**
   * Get visual feedback style for a target
   */
  function getVisualStyle(scope, targetId) {
    const ops = getOperationsForTarget(scope, targetId)
    if (ops.length === 0) return null

    // Use most recent operation's state
    const op = ops[ops.length - 1]
    const visual = scopeVisuals[scope] || scopeVisuals.item
    const color = stateColors[op.state] || stateColors[STATE.ANALYZING]

    // #47: the rundown ROW (item scope) uses a throbbing BACKGROUND, not a
    // border — a 7px border clipped to only the left/top edges inside the
    // rundown's overflow container. The .generating-item CSS class owns the
    // background ENTIRELY via the llm-bg-throb keyframes; returning a static
    // inline backgroundColor here would paint over the animation (inline style
    // on the same element vs the keyframe), so we return NOTHING for item scope
    // and let the CSS class animate. Other scopes keep their border treatment.
    if (scope === 'item') {
      return null
    }

    return {
      border: `${visual.borderWidth} ${visual.borderStyle} ${color}`,
      borderRadius: visual.borderRadius,
      animation: visual.animation
    }
  }

  /**
   * Get CSS class for a target
   */
  function getVisualClass(scope, targetId) {
    const ops = getOperationsForTarget(scope, targetId)
    if (ops.length === 0) return null

    const op = ops[ops.length - 1]
    return `llm-${op.state} llm-scope-${scope}`
  }

  /**
   * Add notification to queue
   */
  function addNotification(notification) {
    const notif = {
      id: `notif-${++notificationIdCounter}`,
      timestamp: Date.now(),
      read: false,
      dismissed: false,
      ...notification
    }

    notifications.push(notif)

    console.log(`📬 Notification Added:`, notif)

    // Auto-dismiss low priority after 10 seconds
    if (notif.priority === PRIORITY.LOW) {
      setTimeout(() => {
        dismissNotification(notif.id)
      }, 10000)
    }

    return notif.id
  }

  /**
   * Mark notification as read
   */
  function markAsRead(notificationId) {
    const notif = notifications.find(n => n.id === notificationId)
    if (notif) {
      notif.read = true
    }
  }

  /**
   * Dismiss notification (marks as dismissed permanently)
   */
  function dismissNotification(notificationId) {
    const notif = notifications.find(n => n.id === notificationId)
    if (notif) {
      // Mark as dismissed instead of removing
      notif.dismissed = true

      // Add to permanent dismissed list
      dismissedNotificationIds.add(notificationId)

      // Remove from active array
      const index = notifications.indexOf(notif)
      notifications.splice(index, 1)

      // Save state to persist dismissal
      savePersistedState()

      console.log(`🗑️ Notification dismissed permanently: ${notificationId}`)
    }
  }

  /**
   * Clear all notifications (marks all as dismissed)
   */
  function clearAllNotifications() {
    // Add all current notification IDs to dismissed list
    notifications.forEach(n => {
      n.dismissed = true
      dismissedNotificationIds.add(n.id)
    })

    // Clear active notifications
    notifications.splice(0, notifications.length)

    // Persist the dismissals
    savePersistedState()

    console.log(`🗑️ All notifications cleared and dismissed permanently`)
  }

  /**
   * Get unread notification count
   */
  const unreadCount = computed(() => {
    return notifications.filter(n => !n.read).length
  })

  /**
   * Get notifications by priority
   */
  function getNotificationsByPriority(priority) {
    return notifications.filter(n => n.priority === priority)
  }

  return {
    // Constants
    PRIORITY,
    STATE,

    // Active operations
    activeOperations,
    getOperationsForTarget,
    isTargetActive,

    // Operation management
    startOperation,
    updateOperation,
    stopOperation,
    failOperation,
    withLLM,

    // Visual feedback
    getVisualStyle,
    getVisualClass,

    // Notifications
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    dismissNotification,
    clearAllNotifications,
    getNotificationsByPriority
  }
}
