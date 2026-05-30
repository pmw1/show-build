<template>
  <v-app>
    <!-- Top App Bar (hidden on iPad scroll view) -->
    <v-app-bar
      v-if="isAuthenticated && $route.name !== 'ipad-scroll'"
      color="surface"
      elevation="1"
      style="padding-top: 5px; padding-bottom: 5px;"
    >
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
      ></v-app-bar-nav-icon>

      <v-app-bar-title class="text-primary font-weight-bold app-title-compact" style="margin-right: 0.25em;">
        Show Builder
      </v-app-bar-title>

      <!-- Status Clock (Today's Date) -->
      <StatusClock v-if="isAuthenticated" style="margin-left: -20px;" />

      <!-- UTC Clock -->
      <TimezoneClock v-if="isAuthenticated" label="UTC" timezone="UTC" class="ms-1" />

      <!-- Custom Timezone Clock -->
      <TimezoneClock v-if="isAuthenticated" label="CUSTOM" :timezone="customClockTz" editable @update:timezone="customClockTz = $event" class="ms-1" />

      <!-- Live Clock (Countdown) -->
      <LiveClock v-if="isAuthenticated" class="ms-1" />

      <!-- Episode Selector -->
      <v-select
        v-if="isAuthenticated"
        v-model="selectedEpisode"
        :items="episodes"
        item-title="display"
        item-value="episode_number"
        label="Episode"
        variant="outlined"
        hide-details
        color="primary"
        bg-color="rgba(25, 118, 210, 0.05)"
        style="max-width: 293px; min-width: 293px; height: 28px;"
        class="ms-3 episode-selector"
        @update:model-value="loadEpisode"
      >
        <template v-slot:prepend-inner>
          <v-icon size="small" color="primary">mdi-television-play</v-icon>
        </template>
      </v-select>

      <v-spacer></v-spacer>

      <!-- Authentication Status -->
      <div v-if="isAuthenticated" class="d-flex align-center user-info-section">
        <!-- User name -->
        <div class="me-3 d-none d-sm-flex align-center">
          <span class="user-name-text text-primary">{{ userFullName }}</span>
          <!-- Access Level Badge -->
          <v-chip
            v-if="userAccessLevel"
            :color="accessLevelColor"
            size="x-small"
            class="ms-2 text-uppercase font-weight-bold"
            variant="flat"
          >
            {{ userAccessLevel }}
          </v-chip>
        </div>

        <!-- LLM Notification Center -->
        <NotificationCenter />

        <!-- Inter-user messaging + presence -->
        <PresenceMenu @compose-to="onComposeTo" />
        <MessagesPanel ref="messagesPanelRef" />

        <!-- Job Monitor (Admin Only) -->
        <JobMonitor v-if="userAccessLevel === 'admin'" class="ms-2" />

        <!-- User Menu -->
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn
              icon
              v-bind="props"
              size="small"
            >
              <v-avatar size="28">
                <v-img
                  v-if="currentUser.profile_picture"
                  :src="currentUser.profile_picture"
                  :alt="userFullName"
                />
                <v-icon color="primary" size="28">mdi-account-circle</v-icon>
              </v-avatar>
            </v-btn>
          </template>
          <v-list>
            <v-list-item
              v-for="(item, i) in userMenuItems"
              :key="i"
              :prepend-icon="item.icon"
              :title="item.title"
              @click="handleUserMenuItem(item)"
            >
            </v-list-item>
          </v-list>
        </v-menu>
      </div>

      <!-- Login Button (when not authenticated) -->
      <v-btn
        v-else
        color="primary"
        variant="outlined"
        prepend-icon="mdi-login"
        @click="showLoginModal = true"
      >
        Login
      </v-btn>
    </v-app-bar>

    <!-- Navigation Drawer (hidden on iPad scroll view) -->
    <v-navigation-drawer
      v-if="isAuthenticated && $route.name !== 'ipad-scroll'"
      v-model="drawer"
      permanent
      width="320"
    >
      <v-list density="compact" nav v-model:opened="openGroups">
        <!-- Top level items -->
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard">
          <v-list-item-title>Dashboard</v-list-item-title>
        </v-list-item>

        <!-- ShowFactory Section -->
        <v-list-group value="scriptfactory">
          <template v-slot:activator="{ props }">
            <v-list-item v-bind="props" prepend-icon="mdi-script-text">
              <v-list-item-title>ShowFactory</v-list-item-title>
            </v-list-item>
          </template>
          <v-list-item to="/episodes" prepend-icon="mdi-television-classic">
            <v-list-item-title>Episodes</v-list-item-title>
          </v-list-item>
          <v-list-item to="/content-editor" prepend-icon="mdi-script-text-outline">
            <v-list-item-title>Content Editor</v-list-item-title>
          </v-list-item>
          <v-list-item to="/stack" prepend-icon="mdi-playlist-edit">
            <v-list-item-title>Stack Manager</v-list-item-title>
          </v-list-item>
          <v-list-item to="/assets" prepend-icon="mdi-folder">
            <v-list-item-title>Asset Pool</v-list-item-title>
          </v-list-item>
          <v-list-item to="/templates" prepend-icon="mdi-file-document">
            <v-list-item-title>Templates</v-list-item-title>
          </v-list-item>
          <v-list-item to="/item-types" prepend-icon="mdi-format-list-bulleted-type">
            <v-list-item-title>Item Types</v-list-item-title>
          </v-list-item>
          <v-list-item to="/reusables-studio" prepend-icon="mdi-content-copy">
            <v-list-item-title>Reusables Studio</v-list-item-title>
          </v-list-item>

          <!-- Unmanaged Data submenu within ShowFactory (admin-only) -->
          <v-list-group v-if="isAdmin" value="unmanaged-data" subgroup>
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" prepend-icon="mdi-database-alert">
                <v-list-item-title>Unmanaged Data</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item to="/unmanaged-data" prepend-icon="mdi-record-rec">
              <v-list-item-title>Showtime Data</v-list-item-title>
            </v-list-item>
          </v-list-group>

          <!-- Preproduction submenu within ShowFactory -->
          <v-list-group value="preproduction" subgroup>
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" prepend-icon="mdi-lightbulb-on">
                <v-list-item-title>Preproduction</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item to="/whiteboard" prepend-icon="mdi-notebook-edit">
              <v-list-item-title>Whiteboard</v-list-item-title>
            </v-list-item>
            <v-list-item to="/generator" prepend-icon="mdi-creation">
              <v-list-item-title>Generator</v-list-item-title>
            </v-list-item>
            <v-list-item to="/voice-meeting" prepend-icon="mdi-microphone">
              <v-list-item-title>Production Meeting</v-list-item-title>
            </v-list-item>
          </v-list-group>
        </v-list-group>

        <!-- MediaFactory Section (conditional based on group membership or admin) -->
        <v-list-item
          v-if="isAdmin || userGroups.some(g => g.slug === 'mediafactory')"
          to="/mediafactory"
          prepend-icon="mdi-factory"
        >
          <v-list-item-title>MediaFactory</v-list-item-title>
        </v-list-item>

        <!-- MetaFactory Section (conditional based on group membership or admin) -->
        <v-list-item
          v-if="isAdmin || userGroups.some(g => g.slug === 'metafactory')"
          to="/metafactory"
          prepend-icon="mdi-database-cog"
        >
          <v-list-item-title>MetaFactory</v-list-item-title>
        </v-list-item>

        <!-- MoneyFactory Section -->
        <v-list-item to="/moneyfactory" prepend-icon="mdi-cash-multiple">
          <v-list-item-title>MoneyFactory</v-list-item-title>
        </v-list-item>

        <!-- Other items -->
        <v-list-item to="/tools" prepend-icon="mdi-toolbox">
          <v-list-item-title>Tools</v-list-item-title>
        </v-list-item>
        <v-list-item to="/organization" prepend-icon="mdi-domain">
          <v-list-item-title>Organization</v-list-item-title>
        </v-list-item>
        <v-list-item
          to="/settings"
          prepend-icon="mdi-cog"
          @click="navigateToSettings"
        >
          <v-list-item-title>Settings</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content Area -->
    <v-main>
      <v-container fluid class="pa-0">
        <router-view :key="$route.fullPath" />
      </v-container>
    </v-main>

    <!-- Login Modal -->
    <LoginModal
      v-model="showLoginModal"
      @login-success="handleLoginSuccess"
    />

    <!-- Global Keyboard Shortcuts Help (triggered by ? or F1) -->
    <KeyboardShortcutsModal v-model="showShortcutsModal" />

    <!-- Urgent Flash Overlay -->
    <UrgentFlash ref="urgentFlash" />

    <!-- Standard Notification -->
    <StandardNotification ref="standardNotification" />

    <!-- New-message toast — fires when the inbox poll finds an unread
         message we hadn't already seen this session. Click "Open" to
         jump straight into MessagesPanel scoped to the sender. -->
    <v-snackbar
      v-model="newMessageToastOpen"
      :timeout="6000"
      location="top right"
      color="info"
      multi-line
    >
      <div class="d-flex align-center">
        <v-icon class="me-2">mdi-message-text</v-icon>
        <div class="flex-grow-1">
          <div class="text-subtitle-2">{{ toastSenderName }}</div>
          <div class="text-caption" style="white-space: pre-wrap; overflow: hidden; text-overflow: ellipsis;">
            {{ toastPreview }}
          </div>
        </div>
      </div>
      <template #actions>
        <v-btn variant="text" @click="newMessageToastOpen = false">Dismiss</v-btn>
        <v-btn variant="elevated" color="white" class="text-info" @click="onOpenToast">Open</v-btn>
      </template>
    </v-snackbar>

    <!-- Session Resume snackbar — offers a one-click jump back to the last
         segment + editor mode the user was working on. Auto-dismisses, and
         one-shot per location so it doesn't re-pop on every refresh. -->
    <v-snackbar
      v-model="resumeSnackbarOpen"
      :timeout="10000"
      location="bottom right"
      color="primary"
      multi-line
    >
      <div class="d-flex align-center">
        <v-icon class="me-2">mdi-history</v-icon>
        <div class="flex-grow-1">
          <div class="text-subtitle-2">Resume where you left off</div>
          <div class="text-caption">
            Episode {{ resumeLocation?.episode_number }}<span v-if="resumeLocation?.segment_title"> — {{ resumeLocation.segment_title }}</span>
          </div>
        </div>
      </div>
      <template #actions>
        <v-btn variant="text" @click="onDismissResume">Not now</v-btn>
        <v-btn variant="elevated" color="white" class="text-primary" @click="onResume">Resume</v-btn>
      </template>
    </v-snackbar>

    <!-- Screen Flash for modal triggers and aborts -->
    <ScreenFlash />

    <!-- Initialization Overlay - shows while health check loads -->
    <InitializationOverlay />

    <!-- Status Grid - Fixed at top right, each cell clickable with detail dropdown -->
    <div v-if="isAuthenticated" class="status-grid-overlay" @click.stop>

      <!-- BACK -->
      <v-menu v-model="activeDropdown" :model-value="isDropdownOpen('back')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'backend-connected': health.status === 'healthy', 'backend-disconnected': health.status === 'error', 'backend-unknown': health.status === 'unknown', 'status-checking': loading }" @click.stop="toggleDropdown('back')">BACK</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">Backend API</div>
          <div v-if="health.status === 'healthy'" class="sd-row sd-ok">Status: Healthy</div>
          <div v-else-if="health.status === 'error'" class="sd-row sd-err">Status: Error</div>
          <div v-else class="sd-row">Status: {{ health.status || 'Unknown' }}</div>
          <div v-if="health.timestamp" class="sd-row sd-dim">Last check: {{ new Date(health.timestamp).toLocaleTimeString() }}</div>
        </v-card>
      </v-menu>

      <!-- DB1 -->
      <v-menu :model-value="isDropdownOpen('db1')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'db-connected': health.services?.database === 'connected', 'db-disconnected': health.services?.database === 'auth_failed' || health.services?.database === 'db_not_found' || health.services?.database === 'connection_refused' || health.services?.database === 'error', 'db-unknown': health.services?.database === 'unknown' || health.services?.database === 'no_config' || !health.services?.database, 'status-checking': loading }" @click.stop="toggleDropdown('db1')">DB1</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">PostgreSQL</div>
          <div class="sd-row" :class="health.services?.database === 'connected' ? 'sd-ok' : 'sd-err'">{{ health.services?.database || 'unknown' }}</div>
        </v-card>
      </v-menu>

      <!-- VMIX (was DB2) -->
      <v-menu v-if="health.services?.vmix" :model-value="isDropdownOpen('vmix')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'vmix-connected': health.services?.vmix?.connected, 'vmix-disconnected': !health.services?.vmix?.connected, 'status-checking': loading }" @click.stop="toggleDropdown('vmix')">VMIX</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">vMix Switcher</div>
          <div class="sd-row" :class="health.services?.vmix?.connected ? 'sd-ok' : 'sd-err'">{{ health.services?.vmix?.connected ? 'Connected' : 'Disconnected' }}</div>
          <div v-if="health.services?.vmix?.host" class="sd-row sd-dim">Host: {{ health.services.vmix.host }}</div>
          <div v-if="health.services?.vmix?.error" class="sd-row sd-err">{{ health.services.vmix.error }}</div>
        </v-card>
      </v-menu>

      <!-- OLLAMA -->
      <v-menu v-if="health.services?.ollama" :model-value="isDropdownOpen('ollama')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'ollama-connected': health.services?.ollama?.status === 'connected', 'ollama-disconnected': health.services?.ollama?.status === 'connection_refused' || health.services?.ollama?.status === 'timeout' || health.services?.ollama?.status?.startsWith?.('error'), 'ollama-unknown': health.services?.ollama?.status === 'unknown', 'status-checking': loading }" @click.stop="toggleDropdown('ollama')">OLLAMA</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">Ollama LLM</div>
          <div class="sd-row" :class="health.services?.ollama?.status === 'connected' ? 'sd-ok' : 'sd-err'">{{ health.services?.ollama?.status || 'unknown' }}</div>
          <div v-if="health.services?.ollama?.model" class="sd-row">Model: {{ health.services.ollama.model }}</div>
          <div v-if="health.services?.ollama?.url" class="sd-row sd-dim">{{ health.services.ollama.url }}</div>
        </v-card>
      </v-menu>

      <!-- FISH / TTS -->
      <v-menu v-if="health.services?.tts || health.services?.xtts" :model-value="isDropdownOpen('tts')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'tts-connected': health.services?.tts?.connected || health.services?.xtts?.status === 'connected', 'tts-depleted': !health.services?.tts && health.services?.xtts?.status === 'depleted', 'tts-disconnected': health.services?.tts ? !health.services.tts.connected : (health.services?.xtts?.status === 'error' || !health.services?.xtts?.connected), 'status-checking': loading }" @click.stop="toggleDropdown('tts')">{{ (health.services?.tts?.label || 'TTS').toUpperCase() }}</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">{{ health.services?.tts?.service === 'fishspeech' ? 'Fish Speech TTS' : 'TTS Service' }}</div>
          <div class="sd-row" :class="health.services?.tts?.connected ? 'sd-ok' : 'sd-err'">{{ health.services?.tts?.connected ? 'Connected' : 'Disconnected' }}</div>
          <div v-if="health.services?.tts?.host" class="sd-row sd-dim">{{ health.services.tts.host }}</div>
          <div v-if="health.services?.tts?.error" class="sd-row sd-err">{{ health.services.tts.error }}</div>
          <div v-if="health.services?.xtts?.status === 'deprecated'" class="sd-row sd-dim">XTTS: deprecated</div>
        </v-card>
      </v-menu>

      <!-- REDIS -->
      <v-menu :model-value="isDropdownOpen('redis')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'redis-connected': health.services?.redis?.connected, 'redis-disconnected': health.services?.redis?.error || !health.services?.redis?.connected, 'redis-slow': health.services?.redis?.latency > 100, 'status-checking': loading }" @click.stop="toggleDropdown('redis')">REDIS</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">Redis Broker</div>
          <div class="sd-row" :class="health.services?.redis?.connected ? 'sd-ok' : 'sd-err'">{{ health.services?.redis?.connected ? 'Connected' : 'Disconnected' }}</div>
          <div v-if="health.services?.redis?.latency != null" class="sd-row" :class="health.services.redis.latency > 100 ? 'sd-warn' : ''">Latency: {{ health.services.redis.latency }}ms</div>
          <div v-if="health.services?.redis?.error" class="sd-row sd-err">{{ health.services.redis.error }}</div>
        </v-card>
      </v-menu>

      <!-- CELERY / WORKERS -->
      <v-menu :model-value="isDropdownOpen('celery')" location="bottom center" :close-on-content-click="false" @update:model-value="v => { if (!v) activeDropdown = null }">
        <template v-slot:activator="{ props: menuProps }">
          <div v-bind="menuProps" class="grid-cell" :class="{ 'celery-connected': health.services?.celery?.workers?.length > 0, 'celery-disconnected': health.services?.celery?.error || health.services?.celery?.workers?.length === 0, 'status-checking': loading }" @click.stop="toggleDropdown('celery')">{{ health.services?.celery?.workers?.length > 0 ? 'W:' + health.services?.celery?.workers?.length : 'CELERY' }}</div>
        </template>
        <v-card class="status-dropdown">
          <div class="sd-title">Celery Workers</div>
          <div v-if="health.services?.celery?.workers?.length > 0">
            <div v-for="w in health.services.celery.workers" :key="w" class="sd-row sd-ok">{{ w }}</div>
          </div>
          <div v-else class="sd-row sd-err">No workers responding</div>
          <div v-if="health.services?.celery?.error" class="sd-row sd-err">{{ health.services.celery.error }}</div>
        </v-card>
      </v-menu>

      <!-- NFS (keeps existing modal behavior) -->
      <div
        class="grid-cell nfs-cell"
        :class="{
          'nfs-connected': health.services?.nfs?.status === 'connected',
          'nfs-warning': health.services?.nfs?.status === 'warning',
          'nfs-disconnected': health.services?.nfs?.status === 'error' || !health.services?.nfs?.status,
          'status-checking': loading
        }"
        @click="openNfsModal"
        style="cursor: pointer;"
      >
        NFS
      </div>
    </div>

    <!-- NFS Status Modal -->
    <NfsStatusModal ref="nfsModalRef" />

    <!-- Episode Loading Overlay -->
    <v-overlay
      v-model="isLoadingEpisode"
      persistent
      class="episode-loading-overlay"
      :scrim="false"
      :contained="false"
    >
      <div class="loading-content">
        <v-progress-circular
          indeterminate
          size="64"
          width="6"
          color="primary"
          class="loading-spinner"
        ></v-progress-circular>
        <div class="loading-text">
          Loading Episode {{ loadingEpisodeInfo.number }}: {{ loadingEpisodeInfo.title }}<span class="loading-dots"></span>
        </div>
      </div>
    </v-overlay>
  </v-app>
