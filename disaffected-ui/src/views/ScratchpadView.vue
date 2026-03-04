<template>
  <v-container fluid class="pa-0 scratchpad-container">
    <!-- Toolbar -->
    <v-toolbar flat density="compact" color="grey-lighten-4" class="border-b flex-grow-0">
      <v-toolbar-title class="text-h6">
        <v-icon class="me-2">mdi-notebook-edit</v-icon>
        Brainstorm
      </v-toolbar-title>

      <v-chip v-if="currentEpisode" size="small" color="primary" class="ms-3">
        Episode {{ currentEpisode }}
      </v-chip>

      <v-spacer></v-spacer>

      <!-- Quick Actions (disabled when no episode) -->
      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-text"
        :disabled="!currentEpisode"
        @click="addTextCard"
      >
        Text (T)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-link"
        :disabled="!currentEpisode"
        @click="addLinkCard"
      >
        Link (L)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-image"
        :disabled="!currentEpisode"
        @click="triggerImageUpload"
      >
        Image (I)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-video"
        :disabled="!currentEpisode"
        @click="triggerVideoUpload"
      >
        Video (V)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-music-note"
        :disabled="!currentEpisode"
        @click="triggerAudioUpload"
      >
        Audio (A)
      </v-btn>

      <v-divider vertical class="mx-2"></v-divider>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-code-tags"
        :disabled="!currentEpisode"
        @click="addHtmlCard"
      >
        HTML (H)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-code-braces"
        :disabled="!currentEpisode"
        @click="addCodeCard"
      >
        Code (C)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-language-markdown"
        :disabled="!currentEpisode"
        @click="addMarkdownCard"
      >
        Markdown (M)
      </v-btn>

      <v-divider vertical class="mx-2"></v-divider>

      <!-- Parent Node Dropdown -->
      <v-menu v-model="showParentMenu" :close-on-content-click="false" location="bottom">
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            size="small"
            variant="text"
            prepend-icon="mdi-hub"
            :disabled="!currentEpisode"
          >
            Parent (P)
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="pt in parentNodeTypes"
            :key="pt.name"
            @click="addParentNode(pt)"
          >
            <template v-slot:prepend>
              <v-icon :color="pt.color">{{ pt.icon }}</v-icon>
            </template>
            <v-list-item-title>{{ pt.name }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <v-divider vertical class="mx-2"></v-divider>

      <!-- Zoom Controls -->
      <v-btn
        size="small"
        variant="text"
        icon="mdi-magnify-plus"
        :disabled="zoomLevel >= 5.0"
        @click="zoomIn"
      ></v-btn>
      <v-chip
        size="small"
        variant="outlined"
        class="mx-1"
        style="cursor: pointer;"
        @click="zoomLevel = 1.0; panX = 0; panY = 0"
        title="Reset zoom & pan"
      >{{ Math.round(zoomLevel * 100) }}%</v-chip>
      <v-btn
        size="small"
        variant="text"
        icon="mdi-magnify-minus"
        :disabled="zoomLevel <= 0.1"
        @click="zoomOut"
      ></v-btn>

      <v-divider vertical class="mx-2"></v-divider>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-delete-sweep"
        :disabled="!currentEpisode"
        @click="clearAll"
      >
        Clear All
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-content-save"
        :disabled="!currentEpisode"
        @click="saveBoard"
      >
        Save
      </v-btn>
    </v-toolbar>

    <!-- Hidden file inputs -->
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      multiple
      style="display: none"
      @change="handleImageUpload"
    />
    <input
      ref="videoInput"
      type="file"
      accept="video/*"
      multiple
      style="display: none"
      @change="handleVideoUpload"
    />
    <input
      ref="audioInput"
      type="file"
      accept="audio/*"
      multiple
      style="display: none"
      @change="handleAudioUpload"
    />

    <!-- Episode Selection Overlay (blocks canvas when no episode) -->
    <div v-if="!currentEpisode" class="episode-required-overlay">
      <v-card max-width="480" elevation="8" class="pa-2">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="warning">mdi-alert-circle</v-icon>
          Episode Required
        </v-card-title>
        <v-card-text>
          <p class="text-body-1 mb-4">
            Select an episode to begin working on the whiteboard, or create a new one.
          </p>
          <v-select
            v-model="selectedEpisodeValue"
            :items="episodeList"
            label="Select Episode"
            variant="outlined"
            density="comfortable"
            item-title="title"
            item-value="value"
            :loading="loadingEpisodes"
            placeholder="Choose an episode..."
            hide-details
            class="mb-4"
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-television-play</v-icon>
            </template>
          </v-select>
        </v-card-text>
        <v-card-actions>
          <EpisodeScaffoldModal @episode-created="handleEpisodeCreated" />
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="elevated"
            :disabled="!selectedEpisodeValue"
            prepend-icon="mdi-check"
            @click="confirmEpisodeSelection"
          >
            Open Whiteboard
          </v-btn>
        </v-card-actions>
      </v-card>
    </div>

    <!-- Episode Selector Dialog (opened from menu when episode already set) -->
    <v-dialog v-model="showEpisodeDialog" max-width="480" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2">mdi-television-play</v-icon>
          Select Episode
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" size="small" @click="showEpisodeDialog = false"></v-btn>
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="selectedEpisodeValue"
            :items="episodeList"
            label="Select Episode"
            variant="outlined"
            density="comfortable"
            item-title="title"
            item-value="value"
            :loading="loadingEpisodes"
            placeholder="Choose an episode..."
            hide-details
          >
            <template v-slot:prepend-inner>
              <v-icon>mdi-television-play</v-icon>
            </template>
          </v-select>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="showEpisodeDialog = false">Cancel</v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="elevated"
            :disabled="!selectedEpisodeValue"
            @click="confirmEpisodeSelection"
          >
            Switch Episode
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteConfirm" max-width="360" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="error">mdi-alert</v-icon>
          Delete Card
        </v-card-title>
        <v-card-text>
          Are you sure you want to delete this card? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showDeleteConfirm = false">Cancel</v-btn>
          <v-btn color="error" variant="elevated" @click="executeDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Whiteboard Canvas -->
    <div
      ref="canvas"
      class="whiteboard-canvas"
      :class="{
        'canvas-disabled': !currentEpisode,
        'canvas-dragging-connection': isDragging
      }"
      @click="handleCanvasClick"
      @dblclick="handleCanvasDblClick"
      @mousedown="handleCanvasMouseDown"
      @mousemove="handleCanvasMouseMove"
      @mouseup="handleCanvasMouseUp"
      @mouseleave="handleCanvasMouseUp"
      @paste="currentEpisode ? handlePaste($event) : null"
      @dragover.prevent
      @drop="currentEpisode ? handleDrop($event) : null"
      @keydown="currentEpisode ? handleKeyDown($event) : null"
      @wheel.prevent="handleCanvasWheel"
      tabindex="0"
    >
      <!-- Floating Options Menu (top-left of canvas, OUTSIDE zoom wrapper) -->
      <div class="floating-menu" @click.stop>
        <!-- Trigger button -->
        <v-btn
          icon
          size="48"
          color="primary"
          variant="elevated"
          elevation="4"
          class="floating-menu-btn"
          :class="{ 'menu-open': floatingMenuOpen }"
          @click="floatingMenuOpen = !floatingMenuOpen"
        >
          <v-icon size="24" :class="{ 'rotate-90': floatingMenuOpen }">mdi-dots-grid</v-icon>
        </v-btn>

        <!-- Flyout actions (horizontal, to the right) -->
        <transition name="flyout">
          <div v-if="floatingMenuOpen" class="flyout-bar">
            <div
              class="flyout-action-wrapper"
              @click="openEpisodeSelector(false); floatingMenuOpen = false"
            >
              <v-btn
                icon
                size="48"
                variant="elevated"
                color="white"
                elevation="3"
                class="flyout-action"
              >
                <v-badge v-if="!currentEpisode" dot color="error" location="top end">
                  <v-icon size="24" color="primary">mdi-television-play</v-icon>
                </v-badge>
                <v-icon v-else size="24" color="primary">mdi-television-play</v-icon>
              </v-btn>
              <span class="flyout-label">Select Episode</span>
            </div>

            <div
              class="flyout-action-wrapper"
              :class="{ 'flyout-disabled': !currentEpisode }"
              @click="currentEpisode && (refreshBoard(), floatingMenuOpen = false)"
            >
              <v-btn
                icon
                size="48"
                variant="elevated"
                color="white"
                elevation="3"
                class="flyout-action"
                :disabled="!currentEpisode"
              >
                <v-icon size="24" color="primary">mdi-refresh</v-icon>
              </v-btn>
              <span class="flyout-label">Refresh</span>
            </div>

            <div
              class="flyout-action-wrapper"
              @click="handleMenuSave(); floatingMenuOpen = false"
            >
              <v-btn
                icon
                size="48"
                variant="elevated"
                color="white"
                elevation="3"
                class="flyout-action"
              >
                <v-badge v-if="!currentEpisode" dot color="warning" location="top end">
                  <v-icon size="24" color="primary">mdi-content-save</v-icon>
                </v-badge>
                <v-icon v-else size="24" color="primary">mdi-content-save</v-icon>
              </v-btn>
              <span class="flyout-label">Save</span>
            </div>
          </div>
        </transition>
      </div>

      <!-- Drag-to-connect Indicator -->
      <div v-if="isDragging" class="connection-mode-banner">
        <v-icon size="small" class="me-1">mdi-vector-line</v-icon>
        <span>Drag to another card's border to connect, or click empty space to spawn a new card</span>
        <v-btn size="x-small" variant="text" class="ms-2" @click="cancelDrag">
          <kbd>Esc</kbd> Cancel
        </v-btn>
      </div>

      <!-- Zoom Wrapper -->
      <div
        class="zoom-wrapper"
        :style="{
          transform: `translate(${panX}px, ${panY}px) scale(${zoomLevel})`,
          transformOrigin: '0 0',
          position: 'relative'
        }"
      >
        <!-- SVG Connection Layer -->
        <svg class="connection-layer" :style="{ width: '100%', height: '100%' }">
          <!-- Rendered connection lines -->
          <g v-for="link in renderedLinks" :key="link.id">
            <!-- Invisible wider hit area for hover -->
            <path
              :d="link.path"
              fill="none"
              stroke="transparent"
              stroke-width="16"
              style="cursor: pointer; pointer-events: stroke;"
              @mouseenter="hoveredLinkId = link.id"
              @mouseleave="hoveredLinkId = null"
            />
            <!-- Visible line -->
            <path
              :d="link.path"
              fill="none"
              :stroke="link.color || '#1976d2'"
              stroke-width="2.5"
              style="pointer-events: none;"
              :style="{ opacity: hoveredLinkId === link.id ? 1 : 0.7 }"
            />
            <!-- Endpoint dots (clickable — opens endpoint popup) -->
            <circle
              :cx="link.x1" :cy="link.y1" r="7"
              :fill="link.color || '#1976d2'"
              stroke="white" stroke-width="2"
              style="cursor: pointer; pointer-events: all;"
              @click.stop="openEndpointPopup(link.id, 'source', link.x1, link.y1)"
            />
            <circle
              :cx="link.x2" :cy="link.y2" r="7"
              :fill="link.color || '#1976d2'"
              stroke="white" stroke-width="2"
              style="cursor: pointer; pointer-events: all;"
              @click.stop="openEndpointPopup(link.id, 'target', link.x2, link.y2)"
            />
            <!-- Label at midpoint -->
            <text
              v-if="link.label"
              :x="link.mx"
              :y="link.my - 10"
              text-anchor="middle"
              class="connection-label"
              :fill="link.color || '#1976d2'"
            >{{ link.label }}</text>
            <!-- Delete button at midpoint (on hover) -->
            <g
              v-if="hoveredLinkId === link.id"
              :transform="`translate(${link.mx}, ${link.my})`"
              style="cursor: pointer; pointer-events: all;"
              @click.stop="deleteLink(link.id)"
            >
              <circle r="12" fill="white" stroke="#e53935" stroke-width="2" />
              <text x="0" y="4" text-anchor="middle" fill="#e53935" font-size="14" font-weight="bold">x</text>
            </g>
          </g>

          <!-- Source anchor dot (concretized, yellow, stays visible during drag) -->
          <circle
            v-if="dragAnchor"
            :cx="dragAnchor.x"
            :cy="dragAnchor.y"
            r="14"
            fill="#FFC107"
            stroke="white"
            stroke-width="2"
            style="pointer-events: none;"
          />

          <!-- Rubber-band line from anchor to mouse/target (yellow dashed) -->
          <line
            v-if="rubberBandLine"
            :x1="rubberBandLine.x1"
            :y1="rubberBandLine.y1"
            :x2="rubberBandLine.x2"
            :y2="rubberBandLine.y2"
            stroke="#FFC107"
            stroke-width="3.5"
            stroke-dasharray="8,5"
            style="pointer-events: none; opacity: 0.85;"
          />

          <!-- Target dot (on target card border during drag, yellow) -->
          <circle
            v-if="dragTargetDot"
            :cx="dragTargetDot.x"
            :cy="dragTargetDot.y"
            r="14"
            fill="#FFC107"
            stroke="white"
            stroke-width="2"
            style="pointer-events: none;"
          />

          <!-- Hover dot (before first click, tracking on border) -->
          <circle
            v-if="hoverDot && !isDragging"
            :cx="hoverDot.x"
            :cy="hoverDot.y"
            r="10"
            fill="#1976d2"
            stroke="white"
            stroke-width="2"
            style="pointer-events: none; opacity: 0.85;"
          />
        </svg>

        <!-- Endpoint popup (click on connection endpoint dot) -->
        <div
          v-if="endpointPopup"
          class="endpoint-popup"
          :style="{ left: endpointPopup.x + 'px', top: endpointPopup.y + 'px' }"
          @click.stop
        >
          <v-card elevation="8" width="190" class="endpoint-popup-card">
            <v-list density="compact" class="pa-0">
              <v-list-item
                @click="handleDisconnectEnd"
                prepend-icon="mdi-link-off"
                title="Disconnect this end"
              ></v-list-item>
              <v-list-item
                @click="handleDestroyConnection"
                prepend-icon="mdi-delete"
                title="Destroy connection"
                class="text-red"
              ></v-list-item>
            </v-list>
          </v-card>
        </div>

        <!-- Help Text (shown when empty and episode selected) -->
        <div v-if="cards.length === 0 && currentEpisode" class="help-overlay">
          <v-icon size="64" color="grey-lighten-1">mdi-gesture-tap</v-icon>
          <p class="text-h6 text-grey-lighten-1 mt-4">Your whiteboard is empty</p>
          <p class="text-body-2 text-grey">
            <strong>Quick actions:</strong><br>
            • Press <kbd>T</kbd> text, <kbd>L</kbd> link, <kbd>I</kbd> image, <kbd>V</kbd> video, <kbd>A</kbd> audio<br>
            • Press <kbd>H</kbd> HTML, <kbd>C</kbd> code, <kbd>M</kbd> markdown<br>
            • Press <kbd>P</kbd> parent node • Hover card edge to connect<br>
            • Paste images, URLs, or text (<kbd>Ctrl+V</kbd>)<br>
            • <kbd>Ctrl+Scroll</kbd> to zoom • Drag items to reposition
          </p>
        </div>

        <!-- Drop-into-empty-space menu -->
        <div
          v-if="showDropMenu"
          class="drop-spawn-menu"
          :style="{ left: dropMenuPos.x + 'px', top: dropMenuPos.y + 'px' }"
          @click.stop
        >
          <v-card elevation="8" width="180" class="drop-menu-card">
            <v-list density="compact" class="pa-0">
              <v-list-item @click="spawnFromDrop('text')" prepend-icon="mdi-text" title="Text"></v-list-item>
              <v-list-item @click="spawnFromDrop('link')" prepend-icon="mdi-link" title="Link"></v-list-item>
              <v-list-item @click="spawnFromDrop('image')" prepend-icon="mdi-image" title="Image"></v-list-item>
              <v-list-item @click="spawnFromDrop('video')" prepend-icon="mdi-video" title="Video"></v-list-item>
              <v-list-item @click="spawnFromDrop('audio')" prepend-icon="mdi-music-note" title="Audio"></v-list-item>
              <v-list-item @click="spawnFromDrop('html')" prepend-icon="mdi-code-tags" title="HTML"></v-list-item>
              <v-list-item @click="spawnFromDrop('code')" prepend-icon="mdi-code-braces" title="Code"></v-list-item>
              <v-list-item @click="spawnFromDrop('markdown')" prepend-icon="mdi-language-markdown" title="Markdown"></v-list-item>
              <v-divider></v-divider>
              <v-list-item
                v-for="pt in parentNodeTypes"
                :key="pt.name"
                @click="spawnFromDrop('parent', pt)"
                :prepend-icon="pt.icon"
                :title="pt.name"
              ></v-list-item>
            </v-list>
            <div class="pa-2 text-caption text-grey text-center">
              or <kbd>Ctrl+V</kbd> to paste
            </div>
          </v-card>
        </div>

        <!-- Cards -->
        <div
          v-for="card in cards"
          :key="card.id"
          :ref="el => { if (el) cardElements[card.id] = el }"
          :style="{
            position: 'absolute',
            left: card.x + 'px',
            top: card.y + 'px',
            zIndex: card.id === activeCardId ? 1000 : 1
          }"
          :class="{
            'card-border-glow': hoverCardId === card.id && !isDragging && card.type !== 'parent',
            'card-border-glow-yellow': dragTargetDot?.cardId === card.id && card.type !== 'parent',
            'card-flash-blue': flashingCards.has(card.id) && card.type !== 'parent',
            'card-is-drag-source': dragAnchor?.cardId === card.id && card.type !== 'parent',
            'parent-glow-blue': hoverCardId === card.id && !isDragging && card.type === 'parent',
            'parent-glow-yellow': (dragTargetDot?.cardId === card.id || dragAnchor?.cardId === card.id) && card.type === 'parent',
            'parent-flash-blue': flashingCards.has(card.id) && card.type === 'parent'
          }"
          @mousedown="startDrag($event, card)"
        >
        <!-- Text Card -->
        <v-card
          v-if="card.type === 'text'"
          :width="card.collapsed ? 220 : (card.width || 500)"
          class="card-item text-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #FFA726; background: #fffbcc;">
            <v-icon size="small" color="amber-darken-2" class="collapsed-pill-icon">mdi-text</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #FFA726;">TEXT</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title
              class="pa-2 d-flex align-center bg-amber-lighten-4"
              @dblclick.stop="toggleCollapse(card)"
              style="cursor: pointer;"
            >
              <v-icon size="small" class="me-2">mdi-text</v-icon>
              <v-text-field
                v-model="card.title"
                variant="plain"
                density="compact"
                hide-details
                placeholder="Text Note"
                class="text-caption editable-title"
                @focus="activeCardId = card.id"
                @click.stop
              ></v-text-field>
              <v-spacer></v-spacer>
              <v-btn
                size="x-small"
                icon="mdi-chevron-up"
                variant="text"
                @dblclick.stop="toggleCollapse(card)"
              ></v-btn>
            </v-card-title>
            <v-card-text class="pa-3 pb-2">
              <v-textarea
                v-model="card.content"
                variant="plain"
                auto-grow
                rows="6"
                hide-details
                placeholder="Type your notes here..."
                class="text-field-no-fade"
                @focus="activeCardId = card.id"
              ></v-textarea>
            </v-card-text>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Link Card -->
        <v-card
          v-if="card.type === 'link'"
          :width="card.collapsed ? (card.socialMetadata ? 300 : 260) : (card.width || 500)"
          class="card-item link-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill collapsed-pill-tall" @dblclick.stop="toggleCollapse(card)" :style="{ borderColor: card.socialMetadata ? '#000' : '#1976D2', background: '#e3f2fd' }">
            <img
              v-if="collapsedThumb(card)"
              :src="collapsedThumb(card)"
              class="collapsed-pill-thumb-wide"
              referrerpolicy="no-referrer"
              @error="$event.target.style.display='none'"
            />
            <v-icon v-else size="small" :color="card.socialMetadata ? 'black' : 'blue'" class="collapsed-pill-icon">{{ card.socialMetadata ? 'mdi-twitter' : 'mdi-link' }}</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: card.socialMetadata ? '#000' : '#1976D2' }">{{ card.socialMetadata ? 'X POST' : 'LINK' }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State: Full Card -->
          <template v-else>
            <v-card-title
              class="pa-2 d-flex align-center bg-blue-lighten-5"
              @dblclick.stop="toggleCollapse(card)"
              style="cursor: pointer;"
            >
              <v-icon size="small" class="me-2">mdi-link</v-icon>
              <v-text-field
                v-model="card.title"
                variant="plain"
                density="compact"
                hide-details
                :placeholder="card.previewTitle || card.url || 'Link'"
                class="text-caption editable-title"
                @focus="activeCardId = card.id"
                @click.stop
              ></v-text-field>
              <v-spacer></v-spacer>
              <v-btn
                size="x-small"
                icon="mdi-chevron-up"
                variant="text"
                @dblclick.stop="toggleCollapse(card)"
              ></v-btn>
            </v-card-title>
            <v-card-text class="pa-3 pb-2" :class="{ 'link-card-content': card.socialMetadata }">
            <v-text-field
              v-model="card.url"
              variant="plain"
              placeholder="https://..."
              hide-details
              density="compact"
              class="text-field-no-fade mb-2"
              @focus="activeCardId = card.id"
            ></v-text-field>

            <!-- Rich X/Twitter Preview -->
            <div v-if="card.socialMetadata" class="twitter-preview-box mb-2">
              <div class="twitter-header pa-3 pb-2">
                <div class="d-flex align-center">
                  <v-avatar
                    v-if="card.socialMetadata.author_avatar"
                    size="48"
                    class="me-3"
                  >
                    <v-img :src="card.socialMetadata.author_avatar" />
                  </v-avatar>
                  <div class="flex-grow-1">
                    <div class="text-subtitle-2 font-weight-bold">
                      {{ card.socialMetadata.author_name || 'Unknown Author' }}
                    </div>
                    <div class="text-caption text-grey">
                      @{{ card.socialMetadata.author_handle || card.socialMetadata.username_from_url }}
                      <span v-if="card.socialMetadata.published_time" class="ms-2">
                        • {{ formatDate(card.socialMetadata.published_time) }}
                      </span>
                    </div>
                  </div>
                  <div class="d-flex gap-1">
                    <!-- Cached Badge (only if _cached flag is true) -->
                    <v-menu v-if="card._cached" open-on-hover location="bottom">
                      <template v-slot:activator="{ props }">
                        <v-chip
                          v-bind="props"
                          size="x-small"
                          color="grey-darken-1"
                          variant="tonal"
                        >
                          <v-icon size="x-small" start>mdi-cached</v-icon>
                          Cached
                        </v-chip>
                      </template>
                      <v-card max-width="200">
                        <v-card-text class="pa-2">
                          <div class="text-caption mb-2">
                            Cached {{ formatDate(card._cached_at) }}
                          </div>
                          <v-btn
                            size="small"
                            block
                            color="primary"
                            variant="tonal"
                            prepend-icon="mdi-refresh"
                            @click="reloadFromServer(card)"
                          >
                            Reload from Server
                          </v-btn>
                        </v-card-text>
                      </v-card>
                    </v-menu>

                    <v-chip
                      size="x-small"
                      color="primary"
                      variant="tonal"
                    >
                      <v-icon size="x-small" start>mdi-twitter</v-icon>
                      {{ card.socialMetadata.platform === 'x' ? 'X' : 'Twitter' }}
                    </v-chip>
                  </div>
                </div>
              </div>

              <!-- Tweet text -->
              <div v-if="card.socialMetadata.tweet_text" class="pa-3 pt-2">
                <div class="text-body-2">{{ card.socialMetadata.tweet_text }}</div>
              </div>

              <!-- Media -->
              <div v-if="card.socialMetadata.media_urls && card.socialMetadata.media_urls.length > 0" class="twitter-media" :class="{ 'twitter-media-single': card.socialMetadata.media_urls.length === 1 }">
                <img
                  v-for="(mediaUrl, idx) in card.socialMetadata.media_urls.slice(0, 4)"
                  :key="idx"
                  :src="mediaUrl"
                  class="twitter-media-image"
                  :style="{ height: (card.socialMetadata.media_urls.length === 1 ? '250px' : '150px') }"
                  referrerpolicy="no-referrer"
                  loading="eager"
                  @error="$event.target.style.display='none'"
                />
              </div>

              <!-- Tweet Metadata Expansion (default expanded) -->
              <v-expansion-panels variant="accordion" flat :model-value="[0]" multiple>
                <v-expansion-panel>
                  <v-expansion-panel-title class="py-2 px-3 text-caption">
                    <v-icon size="small" class="me-2">mdi-chart-bar</v-icon>
                    Tweet Analytics & Author Info
                  </v-expansion-panel-title>
                  <v-expansion-panel-text class="pa-3">
                    <!-- Engagement Stats -->
                    <div v-if="card.socialMetadata.likes || card.socialMetadata.retweets || card.socialMetadata.replies || card.socialMetadata.quotes" class="mb-3">
                      <div class="text-caption font-weight-bold mb-2">Engagement</div>
                      <div class="d-flex flex-wrap gap-3">
                        <v-chip v-if="card.socialMetadata.likes" size="small" variant="tonal" prepend-icon="mdi-heart">
                          {{ card.socialMetadata.likes.toLocaleString() }} Likes
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.retweets" size="small" variant="tonal" prepend-icon="mdi-repeat">
                          {{ card.socialMetadata.retweets.toLocaleString() }} Retweets
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.replies" size="small" variant="tonal" prepend-icon="mdi-reply">
                          {{ card.socialMetadata.replies.toLocaleString() }} Replies
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.quotes" size="small" variant="tonal" prepend-icon="mdi-format-quote-close">
                          {{ card.socialMetadata.quotes.toLocaleString() }} Quotes
                        </v-chip>
                      </div>
                    </div>

                    <!-- Author Stats -->
                    <div v-if="card.socialMetadata.author_followers || card.socialMetadata.author_following || card.socialMetadata.author_bio" class="mb-3">
                      <div class="text-caption font-weight-bold mb-2">Author Details</div>
                      <div class="d-flex flex-wrap gap-3 mb-2">
                        <v-chip v-if="card.socialMetadata.author_followers" size="small" variant="tonal" prepend-icon="mdi-account-group">
                          {{ card.socialMetadata.author_followers.toLocaleString() }} Followers
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.author_following" size="small" variant="tonal" prepend-icon="mdi-account-multiple">
                          {{ card.socialMetadata.author_following.toLocaleString() }} Following
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.author_verified" size="small" variant="tonal" color="primary" prepend-icon="mdi-check-decagram">
                          Verified
                        </v-chip>
                      </div>
                      <div v-if="card.socialMetadata.author_bio" class="text-caption text-grey">
                        {{ card.socialMetadata.author_bio }}
                      </div>
                    </div>

                    <!-- Media URLs -->
                    <div v-if="card.socialMetadata.media_urls && card.socialMetadata.media_urls.length > 0" class="mb-3">
                      <div class="text-caption font-weight-bold mb-2">Media Attachments</div>
                      <div v-for="(mediaUrl, idx) in card.socialMetadata.media_urls" :key="idx" class="mb-2">
                        <a :href="mediaUrl" target="_blank" class="text-caption text-primary text-decoration-none">
                          <v-icon size="x-small" class="me-1">mdi-image</v-icon>
                          Media {{ idx + 1 }}
                        </a>
                        <div class="text-caption text-grey">{{ mediaUrl }}</div>
                      </div>
                    </div>

                    <!-- Entity Annotations -->
                    <div v-if="card.socialMetadata.entities" class="mb-3">
                      <div class="text-caption font-weight-bold mb-2">Mentions & Links</div>

                      <!-- URLs -->
                      <div v-if="card.socialMetadata.entities.urls && card.socialMetadata.entities.urls.length > 0" class="mb-2">
                        <div class="text-caption font-weight-medium mb-1">Links:</div>
                        <div v-for="(urlEntity, idx) in card.socialMetadata.entities.urls" :key="idx" class="mb-1">
                          <a :href="urlEntity.expanded_url || urlEntity.url" target="_blank" class="text-caption text-primary text-decoration-none">
                            {{ urlEntity.display_url || urlEntity.url }}
                          </a>
                        </div>
                      </div>

                      <!-- Annotations (People, Places, Organizations) -->
                      <div v-if="card.socialMetadata.entities.annotations && card.socialMetadata.entities.annotations.length > 0" class="mb-2">
                        <div class="text-caption font-weight-medium mb-1">Mentioned:</div>
                        <div class="d-flex flex-wrap gap-2">
                          <v-chip
                            v-for="(annotation, idx) in card.socialMetadata.entities.annotations"
                            :key="idx"
                            size="x-small"
                            variant="outlined"
                            :prepend-icon="annotation.type === 'Person' ? 'mdi-account' : annotation.type === 'Place' ? 'mdi-map-marker' : 'mdi-domain'"
                          >
                            {{ annotation.normalized_text }}
                            <span v-if="annotation.type" class="text-grey ms-1">({{ annotation.type }})</span>
                          </v-chip>
                        </div>
                      </div>

                      <!-- Hashtags -->
                      <div v-if="card.socialMetadata.entities.hashtags && card.socialMetadata.entities.hashtags.length > 0" class="mb-2">
                        <div class="text-caption font-weight-medium mb-1">Hashtags:</div>
                        <div class="d-flex flex-wrap gap-2">
                          <v-chip
                            v-for="(hashtag, idx) in card.socialMetadata.entities.hashtags"
                            :key="idx"
                            size="x-small"
                            variant="tonal"
                            prepend-icon="mdi-pound"
                          >
                            {{ hashtag.tag }}
                          </v-chip>
                        </div>
                      </div>

                      <!-- Mentions -->
                      <div v-if="card.socialMetadata.entities.mentions && card.socialMetadata.entities.mentions.length > 0" class="mb-2">
                        <div class="text-caption font-weight-medium mb-1">User Mentions:</div>
                        <div class="d-flex flex-wrap gap-2">
                          <v-chip
                            v-for="(mention, idx) in card.socialMetadata.entities.mentions"
                            :key="idx"
                            size="x-small"
                            variant="tonal"
                            prepend-icon="mdi-at"
                          >
                            @{{ mention.username }}
                          </v-chip>
                        </div>
                      </div>
                    </div>

                    <!-- Referenced Tweets (Quotes, Replies) -->
                    <div v-if="card.socialMetadata.referenced_tweets && card.socialMetadata.referenced_tweets.length > 0" class="mb-3">
                      <div class="text-caption font-weight-bold mb-2">Thread Context</div>
                      <div v-for="(ref, idx) in card.socialMetadata.referenced_tweets" :key="idx" class="mb-1">
                        <v-chip size="x-small" variant="outlined" :prepend-icon="ref.type === 'replied_to' ? 'mdi-reply' : ref.type === 'quoted' ? 'mdi-format-quote-close' : 'mdi-repeat'">
                          {{ ref.type === 'replied_to' ? 'Reply to' : ref.type === 'quoted' ? 'Quote of' : 'Retweet of' }} {{ ref.id }}
                        </v-chip>
                      </div>
                    </div>

                    <!-- Tweet Metadata -->
                    <div v-if="card.socialMetadata.tweet_id || card.socialMetadata.conversation_id || card.socialMetadata.published_time">
                      <div class="text-caption font-weight-bold mb-2">Technical Details</div>
                      <div class="text-caption text-grey">
                        <div v-if="card.socialMetadata.published_time">Published: {{ new Date(card.socialMetadata.published_time).toLocaleString() }}</div>
                        <div v-if="card.socialMetadata.tweet_id">Tweet ID: {{ card.socialMetadata.tweet_id }}</div>
                        <div v-if="card.socialMetadata.conversation_id">Conversation ID: {{ card.socialMetadata.conversation_id }}</div>
                      </div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>

            <!-- Standard Link Preview (Facebook-style) for non-social links -->
            <div v-else-if="card.previewTitle || card.previewImage" class="link-preview-box mb-2">
              <!-- Enhanced display for Twitter direct media URLs -->
              <div v-if="card.previewDomain === 'pbs.twimg.com'" class="pa-3">
                <div class="d-flex align-center mb-2">
                  <img
                    v-if="card.previewFavicon"
                    :src="card.previewFavicon"
                    width="20"
                    height="20"
                    class="me-2"
                  />
                  <v-chip size="small" color="black" variant="flat">
                    <v-icon size="small" start>mdi-twitter</v-icon>
                    <span style="color: white;">Twitter/X Media</span>
                  </v-chip>
                  <v-spacer></v-spacer>
                  <v-chip
                    v-if="card.previewDescription && card.previewDescription.includes('video')"
                    size="x-small"
                    color="red"
                    variant="tonal"
                    prepend-icon="mdi-video"
                  >
                    Video Thumbnail
                  </v-chip>
                </div>
                <v-img
                  v-if="card.previewImage"
                  :src="card.previewImage"
                  max-height="400"
                  contain
                  class="link-preview-image mb-2"
                  style="border: 2px solid #1DA1F2;"
                ></v-img>
                <div class="text-caption text-grey">
                  Direct media link - may be from a tweet video or image
                </div>
              </div>

              <!-- Standard preview for other links -->
              <template v-else>
                <v-img
                  v-if="card.previewImage"
                  :src="card.previewImage"
                  max-height="200"
                  cover
                  class="link-preview-image"
                ></v-img>
                <div class="link-preview-content pa-3">
                  <div v-if="card.previewDomain" class="text-caption text-grey mb-1 d-flex align-center">
                    <img
                      v-if="card.previewFavicon"
                      :src="card.previewFavicon"
                      width="16"
                      height="16"
                      class="me-1"
                      @error="$event.target.style.display='none'"
                    />
                    {{ card.previewDomain }}
                  </div>
                  <div v-if="card.previewTitle" class="text-subtitle-2 font-weight-bold mb-1">
                    {{ card.previewTitle }}
                  </div>
                  <div v-if="card.previewDescription" class="text-caption text-grey line-clamp-2">
                    {{ card.previewDescription }}
                  </div>
                </div>
              </template>
            </div>

            <!-- Loading indicator -->
            <div v-if="card.fetchingPreview" class="text-caption text-grey mb-2">
              <v-icon size="x-small" class="me-1">mdi-loading mdi-spin</v-icon>
              Fetching preview...
            </div>

            <v-textarea
              v-model="card.notes"
              variant="plain"
              auto-grow
              rows="4"
              hide-details
              placeholder="Notes about this link..."
              class="text-field-no-fade"
            ></v-textarea>
            <div v-if="card.url" class="mt-2">
              <v-btn
                size="x-small"
                variant="tonal"
                prepend-icon="mdi-open-in-new"
                :href="card.url"
                target="_blank"
              >
                Open Link
              </v-btn>
            </div>
          </v-card-text>
          <v-card-actions class="pa-2 pt-0">
            <v-spacer></v-spacer>
            <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
          </v-card-actions>
          </template>
        </v-card>

        <!-- Image Card -->
        <v-card
          v-if="card.type === 'image'"
          :width="card.collapsed ? 240 : (card.width || 600)"
          class="card-item image-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #757575; background: white;">
            <v-img v-if="card.imageUrl" :src="card.imageUrl" width="48" height="48" cover class="collapsed-pill-thumb"></v-img>
            <v-icon v-else size="small" color="grey-darken-2" class="collapsed-pill-icon">mdi-image</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #757575;">IMAGE</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title
              class="pa-2 d-flex align-center bg-grey-lighten-4"
              @dblclick.stop="toggleCollapse(card)"
              style="cursor: pointer;"
            >
              <v-icon size="small" class="me-2">mdi-image</v-icon>
              <v-text-field
                v-model="card.title"
                variant="plain"
                density="compact"
                hide-details
                :placeholder="card.caption || 'Image'"
                class="text-caption editable-title"
                @focus="activeCardId = card.id"
                @click.stop
              ></v-text-field>
              <v-spacer></v-spacer>
              <v-btn
                size="x-small"
                icon="mdi-chevron-up"
                variant="text"
                @dblclick.stop="toggleCollapse(card)"
              ></v-btn>
            </v-card-title>
            <div>
              <v-img
                :src="card.imageUrl"
                :max-width="600"
                cover
              ></v-img>
              <v-card-text class="pa-3">
                <v-text-field
                  v-model="card.caption"
                  variant="outlined"
                  label="Caption"
                  hide-details
                  density="compact"
                  class="mb-2"
                  @focus="activeCardId = card.id"
                ></v-text-field>
                <v-textarea
                  v-model="card.notes"
                  variant="outlined"
                  label="Notes"
                  auto-grow
                  rows="3"
                  hide-details
                  placeholder="Add notes about this image..."
                  @focus="activeCardId = card.id"
                ></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Video Card -->
        <v-card
          v-if="card.type === 'video'"
          :width="card.collapsed ? 220 : (card.width || 640)"
          class="card-item video-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #E53935; background: #FFEBEE;">
            <v-icon size="small" color="red-darken-1" class="collapsed-pill-icon">mdi-video</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #E53935;">VIDEO</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-red-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-video</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Video" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <video v-if="card.videoUrl" :src="card.videoUrl" controls style="width: 100%; max-height: 400px;"></video>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.notes" variant="outlined" label="Notes" auto-grow rows="2" hide-details placeholder="Add notes..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-chip v-if="card.assetId" size="x-small" variant="outlined">{{ card.assetId }}</v-chip>
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Audio Card -->
        <v-card
          v-if="card.type === 'audio'"
          :width="card.collapsed ? 220 : (card.width || 500)"
          class="card-item audio-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #8E24AA; background: #F3E5F5;">
            <v-icon size="small" color="purple-darken-1" class="collapsed-pill-icon">mdi-music-note</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #8E24AA;">AUDIO</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-purple-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-music-note</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Audio" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <audio v-if="card.audioUrl" :src="card.audioUrl" controls style="width: 100%;"></audio>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.notes" variant="outlined" label="Notes" auto-grow rows="2" hide-details placeholder="Add notes..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-chip v-if="card.assetId" size="x-small" variant="outlined">{{ card.assetId }}</v-chip>
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- HTML Card -->
        <v-card
          v-if="card.type === 'html'"
          :width="card.collapsed ? 220 : (card.width || 600)"
          class="card-item html-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #F57C00; background: #FFF3E0;">
            <v-icon size="small" color="orange-darken-1" class="collapsed-pill-icon">mdi-code-tags</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #F57C00;">HTML</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-orange-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-code-tags</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="HTML" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.htmlContent" variant="outlined" label="HTML Content" auto-grow rows="8" hide-details placeholder="<div>Paste HTML here...</div>" font-family="monospace" @focus="activeCardId = card.id"></v-textarea>
                <div v-if="card.htmlContent" class="mt-3 pa-3 bg-grey-lighten-4 rounded" style="max-height: 300px; overflow: auto;">
                  <div v-html="card.htmlContent"></div>
                </div>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Code Card -->
        <v-card
          v-if="card.type === 'code'"
          :width="card.collapsed ? 220 : (card.width || 700)"
          class="card-item code-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #43A047; background: #E8F5E9;">
            <v-icon size="small" color="green-darken-1" class="collapsed-pill-icon">mdi-code-braces</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #43A047;">CODE</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-green-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-code-braces</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Code Snippet" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-select v-model="card.codeLanguage" :items="['javascript', 'python', 'html', 'css', 'json', 'bash', 'sql']" variant="outlined" density="compact" hide-details class="ms-2" style="max-width: 120px;" @click.stop></v-select>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.codeContent" variant="outlined" label="Code" auto-grow rows="12" hide-details placeholder="// Paste code here..." font-family="monospace" @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Markdown Card -->
        <v-card
          v-if="card.type === 'markdown'"
          :width="card.collapsed ? 220 : (card.width || 600)"
          class="card-item markdown-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="toggleCollapse(card)" style="border-color: #3949AB; background: #E8EAF6;">
            <v-icon size="small" color="indigo-darken-1" class="collapsed-pill-icon">mdi-language-markdown</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" style="color: #3949AB;">MD</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-indigo-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-language-markdown</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Markdown" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.markdownContent" variant="outlined" label="Markdown" auto-grow rows="10" hide-details placeholder="# Paste markdown here..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="text" class="delete-text-btn" @click.stop="confirmDelete(card.id)">[DELETE]</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Parent Node Card (Round dark-blue circle) -->
        <div
          v-if="card.type === 'parent'"
          class="parent-node-circle"
          :style="{ width: (card.collapsed ? '140px' : '240px'), height: (card.collapsed ? '140px' : '240px') }"
          @dblclick.stop="toggleCollapse(card)"
        >
          <!-- Collapsed State -->
          <template v-if="card.collapsed">
            <v-icon size="20" color="white" class="mb-1">{{ card.socialMetadata?.parentNodeIcon || 'mdi-hub' }}</v-icon>
            <span class="parent-node-type">{{ (card.socialMetadata?.parentNodeType || 'PARENT').toUpperCase() }}</span>
            <span v-if="card.title" class="parent-node-slug">{{ card.title }}</span>
          </template>

          <!-- Expanded State -->
          <template v-else>
            <v-icon size="22" color="white" class="mb-1">{{ card.socialMetadata?.parentNodeIcon || 'mdi-hub' }}</v-icon>
            <span class="parent-node-type">{{ (card.socialMetadata?.parentNodeType || 'PARENT').toUpperCase() }}</span>
            <input
              v-model="card.title"
              type="text"
              class="parent-node-input"
              :placeholder="'Segment slug...'"
              @focus="activeCardId = card.id"
              @click.stop
              @mousedown.stop
            />
            <textarea
              v-model="card.content"
              class="parent-node-desc"
              rows="3"
              placeholder="Description..."
              @focus="activeCardId = card.id"
              @click.stop
              @mousedown.stop
            ></textarea>
            <v-badge
              :content="getChildCount(card.id)"
              color="white"
              text-color="#1565C0"
              inline
            ></v-badge>
            <span
              class="parent-node-delete"
              @click.stop="confirmDelete(card.id)"
            >[DELETE]</span>
          </template>
        </div>
      </div>
      </div><!-- /zoom-wrapper -->
    </div>

    <!-- Status Bar -->
    <v-footer height="32" class="bg-grey-lighten-4 border-t flex-grow-0">
      <span class="text-caption text-grey">
        {{ cards.length }} item{{ cards.length !== 1 ? 's' : '' }} on board
        <span v-if="nodeLinks.length > 0" class="ms-2">
          | {{ nodeLinks.length }} connection{{ nodeLinks.length !== 1 ? 's' : '' }}
        </span>
        <span v-if="isDragging" class="ms-2 text-primary font-weight-bold">
          | CONNECTING...
        </span>
        <span v-if="saving" class="ms-4 text-primary">
          <v-icon size="x-small" class="me-1">mdi-loading mdi-spin</v-icon>
          Saving...
        </span>
        <span v-else-if="lastSaved" class="ms-4">
          Last saved: {{ formatTime(lastSaved) }}
        </span>
        <span v-if="zoomLevel !== 1" class="ms-4">
          Zoom: {{ Math.round(zoomLevel * 100) }}%
        </span>
        <span v-if="!currentEpisode" class="ms-4 text-warning">
          No episode selected
        </span>
      </span>
    </v-footer>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStandardNotification, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { useWhiteboardConnections } from '@/composables/useWhiteboardConnections'
