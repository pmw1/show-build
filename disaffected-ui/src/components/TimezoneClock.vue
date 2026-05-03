<template>
  <div ref="rootRef" class="clock-display" :class="{ clickable: editable }" @click="editable && toggleDropdown()">
    <div class="label-primary">{{ editable ? activeTzShortLabel : label }}</div>
    <div class="time">{{ currentTime }}</div>
    <div class="label-secondary" v-if="!editable">{{ timezoneLabel }}</div>
    <div class="label-secondary tz-clickable" v-else>
      {{ dateLabel }}
      <span class="tz-caret">&#9662;</span>
    </div>

    <!-- Dropdown panel — teleported to <body> so it escapes the app-bar
         stacking context and renders above everything else. -->
    <Teleport to="body">
      <div
        v-if="showDropdown"
        class="tz-dropdown"
        :style="dropdownStyle"
        @click.stop
      >
        <!-- Timezone search -->
        <div class="tz-search-row">
          <input
            ref="tzSearchRef"
            v-model="tzSearch"
            class="tz-search-input"
            placeholder="Search timezones..."
            spellcheck="false"
            @keydown.escape="showDropdown = false"
          />
        </div>

        <!-- Common timezones -->
        <div class="tz-section-label">TIMEZONES</div>
        <div class="tz-list">
          <div
            v-for="tz in filteredTimezones"
            :key="tz.value"
            class="tz-item"
            :class="{ active: tz.value === activeTz }"
            @click="selectTimezone(tz.value)"
          >
            <span class="tz-item-label">{{ tz.label }}</span>
            <span class="tz-item-time">{{ tz.currentTime }}</span>
          </div>
        </div>

        <!-- Guest timezones (if provided) -->
        <template v-if="guests && guests.length">
          <div class="tz-section-label" style="margin-top: 4px;">EPISODE GUESTS</div>
          <div class="tz-list">
            <div
              v-for="guest in guests"
              :key="guest.name"
              class="tz-item guest-item"
              @click="guest.timezone && selectTimezone(guest.timezone)"
            >
              <span class="tz-item-label">{{ guest.name }}</span>
              <span class="tz-item-time" v-if="guest.timezone">{{ guest.timezone.replace(/_/g, ' ') }}</span>
              <span class="tz-item-time" v-else style="color: #aaa;">No TZ set</span>
            </div>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  label: { type: String, default: 'UTC' },
  timezone: { type: String, default: 'UTC' },
  editable: { type: Boolean, default: false },
  guests: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:timezone'])

const currentTime = ref('--:--:--')
const timezoneLabel = ref('')
const activeTz = ref('UTC')
const showDropdown = ref(false)
const tzSearch = ref('')
const tzSearchRef = ref(null)
const rootRef = ref(null)
const dropdownPos = ref({ top: 0, left: 0, width: 260 })  // updated when dropdown opens
let clockInterval = null

const dropdownStyle = computed(() => ({
  top: `${dropdownPos.value.top}px`,
  left: `${dropdownPos.value.left}px`,
  minWidth: `${dropdownPos.value.width}px`
}))

function recomputeDropdownPosition() {
  const el = rootRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const minWidth = Math.max(rect.width, 260)
  // Default: open below the activator, left-aligned. If there's no room
  // below, open above instead so the menu doesn't run off-screen.
  const dropdownEstimatedHeight = 360
  const spaceBelow = window.innerHeight - rect.bottom
  const top = (spaceBelow < dropdownEstimatedHeight && rect.top > dropdownEstimatedHeight)
    ? Math.max(8, rect.top - dropdownEstimatedHeight)
    : rect.bottom
  // Keep it within the viewport horizontally.
  const left = Math.min(Math.max(8, rect.left), window.innerWidth - minWidth - 8)
  dropdownPos.value = { top, left, width: minWidth }
}

const commonTimezones = [
  { label: 'US Eastern (New York)', value: 'America/New_York' },
  { label: 'US Central (Chicago)', value: 'America/Chicago' },
  { label: 'US Mountain (Denver)', value: 'America/Denver' },
  { label: 'US Pacific (Los Angeles)', value: 'America/Los_Angeles' },
  { label: 'UTC / GMT', value: 'UTC' },
  { label: 'UK (London)', value: 'Europe/London' },
  { label: 'Central Europe (Paris)', value: 'Europe/Paris' },
  { label: 'Eastern Europe (Istanbul)', value: 'Europe/Istanbul' },
  { label: 'India (Kolkata)', value: 'Asia/Kolkata' },
  { label: 'China (Shanghai)', value: 'Asia/Shanghai' },
  { label: 'Japan (Tokyo)', value: 'Asia/Tokyo' },
  { label: 'Korea (Seoul)', value: 'Asia/Seoul' },
  { label: 'Australia East (Sydney)', value: 'Australia/Sydney' },
  { label: 'New Zealand (Auckland)', value: 'Pacific/Auckland' },
  { label: 'Hawaii', value: 'Pacific/Honolulu' },
  { label: 'Alaska', value: 'America/Anchorage' },
  { label: 'Brazil (Sao Paulo)', value: 'America/Sao_Paulo' },
  { label: 'Dubai', value: 'Asia/Dubai' },
  { label: 'Singapore', value: 'Asia/Singapore' },
  { label: 'Moscow', value: 'Europe/Moscow' }
]

const getTimeForTz = (tz) => {
  try {
    return new Date().toLocaleTimeString('en-US', {
      hour12: false, hour: '2-digit', minute: '2-digit', timeZone: tz
    })
  } catch {
    return '??:??'
  }
}