</template>

<script setup>
import LoginModal from '@/components/LoginModal.vue' // eslint-disable-line no-unused-vars
import UrgentFlash from '@/components/UrgentFlash.vue' // eslint-disable-line no-unused-vars
import StandardNotification from '@/components/StandardNotification.vue' // eslint-disable-line no-unused-vars
import ScreenFlash from '@/components/ScreenFlash.vue' // eslint-disable-line no-unused-vars
import InitializationOverlay from '@/components/InitializationOverlay.vue' // eslint-disable-line no-unused-vars
import LiveClock from '@/components/LiveClock.vue' // eslint-disable-line no-unused-vars
import StatusClock from '@/components/StatusClock.vue' // eslint-disable-line no-unused-vars
import TimezoneClock from '@/components/TimezoneClock.vue' // eslint-disable-line no-unused-vars
import NfsStatusModal from '@/components/NfsStatusModal.vue' // eslint-disable-line no-unused-vars
import NotificationCenter from '@/components/NotificationCenter.vue' // eslint-disable-line no-unused-vars
import JobMonitor from '@/components/JobMonitor.vue' // eslint-disable-line no-unused-vars
import KeyboardShortcutsModal from '@/components/KeyboardShortcutsModal.vue' // eslint-disable-line no-unused-vars
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useUrgentFlash } from '@/composables/useUrgentFlash'
import { useStandardNotification } from '@/composables/useStandardNotification'
import { useSystemHealth } from '@/composables/useSystemHealth'
import { NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserPrefs } from '@/composables/useUserPrefs'
import { useSessionResume } from '@/composables/useSessionResume'
import { useMessages } from '@/composables/useMessages'
import { useEditorDisplayPrefs } from '@/composables/useEditorDisplayPrefs'
import { installModalStackHandler, uninstallModalStackHandler } from '@/composables/useModalStack'
import { useUndoManager } from '@/composables/useUndoManager'
import PresenceMenu from '@/components/PresenceMenu.vue'
import MessagesPanel from '@/components/MessagesPanel.vue'
import { useHotkeys } from '@/composables/useHotkeys'
import { applyIndicatorCSSVars } from '@/composables/useContentIndicators'