import { fetchJson } from '@/utils/apiHelpers'
import axios from 'axios'
import EpisodeScaffoldModal from '@/components/EpisodeScaffoldModal.vue'

const { notifyUserStandard } = useStandardNotification()
const route = useRoute()
const router = useRouter()

// Floating menu state
const floatingMenuOpen = ref(false)

// Episode selector state
const showEpisodeDialog = ref(false)
const episodeList = ref([])
const selectedEpisodeValue = ref(null)
const loadingEpisodes = ref(false)
const pendingSaveAfterSelect = ref(false)

// Refs
const canvas = ref(null)
const imageInput = ref(null)
const videoInput = ref(null)
const audioInput = ref(null)
const cards = ref([])
const activeCardId = ref(null)
const lastSaved = ref(null)
const scratchpadId = ref(null)
const saving = ref(false)

// Workspace/Episode
const identifier = computed(() => route.query.episode || route.query.workspace || null)

// Current episode from session storage (set by episode selector)
const currentEpisode = computed(() => {
  return sessionStorage.getItem('currentEpisode') || route.query.episode || null
})

// Connections composable
const {
  nodeLinks,
  loadLinks,
  deleteLink,
  deleteLinksForCard,
  getLineCoords,
  getLinksForSave,
  // Border hover
  hoverCardId,
  hoverDot,
  // Drag-to-connect
  isDragging,
  dragAnchor,
  dragTargetDot,
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
  disconnectEnd
} = useWhiteboardConnections(cards)

