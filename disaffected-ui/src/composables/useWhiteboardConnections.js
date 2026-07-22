import { ref } from 'vue'

/**
 * Whiteboard link store.
 *
 * This used to own the whole hand-rolled connection system — border-zone hover
 * detection, rubber-band drag state, endpoint re-aim, path building. The canvas
 * now runs on Vue Flow, which provides connection dragging, edge rendering and
 * hit-testing natively, so what remains here is the part Vue Flow does NOT own:
 * the persisted link data and its mapping to/from the save API.
 */
export function useWhiteboardConnections() {
  // === Persisted link state ===
  const nodeLinks = ref([])

  // === Flash animation state (cards pulse when a connection lands) ===
  const flashingCards = ref(new Set())

  // ─── Link CRUD ───

  function loadLinks(linkData, cardsList) {
    if (!linkData || !Array.isArray(linkData)) {
      nodeLinks.value = []
      return
    }
    nodeLinks.value = linkData.map(link => ({
      id: link.id,
      sourceCardId: cardsList[link.source_index]?.id ?? null,
      targetCardId: cardsList[link.target_index]?.id ?? null,
      relationshipType: link.relationship_type || null,
      label: link.label || null,
      color: link.color || '#1976d2'
    })).filter(l => l.sourceCardId !== null && l.targetCardId !== null)
  }

  function createLink(sourceCardId, targetCardId, options = {}) {
    if (sourceCardId === targetCardId) return false
    const exists = nodeLinks.value.some(
      l => (l.sourceCardId === sourceCardId && l.targetCardId === targetCardId) ||
           (l.sourceCardId === targetCardId && l.targetCardId === sourceCardId)
    )
    if (exists) return false

    nodeLinks.value.push({
      id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      sourceCardId,
      targetCardId,
      relationshipType: options.relationshipType || null,
      label: options.label || null,
      color: options.color || '#1976d2'
    })
    return true
  }

  function deleteLink(linkId) {
    nodeLinks.value = nodeLinks.value.filter(l => l.id !== linkId)
  }

  function deleteLinksForCard(cardId) {
    nodeLinks.value = nodeLinks.value.filter(
      l => l.sourceCardId !== cardId && l.targetCardId !== cardId
    )
  }

  // ─── Flash animation ───

  function triggerFlash(cardId) {
    flashingCards.value.add(cardId)
    setTimeout(() => {
      flashingCards.value.delete(cardId)
      flashingCards.value = new Set(flashingCards.value)
    }, 600)
    flashingCards.value = new Set(flashingCards.value)
  }

  // ─── Save helpers ───

  function getLinksForSave(cardsList) {
    return nodeLinks.value.map(link => {
      const sourceIndex = cardsList.findIndex(c => c.id === link.sourceCardId)
      const targetIndex = cardsList.findIndex(c => c.id === link.targetCardId)
      if (sourceIndex === -1 || targetIndex === -1) return null
      return {
        source_client_id: sourceIndex,
        target_client_id: targetIndex,
        relationship_type: link.relationshipType,
        label: link.label,
        color: link.color
      }
    }).filter(Boolean)
  }

  return {
    nodeLinks,
    loadLinks,
    createLink,
    deleteLink,
    deleteLinksForCard,
    getLinksForSave,
    triggerFlash,
    flashingCards
  }
}

/**
 * Where does the ray from a rect's center toward `to` cross that rect's border?
 *
 * Used by the floating edge to trim the visible line (and place the endpoint
 * handles) exactly where the center-to-center line meets each node's perimeter.
 */
export function borderIntersection(rect, to) {
  const cx = rect.x + rect.w / 2
  const cy = rect.y + rect.h / 2
  const dx = to.x - cx
  const dy = to.y - cy

  // Degenerate: concentric rects — fall back to the top edge.
  if (Math.abs(dx) < 1e-6 && Math.abs(dy) < 1e-6) {
    return { x: cx, y: rect.y, side: 'top' }
  }

  const hw = rect.w / 2
  const hh = rect.h / 2

  // Scale the direction vector until it hits a vertical or horizontal edge,
  // whichever comes first.
  const tx = dx !== 0 ? hw / Math.abs(dx) : Infinity
  const ty = dy !== 0 ? hh / Math.abs(dy) : Infinity
  const t = Math.min(tx, ty)

  const x = cx + dx * t
  const y = cy + dy * t

  let side
  if (t === tx) side = dx > 0 ? 'right' : 'left'
  else side = dy > 0 ? 'bottom' : 'top'

  return { x, y, side }
}
