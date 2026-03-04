import { ref, computed } from 'vue'

export function useWhiteboardConnections(cards) {
  // === Persisted link state ===
  const nodeLinks = ref([])

  // === Border-hover connection state ===
  // Which card's border is the mouse currently over?
  const hoverCardId = ref(null)
  // Position of the tracking dot on the hovered card's border {x, y}
  const hoverDot = ref(null)

  // === Active drag state (after first click) ===
  // The source anchor point {cardId, x, y} - concretized on click
  const dragAnchor = ref(null)
  // Current mouse position in canvas coords (for rubber-band line)
  const mousePos = ref({ x: 0, y: 0 })
  // Target card hover dot during drag {cardId, x, y}
  const dragTargetDot = ref(null)

  // === Drop menu state ===
  const showDropMenu = ref(false)
  const dropMenuPos = ref({ x: 0, y: 0 })

  // === Flash animation state ===
  const flashingCards = ref(new Set())

  // Is a drag-to-connect in progress?
  const isDragging = computed(() => dragAnchor.value !== null)

  // Hovered link (for midpoint delete button on existing lines)
  const hoveredLinkId = ref(null)

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
      sourceAnchor: link.source_anchor || null,
      targetAnchor: link.target_anchor || null,
      relationshipType: link.relationship_type || null,
      label: link.label || null,
      color: link.color || '#1976d2'
    })).filter(l => l.sourceCardId !== null && l.targetCardId !== null)
  }

  function createLink(sourceCardId, targetCardId, sourceAnchor = null, targetAnchor = null, options = {}) {
    const exists = nodeLinks.value.some(
      l => (l.sourceCardId === sourceCardId && l.targetCardId === targetCardId) ||
           (l.sourceCardId === targetCardId && l.targetCardId === sourceCardId)
    )
    if (exists) return false

    nodeLinks.value.push({
      id: `local-${Date.now()}`,
      sourceCardId,
      targetCardId,
      sourceAnchor,
      targetAnchor,
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

  // ─── Border geometry: find nearest point on card border to mouse ───

  function getCardRect(card, cardElements) {
    const el = cardElements?.[card.id]
    // Use actual DOM dimensions when available; fallback to sensible defaults
    // Collapsed pills are ~220-260px wide x ~52px tall (not the old 160x160 squares)
    const w = el ? el.offsetWidth : (card.collapsed ? 220 : (card.width || 300))
    const h = el ? el.offsetHeight : (card.collapsed ? 52 : 200)
    return { x: card.x, y: card.y, w, h }
  }

  /**
   * Given a card rect and a mouse position, find the closest point
   * on the card's border (perimeter) to the mouse.
   * Returns {x, y, side} where side is 'top'|'right'|'bottom'|'left'.
   */
  function nearestBorderPoint(rect, mx, my) {
    const { x, y, w, h } = rect
    // Clamp mouse coords to card edges
    const cx = Math.max(x, Math.min(x + w, mx))
    const cy = Math.max(y, Math.min(y + h, my))

    // Distance to each edge from the clamped point
    const dTop = Math.abs(cy - y)
    const dBottom = Math.abs(cy - (y + h))
    const dLeft = Math.abs(cx - x)
    const dRight = Math.abs(cx - (x + w))

    const minD = Math.min(dTop, dBottom, dLeft, dRight)

    if (minD === dTop) return { x: cx, y: y, side: 'top' }
    if (minD === dBottom) return { x: cx, y: y + h, side: 'bottom' }
    if (minD === dLeft) return { x: x, y: cy, side: 'left' }
    return { x: x + w, y: cy, side: 'right' }
  }

  /**
   * Is the mouse within the card's "border zone"?
   * The border is 9px thick. The active zone extends:
   *  - inward by the border width (9px)
   *  - outward by 50% of the border width (14px, rounded from 13.5)
   * Total detection band: ~23px straddling the card edge.
   */
  function isNearBorder(rect, mx, my) {
    // The CSS outline is 9px thick starting 2px outside the card edge (outline-offset: 2px)
    // So the visible border covers 2px to 11px outside the card edge.
    // We extend detection well beyond that for comfort.
    const outerExtend = 22  // 22px outside the card edge (generous beyond visible border)
    const innerExtend = 12  // 12px inside the card edge (covers card edge clicks)
    const { x, y, w, h } = rect
    // Must be within outer extend of the card edge
    const inOuter = mx >= x - outerExtend && mx <= x + w + outerExtend &&
                    my >= y - outerExtend && my <= y + h + outerExtend
    // Must NOT be deep inside (further than innerExtend from all edges)
    const inInner = mx > x + innerExtend && mx < x + w - innerExtend &&
                    my > y + innerExtend && my < y + h - innerExtend
    return inOuter && !inInner
  }

  /**
   * Is the mouse anywhere over the card (with a small buffer)?
   * Used during drag — the entire card surface is a valid drop target.
   */
  function isOverCard(rect, mx, my) {
    const buffer = 8 // small buffer around the card for comfort
    const { x, y, w, h } = rect
    return mx >= x - buffer && mx <= x + w + buffer &&
           my >= y - buffer && my <= y + h + buffer
  }

  // ─── Mouse tracking on canvas ───

  function handleMouseMove(canvasX, canvasY, cardElements) {
    mousePos.value = { x: canvasX, y: canvasY }

    let foundHover = false
    for (const card of cards.value) {
      const rect = getCardRect(card, cardElements)
      const isParent = card.type === 'parent'
      // Parent nodes: center point instead of border point
      const centerX = rect.x + rect.w / 2
      const centerY = rect.y + rect.h / 2

      if (isDragging.value) {
        // During drag: the ENTIRE card is a drop target.
        if (card.id !== dragAnchor.value.cardId && isOverCard(rect, canvasX, canvasY)) {
          if (isParent) {
            // Parent: dot locks to center
            dragTargetDot.value = { cardId: card.id, x: centerX, y: centerY, side: 'center' }
          } else {
            // Others: dot clings to nearest border point
            const bp = nearestBorderPoint(rect, canvasX, canvasY)
            dragTargetDot.value = { cardId: card.id, x: bp.x, y: bp.y, side: bp.side }
          }
          foundHover = true
          break
        }
      } else {
        // Not dragging: show hover state
        if (isParent) {
          // Parent: entire card area triggers hover, dot at center
          if (isOverCard(rect, canvasX, canvasY)) {
            hoverCardId.value = card.id
            hoverDot.value = { x: centerX, y: centerY, side: 'center' }
            foundHover = true
            break
          }
        } else {
          // Others: only near the border
          if (isNearBorder(rect, canvasX, canvasY)) {
            const bp = nearestBorderPoint(rect, canvasX, canvasY)
            hoverCardId.value = card.id
            hoverDot.value = { x: bp.x, y: bp.y, side: bp.side }
            foundHover = true
            break
          }
        }
      }
    }

    if (!foundHover) {
      if (isDragging.value) {
        dragTargetDot.value = null
      } else {
        hoverCardId.value = null
        hoverDot.value = null
      }
    }
  }

  // ─── Click: concretize anchor or complete connection ───

  function handleBorderClick() {
    if (!isDragging.value && hoverCardId.value && hoverDot.value) {
      // First click: concretize the anchor
      dragAnchor.value = {
        cardId: hoverCardId.value,
        x: hoverDot.value.x,
        y: hoverDot.value.y,
        side: hoverDot.value.side
      }
      // Clear hover state (now in drag mode)
      hoverCardId.value = null
      hoverDot.value = null
      return 'anchor-set'
    }

    if (isDragging.value && dragTargetDot.value) {
      // Second click on a target card border: complete the connection
      const sourceAnchor = { x: dragAnchor.value.x, y: dragAnchor.value.y, side: dragAnchor.value.side }
      const targetAnchor = { x: dragTargetDot.value.x, y: dragTargetDot.value.y, side: dragTargetDot.value.side }

      createLink(
        dragAnchor.value.cardId,
        dragTargetDot.value.cardId,
        sourceAnchor,
        targetAnchor
      )

      // Flash both cards
      triggerFlash(dragAnchor.value.cardId)
      triggerFlash(dragTargetDot.value.cardId)

      // Reset
      dragAnchor.value = null
      dragTargetDot.value = null
      return 'connection-made'
    }

    if (isDragging.value && !dragTargetDot.value) {
      // Clicked in empty space while dragging -> show drop menu
      dropMenuPos.value = { x: mousePos.value.x, y: mousePos.value.y }
      showDropMenu.value = true
      return 'drop-menu'
    }

    return null
  }

  // Force-complete a connection to a target card (bypasses border detection zone)
  // Used when clicking on a card during drag — computes border point at click time
  function forceCompleteConnection(targetCardId, cardElements) {
    if (!dragAnchor.value || targetCardId === dragAnchor.value.cardId) return false

    const targetCard = cards.value.find(c => c.id === targetCardId)
    if (!targetCard) return false

    const targetRect = getCardRect(targetCard, cardElements)
    const targetAnchor = nearestBorderPoint(targetRect, dragAnchor.value.x, dragAnchor.value.y)
    const sourceAnchor = { x: dragAnchor.value.x, y: dragAnchor.value.y, side: dragAnchor.value.side }

    createLink(dragAnchor.value.cardId, targetCardId, sourceAnchor, targetAnchor)
    triggerFlash(dragAnchor.value.cardId)
    triggerFlash(targetCardId)
    cancelDrag()
    return true
  }

  // Complete connection after spawning a new card from the drop menu
  function completeDropConnection(newCardId) {
    if (!dragAnchor.value) return
    const sourceAnchor = { x: dragAnchor.value.x, y: dragAnchor.value.y, side: dragAnchor.value.side }
    createLink(dragAnchor.value.cardId, newCardId, sourceAnchor, null)
    triggerFlash(dragAnchor.value.cardId)
    triggerFlash(newCardId)
    cancelDrag()
  }

  // ─── Cancel ───

  function cancelDrag() {
    dragAnchor.value = null
    dragTargetDot.value = null
    showDropMenu.value = false
  }

  // ─── Flash animation ───

  function triggerFlash(cardId) {
    flashingCards.value.add(cardId)
    setTimeout(() => {
      flashingCards.value.delete(cardId)
      // Force reactivity update
      flashingCards.value = new Set(flashingCards.value)
    }, 600)
    // Force reactivity
    flashingCards.value = new Set(flashingCards.value)
  }

  // ─── Line coordinates for rendered links ───

  function getLineCoords(link, cardElements) {
    const sourceCard = cards.value.find(c => c.id === link.sourceCardId)
    const targetCard = cards.value.find(c => c.id === link.targetCardId)
    if (!sourceCard || !targetCard) return null

    const sourceRect = getCardRect(sourceCard, cardElements)
    const targetRect = getCardRect(targetCard, cardElements)

    const sourceIsParent = sourceCard.type === 'parent'
    const targetIsParent = targetCard.type === 'parent'

    // Centers of both cards
    const sCenter = { x: sourceRect.x + sourceRect.w / 2, y: sourceRect.y + sourceRect.h / 2 }
    const tCenter = { x: targetRect.x + targetRect.w / 2, y: targetRect.y + targetRect.h / 2 }

    // Parent nodes: anchor at center (hub-and-spoke). Others: nearest border point.
    let x1, y1, x2, y2
    if (sourceIsParent) {
      x1 = sCenter.x
      y1 = sCenter.y
    } else {
      const bp = nearestBorderPoint(sourceRect, tCenter.x, tCenter.y)
      x1 = bp.x
      y1 = bp.y
    }

    if (targetIsParent) {
      x2 = tCenter.x
      y2 = tCenter.y
    } else {
      const bp = nearestBorderPoint(targetRect, sCenter.x, sCenter.y)
      x2 = bp.x
      y2 = bp.y
    }

    const mx = (x1 + x2) / 2
    const my = (y1 + y2) / 2

    // Straight line path
    const path = `M ${x1} ${y1} L ${x2} ${y2}`

    return { x1, y1, x2, y2, mx, my, path }
  }

  // ─── Rubber-band line from anchor to mouse ───

  const rubberBandLine = computed(() => {
    if (!dragAnchor.value) return null
    const x1 = dragAnchor.value.x
    const y1 = dragAnchor.value.y
    // If hovering a target card, snap to target dot
    const x2 = dragTargetDot.value ? dragTargetDot.value.x : mousePos.value.x
    const y2 = dragTargetDot.value ? dragTargetDot.value.y : mousePos.value.y
    return { x1, y1, x2, y2 }
  })

  // ─── Disconnect one end of an existing link ───
  // Detaches one endpoint and enters drag mode from the opposite end
  function disconnectEnd(linkId, whichEnd, cardElements) {
    const link = nodeLinks.value.find(l => l.id === linkId)
    if (!link) return

    // The end that STAYS connected becomes the new drag anchor
    const keepCardId = whichEnd === 'source' ? link.targetCardId : link.sourceCardId
    const keepCard = cards.value.find(c => c.id === keepCardId)
    if (!keepCard) return

    // Compute border point on the kept card facing toward the detached card
    const detachCardId = whichEnd === 'source' ? link.sourceCardId : link.targetCardId
    const detachCard = cards.value.find(c => c.id === detachCardId)
    const keepRect = getCardRect(keepCard, cardElements)
    let anchorPoint
    if (detachCard) {
      const detachRect = getCardRect(detachCard, cardElements)
      const detachCenter = { x: detachRect.x + detachRect.w / 2, y: detachRect.y + detachRect.h / 2 }
      anchorPoint = nearestBorderPoint(keepRect, detachCenter.x, detachCenter.y)
    } else {
      const keepCenter = { x: keepRect.x + keepRect.w / 2, y: keepRect.y }
      anchorPoint = { x: keepCenter.x, y: keepRect.y, side: 'top' }
    }

    // Delete the old link
    nodeLinks.value = nodeLinks.value.filter(l => l.id !== linkId)

    // Enter drag mode from the kept card's border point
    dragAnchor.value = {
      cardId: keepCardId,
      x: anchorPoint.x,
      y: anchorPoint.y,
      side: anchorPoint.side
    }
    dragTargetDot.value = null
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
    // Link data
    nodeLinks,
    loadLinks,
    createLink,
    deleteLink,
    deleteLinksForCard,
    getLinksForSave,
    getLineCoords,

    // Border hover
    hoverCardId,
    hoverDot,

    // Drag-to-connect
    isDragging,
    dragAnchor,
    dragTargetDot,
    mousePos,
    rubberBandLine,
    handleMouseMove,
    handleBorderClick,
    cancelDrag,

    // Drop menu
    showDropMenu,
    dropMenuPos,
    completeDropConnection,
    forceCompleteConnection,

    // Flash
    flashingCards,

    // Existing link hover
    hoveredLinkId,

    // Disconnect
    disconnectEnd
  }
}