// Card element refs for measuring dimensions
const cardElements = ref({})

// Collapse generation counter — bumped on every collapse/expand to force line recomputation
const collapseGeneration = ref(0)

// Endpoint popup state (click on connection endpoint dot)
const endpointPopup = ref(null) // { linkId, end: 'source'|'target', x, y }

// Zoom & pan state (infinite canvas)
const zoomLevel = ref(1.0)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const wasPanning = ref(false) // true briefly after a pan ends, to suppress click
const panStart = ref({ x: 0, y: 0, panX: 0, panY: 0 })

// Parent node types (default set, overridden by settings)
const parentNodeTypes = ref([
  { name: 'Segment', color: '#2196F3', icon: 'mdi-filmstrip' },
  { name: 'Interview', color: '#009688', icon: 'mdi-account-voice' },
  { name: 'Topic', color: '#9C27B0', icon: 'mdi-tag' },
  { name: 'Research', color: '#FF9800', icon: 'mdi-magnify' }
])
const showParentMenu = ref(false)

// Delete confirmation state
const showDeleteConfirm = ref(false)
const deleteTargetId = ref(null)

// Drag state
const dragging = ref(false)
const dragCard = ref(null)
const dragOffset = ref({ x: 0, y: 0 })

// Card ID counter
let nextId = 1
let saveTimeout = null