const filteredTimezones = computed(() => {
  const search = tzSearch.value.toLowerCase()
  const list = commonTimezones.filter(tz =>
    !search || tz.label.toLowerCase().includes(search) || tz.value.toLowerCase().includes(search)
  )
  return list.map(tz => ({
    ...tz,
    currentTime: getTimeForTz(tz.value)
  }))
})

const activeTzShortLabel = computed(() => {
  // Show a short label like "London" or "Tokyo" from the timezone
  const parts = activeTz.value.split('/')
  const city = parts[parts.length - 1] || activeTz.value
  return city.replace(/_/g, ' ')
})

const dateLabel = computed(() => {
  try {
    const now = new Date()
    return now.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: activeTz.value
    })
  } catch {
    return activeTz.value.replace(/_/g, ' ')
  }
})

const toggleDropdown = async () => {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value) {
    tzSearch.value = ''
    recomputeDropdownPosition()
    await nextTick()
    if (tzSearchRef.value) tzSearchRef.value.focus()
  }
}

const selectTimezone = (tz) => {
  activeTz.value = tz
  emit('update:timezone', tz)
  showDropdown.value = false
  updateTime()
}

const updateTime = () => {
  try {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: activeTz.value
    })
    if (!props.editable) {
      timezoneLabel.value = now.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: activeTz.value
      })
    }
  } catch {
    currentTime.value = 'INVALID TZ'
  }
}

// Close dropdown on outside click. Use the local rootRef for the activator
// so clicks on OTHER editable clocks correctly close this one.
const handleOutsideClick = (e) => {
  if (!showDropdown.value) return
  const dropdownEl = document.querySelector('.tz-dropdown')
  const activator = rootRef.value
  if (dropdownEl && dropdownEl.contains(e.target)) return
  if (activator && activator.contains(e.target)) return
  showDropdown.value = false
}

watch(() => props.timezone, (newTz) => {
  activeTz.value = newTz
  updateTime()
}, { immediate: true })

function handleViewportChange() {
  if (showDropdown.value) recomputeDropdownPosition()
}

onMounted(() => {
  updateTime()
  clockInterval = setInterval(updateTime, 1000)
  document.addEventListener('mousedown', handleOutsideClick)
  window.addEventListener('resize', handleViewportChange)
  window.addEventListener('scroll', handleViewportChange, true)
})

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval)
  document.removeEventListener('mousedown', handleOutsideClick)
  window.removeEventListener('resize', handleViewportChange)
  window.removeEventListener('scroll', handleViewportChange, true)
})
</script>

<style scoped>
.clock-display {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.05);
  padding: 0;
  border-radius: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  min-width: 140px;
  overflow: visible;
  height: 100%;
  justify-content: flex-start;
  position: relative;
}

.clock-display.clickable {
  cursor: pointer;
}

.clock-display.clickable:hover {
  background: rgba(0, 0, 0, 0.08);
}

.label-primary {
  font-size: 0.56rem;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  text-align: center;
  margin-bottom: 0;
  background-color: #1976d2;
  padding: 2px 10px;
  border-radius: 0;
}

.time {
  font-family: 'Courier New', Courier, monospace;
  font-size: 1.6rem;
  font-weight: 900;
  color: #888;
  letter-spacing: 2.4px;
  text-align: center;
  align-self: center;
  width: 100%;
  margin-bottom: 0;
  padding: 2px 10px 0 10px;
}

.label-secondary {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.56rem;
  color: rgba(0, 0, 0, 0.7);
  font-weight: bold;
  text-align: center;
  text-transform: uppercase;
  padding: 0 8px 1px 8px;
  margin-top: -6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tz-clickable {
  cursor: pointer;
  font-size: 0.5rem;
}

.tz-caret {
  font-size: 0.5rem;
  margin-left: 2px;
  opacity: 0.5;
}

/* Dropdown panel styles live in the non-scoped block below because
   the dropdown is teleported to <body> and scoped styles don't follow it. */
</style>

<style>
/* Non-scoped: targets the teleported .tz-dropdown that lives directly under <body>. */
.tz-dropdown {
  position: fixed;
  max-height: 360px;
  overflow-y: auto;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.15);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  /* Vuetify's overlay layer caps around 2400; menus sit at 2002. Sit above all. */
  z-index: 99999;
  border-radius: 0 0 4px 4px;
}

.tz-dropdown .tz-search-row {
  padding: 6px 8px;
  border-bottom: 1px solid #eee;
}

.tz-dropdown .tz-search-input {
  width: 100%;
  font-size: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 3px;
  padding: 4px 8px;
  outline: none;
}

.tz-dropdown .tz-search-input:focus {
  border-color: #1976d2;
}

.tz-dropdown .tz-section-label {
  font-size: 0.6rem;
  font-weight: bold;
  color: #888;
  padding: 4px 10px 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: #f5f5f5;
}

.tz-dropdown .tz-list {
  max-height: 240px;
  overflow-y: auto;
}

.tz-dropdown .tz-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  cursor: pointer;
  font-size: 0.72rem;
  border-bottom: 1px solid #f5f5f5;
}

.tz-dropdown .tz-item:hover {
  background: #e3f2fd;
}

.tz-dropdown .tz-item.active {
  background: #e3f2fd;
  font-weight: bold;
}

.tz-dropdown .tz-item-label {
  color: #333;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 8px;
}

.tz-dropdown .tz-item-time {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.7rem;
  color: #666;
  font-weight: bold;
  white-space: nowrap;
}

.tz-dropdown .guest-item .tz-item-label {
  color: #1976d2;
}
</style>