const { isAuthenticated, currentUser, checkAuthStatus, handleLogout, setAuth } = useAuth()
const { registerFlashComponent } = useUrgentFlash()
const { toggleModal: toggleHotkeyModal } = useHotkeys()
const undoManager = useUndoManager()

// True when the keyboard target is a real text-entry element where the
// browser's native undo should win (sidebar fields, modal inputs, etc).
// Script-mode paragraph contenteditables are excluded — they carry the
// `script-paragraph` class and belong to our undo manager because the
// reactive `rawMarkdownContent` is the source of truth, not the DOM.
function isInNativeTextField(target) {
  if (!target || !(target instanceof Element)) return false
  return !!target.closest('input, textarea, [contenteditable="true"]:not(.script-paragraph)')
}

function handleGlobalHotkey(e) {
  if (e.altKey && e.key === '1') {
    e.preventDefault()
    toggleHotkeyModal()
    return
  }

  const isUndo = (e.ctrlKey || e.metaKey) && !e.altKey && e.key === 'z' && !e.shiftKey
  const isRedo = (e.ctrlKey || e.metaKey) && !e.altKey && (e.key === 'y' || ((e.key === 'z' || e.key === 'Z') && e.shiftKey))
  if (isUndo || isRedo) {
    if (isInNativeTextField(e.target)) return
    if (isUndo && undoManager.canUndo.value) {
      e.preventDefault()
      e.stopPropagation()
      undoManager.undo()
    } else if (isRedo && undoManager.canRedo.value) {
      e.preventDefault()
      e.stopPropagation()
      undoManager.redo()
    }
  }
}
document.addEventListener('keydown', handleGlobalHotkey)
installModalStackHandler()
onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleGlobalHotkey)
  window.removeEventListener('keydown', handleGlobalShortcutKey)
  uninstallModalStackHandler()
})
const { registerNotificationComponent } = useStandardNotification()
const { health, isLoading: loading } = useSystemHealth() // eslint-disable-line no-unused-vars
const router = useRouter()