// Load saved whiteboard on mount
// Global hotkey: Ctrl+Shift+S to save
function handleGlobalKeydown(event) {
  if (event.ctrlKey && event.shiftKey && event.key === 'S') {
    event.preventDefault()
    handleMenuSave()
  }
}

onMounted(async () => {
  document.addEventListener('keydown', handleGlobalKeydown)
  // If no episode, fetch episode list for the overlay selector
  if (!currentEpisode.value) {
    fetchEpisodes()
  }
  // Load whiteboard settings (parent node types, etc.)
  loadWhiteboardSettings()
  await loadBoard()
  canvas.value?.focus()
})

// Load whiteboard settings from API
async function loadWhiteboardSettings() {
  try {
    const response = await fetchJson('/api/settings/api-configs')
    if (response?.success && response?.data?.whiteboard) {
      const wb = response.data.whiteboard
      if (wb.parent_node_types) parentNodeTypes.value = wb.parent_node_types
      if (wb.default_zoom) {
        if (wb.default_zoom) zoomLevel.value = wb.default_zoom
      }
    }
  } catch {
    // Use defaults silently
  }
}

// Auto-save on unmount
onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
  if (saveTimeout) clearTimeout(saveTimeout)
  saveBoard()
})

// Watch for card changes and auto-save
watch(cards, () => {
  if (currentEpisode.value) {
    debouncedSave()
  }
}, { deep: true })

// Watch for episode changes and reload board
watch(currentEpisode, async (newEpisode, oldEpisode) => {
  if (newEpisode !== oldEpisode) {
    // Save current board before switching
    if (oldEpisode) {
      await saveBoard()
    }
    // Load new episode's board
    await loadBoard()
  }
})

// Helper: get center of visible canvas area in canvas coordinates
function getCanvasCenter(offsetX = 0, offsetY = 0) {
  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return { x: 100 + offsetX, y: 100 + offsetY }
  return {
    x: (rect.width / 2 - panX.value) / zoomLevel.value + offsetX,
    y: (rect.height / 2 - panY.value) / zoomLevel.value + offsetY
  }
}

// Add text card
function addTextCard(x = null, y = null) {
  const center = getCanvasCenter(-250, -100)
  cards.value.push({
    id: nextId++,
    type: 'text',
    content: '',
    title: '',
    x: x ?? center.x,
    y: y ?? center.y,
    width: 500,
    collapsed: false
  })
}

// Add link card
function addLinkCard() {
  const center = getCanvasCenter(-250, -100)
  cards.value.push({
    id: nextId++,
    type: 'link',
    url: '',
    notes: '',
    title: '',
    x: center.x,
    y: center.y,
    width: 500,
    collapsed: false,
    // Preview metadata
    previewTitle: null,
    previewDescription: null,
    previewImage: null,
    previewDomain: null,
    previewFavicon: null,
    fetchingPreview: false,
    // Social media metadata
    socialMetadata: null
  })
}

// Trigger image upload
function triggerImageUpload() {
  imageInput.value?.click()
}

