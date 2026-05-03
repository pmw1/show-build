<template>
  <v-menu :close-on-content-click="false" location="end">
    <template #activator="{ props: activatorProps }">
      <button
        v-bind="activatorProps"
        type="button"
        class="overridable-dot"
        :class="dotClass"
        :title="dotTitle"
        :aria-label="dotTitle"
      />
    </template>

    <v-card class="overridable-popover pa-3" min-width="260" max-width="320">
      <div class="d-flex align-center mb-2">
        <span class="overridable-dot" :class="dotClass" />
        <span class="ms-2 text-subtitle-2">{{ stateLabel }}</span>
      </div>

      <div class="text-caption text-grey-darken-1 mb-3">
        Setting key:
        <code class="text-caption pref-key-code">{{ prefKey }}</code>
      </div>

      <!-- State-specific actions -->
      <div v-if="overridable && !hasUserValue" class="popover-section">
        <p class="text-body-2 mb-2">
          You haven't personalized this setting. Switch the field below
          and your change will apply only to your account.
        </p>
        <v-alert v-if="reason" density="compact" type="info" variant="tonal" class="text-caption">
          {{ reason }}
        </v-alert>
      </div>

      <div v-else-if="overridable && hasUserValue" class="popover-section">
        <p class="text-body-2 mb-2">
          You have a personal override for this setting. Reset to fall
          back to the global value.
        </p>
        <v-btn
          size="small"
          variant="tonal"
          color="primary"
          prepend-icon="mdi-restore"
          block
          @click="onResetToGlobal"
          :loading="busy"
        >
          Reset to global
        </v-btn>
      </div>

      <div v-else class="popover-section">
        <p class="text-body-2 mb-2">
          This setting can't be personalized — it stays the same for everyone.
        </p>
        <v-alert v-if="reason" density="compact" type="warning" variant="tonal" class="text-caption">
          {{ reason }}
        </v-alert>
      </div>

      <!-- Admin controls -->
      <v-divider v-if="isAdmin" class="my-3" />
      <div v-if="isAdmin" class="popover-section">
        <div class="text-caption text-grey-darken-1 mb-2">Admin actions</div>

        <!-- Quick action: write the current field value as the global default -->
        <v-btn
          v-if="hasCurrentValue"
          size="small"
          variant="tonal"
          color="error"
          prepend-icon="mdi-earth"
          block
          class="mb-2"
          @click="onSaveAsGlobal"
          :loading="busy"
        >
          Save current value as global default
        </v-btn>

        <v-switch
          :model-value="overridable"
          @update:model-value="onToggleOverridable"
          color="primary"
          density="compact"
          hide-details
          :label="overridable ? 'Users may personalize' : 'Users may NOT personalize'"
          :loading="busy"
        />
      </div>
    </v-card>
  </v-menu>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useUserPrefs } from '@/composables/useUserPrefs'
import { useOverridableSettings } from '@/composables/useOverridableSettings'

const props = defineProps({
  prefKey: { type: String, required: true },
  // Optional: pass the field's CURRENT value so the admin "Save as global
  // default" button knows what to write. When omitted, that button is
  // hidden (we have no value to save).
  currentValue: { type: null, default: undefined },
  // Optional: a custom setter for the admin "Save as global default"
  // button. Useful when the field's state is nested inside a larger
  // pref blob (e.g. interface.settings.*) rather than at this prefKey
  // directly. Receives (value) and is responsible for writing it
  // globally however makes sense for that field.
  globalSetter: { type: Function, default: null }
})

const userPrefs = useUserPrefs()
const overrides = useOverridableSettings()

const busy = ref(false)

const overridable = computed(() => overrides.isOverridable(props.prefKey))
const hasUserValue = computed(() => overrides.hasOverride(props.prefKey))
const reason = computed(() => overrides.reasonFor(props.prefKey))

const isAdmin = computed(() => {
  // Permissive admin detection — falls back closed at the API layer anyway.
  try {
    const u = JSON.parse(localStorage.getItem('user-data') || '{}')
    if (u.is_admin || u.is_superuser) return true
    if (typeof u.role === 'string' && u.role.toLowerCase().includes('admin')) return true
    if (Array.isArray(u.roles) && u.roles.some(r => String(r).toLowerCase().includes('admin'))) return true
    if (Array.isArray(u.permissions) && (u.permissions.includes('admin.*') || u.permissions.includes('*'))) return true
  } catch { /* noop */ }
  return false
})

const dotClass = computed(() => {
  if (!overridable.value) return 'dot-forbidden'
  return hasUserValue.value ? 'dot-overridden' : 'dot-overridable'
})

const stateLabel = computed(() => {
  if (!overridable.value) return 'Not personalizable'
  return hasUserValue.value ? 'Personal override active' : 'Available to personalize'
})

const dotTitle = computed(() => {
  return `${stateLabel.value} — click for details`
})

async function onResetToGlobal() {
  busy.value = true
  try {
    await userPrefs.remove(props.prefKey)
  } finally {
    busy.value = false
  }
}

async function onToggleOverridable(next) {
  busy.value = true
  try {
    await overrides.setOverridable(props.prefKey, !!next)
  } finally {
    busy.value = false
  }
}

const hasCurrentValue = computed(() => props.currentValue !== undefined)

async function onSaveAsGlobal() {
  if (!hasCurrentValue.value) return
  busy.value = true
  try {
    if (typeof props.globalSetter === 'function') {
      // Custom path: the field lives inside a larger blob.
      await props.globalSetter(props.currentValue)
    } else {
      await userPrefs.set(props.prefKey, props.currentValue, { scope: 'global' })
    }
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.overridable-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: none;
  padding: 0;
  cursor: pointer;
  vertical-align: middle;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.overridable-dot:hover {
  transform: scale(1.25);
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.06);
}

.dot-overridable {
  background: #fb8c00;            /* orange — can personalize */
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.12);
}

.dot-overridden {
  background: #43a047;            /* green — currently personalized */
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.12);
}

.dot-forbidden {
  background: #e53935;            /* red — admin-disallowed */
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.12);
}

.overridable-popover {
  background: #fff;
}

.popover-section {
  margin-top: 4px;
}

.pref-key-code {
  background: rgba(0, 0, 0, 0.04);
  padding: 1px 6px;
  border-radius: 3px;
  font-family: 'Roboto Mono', monospace;
}
</style>