// Status bar dropdown state — only one dropdown open at a time
const activeDropdown = ref(null)
function toggleDropdown(key) {
  activeDropdown.value = activeDropdown.value === key ? null : key
}
function isDropdownOpen(key) {
  return activeDropdown.value === key
}

const drawer = ref(false)
const showLoginModal = ref(false)
const showShortcutsModal = ref(false)

// Episode selector state
const episodes = ref([])
const selectedEpisode = ref(null)
const isLoadingEpisode = ref(false)
const loadingEpisodeInfo = ref({ number: '', title: '' })

// Close drawer when navigating to a new route
watch(
  () => router.currentRoute.value,
  () => {
    drawer.value = false
  }
)
const isAdmin = ref(false)
const allOrganizations = ref([]) // eslint-disable-line no-unused-vars
const selectedOrgId = ref(null) // eslint-disable-line no-unused-vars
const urgentFlash = ref(null)
const standardNotification = ref(null)
const nfsModalRef = ref(null)
const userGroups = ref([])
const openGroups = ref(['scriptfactory', 'brainstorm', 'mediafactory', 'metafactory']) // Auto-expand all factory groups
// User-preference: clock timezone. One-time read of legacy localStorage value
// migrates the user forward; future writes go to /api/user/prefs (see watcher
// below). The cache is hydrated on login by the auth store, so by the time
// this ref is created `userPrefs.get()` will already have the user's value.
const userPrefs = useUserPrefs()
const customClockTz = ref(
  userPrefs.get('clock.timezone', localStorage.getItem('customClockTz') || 'Europe/London')
)

