import { ref, computed } from 'vue'

const MAX_HISTORY = 100

const undoStack = ref([])
const redoStack = ref([])
let isApplying = false

function push(entry) {
  if (isApplying) return
  if (!entry || typeof entry.undo !== 'function' || typeof entry.redo !== 'function') {
    console.warn('useUndoManager: push() requires { label, undo, redo }', entry)
    return
  }
  undoStack.value.push(entry)
  redoStack.value = []
  if (undoStack.value.length > MAX_HISTORY) {
    undoStack.value.shift()
  }
}

async function undo() {
  if (!undoStack.value.length) return false
  const entry = undoStack.value.pop()
  isApplying = true
  try {
    await entry.undo()
    redoStack.value.push(entry)
  } catch (err) {
    console.error('useUndoManager: undo() threw, dropping entry', err)
  } finally {
    setTimeout(() => { isApplying = false }, 500)
  }
  return true
}

async function redo() {
  if (!redoStack.value.length) return false
  const entry = redoStack.value.pop()
  isApplying = true
  try {
    await entry.redo()
    undoStack.value.push(entry)
  } catch (err) {
    console.error('useUndoManager: redo() threw, dropping entry', err)
  } finally {
    setTimeout(() => { isApplying = false }, 500)
  }
  return true
}

function clear() {
  undoStack.value = []
  redoStack.value = []
}

const canUndo = computed(() => undoStack.value.length > 0)
const canRedo = computed(() => redoStack.value.length > 0)
const undoLabel = computed(() => undoStack.value[undoStack.value.length - 1]?.label || '')
const redoLabel = computed(() => redoStack.value[redoStack.value.length - 1]?.label || '')

export function useUndoManager() {
  return { push, undo, redo, clear, canUndo, canRedo, undoLabel, redoLabel }
}

export function isUndoRedoApplying() {
  return isApplying
}