// Handle image upload
function handleImageUpload(event) {
  const files = event.target.files
  if (!files || files.length === 0) return

  Array.from(files).forEach((file, index) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const rect = canvas.value?.getBoundingClientRect()
      cards.value.push({
        id: nextId++,
        type: 'image',
        imageUrl: e.target.result,
        caption: '',
        notes: '',
        title: '',
        x: (rect ? rect.width / 2 - 300 : 100) + (index * 20),
        y: (rect ? rect.height / 2 - 150 : 100) + (index * 20),
        width: 600,
        collapsed: false
      })
    }
    reader.readAsDataURL(file)
  })

  // Reset input
  event.target.value = ''
}

// Trigger video upload
function triggerVideoUpload() {
  videoInput.value?.click()
}

// Handle video upload
async function handleVideoUpload(event) {
  const files = event.target.files
  if (!files || files.length === 0) return

  for (const file of Array.from(files)) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', `episode:${currentEpisode.value}`)
    formData.append('source', 'whiteboard')

    try {
      const response = await fetchJson(`/api/whiteboard/${identifier.value}/upload-media`, {
        method: 'POST',
        body: formData
      })

      const rect = canvas.value?.getBoundingClientRect()
      cards.value.push({
        id: nextId++,
        type: 'video',
        videoUrl: response.file_url,
        assetId: response.asset_id,
        title: file.name,
        notes: '',
        x: rect ? rect.width / 2 - 320 : 100,
        y: rect ? rect.height / 2 - 150 : 100,
        width: 640,
        collapsed: false
      })

      notifyUserStandard('Video uploaded to asset pool', NOTIFICATION_COLORS.success)
    } catch (error) {
      console.error('Error uploading video:', error)
      notifyUserStandard('Failed to upload video', NOTIFICATION_COLORS.error)
    }
  }

  event.target.value = ''
}

// Trigger audio upload
function triggerAudioUpload() {
  audioInput.value?.click()
}

// Handle audio upload
async function handleAudioUpload(event) {
  const files = event.target.files
  if (!files || files.length === 0) return

  for (const file of Array.from(files)) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', `episode:${currentEpisode.value}`)
    formData.append('source', 'whiteboard')

    try {
      const response = await fetchJson(`/api/whiteboard/${identifier.value}/upload-media`, {
        method: 'POST',
        body: formData
      })

      const rect = canvas.value?.getBoundingClientRect()
      cards.value.push({
        id: nextId++,
        type: 'audio',
        audioUrl: response.file_url,
        assetId: response.asset_id,
        title: file.name,
        notes: '',
        x: rect ? rect.width / 2 - 250 : 100,
        y: rect ? rect.height / 2 - 100 : 100,
        width: 500,
        collapsed: false
      })

      notifyUserStandard('Audio uploaded to asset pool', NOTIFICATION_COLORS.success)
    } catch (error) {
      console.error('Error uploading audio:', error)
      notifyUserStandard('Failed to upload audio', NOTIFICATION_COLORS.error)
    }
  }

  event.target.value = ''
}

// Add HTML card
function addHtmlCard() {
  const rect = canvas.value?.getBoundingClientRect()
  cards.value.push({
    id: nextId++,
    type: 'html',
    htmlContent: '',
    title: '',
    x: rect ? rect.width / 2 - 300 : 100,
    y: rect ? rect.height / 2 - 100 : 100,
    width: 600,
    collapsed: false
  })
}

// Add code card
function addCodeCard() {
  const rect = canvas.value?.getBoundingClientRect()
  cards.value.push({
    id: nextId++,
    type: 'code',
    codeContent: '',
    codeLanguage: 'javascript',
    title: '',
    x: rect ? rect.width / 2 - 350 : 100,
    y: rect ? rect.height / 2 - 150 : 100,
    width: 700,
    collapsed: false
  })
}

// Add markdown card
function addMarkdownCard() {
  const rect = canvas.value?.getBoundingClientRect()
  cards.value.push({
    id: nextId++,
    type: 'markdown',
    markdownContent: '',
    title: '',
    x: rect ? rect.width / 2 - 300 : 100,
    y: rect ? rect.height / 2 - 100 : 100,
    width: 600,
    collapsed: false
  })
}

// Toggle card collapse
function toggleCollapse(card) {
  card.collapsed = !card.collapsed
  // Bump generation after DOM updates so connection lines recompute with new card dimensions
  nextTick(() => {
    collapseGeneration.value++
  })
}

// Get display label for collapsed card
function collapsedLabel(card) {
  // For tweets: show the actual username (prefer handle > username_from_url > author_name)
  if (card.socialMetadata?.author_handle) return '@' + card.socialMetadata.author_handle
  if (card.socialMetadata?.username_from_url) return '@' + card.socialMetadata.username_from_url
  // Only use author_name if it's not the generic "X (formerly Twitter)" scraping fallback
  if (card.socialMetadata?.author_name && !card.socialMetadata.author_name.includes('formerly')) return card.socialMetadata.author_name
  if (card.title) return card.title
  if (card.previewTitle) return card.previewTitle
  if (card.caption) return card.caption
  if (card.content) return card.content.substring(0, 40)
  if (card.url) return card.url.replace(/^https?:\/\//, '').substring(0, 35)
  if (card.htmlContent) return 'HTML snippet'
  if (card.codeContent) return card.codeLanguage || 'Code'
  if (card.markdownContent) return card.markdownContent.substring(0, 40)
  if (card.socialMetadata?.parentNodeType) return card.socialMetadata.parentNodeType
  return ''
}

// Get thumbnail URL for collapsed card
function collapsedThumb(card) {
  if (card.socialMetadata?.media_urls?.[0]) return card.socialMetadata.media_urls[0]
  if (card.previewImage) return card.previewImage
  if (card.imageUrl) return card.imageUrl
  return null
}

// Handle canvas mousedown - catches clicks on card outline/border area (outside card div)
function handleCanvasMouseDown(event) {
  // If the hover dot is showing on a card border, initiate a connection.
  // This catches clicks on the CSS outline zone which is painted outside the card div,
  // so the card's own @mousedown doesn't fire for those clicks.
  if (!isDragging.value && hoverCardId.value && hoverDot.value) {
    event.stopPropagation()
    event.preventDefault()
    handleBorderClick()
    return
  }

  // If dragging a connection, also check: the user may have clicked on a target card's
  // outline area. In that case dragTargetDot is set, so complete the connection.
  if (isDragging.value && dragTargetDot.value) {
    event.stopPropagation()
    event.preventDefault()
    handleBorderClick()
    return
  }

  // Start panning on whitespace mousedown (not on cards, not during connection drag)
  if (!isDragging.value && (event.target === canvas.value || event.target.classList.contains('zoom-wrapper'))) {
    isPanning.value = true
    panStart.value = { x: event.clientX, y: event.clientY, panX: panX.value, panY: panY.value }
    event.preventDefault()
  }
}

// Handle canvas click - focus, or handle connection border click / drop into empty space
function handleCanvasClick(event) {
  // Close endpoint popup on any canvas click
  endpointPopup.value = null

  // Suppress click after panning
  if (wasPanning.value) return

  // If drop menu is open and user clicks outside it, close it and cancel
  if (showDropMenu.value) {
    cancelDrag()
    return
  }

  // If dragging a connection line and clicking empty canvas space -> show drop menu
  if (isDragging.value && !dragTargetDot.value) {
    const pos = screenToCanvas(event.clientX, event.clientY)
    dropMenuPos.value = { x: pos.x, y: pos.y }
    showDropMenu.value = true
    return
  }

  if (event.target === canvas.value || event.target.classList.contains('zoom-wrapper')) {
    canvas.value?.focus()
    activeCardId.value = null
    floatingMenuOpen.value = false
    endpointPopup.value = null
  }
}

// Handle canvas double-click — open spawn menu at click position (same as connection drop menu)
function handleCanvasDblClick(event) {
  if (!currentEpisode.value) return
  if (isDragging.value || showDropMenu.value || wasPanning.value) return
  // Only trigger on empty canvas / zoom wrapper (not on cards)
  if (event.target !== canvas.value && !event.target.classList.contains('zoom-wrapper')) return
  const pos = screenToCanvas(event.clientX, event.clientY)
  dropMenuPos.value = { x: pos.x, y: pos.y }
  showDropMenu.value = true
}

// Open endpoint popup on connection endpoint dot click
function openEndpointPopup(linkId, end, x, y) {
  endpointPopup.value = { linkId, end, x, y }
}

// Handle "Disconnect this end" from endpoint popup
function handleDisconnectEnd() {
  if (!endpointPopup.value) return
  const { linkId, end } = endpointPopup.value
  endpointPopup.value = null
  disconnectEnd(linkId, end, cardElements.value)
}

// Handle "Destroy connection" from endpoint popup
function handleDestroyConnection() {
  if (!endpointPopup.value) return
  const { linkId } = endpointPopup.value
  endpointPopup.value = null
  deleteLink(linkId)
  // Fully exit connection mode — clear all drag/hover state
  cancelDrag()
  hoverCardId.value = null
  hoverDot.value = null
}

// Handle paste
function handlePaste(event) {
  // If drop menu is open, handle paste-to-link
  if (showDropMenu.value && handleDropPaste(event)) {
    return
  }

  const items = event.clipboardData?.items
  if (!items) return

  let handledPaste = false

  // Check for images first
  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      const blob = item.getAsFile()
      const reader = new FileReader()
      reader.onload = (e) => {
        const rect = canvas.value?.getBoundingClientRect()
        cards.value.push({
          id: nextId++,
          type: 'image',
          imageUrl: e.target.result,
          caption: '',
          notes: '',
          title: '',
          x: rect ? rect.width / 2 - 300 : 100,
          y: rect ? rect.height / 2 - 150 : 100,
          width: 600,
          collapsed: false
        })
      }
      reader.readAsDataURL(blob)
      handledPaste = true
      break
    }
  }

  // Check for HTML content
  if (!handledPaste) {
    for (const item of items) {
      if (item.type === 'text/html') {
        item.getAsString((text) => {
          const rect = canvas.value?.getBoundingClientRect()
          cards.value.push({
            id: nextId++,
            type: 'html',
            htmlContent: text,
            title: '',
            x: rect ? rect.width / 2 - 300 : 100,
            y: rect ? rect.height / 2 - 100 : 100,
            width: 600,
            collapsed: false
          })
        })
        handledPaste = true
        break
      }
    }
  }

  // If no image or HTML, check for text
  if (!handledPaste) {
    for (const item of items) {
      if (item.type === 'text/plain') {
        item.getAsString(async (text) => {
          const rect = canvas.value?.getBoundingClientRect()

          // Detect HTML tags in plain text
          if (text.match(/<[a-z][\s\S]*>/i)) {
            cards.value.push({
              id: nextId++,
              type: 'html',
              htmlContent: text,
              title: '',
              x: rect ? rect.width / 2 - 300 : 100,
              y: rect ? rect.height / 2 - 100 : 100,
              width: 600,
              collapsed: false
            })
          }
          // Detect URLs
          else if (text.match(/^https?:\/\//)) {
            const newCard = {
              id: nextId++,
              type: 'link',
              url: text,
              notes: '',
              x: rect ? rect.width / 2 - 250 : 100,
              y: rect ? rect.height / 2 - 100 : 100,
              width: 500,
              collapsed: false,
              previewTitle: null,
              previewDescription: null,
              previewImage: null,
              previewDomain: null,
              previewFavicon: null,
              fetchingPreview: false,
              socialMetadata: null
            }
            cards.value.push(newCard)

            // Analyze URL for smart child spawning
            try {
              const analysis = await fetchJson(`/api/whiteboard/analyze-url?url=${encodeURIComponent(text)}`)

              if (analysis.spawn_children && analysis.has_media) {
                // Download media and spawn child nodes
                const downloadResult = await fetchJson(`/api/whiteboard/${identifier.value}/download-social-media?url=${encodeURIComponent(text)}`, {
                  method: 'POST'
                })

                if (downloadResult.assets && downloadResult.assets.length > 0) {
                  // Spawn child nodes for each media file
                  downloadResult.assets.forEach((asset, index) => {
                    let childCard
                    if (asset.media_category === 'video') {
                      childCard = {
                        id: nextId++,
                        type: 'video',
                        videoUrl: asset.file_url,
                        assetId: asset.asset_id,
                        title: asset.source_context?.title || 'Video',
                        notes: '',
                        x: newCard.x + 550 + (index * 20),
                        y: newCard.y + (index * 20),
                        width: 640,
                        collapsed: false,
                        parentId: newCard.id
                      }
                    } else if (asset.media_category === 'audio') {
                      childCard = {
                        id: nextId++,
                        type: 'audio',
                        audioUrl: asset.file_url,
                        assetId: asset.asset_id,
                        title: asset.source_context?.title || 'Audio',
                        notes: '',
                        x: newCard.x + 550 + (index * 20),
                        y: newCard.y + (index * 20),
                        width: 500,
                        collapsed: false,
                        parentId: newCard.id
                      }
                    } else if (asset.media_category === 'image') {
                      childCard = {
                        id: nextId++,
                        type: 'image',
                        imageUrl: asset.file_url,
                        assetId: asset.asset_id,
                        caption: asset.source_context?.title || '',
                        notes: '',
                        title: '',
                        x: newCard.x + 550 + (index * 20),
                        y: newCard.y + (index * 20),
                        width: 600,
                        collapsed: false,
                        parentId: newCard.id
                      }
                    }
                    if (childCard) {
                      cards.value.push(childCard)
                    }
                  })
                  notifyUserStandard(`Downloaded ${downloadResult.assets.length} media file(s) from ${analysis.service}`, NOTIFICATION_COLORS.success)
                }
              }
            } catch (error) {
              console.error('Error analyzing URL:', error)
            }

            // Also fetch link preview
            fetchLinkPreview(newCard)
          }
          // Detect Markdown
          else if (text.match(/^(#{1,6}\s)|(\*\*.*\*\*)|(__.*__)|(\[.*\]\(.*\))/m)) {
            cards.value.push({
              id: nextId++,
              type: 'markdown',
              markdownContent: text,
              title: '',
              x: rect ? rect.width / 2 - 300 : 100,
              y: rect ? rect.height / 2 - 100 : 100,
              width: 600,
              collapsed: false
            })
          }
          // Detect code (function, class, import statements, etc.)
          else if (text.match(/(function\s+\w+|class\s+\w+|import\s+|const\s+\w+\s*=|def\s+\w+|public\s+class)/)) {
            const lang = text.match(/import\s+/) ? 'javascript' :
                        text.match(/def\s+\w+/) ? 'python' :
                        text.match(/public\s+class/) ? 'java' : 'javascript'
            cards.value.push({
              id: nextId++,
              type: 'code',
              codeContent: text,
              codeLanguage: lang,
              title: '',
              x: rect ? rect.width / 2 - 350 : 100,
              y: rect ? rect.height / 2 - 150 : 100,
              width: 700,
              collapsed: false
            })
          }
          // Regular text
          else {
            cards.value.push({
              id: nextId++,
              type: 'text',
              content: text,
              title: '',
              x: rect ? rect.width / 2 - 250 : 100,
              y: rect ? rect.height / 2 - 100 : 100,
              width: 500,
              collapsed: false
            })
          }
        })
        handledPaste = true
        break
      }
    }
  }

  if (handledPaste) {
    event.preventDefault()
  }
}

// Handle drop
function handleDrop(event) {
  event.preventDefault()

  const files = event.dataTransfer.files
  if (files && files.length > 0) {
    const rect = canvas.value.getBoundingClientRect()
    Array.from(files).forEach((file, index) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => {
          cards.value.push({
            id: nextId++,
            type: 'image',
            imageUrl: e.target.result,
            caption: '',
            notes: '',
            title: '',
            x: event.clientX - rect.left - 300 + (index * 20),
            y: event.clientY - rect.top - 150 + (index * 20),
            width: 600,
            collapsed: false
          })
        }
        reader.readAsDataURL(file)
      }
    })
  }
}