const navItems = [ // eslint-disable-line no-unused-vars
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
  { title: 'Episodes', icon: 'mdi-television-classic', to: '/episodes' },
  { title: 'Tools', icon: 'mdi-toolbox', to: '/tools' },
  { title: 'Organization', icon: 'mdi-domain', to: '/organization' },
  { title: 'Stack Manager', icon: 'mdi-playlist-edit', to: '/stack' },
  { title: 'Content Editor', icon: 'mdi-script-text-outline', to: '/content-editor' },
  { title: 'Asset Pool', icon: 'mdi-folder', to: '/assets' },
  { title: 'Templates', icon: 'mdi-file-document', to: '/templates' },
  { title: 'Item Types', icon: 'mdi-format-list-bulleted-type', to: '/item-types' },
  { title: 'MediaFactory', icon: 'mdi-factory', to: '/mediafactory', requiresGroup: 'mediafactory' },
  { title: 'MetaFactory', icon: 'mdi-database-cog', to: '/metafactory', requiresGroup: 'metafactory' },
  { title: 'Settings', icon: 'mdi-cog', to: '/settings' }
]

const userMenuItems = [
  { title: 'Profile', icon: 'mdi-account', action: 'profile' },
  { title: 'Settings', icon: 'mdi-cog', action: 'settings' },
  { title: 'Logout', icon: 'mdi-logout', action: 'logout' }
]

// Computed property for user's full name
const userFullName = computed(() => {
  if (currentUser.value?.first_name && currentUser.value?.last_name) {
    return `${currentUser.value.first_name} ${currentUser.value.last_name}`
  } else if (currentUser.value?.first_name) {
    return currentUser.value.first_name
  } else if (currentUser.value?.last_name) {
    return currentUser.value.last_name
  } else {
    return currentUser.value?.username || 'User'
  }
})

// Computed property for user's access level
const userAccessLevel = computed(() => {
  return currentUser.value?.access_level || null
})

// Computed property for access level badge color
const accessLevelColor = computed(() => {
  const level = userAccessLevel.value
  if (level === 'admin') return 'error'
  if (level === 'editor') return 'warning'
  if (level === 'viewer') return 'info'
  return 'grey'
})

// Computed property to filter nav items based on group membership
const filteredNavItems = computed(() => { // eslint-disable-line no-unused-vars
  return navItems.filter(item => {
    // If item doesn't require a group, always show it
    if (!item.requiresGroup) return true

    // Check if user is in the required group
    return userGroups.value.some(group => group.slug === item.requiresGroup)
  })
})

// Load user groups
const loadUserGroups = async () => {
  if (!currentUser.value || !currentUser.value.id) {
    userGroups.value = []
    return
  }

  try {
    const response = await axios.get(`/api/rbac/users/${currentUser.value.id}/groups`)
    if (response.data.success) {
      userGroups.value = response.data.groups || []
    }
  } catch (error) {
    console.error('Failed to load user groups:', error)
    userGroups.value = []
  }
}

const handleLoginSuccess = async (authData) => {
  setAuth(authData.token, authData.user, authData.expiry)
  showLoginModal.value = false

  // Show success notification
  window.notifyUserStandard("Login successful!", NOTIFICATION_COLORS.SUCCESS, 2000)

  // Check if user is admin and load organizations
  isAdmin.value = authData.user?.access_level === 'admin'
  if (isAdmin.value) {
    await loadOrganizations()
  }

  // Load user groups for menu filtering
  await loadUserGroups()
}

const handleUserMenuItem = (item) => {
  if (item.action === 'profile') router.push('/profile')
  else if (item.action === 'settings') router.push('/settings')
  else if (item.action === 'logout') {
    handleLogout()
    router.push('/dashboard')
  }
}

const loadOrganizations = async () => {
  try {
    const response = await axios.get('/api/organizations/')
    if (response.data && response.data.length > 0) {
      allOrganizations.value = response.data

      // Set Polaris as default or first org
      let defaultOrg = response.data.find(org =>
        org.name.toLowerCase().includes('polaris') ||
        org.legal_name?.toLowerCase().includes('polaris')
      )
      if (!defaultOrg) {
        defaultOrg = response.data[0]
      }
      selectedOrgId.value = defaultOrg.id
    }
  } catch (error) {
    console.error('Failed to load organizations:', error)
  }
}

const switchOrganization = (orgId) => { // eslint-disable-line no-unused-vars
  // You can emit an event or use a global state management solution
  // For now, just update the selected org
  selectedOrgId.value = orgId
  console.log('Switched to organization ID:', orgId)
}

const openNfsModal = () => {
  if (nfsModalRef.value) {
    nfsModalRef.value.open()
  }
}

// Explicit navigation to settings (backup for v-list-item to prop)
const navigateToSettings = () => {
  router.push('/settings')
}

// Fetch episodes for selector
async function fetchEpisodes() {
  try {
    const response = await axios.get('/api/episodes')
    episodes.value = response.data.episodes
      .sort((a, b) => b.episode_number.localeCompare(a.episode_number))
      .map(ep => ({
        episode_number: ep.episode_number,
        display: `${ep.episode_number} - ${ep.title || 'Untitled'}`
      }))

    // Load current episode from sessionStorage
    const storedEpisode = sessionStorage.getItem('currentEpisode')
    if (storedEpisode) {
      selectedEpisode.value = storedEpisode
    }
  } catch (error) {
    console.error('Failed to fetch episodes:', error)
  }
}

// Update current episode session variable (stay on current route)
function loadEpisode(episodeNumber) {
  if (!episodeNumber) return

  // Check if this is a different episode
  const currentEpisode = sessionStorage.getItem('currentEpisode')
  if (currentEpisode !== episodeNumber) {
    // Different episode - show loading overlay
    const episodeData = episodes.value.find(ep => ep.episode_number === episodeNumber)
    if (episodeData) {
      loadingEpisodeInfo.value = {
        number: episodeNumber,
        title: episodeData.title || episodeData.display || 'Untitled Episode'
      }
      isLoadingEpisode.value = true

      // Hide overlay after a delay (components will finish loading)
      setTimeout(() => {
        isLoadingEpisode.value = false
      }, 1500)
    }
  }

  // Store in sessionStorage for cross-component access
  sessionStorage.setItem('currentEpisode', episodeNumber)

  // Update route parameter if current route supports it
  const currentRoute = router.currentRoute.value

  if (currentRoute.params.episode !== undefined || currentRoute.query.episode !== undefined) {
    // Route has episode parameter - update it
    if (currentRoute.params.episode !== undefined) {
      router.push({ ...currentRoute, params: { ...currentRoute.params, episode: episodeNumber } })
    } else if (currentRoute.query.episode !== undefined) {
      router.push({ ...currentRoute, query: { ...currentRoute.query, episode: episodeNumber } })
    }
  }
  // If route doesn't have episode param, just update session (components will pick it up)
}

// Persist custom clock timezone — write to per-user prefs (DB) AND keep the
// localStorage copy as an offline fallback so logged-out reload still works.
watch(customClockTz, (tz) => {
  localStorage.setItem('customClockTz', tz)
  userPrefs.set('clock.timezone', tz)
})

// If the prefs cache hydrates after this ref initialized (e.g. on a fresh
// login mid-session), pick up the new value.
watch(() => userPrefs.cache.value['clock.timezone'], (tz) => {
  if (tz && tz !== customClockTz.value) customClockTz.value = tz
})

// Mirror the user's `interface.settings` pref into localStorage on hydrate.
// Several pre-existing consumers (ContentEditor, useEditorPaste,
// useContentIndicators) read localStorage directly; this keeps them in sync
// with the current user without each having to know about useUserPrefs.
watch(() => userPrefs.cache.value['interface.settings'], (settings) => {
  if (settings && typeof settings === 'object') {
    try {
      localStorage.setItem('showbuild_interface_settings', JSON.stringify(settings))
    } catch (e) { /* noop */ }
  }
})

// Same for `content.editor` (real-content-settings) — MetadataPanel and
// GenerationSettings both read the localStorage key directly.
watch(() => userPrefs.cache.value['content.editor'], (settings) => {
  if (settings && typeof settings === 'object') {
    try {
      localStorage.setItem('real-content-settings', JSON.stringify(settings))
    } catch (e) { /* noop */ }
  }
})

// LLM routing — useLLM, GenerationSettings, SettingsView all read the
// localStorage value directly.
watch(() => userPrefs.cache.value['llm.routing'], (settings) => {
  if (settings && typeof settings === 'object') {
    try {
      localStorage.setItem('llm-routing-settings', JSON.stringify(settings))
    } catch (e) { /* noop */ }
  }
})

// TTS config (useTts already prefers the user pref; this keeps the
// localStorage cache in sync for any other reader).
watch(() => userPrefs.cache.value['tts.config'], (settings) => {
  if (settings && typeof settings === 'object') {
    try {
      localStorage.setItem('tts-config', JSON.stringify(settings))
    } catch (e) { /* noop */ }
  }
})

// ──────────────────────────────────────────────────────────────────────
// Session resume — offer a snackbar to jump back to last segment/cursor
// ──────────────────────────────────────────────────────────────────────
const sessionResume = useSessionResume()
const resumeSnackbarOpen = ref(false)
const resumeLocation = ref(null)

// The resume offer is only sensible when the user is on a "neutral" page
// (dashboard, root, etc.) — not while they're already inside the editor.
const RESUME_OFFER_ROUTES = new Set(['dashboard', 'root', 'home'])

function maybeOfferResume() {
  if (!isAuthenticated.value) return
  const loc = sessionResume.getLastLocation()
  if (!loc || !loc.episode_number) return
  if (sessionResume.hasBeenShown(loc)) return
  const routeName = router.currentRoute.value?.name
  if (routeName && !RESUME_OFFER_ROUTES.has(String(routeName))) return
  resumeLocation.value = loc
  resumeSnackbarOpen.value = true
  sessionResume.markShown(loc)
}

function onResume() {
  const loc = resumeLocation.value
  resumeSnackbarOpen.value = false
  if (!loc?.episode_number) return
  router.push({
    path: `/content-editor/${loc.episode_number}`,
    query: {
      segment: loc.segment_id || undefined,
      mode: loc.mode || undefined
    }
  })
}