// Handle keyboard shortcuts
function handleKeyDown(event) {
  // Block shortcuts when no episode selected
  if (!currentEpisode.value) return
  // Don't trigger if user is typing in a field
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
    return
  }

  // Don't intercept Ctrl+V, Ctrl+C, etc. (let browser handle paste/copy)
  if (event.ctrlKey || event.metaKey) {
    return
  }

  if (event.key === 't' || event.key === 'T') {
    event.preventDefault()
    addTextCard()
  } else if (event.key === 'l' || event.key === 'L') {
    event.preventDefault()
    addLinkCard()
  } else if (event.key === 'i' || event.key === 'I') {
    event.preventDefault()
    triggerImageUpload()
  } else if (event.key === 'v' || event.key === 'V') {
    event.preventDefault()
    triggerVideoUpload()
  } else if (event.key === 'a' || event.key === 'A') {
    event.preventDefault()
    triggerAudioUpload()
  } else if (event.key === 'h' || event.key === 'H') {
    event.preventDefault()
    addHtmlCard()
  } else if (event.key === 'c' || event.key === 'C') {
    event.preventDefault()
    addCodeCard()
  } else if (event.key === 'm' || event.key === 'M') {
    event.preventDefault()
    addMarkdownCard()
  } else if (event.key === 'p' || event.key === 'P') {
    event.preventDefault()
    showParentMenu.value = !showParentMenu.value
  } else if (event.key === 'Escape') {
    event.preventDefault()
    // Fully exit connection mode and any popups
    cancelDrag()
    hoverCardId.value = null
    hoverDot.value = null
    endpointPopup.value = null
    showParentMenu.value = false
  } else if (event.key === 'Delete' && activeCardId.value) {
    event.preventDefault()
    deleteCard(activeCardId.value)
  }
}

// Convert screen coordinates to canvas coordinates (accounting for zoom and pan)
function screenToCanvas(clientX, clientY) {
  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return { x: clientX, y: clientY }
  return {
    x: (clientX - rect.left - panX.value) / zoomLevel.value,
    y: (clientY - rect.top - panY.value) / zoomLevel.value
  }
}

// Track mouse position on canvas for border detection and rubber-band line
function handleCanvasMouseMove(event) {
  // Handle panning
  if (isPanning.value) {
    const dx = event.clientX - panStart.value.x
    const dy = event.clientY - panStart.value.y
    panX.value = panStart.value.panX + dx
    panY.value = panStart.value.panY + dy
    return
  }
  const pos = screenToCanvas(event.clientX, event.clientY)
  handleMouseMove(pos.x, pos.y, cardElements.value)
}

// Stop panning
function handleCanvasMouseUp() {
  if (isPanning.value) {
    // Check if we actually moved (not just a click)
    const dx = Math.abs(panX.value - panStart.value.panX)
    const dy = Math.abs(panY.value - panStart.value.panY)
    if (dx > 3 || dy > 3) {
      wasPanning.value = true
      setTimeout(() => { wasPanning.value = false }, 50)
    }
  }
  isPanning.value = false
}