function onDismissResume() {
  resumeSnackbarOpen.value = false
  sessionResume.dismiss()
}

// Offer once after prefs hydrate post-login.
watch(() => userPrefs.cache.value['session.last_location'], () => {
  // Wait a tick so the route is settled.
  setTimeout(maybeOfferResume, 100)
})

// Also offer once on initial mount if we're already authed + on a neutral route.
onMounted(() => {
  setTimeout(maybeOfferResume, 800)  // give prefs time to hydrate
})

// Install editor display CSS variables once. The composable picks up
// fallback values immediately and overrides land when prefs hydrate.
useEditorDisplayPrefs().install()

// ──────────────────────────────────────────────────────────────────────
// Inter-user messaging + presence — start polling while authed
// ──────────────────────────────────────────────────────────────────────
const msg = useMessages()
const messagesPanelRef = ref(null)
const newMessageToastOpen = ref(false)
const toastSenderName = ref('')
const toastPreview = ref('')
const _toastSenderId = ref(null)

function onComposeTo(user) {
  messagesPanelRef.value?.composeTo(user)
}

function onOpenToast() {
  newMessageToastOpen.value = false
  // Find the sender in the user directory and open their thread.
  const sender = msg.users.value.find(u => u.id === _toastSenderId.value)
  if (sender) onComposeTo(sender)
}

// React to newly-arrived inbox messages — surface as a toast unless
// the user has muted notifications via PresenceMenu.
watch(() => msg.newMessage.value, (m) => {
  if (!m) return
  if (userPrefs.get('messages.notifications.muted', false)) return
  toastSenderName.value = m.from_display || m.from_username || 'New message'
  const text = String(m.content || '')
  toastPreview.value = text.length > 120 ? text.slice(0, 117) + '…' : text
  _toastSenderId.value = m.from_user_id
  newMessageToastOpen.value = true
})

watch(isAuthenticated, (v) => {
  if (v) msg.startPolling()
  else msg.stopPolling()
}, { immediate: true })

// Watch route changes to sync selected episode with URL
watch(
  () => router.currentRoute.value,
  (newRoute) => {
    // Check if route has episode parameter (params or query)
    const routeEpisode = newRoute.params.episode || newRoute.query.episode

    if (routeEpisode) {
      selectedEpisode.value = routeEpisode
      sessionStorage.setItem('currentEpisode', routeEpisode)
    } else {
      // Route doesn't have episode param, use sessionStorage value
      const storedEpisode = sessionStorage.getItem('currentEpisode')
      if (storedEpisode) {
        selectedEpisode.value = storedEpisode
      }
    }

    // Fetch episodes if not already loaded
    if (episodes.value.length === 0) {
      fetchEpisodes()
    }
  },
  { immediate: true }
)

// ===== Global keyboard shortcut: ? or F1 opens the shortcuts modal =====
function handleGlobalShortcutKey(event) {
  // Don't intercept when the user is typing in a text field
  const target = event.target
  if (target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target?.isContentEditable) {
    return
  }
  // F1 — open help
  if (event.key === 'F1') {
    event.preventDefault()
    showShortcutsModal.value = true
    return
  }
  // ? (Shift+/) — open help
  if (event.key === '?' && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault()
    showShortcutsModal.value = true
  }
}

onMounted(async () => {
  checkAuthStatus()
  applyIndicatorCSSVars()

  window.addEventListener('keydown', handleGlobalShortcutKey)

  // Register the urgent flash component
  if (urgentFlash.value) {
    registerFlashComponent(urgentFlash.value)
  }

  // Register the standard notification component
  if (standardNotification.value) {
    registerNotificationComponent(standardNotification.value)
  }

  // Check if user is admin and load organizations
  if (isAuthenticated.value) {
    isAdmin.value = currentUser.value?.access_level === 'admin'
    if (isAdmin.value) {
      await loadOrganizations()
    }
    // Load user groups for menu filtering
    await loadUserGroups()
    // Load episodes for selector
    await fetchEpisodes()
  }

  // Setup axios interceptors
  axios.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        // Don't clear localStorage token on 401 - just show login modal
        // This prevents logout loops when token expires or API calls fail
        isAuthenticated.value = false
        showLoginModal.value = true
      }
      return Promise.reject(error)
    }
  )
})
</script>

<style>
.v-app-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

/* App title - shrink to content width */
.app-title-compact {
  min-width: 150px !important;
  max-width: 200px !important;
}

/* User info section - add spacing below status indicators */
.user-info-section {
  margin-top: 14px;
}