// Start dragging
function startDrag(event, card) {
  // Don't drag if clicking on input fields
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
    return
  }

  // Check if we're near a card border (connection dot is visible)
  // If so, start a connection instead of dragging the card.
  if (hoverCardId.value === card.id && hoverDot.value) {
    event.stopPropagation()
    event.preventDefault()
    handleBorderClick()
    return
  }

  // If dragging a connection and clicking on ANY card (not the source),
  // force-complete the connection by computing the border point at click time.
  // This is more forgiving than requiring the mouse to be exactly on the border zone.
  if (isDragging.value && dragAnchor.value && card.id !== dragAnchor.value.cardId) {
    event.stopPropagation()
    event.preventDefault()
    forceCompleteConnection(card.id, cardElements.value)
    return
  }

  dragging.value = true
  dragCard.value = card
  activeCardId.value = card.id

  const rect = event.currentTarget.getBoundingClientRect()
  dragOffset.value = {
    x: (event.clientX - rect.left) / zoomLevel.value,
    y: (event.clientY - rect.top) / zoomLevel.value
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

// Drag
function onDrag(event) {
  if (!dragging.value || !dragCard.value) return

  const pos = screenToCanvas(event.clientX, event.clientY)
  dragCard.value.x = pos.x - dragOffset.value.x
  dragCard.value.y = pos.y - dragOffset.value.y
}

// Stop dragging
function stopDrag() {
  dragging.value = false
  dragCard.value = null
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// Zoom in/out (continuous, centered on mouse or viewport center)
function zoomIn() {
  zoomAtPoint(zoomLevel.value * 1.15, null)
}

function zoomOut() {
  zoomAtPoint(zoomLevel.value / 1.15, null)
}

// Zoom toward a specific screen point (or viewport center if null)
function zoomAtPoint(newZoom, screenPoint) {
  const minZoom = 0.1
  const maxZoom = 5.0
  newZoom = Math.max(minZoom, Math.min(maxZoom, newZoom))

  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) {
    zoomLevel.value = newZoom
    return
  }

  // Zoom toward the mouse position (or viewport center)
  const px = screenPoint ? screenPoint.x - rect.left : rect.width / 2
  const py = screenPoint ? screenPoint.y - rect.top : rect.height / 2

  // The canvas point under the cursor before zoom
  const canvasX = (px - panX.value) / zoomLevel.value
  const canvasY = (py - panY.value) / zoomLevel.value

  // After zoom, that same canvas point should stay under the cursor
  panX.value = px - canvasX * newZoom
  panY.value = py - canvasY * newZoom
  zoomLevel.value = newZoom
}

// Mouse wheel for zoom (no modifier key needed)
function handleCanvasWheel(event) {
  event.preventDefault()
  const factor = event.deltaY < 0 ? 1.08 : 1 / 1.08
  zoomAtPoint(zoomLevel.value * factor, { x: event.clientX, y: event.clientY })
}

// Add parent node card
function addParentNode(parentType) {
  const rect = canvas.value?.getBoundingClientRect()
  const pos = rect ? {
    x: (rect.width / 2 - panX.value) / zoomLevel.value - 90,
    y: (rect.height / 2 - panY.value) / zoomLevel.value - 90
  } : { x: 100, y: 100 }

  cards.value.push({
    id: nextId++,
    type: 'parent',
    title: parentType.name,
    content: '',
    x: pos.x,
    y: pos.y,
    width: 300,
    collapsed: false,
    socialMetadata: {
      parentNodeType: parentType.name,
      parentNodeColor: parentType.color,
      parentNodeIcon: parentType.icon
    }
  })
  showParentMenu.value = false
}

// Get child count for a parent node
function getChildCount(cardId) {
  return nodeLinks.value.filter(l => l.sourceCardId === cardId || l.targetCardId === cardId).length
}

// Spawn a new card from the drop menu (connection drag dropped into empty space)
function spawnFromDrop(type, parentType = null) {
  const x = dropMenuPos.value.x
  const y = dropMenuPos.value.y
  const newCard = {
    id: nextId++,
    type,
    title: '',
    x,
    y,
    collapsed: false
  }

  if (type === 'text') {
    newCard.content = ''
    newCard.width = 500
  } else if (type === 'link') {
    newCard.url = ''
    newCard.notes = ''
    newCard.width = 500
    newCard.previewTitle = null
    newCard.previewDescription = null
    newCard.previewImage = null
    newCard.previewDomain = null
    newCard.previewFavicon = null
    newCard.fetchingPreview = false
    newCard.socialMetadata = null
  } else if (type === 'image') {
    newCard.imageUrl = ''
    newCard.caption = ''
    newCard.notes = ''
    newCard.width = 600
  } else if (type === 'video') {
    newCard.videoUrl = ''
    newCard.notes = ''
    newCard.width = 640
  } else if (type === 'audio') {
    newCard.audioUrl = ''
    newCard.notes = ''
    newCard.width = 500
  } else if (type === 'html') {
    newCard.htmlContent = ''
    newCard.width = 600
  } else if (type === 'code') {
    newCard.codeContent = ''
    newCard.codeLanguage = 'javascript'
    newCard.width = 700
  } else if (type === 'markdown') {
    newCard.markdownContent = ''
    newCard.width = 600
  } else if (type === 'parent' && parentType) {
    newCard.content = ''
    newCard.width = 300
    newCard.title = parentType.name
    newCard.socialMetadata = {
      parentNodeType: parentType.name,
      parentNodeColor: parentType.color,
      parentNodeIcon: parentType.icon
    }
  }

  cards.value.push(newCard)
  completeDropConnection(newCard.id)
}

// Handle Ctrl+V while drop menu is open -> paste content and auto-link
function handleDropPaste(event) {
  if (!showDropMenu.value || !isDragging.value) return false

  const items = event.clipboardData?.items
  if (!items) return false

  event.preventDefault()
  const x = dropMenuPos.value.x
  const y = dropMenuPos.value.y

  // Check for images
  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      const blob = item.getAsFile()
      const reader = new FileReader()
      reader.onload = (e) => {
        const newCard = {
          id: nextId++,
          type: 'image',
          imageUrl: e.target.result,
          caption: '',
          notes: '',
          title: '',
          x,
          y,
          width: 600,
          collapsed: false
        }
        cards.value.push(newCard)
        completeDropConnection(newCard.id)
      }
      reader.readAsDataURL(blob)
      return true
    }
  }

  // Check for text
  for (const item of items) {
    if (item.type === 'text/plain') {
      item.getAsString((text) => {
        let newCard
        if (text.match(/^https?:\/\//)) {
          newCard = {
            id: nextId++,
            type: 'link',
            url: text,
            notes: '',
            title: '',
            x,
            y,
            width: 500,
            collapsed: false,
            previewTitle: null,
            previewDescription: null,
            previewImage: null,
            previewDomain: null,
            previewFavicon: null,
            fetchingPreview: false,
            socialMetadata: null
          }
        } else if (text.match(/<[a-z][\s\S]*>/i)) {
          newCard = {
            id: nextId++,
            type: 'html',
            htmlContent: text,
            title: '',
            x,
            y,
            width: 600,
            collapsed: false
          }
        } else if (text.match(/^(#{1,6}\s)|(\*\*.*\*\*)|(__.*__)|(\[.*\]\(.*\))/m)) {
          newCard = {
            id: nextId++,
            type: 'markdown',
            markdownContent: text,
            title: '',
            x,
            y,
            width: 600,
            collapsed: false
          }
        } else {
          newCard = {
            id: nextId++,
            type: 'text',
            content: text,
            title: '',
            x,
            y,
            width: 500,
            collapsed: false
          }
        }
        cards.value.push(newCard)
        completeDropConnection(newCard.id)

        // Auto-fetch link preview if link
        if (newCard.type === 'link') {
          fetchLinkPreview(newCard)
        }
      })
      return true
    }
  }

  return false
}

// Computed: rendered link lines with coordinates
// Depends on collapseGeneration to recompute when cards collapse/expand (changes DOM dimensions)
const renderedLinks = computed(() => {
  void collapseGeneration.value // reactive dependency — forces recompute on collapse/expand
  return nodeLinks.value.map(link => {
    const coords = getLineCoords(link, cardElements.value)
    if (!coords) return null
    return { ...link, ...coords }
  }).filter(Boolean)
})

// Confirm delete (shows dialog)
function confirmDelete(id) {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

// Execute delete (after confirmation)
function executeDelete() {
  if (deleteTargetId.value !== null) {
    deleteLinksForCard(deleteTargetId.value)
    cards.value = cards.value.filter(c => c.id !== deleteTargetId.value)
    if (activeCardId.value === deleteTargetId.value) {
      activeCardId.value = null
    }
  }
  showDeleteConfirm.value = false
  deleteTargetId.value = null
}

// Delete card (legacy direct delete for keyboard shortcut)
function deleteCard(id) {
  deleteLinksForCard(id)
  cards.value = cards.value.filter(c => c.id !== id)
  if (activeCardId.value === id) {
    activeCardId.value = null
  }
}

// Clear all
function clearAll() {
  if (confirm('Clear all items from the board?')) {
    cards.value = []
    nodeLinks.value = []
    activeCardId.value = null
    notifyUserStandard('Board cleared', NOTIFICATION_COLORS.INFO, 3000)
  }
}

// Debounced save
function debouncedSave() {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    saveBoard()
  }, 2000) // 2 second debounce
}

// Save whiteboard
async function saveBoard() {
  if (!currentEpisode.value) {
    // No episode selected, use localStorage only
    try {
      localStorage.setItem('whiteboard-cards', JSON.stringify(cards.value))
      lastSaved.value = new Date()
    } catch (error) {
      console.error('Failed to save to localStorage:', error)
    }
    return
  }

  if (saving.value) return

  try {
    saving.value = true

    // Convert cards to API format
    const items = cards.value.map(card => ({
      item_type: card.type,
      title: card.title || null,
      x_position: card.x,
      y_position: card.y,
      text_content: card.content || null,
      url: card.url || null,
      notes: card.notes || null,
      image_data: card.imageUrl || null,
      caption: card.caption || null,
      width: card.width || null,
      z_index: card.id === activeCardId.value ? 1000 : 1,
      collapsed: card.collapsed || false,
      // Link preview fields
      preview_title: card.previewTitle || null,
      preview_description: card.previewDescription || null,
      preview_image: card.previewImage || null,
      preview_domain: card.previewDomain || null,
      preview_favicon: card.previewFavicon || null,
      // Social media metadata
      social_metadata: card.socialMetadata || null
    }))

    // Prepare node links for save (map card IDs to array indices)
    const node_links = getLinksForSave(cards.value)

    const response = await fetchJson(`/api/whiteboard/${currentEpisode.value}/save`, {
      method: 'POST',
      body: JSON.stringify({ items, node_links })
    })

    scratchpadId.value = response.whiteboard_id
    lastSaved.value = new Date()
  } catch (error) {
    console.error('Failed to save whiteboard:', error)
    notifyUserStandard('Failed to save whiteboard', NOTIFICATION_COLORS.ERROR, 3000)
  } finally {
    saving.value = false
  }
}

// Load whiteboard
async function loadBoard() {
  if (!currentEpisode.value) {
    // No episode selected, use localStorage
    try {
      const saved = localStorage.getItem('whiteboard-cards')
      if (saved) {
        cards.value = JSON.parse(saved)
        if (cards.value.length > 0) {
          nextId = Math.max(...cards.value.map(c => c.id)) + 1
        }
      }
    } catch (error) {
      console.error('Failed to load from localStorage:', error)
    }
    return
  }

  try {
    const response = await fetchJson(`/api/whiteboard/${currentEpisode.value}`)

    scratchpadId.value = response.id

    // Convert API format to cards
    cards.value = response.items.map(item => {
      const card = {
        id: nextId++,
        type: item.item_type,
        title: item.title || '',
        x: item.x_position,
        y: item.y_position,
        width: item.width,
        collapsed: item.collapsed || false
      }

      if (item.item_type === 'text') {
        card.content = item.text_content || ''
      } else if (item.item_type === 'link') {
        card.url = item.url || ''
        card.notes = item.notes || ''
        // Restore link preview metadata
        card.previewTitle = item.preview_title || null
        card.previewDescription = item.preview_description || null
        card.previewImage = item.preview_image || null
        card.previewDomain = item.preview_domain || null
        card.previewFavicon = item.preview_favicon || null
        card.fetchingPreview = false
        // Restore social media metadata
        card.socialMetadata = item.social_metadata || null
        // Restore cache metadata (will trigger cached badge if true)
        card._cached = item.social_metadata?._cached || false
        card._cached_at = item.social_metadata?._cached_at || null
      } else if (item.item_type === 'image') {
        card.imageUrl = item.image_data
        card.caption = item.caption || ''
        card.notes = item.notes || ''
      } else if (item.item_type === 'video') {
        card.videoUrl = item.video_url || item.url || ''
        card.assetId = item.asset_id || ''
        card.notes = item.notes || ''
      } else if (item.item_type === 'audio') {
        card.audioUrl = item.audio_url || item.url || ''
        card.assetId = item.asset_id || ''
        card.notes = item.notes || ''
      } else if (item.item_type === 'html') {
        card.htmlContent = item.html_content || item.text_content || ''
      } else if (item.item_type === 'code') {
        card.codeContent = item.code_content || item.text_content || ''
        card.codeLanguage = item.code_language || 'javascript'
      } else if (item.item_type === 'markdown') {
        card.markdownContent = item.markdown_content || item.text_content || ''
      } else if (item.item_type === 'parent') {
        card.content = item.text_content || ''
      }

      return card
    })

    // Load node links (map DB indices back to client card IDs)
    if (response.node_links) {
      loadLinks(response.node_links, cards.value)
    }

  } catch (error) {
    console.error('Failed to load whiteboard:', error)
    notifyUserStandard('Failed to load whiteboard', NOTIFICATION_COLORS.ERROR, 3000)
  }
}

// Fetch episodes for selector
async function fetchEpisodes() {
  loadingEpisodes.value = true
  try {
    const response = await axios.get('/api/episodes')
    if (response.data && response.data.episodes) {
      const activeStatuses = ['draft', 'production', 'promotion']
      episodeList.value = response.data.episodes
        .filter(ep => activeStatuses.includes((ep.status || '').toLowerCase()))
        .map(ep => ({
          title: `${ep.episode_number} — ${ep.title || 'Untitled'}`,
          value: ep.episode_number
        }))
    }
  } catch (error) {
    console.error('Failed to load episodes:', error)
    notifyUserStandard('Failed to load episode list', NOTIFICATION_COLORS.ERROR, 3000)
  } finally {
    loadingEpisodes.value = false
  }
}

// Open episode selector
function openEpisodeSelector(saveAfter = false) {
  pendingSaveAfterSelect.value = saveAfter
  fetchEpisodes()
  showEpisodeDialog.value = true
}

// Confirm episode selection
async function confirmEpisodeSelection() {
  if (!selectedEpisodeValue.value) return

  const ep = selectedEpisodeValue.value
  sessionStorage.setItem('currentEpisode', ep)
  sessionStorage.setItem('currentEpisodeId', ep)

  // Update URL query param so identifier computed picks it up
  await router.replace({ query: { ...route.query, episode: ep } })

  showEpisodeDialog.value = false
  notifyUserStandard(`Episode ${ep} selected`, NOTIFICATION_COLORS.SUCCESS, 3000)

  // Reload board for the new episode
  await loadBoard()

  // If save was pending, do it now
  if (pendingSaveAfterSelect.value) {
    pendingSaveAfterSelect.value = false
    await saveBoard()
  }
}

// Menu-triggered save — prompts for episode if none selected
function handleMenuSave() {
  if (!currentEpisode.value) {
    openEpisodeSelector(true)
  } else {
    saveBoard()
  }
}

// Handle episode created from scaffold modal
async function handleEpisodeCreated(episode) {
  const epNum = episode?.episode_number || episode
  if (epNum) {
    sessionStorage.setItem('currentEpisode', epNum)
    sessionStorage.setItem('currentEpisodeId', epNum)
    await router.replace({ query: { ...route.query, episode: epNum } })
    notifyUserStandard(`Episode ${epNum} created and selected`, NOTIFICATION_COLORS.SUCCESS, 3000)
    await loadBoard()
  }
}

// Refresh board
async function refreshBoard() {
  await loadBoard()
  notifyUserStandard('Whiteboard refreshed', NOTIFICATION_COLORS.INFO, 3000)
}

// Format time
function formatTime(date) {
  return date.toLocaleTimeString()
}

// Format date for social media posts
function formatDate(dateString) {
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m`
    if (diffHours < 24) return `${diffHours}h`
    if (diffDays < 7) return `${diffDays}d`

    // Format as date
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch (e) {
    return ''
  }
}

// Fetch link preview
async function fetchLinkPreview(card, bypassCache = false) {
  if (!card.url || !card.url.match(/^https?:\/\//)) {
    return
  }

  // CRITICAL: If card already has social metadata or preview data, skip the API call.
  // Data is fully persisted in the database — no need to re-fetch from X/Twitter API.
  if (!bypassCache && (card.socialMetadata || card.previewTitle || card.previewImage)) {
    return
  }

  // Check if already fetching
  if (card.fetchingPreview) {
    return
  }

  try {
    card.fetchingPreview = true

    const url = `/api/whiteboard/fetch-link-preview?url=${encodeURIComponent(card.url)}${bypassCache ? '&bypass_cache=true' : ''}`
    const response = await fetchJson(url, { method: 'POST' })

    if (response && !response.error) {
      card.previewTitle = response.title || null
      card.previewDescription = response.description || null
      card.previewImage = response.image || null
      card.previewDomain = response.domain || null
      card.previewFavicon = response.favicon || null

      // Store cache metadata
      card._cached = response._cached || false
      card._cached_at = response._cached_at || null

      // Extract social metadata (X/Twitter, etc.)
      // All x_* fields from backend get collected into socialMetadata
      const socialMetadata = {}
      for (const [key, value] of Object.entries(response)) {
        if (key.startsWith('x_') && value) {
          // Remove 'x_' prefix and store
          socialMetadata[key.substring(2)] = value
        }
      }

      if (Object.keys(socialMetadata).length > 0) {
        card.socialMetadata = socialMetadata
      }
    } else {
      console.warn('Failed to fetch link preview:', response?.error)
    }
  } catch (error) {
    console.error('Error fetching link preview:', error)
  } finally {
    card.fetchingPreview = false
  }
}

// Reload link preview from server (bypass cache)
async function reloadFromServer(card) {
  await fetchLinkPreview(card, true)
  notifyUserStandard('Reloaded from server', NOTIFICATION_COLORS.SUCCESS, 2000)
}

// Watch for URL changes in link cards and auto-fetch preview
watch(cards, (newCards, oldCards) => {
  newCards.forEach((newCard, index) => {
    if (newCard.type === 'link' && newCard.url) {
      // Skip if card already has fetched data (loaded from DB)
      if (newCard.socialMetadata || newCard.previewTitle || newCard.previewImage) {
        return
      }
      const oldCard = oldCards?.[index]
      // Check if URL changed
      if (!oldCard || oldCard.url !== newCard.url) {
        // Debounce: only fetch if URL hasn't changed for 1 second
        if (newCard._urlChangeTimeout) {
          clearTimeout(newCard._urlChangeTimeout)
        }
        newCard._urlChangeTimeout = setTimeout(() => {
          fetchLinkPreview(newCard)
        }, 1000)
      }
    }
  })
}, { deep: true })
</script>

<style scoped>
.scratchpad-container {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

.whiteboard-canvas {
  flex: 1;
  position: relative;
  background:
    linear-gradient(90deg, rgba(200, 200, 200, 0.1) 1px, transparent 1px),
    linear-gradient(rgba(200, 200, 200, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  overflow: hidden;
  outline: none;
  cursor: grab;
}

.whiteboard-canvas:active {
  cursor: grabbing;
}

.help-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}

.help-overlay kbd {
  background: #f5f5f5;
  border: 1px solid #ccc;
  border-radius: 3px;
  padding: 2px 6px;
  font-family: monospace;
  font-size: 0.9em;
}

/* Floating options menu - top-left of canvas */
.floating-menu {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 16px;
}

.floating-menu-btn {
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.floating-menu-btn:hover {
  transform: scale(1.08);
}

.floating-menu-btn.menu-open {
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.3) !important;
}

.rotate-90 {
  transform: rotate(90deg);
  transition: transform 0.25s ease;
}

/* Flyout bar - horizontal row of action buttons with labels */
.flyout-bar {
  display: flex;
  align-items: flex-start;
  gap: 28px;
}

.flyout-action-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.flyout-action-wrapper.flyout-disabled {
  opacity: 0.45;
  pointer-events: none;
}

.flyout-action {
  transition: transform 0.15s ease;
}

.flyout-action-wrapper:hover .flyout-action {
  transform: scale(1.1);
}

.flyout-label {
  margin-top: 3px;
  font-size: 0.65rem;
  font-weight: 600;
  color: #424242;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  user-select: none;
}

/* Flyout transition */
.flyout-enter-active {
  transition: opacity 0.2s ease, transform 0.25s ease;
}

.flyout-leave-active {
  transition: opacity 0.15s ease, transform 0.2s ease;
}

.flyout-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}

.flyout-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

.card-item {
  cursor: move;
  transition: box-shadow 0.2s;
}

.card-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

.text-card {
  background: #fffbcc;
}

.link-card {
  background: #e3f2fd;
}

.image-card {
  background: white;
}

.border-b {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.border-t {
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

/* Fix text field fade at top */
.text-field-no-fade :deep(.v-field) {
  padding-top: 0 !important;
}

.text-field-no-fade :deep(.v-field__input) {
  padding-top: 0 !important;
  mask-image: none !important;
  -webkit-mask-image: none !important;
  align-items: flex-start !important;
}

.text-field-no-fade :deep(.v-field__field) {
  padding-top: 0 !important;
  align-items: flex-start !important;
}

.text-field-no-fade :deep(.v-input__control) {
  padding-top: 0 !important;
}

.text-field-no-fade :deep(textarea) {
  padding-top: 0 !important;
  margin-top: 0 !important;
  line-height: 1.5 !important;
}

.text-field-no-fade :deep(input) {
  padding-top: 0 !important;
  margin-top: 0 !important;
}

/* Ensure consistent text alignment */
.v-card-text {
  overflow: visible !important;
}

/* Episode required overlay — blocks canvas until episode selected */
.episode-required-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(158, 158, 158, 0.15);
  backdrop-filter: blur(2px);
}

/* Disabled canvas — grey and non-interactive */
.canvas-disabled {
  pointer-events: none;
  background: #e0e0e0 !important;
}

/* Link preview box (Facebook-style) */
.link-preview-box {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  overflow: hidden;
  background: white;
  transition: box-shadow 0.2s;
}

.link-preview-box:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.link-preview-image {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.link-preview-content {
  background: #f8f9fa;
}

/* Text line clamping */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Link card scrollable content (expanded Twitter/X cards) */
.link-card-content {
  max-height: 500px !important;
  overflow-y: auto !important;
}

/* Twitter/X Preview Box */
.twitter-preview-box {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: box-shadow 0.2s;
}

.twitter-preview-box:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.twitter-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.twitter-media {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  background: rgba(0, 0, 0, 0.08);
}

.twitter-media-single {
  grid-template-columns: 1fr;
}

.twitter-media-image {
  border-radius: 0;
  width: 100%;
  object-fit: cover;
  display: block;
}

/* Editable title styling */
.editable-title :deep(.v-field) {
  padding: 0 !important;
  min-height: unset !important;
}

.editable-title :deep(.v-field__input) {
  padding: 0 !important;
  min-height: unset !important;
  font-size: inherit !important;
  font-weight: inherit !important;
}

.editable-title :deep(.v-field__field) {
  padding: 0 !important;
}

/* Collapsed thumbnail for link cards */
.collapsed-thumbnail {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.collapsed-overlay {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.x-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 10;
}

.collapsed-badge {
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.collapsed-thumbnail {
  border-radius: 4px;
  background: #f5f5f5;
}

.collapsed-icon-fallback {
  width: 160px;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(25, 118, 210, 0.1);
  border-radius: 8px;
  cursor: pointer;
}

.collapsed-icon-fallback:hover {
  background: rgba(25, 118, 210, 0.2);
}

.collapsed-icon-container {
  width: 160px;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapsed-icon-container:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Add smooth transition to card width */
.link-card {
  transition: width 0.3s ease;
}

.editable-title :deep(input) {
  padding: 0 !important;
}

/* === SVG Connection Layer === */
.connection-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
  overflow: visible;
}

.connection-label {
  font-size: 12px;
  font-weight: 600;
  paint-order: stroke;
  stroke: white;
  stroke-width: 3px;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* === Border-hover connection system === */

/* Invisible thick border becomes visible on hover */
.card-border-glow {
  outline: 9px solid rgba(25, 118, 210, 0.45) !important;
  outline-offset: 2px;
  border-radius: 6px;
  transition: outline 0.15s ease;
}

/* Yellow border glow on target card during connection drag */
.card-border-glow-yellow {
  outline: 9px solid rgba(255, 193, 7, 0.6) !important;
  outline-offset: 2px;
  border-radius: 6px;
  transition: outline 0.15s ease;
}

/* Blue flash animation on successful connection */
@keyframes flash-blue {
  0% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); outline-color: transparent; }
  25% { box-shadow: 0 0 28px 6px rgba(25, 118, 210, 0.7); outline: 9px solid #1976d2; outline-offset: 2px; }
  50% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); outline-color: transparent; }
  75% { box-shadow: 0 0 28px 6px rgba(25, 118, 210, 0.7); outline: 9px solid #1976d2; outline-offset: 2px; }
  100% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); outline-color: transparent; }
}

.card-flash-blue {
  animation: flash-blue 0.6s ease-out;
  z-index: 1001 !important;
}

/* Source card yellow glow while connection is active */
.card-is-drag-source {
  outline: 9px solid rgba(255, 193, 7, 0.7) !important;
  outline-offset: 2px;
}

/* === Parent node connection glow (circle, not rectangular border) === */
.parent-glow-blue .parent-node-circle {
  background: #1565C0 !important;
  box-shadow: 0 0 20px 8px rgba(25, 118, 210, 0.5) !important;
}

.parent-glow-yellow .parent-node-circle {
  background: #FFC107 !important;
  color: #333 !important;
  box-shadow: 0 0 24px 10px rgba(255, 193, 7, 0.5) !important;
}

.parent-flash-blue .parent-node-circle {
  animation: parent-flash 0.6s ease-out;
}

@keyframes parent-flash {
  0% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); }
  25% { box-shadow: 0 0 30px 12px rgba(25, 118, 210, 0.8); }
  50% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); }
  75% { box-shadow: 0 0 30px 12px rgba(25, 118, 210, 0.8); }
  100% { box-shadow: 0 0 0 0 rgba(25, 118, 210, 0); }
}

/* Canvas cursor during connection drag */
.canvas-dragging-connection {
  cursor: crosshair !important;
}

/* Connection banner (drag in progress) */
.connection-mode-banner {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 60;
  background: rgba(25, 118, 210, 0.9);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.connection-mode-banner kbd {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.4);
  border-radius: 3px;
  padding: 1px 4px;
  font-family: monospace;
  font-size: 0.85em;
}

/* Drop-into-empty-space spawn menu */
.drop-spawn-menu {
  position: absolute;
  z-index: 1100;
  transform: translate(-50%, 0);
}

.drop-menu-card {
  border: 2px solid #1976d2 !important;
  border-radius: 12px !important;
  overflow: hidden;
}

.endpoint-popup {
  position: absolute;
  transform: translate(-50%, -100%) translateY(-12px);
  z-index: 2000;
  pointer-events: all;
}

.endpoint-popup-card {
  border: 2px solid #757575 !important;
  border-radius: 10px !important;
  overflow: hidden;
}

.drop-menu-card kbd {
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 3px;
  padding: 1px 4px;
  font-family: monospace;
  font-size: 0.85em;
}

/* === Zoom Wrapper === */
.zoom-wrapper {
  min-height: 100%;
  min-width: 100%;
}

/* === Parent Node Card === */
/* === Parent Node Circle === */
.parent-node-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #1565C0;
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(21, 101, 192, 0.4);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
  text-align: center;
  padding: 16px;
  user-select: none;
}

.parent-node-circle:hover {
  box-shadow: 0 6px 24px rgba(21, 101, 192, 0.55);
  transform: scale(1.02);
}

.parent-node-type {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.2;
}

.parent-node-slug {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

.parent-node-input {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 4px;
  color: white;
  font-size: 0.75rem;
  text-align: center;
  padding: 3px 6px;
  width: 130px;
  margin-top: 4px;
  outline: none;
}

.parent-node-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.parent-node-input:focus {
  border-color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.25);
}

.parent-node-desc {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  color: white;
  font-size: 0.8rem;
  text-align: center;
  padding: 4px 6px;
  width: 170px;
  margin-top: 3px;
  outline: none;
  resize: none;
  line-height: 1.3;
}

.parent-node-desc::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.parent-node-desc:focus {
  border-color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.2);
}

.parent-node-delete {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  margin-top: 4px;
}

.parent-node-delete:hover {
  color: #ff8a80;
}

/* === Collapsed Pill Layout === */
.collapsed-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 2px solid;
  border-radius: 8px;
  cursor: pointer;
  min-height: 48px;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}

.collapsed-pill:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transform: scale(1.02);
}

.collapsed-pill-icon {
  flex-shrink: 0;
}

.collapsed-pill-thumb {
  flex-shrink: 0;
  border-radius: 4px;
  object-fit: cover;
}

.collapsed-pill-tall {
  min-height: 64px;
  padding: 6px 10px;
}

.collapsed-pill-thumb-wide {
  flex-shrink: 0;
  width: 72px;
  height: 54px;
  border-radius: 4px;
  object-fit: cover;
}

.collapsed-pill-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.collapsed-pill-type {
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  line-height: 1;
}

.collapsed-pill-label {
  font-size: 0.75rem;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #424242;
  margin-top: 2px;
}

/* === Delete text button === */
.delete-text-btn {
  font-size: 0.65rem !important;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: #9e9e9e !important;
  text-transform: none !important;
  min-width: unset !important;
  padding: 0 4px !important;
}

.delete-text-btn:hover {
  color: #e53935 !important;
}
</style>