/* User name styling - matches Show Builder title color */
.user-name-text {
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* Episode Selector - Match clock height and blue theme */
.episode-selector {
  border: 1px solid rgba(25, 118, 210, 0.3) !important;
  height: 28px !important;
  max-height: 28px !important;
  min-height: 28px !important;
  display: flex;
  align-items: stretch;
}

.episode-selector .v-input__control {
  height: 28px !important;
  max-height: 28px !important;
  min-height: 28px !important;
}

.episode-selector .v-field__input {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
  font-size: 0.95rem !important;
  font-weight: 500 !important;
  padding: 0 8px !important;
  min-height: 28px !important;
  display: flex !important;
  align-items: center !important;
  padding-bottom: 2px !important;
}

.episode-selector .v-select__selection-text {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
  font-size: 0.95rem !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  margin-top: -2px !important;
}

.episode-selector .v-field {
  background: rgba(25, 118, 210, 0.05) !important;
  border-color: rgba(25, 118, 210, 0.3) !important;
  border-radius: 0 !important;
  height: 28px !important;
  max-height: 28px !important;
  min-height: 28px !important;
}

.episode-selector .v-field__field {
  height: 28px !important;
  max-height: 28px !important;
  min-height: 28px !important;
}

.episode-selector .v-field--focused {
  border-color: #1976d2 !important;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2) !important;
}

.episode-selector .v-field__outline {
  color: rgba(25, 118, 210, 0.3) !important;
}

.episode-selector .v-field--focused .v-field__outline {
  color: #1976d2 !important;
}

.episode-selector .v-label {
  color: #1976d2 !important;
  font-weight: 500 !important;
}

/* Episode Selector Dropdown Menu - Blue theme, no rounded corners */
.v-overlay .v-menu__content {
  border-radius: 0 !important;
}

.episode-selector + .v-overlay .v-list {
  background: rgba(25, 118, 210, 0.02) !important;
  border: 1px solid rgba(25, 118, 210, 0.3) !important;
  border-radius: 0 !important;
}

.episode-selector + .v-overlay .v-list-item {
  border-radius: 0 !important;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
  font-size: 0.9rem !important;
}

.episode-selector + .v-overlay .v-list-item:hover {
  background: rgba(25, 118, 210, 0.1) !important;
}

.episode-selector + .v-overlay .v-list-item--active {
  background: rgba(25, 118, 210, 0.15) !important;
  color: #1976d2 !important;
}

/* Episode Selector Scrollbar - Blue themed */
.episode-selector + .v-overlay .v-list::-webkit-scrollbar {
  width: 8px;
}

.episode-selector + .v-overlay .v-list::-webkit-scrollbar-track {
  background: rgba(25, 118, 210, 0.05);
  border-radius: 0;
}

.episode-selector + .v-overlay .v-list::-webkit-scrollbar-thumb {
  background: rgba(25, 118, 210, 0.4);
  border-radius: 0;
}

.episode-selector + .v-overlay .v-list::-webkit-scrollbar-thumb:hover {
  background: rgba(25, 118, 210, 0.6);
}

.v-main {
  background: #f5f5f5;
  padding-top: 64px !important;  /* Only app bar height */
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-bottom: 0 !important;
}

/* Status Grid Overlay - Fixed at top right above user info */
.status-grid-overlay {
  position: fixed;
  top: 0px;
  right: 0px;
  transform: scale(0.75);
  transform-origin: top right;
  display: flex;
  flex-direction: row;
  gap: 1px;
  align-items: center;
  z-index: 9999;
  pointer-events: auto;
  border-radius: 4px;
  padding: 2px;
}

.grid-cell {
  width: 60px;
  height: 25px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: #666;
  flex-shrink: 0;
  border-radius: 2px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.grid-cell:hover {
  opacity: 0.85;
}

/* Status dropdown cards */
.status-dropdown {
  background: #333 !important;
  color: #eee !important;
  max-width: 240px;
  min-width: 160px;
  padding: 8px 10px !important;
  font-size: 0.75rem;
  border-radius: 6px !important;
}
.sd-title {
  font-weight: 700;
  font-size: 0.8rem;
  margin-bottom: 4px;
  color: #fff;
}
.sd-row {
  padding: 1px 0;
  line-height: 1.3;
}
.sd-ok { color: #81c784; }
.sd-err { color: #ef5350; }
.sd-warn { color: #ffb74d; }
.sd-dim { color: #9e9e9e; font-size: 0.7rem; }

.grid-cell.backend-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.backend-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.backend-unknown {
  background-color: #757575;
  color: white;
  font-weight: bold;
}

.grid-cell.db-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.db-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.db-unknown {
  background-color: #ff9800;
  color: black;
  font-weight: bold;
}

.grid-cell.tts-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.tts-depleted {
  background-color: #ffc107;
  color: black;
  font-weight: bold;
}

.grid-cell.tts-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-disabled {
  background-color: #9e9e9e;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-unknown {
  background-color: #757575;
  color: white;
  font-weight: bold;
}

.grid-cell.redis-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.redis-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.redis-slow {
  background-color: #ff9800;
  color: black;
  font-weight: bold;
}

.grid-cell.celery-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.celery-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.nfs-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.nfs-warning {
  background-color: #ff9800;
  color: black;
  font-weight: bold;
}

.grid-cell.nfs-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.vmix-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.vmix-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.nfs-cell:hover {
  opacity: 0.8;
  transform: scale(1.05);
  transition: all 0.2s ease;
}

/* Status checking animation - blue/white throb */
.grid-cell.status-checking {
  animation: status-throb 1.5s ease-in-out infinite;
  position: relative;
}

@keyframes status-throb {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7);
  }
  50% {
    box-shadow: 0 0 12px 4px rgba(33, 150, 243, 0.4);
  }
}

/* GLOBAL FIX: Vuetify 3 label positioning issues across all modals and forms */
.v-field .v-field__label {
  transition: all 0.2s ease !important;
  transform-origin: top left !important;
}

/* Ensure labels start in the correct position */
.v-field:not(.v-field--focused):not(.v-field--active):not(.v-field--dirty) .v-field__label {
  top: 50% !important;
  transform: translateY(-50%) !important;
  font-size: 1rem !important;
}

/* When field is focused, active, or has value, move label up */
.v-field--focused .v-field__label,
.v-field--active .v-field__label,
.v-field--dirty .v-field__label {
  top: 0 !important;
  transform: translateY(-50%) scale(0.75) !important;
  font-size: 0.75rem !important;
  background-color: white !important;
  padding: 0 4px !important;
  z-index: 1 !important;
}

/* Episode Loading Overlay */
.episode-loading-overlay {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

.episode-loading-overlay .v-overlay__scrim {
  opacity: 0 !important;
}

.episode-loading-overlay > .v-overlay__content {
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.loading-spinner {
  margin-bottom: 8px;
}

.loading-text {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  text-align: center;
  letter-spacing: 0.5px;
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% {
    content: '';
  }
  40% {
    content: '.';
  }
  60% {
    content: '..';
  }
  80%, 100% {
    content: '...';
  }
}

</style>
