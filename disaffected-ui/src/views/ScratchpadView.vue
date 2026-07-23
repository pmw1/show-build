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
        :disabled="zoomPct >= 400"
        @click="zoomIn({ duration: 150 })"
      ></v-btn>
      <v-chip
        size="small"
        variant="outlined"
        class="mx-1"
        style="cursor: pointer;"
        @click="setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 300 })"
        title="Reset zoom & pan"
      >{{ zoomPct }}%</v-chip>
      <v-btn
        size="small"
        variant="text"
        icon="mdi-magnify-minus"
        :disabled="zoomPct <= 5"
        @click="zoomOut({ duration: 150 })"
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

    <!-- Delete Confirmation Dialog. While it is open, every would-be-deleted
         node on the canvas is dimmed, desaturated, and pulses a red outline
         (.doomed-node) so the blast radius is unmistakable. -->
    <v-dialog v-model="showDeleteConfirm" max-width="420" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="error">mdi-alert</v-icon>
          {{ deleteTargetIds.length > 1 ? `Delete ${deleteTargetIds.length} Nodes` : 'Delete Node' }}
        </v-card-title>
        <v-card-text>
          <p class="delete-warning-headline mb-2">This is not undoable.</p>
          <p class="mb-2">You cannot <kbd>Ctrl</kbd>+<kbd>Z</kbd> your way out of this.</p>
          <p class="mb-0">
            {{ deleteTargetIds.length > 1
              ? `All ${deleteTargetIds.length} selected whiteboard nodes will be permanently deleted.`
              : 'The selected whiteboard node will be permanently deleted.' }}
            The affected {{ deleteTargetIds.length > 1 ? 'nodes are' : 'node is' }} pulsing red on the board.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancelDelete">Cancel</v-btn>
          <v-btn color="error" variant="elevated" @click="executeDelete">
            Delete {{ deleteTargetIds.length > 1 ? `${deleteTargetIds.length} Nodes` : '' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Whiteboard Canvas -->
    <div
      ref="canvas"
      class="whiteboard-canvas"
      :class="{
        'canvas-disabled': !currentEpisode,
        'canvas-dragging-connection': connecting,
        'layout-animating': autoArranging || layoutAnimating
      }"
      @dblclick="handlePaneDblClick"
      @paste="currentEpisode ? handlePaste($event) : null"
      @dragstart="handleCanvasDragStart"
      @dragend="internalDragActive = false"
      @dragover.prevent
      @drop="currentEpisode ? handleDrop($event) : null"
      @keydown="currentEpisode ? handleKeyDown($event) : null"
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

            <!-- Visualizer: hovering reveals the layout modes -->
            <div
              class="flyout-action-wrapper visualizer-wrapper"
              @mouseenter="visualizerMenuOpen = true"
              @mouseleave="visualizerMenuOpen = false"
            >
              <v-btn
                icon
                size="48"
                variant="elevated"
                color="white"
                elevation="3"
                class="flyout-action"
              >
                <v-icon size="24" color="primary">{{ currentVisualizer.icon }}</v-icon>
              </v-btn>
              <span class="flyout-label">Visualizer</span>

              <!-- Pop-down options -->
              <transition name="visualizer-drop">
                <div v-if="visualizerMenuOpen" class="visualizer-menu">
                  <div
                    v-for="viz in VISUALIZERS"
                    :key="viz.key"
                    class="visualizer-option"
                    :class="{ 'visualizer-option-active': activeVisualizer === viz.key }"
                    @click.stop="setVisualizer(viz.key)"
                  >
                    <v-icon size="18" class="me-2" :color="activeVisualizer === viz.key ? 'primary' : 'grey-darken-1'">{{ viz.icon }}</v-icon>
                    <div class="visualizer-option-body">
                      <span class="visualizer-option-label">{{ viz.label }}</span>
                      <span class="visualizer-option-desc">{{ viz.description }}</span>
                    </div>
                    <v-icon v-if="activeVisualizer === viz.key" size="16" color="primary">mdi-check</v-icon>
                  </div>
                </div>
              </transition>
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

      <!-- Node right-click context menu (screen-space overlay) -->
      <div
        v-if="contextMenu"
        class="node-context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
        @contextmenu.prevent
      >
        <v-card elevation="8" width="240" class="drop-menu-card">
          <v-list density="compact" class="pa-0">
            <v-list-item
              prepend-icon="mdi-pencil"
              :title="`Edit ${contextMenuTypeLabel}`"
              @click="editFromContextMenu"
            ></v-list-item>
            <v-divider></v-divider>
            <v-list-item
              prepend-icon="mdi-delete"
              title="Delete"
              class="text-red"
              @click="deleteFromContextMenu"
            ></v-list-item>
            <v-list-item
              v-if="contextMenuBranchCount > 0"
              prepend-icon="mdi-delete-sweep"
              :title="`Delete Full Branch (${contextMenuBranchCount + 1} nodes)`"
              class="text-red"
              @click="deleteBranchFromContextMenu"
            ></v-list-item>
          </v-list>
        </v-card>
      </div>

      <!-- Drag-to-connect Indicator -->
      <div v-if="connecting" class="connection-mode-banner">
        <v-icon size="small" class="me-1">mdi-vector-line</v-icon>
        <span>Release on another card to connect, or on empty space to spawn a new card</span>
      </div>

      <!-- Current view indicator / selector (top-right of the canvas) -->
      <div class="view-indicator" @click.stop>
        <!-- One-shot tidy-up: solves positions, animates, stays in free web. -->
        <div
          class="view-indicator-chip collapse-all-chip"
          :class="{ 'view-chip-disabled': !cards.length || autoArranging }"
          title="Auto-arrange nodes (stays editable — you can still drag them)"
          @click="cards.length && autoArrange()"
        >
          <v-icon size="16" color="primary" class="me-2">{{ autoArranging ? 'mdi-loading mdi-spin' : 'mdi-auto-fix' }}</v-icon>
          <span class="view-indicator-label">Arrange</span>
        </div>

        <!-- Frame all nodes in the viewport. Same chip styling. -->
        <div
          class="view-indicator-chip collapse-all-chip"
          :class="{ 'view-chip-disabled': !cards.length }"
          title="Fit all nodes to the screen"
          @click="cards.length && fitBoard()"
        >
          <v-icon size="16" color="primary" class="me-2">mdi-fit-to-screen-outline</v-icon>
          <span class="view-indicator-label">Fit</span>
        </div>

        <!-- Collapse / expand every node. Same chip styling as the view selector. -->
        <div
          class="view-indicator-chip collapse-all-chip"
          :class="{ 'view-chip-disabled': !cards.length }"
          :title="allCollapsed ? 'Expand all nodes' : 'Collapse all nodes'"
          @click="cards.length && toggleCollapseAll()"
        >
          <v-icon size="16" color="primary" class="me-2">{{ allCollapsed ? 'mdi-arrow-expand-vertical' : 'mdi-arrow-collapse-vertical' }}</v-icon>
          <span class="view-indicator-label">{{ allCollapsed ? 'Expand All' : 'Collapse All' }}</span>
        </div>

        <!-- Auto Center toggle. When ON: selecting a card pans it to the middle
             of the viewport (zoom untouched), and double-clicking a card
             redistributes the whole board around it as the centre of the
             universe. When OFF, double-click keeps its zoom-to-read behaviour. -->
        <div
          class="view-indicator-chip collapse-all-chip"
          :class="{ 'view-chip-active': autoCenter }"
          :title="autoCenter
            ? 'Auto Center is ON — selecting a card centers it; double-click redistributes the board around it. Click to turn off.'
            : 'Auto Center is OFF — click to turn on'"
          @click="autoCenter = !autoCenter"
        >
          <v-icon size="16" :color="autoCenter ? 'white' : 'primary'" class="me-2">mdi-image-filter-center-focus</v-icon>
          <span class="view-indicator-label">Auto Center</span>
        </div>

        <!-- Auto Condense toggle. When ON and the board is viewed below the
             compact tier, rendered positions contract uniformly toward the
             board centre — as tight as possible without cards touching — so
             zoomed-out views waste far less white space. View-only: stored
             positions are never modified, and zooming back in restores the
             true arrangement. -->
        <div
          class="view-indicator-chip collapse-all-chip"
          :class="{ 'view-chip-active': autoCondense }"
          :title="autoCondense
            ? 'Auto Condense is ON — zoomed-out views compress empty space (positions are not changed). Click to turn off.'
            : 'Auto Condense is OFF — click to compress white space at zoomed-out levels'"
          @click="autoCondense = !autoCondense"
        >
          <v-icon size="16" :color="autoCondense ? 'white' : 'primary'" class="me-2">mdi-arrow-collapse-all</v-icon>
          <span class="view-indicator-label">Auto Condense</span>
        </div>

        <div class="view-selector-anchor">
        <div
          class="view-indicator-chip"
          :class="{ 'view-indicator-open': viewSelectorOpen }"
          @click="viewSelectorOpen = !viewSelectorOpen"
        >
          <v-icon size="16" color="primary" class="me-2">{{ currentVisualizer.icon }}</v-icon>
          <span class="view-indicator-label">{{ currentVisualizer.label }}</span>
          <v-icon size="16" class="ms-1 view-indicator-caret">mdi-chevron-down</v-icon>
        </div>

        <transition name="view-drop">
          <div v-if="viewSelectorOpen" class="view-indicator-menu">
            <div
              v-for="viz in VISUALIZERS"
              :key="viz.key"
              class="visualizer-option"
              :class="{ 'visualizer-option-active': activeVisualizer === viz.key }"
              @click.stop="setVisualizer(viz.key); viewSelectorOpen = false"
            >
              <v-icon size="18" class="me-2" :color="activeVisualizer === viz.key ? 'primary' : 'grey-darken-1'">{{ viz.icon }}</v-icon>
              <div class="visualizer-option-body">
                <span class="visualizer-option-label">{{ viz.label }}</span>
                <span class="visualizer-option-desc">{{ viz.description }}</span>
              </div>
              <v-icon v-if="activeVisualizer === viz.key" size="16" color="primary">mdi-check</v-icon>
            </div>
          </div>
        </transition>
        </div><!-- /view-selector-anchor -->
      </div>

      <!-- Zoom level (bottom-right of the canvas). Also names the current detail
           tier, since that is what governs how much of each card renders. -->
      <div
        v-if="currentEpisode"
        class="zoom-readout"
        :class="{ 'zoom-readout-active': zoomPct !== 100 }"
        title="Click to reset zoom to 100%"
        @click.stop="zoomTo(1, { duration: 250 })"
      >
        <v-icon size="14" class="me-1">mdi-magnify</v-icon>
        <span class="zoom-readout-value">{{ zoomPct }}%</span>
        <span class="zoom-readout-tier">{{ zoomTier }}</span>
      </div>

      <!-- Vue Flow canvas: owns the viewport (pan/zoom via d3-zoom), node
           positioning/dragging, edges, and drag-to-connect. Card content renders
           through the #node-card slot below, so every template and handler in this
           component keeps working unchanged. -->
      <VueFlow
        class="whiteboard-flow"
        :min-zoom="0.05"
        :max-zoom="4"
        :zoom-on-double-click="false"
        :nodes-draggable="nodesDraggable"
        :edges-updatable="false"
        :delete-key-code="null"
        :connection-radius="34"
        :connection-mode="'loose'"
        :is-valid-connection="isValidConnection"
        :elevate-nodes-on-select="true"
        @node-double-click="onFlowNodeDblClick"
        @node-click="onFlowNodeClick"
        @node-context-menu="onFlowNodeContextMenu"
        @node-drag-start="onFlowNodeDragStart"
        @node-drag="onFlowNodeDrag"
        @node-drag-stop="onFlowNodeDragStop"
        @edge-mouse-enter="hoveredLinkId = $event.edge.data.link.id"
        @edge-mouse-leave="hoveredLinkId = null"
        @connect-start="onConnectStart"
        @connect="onConnect"
        @connect-end="onConnectEnd"
        @pane-click="onPaneClick"
        @move-start="onViewportMoveStart"
      >
        <!-- Dot grid scales with the canvas — a real zoom cue, unlike the old
             fixed-size CSS gradient grid. -->
        <Background pattern-color="#bdbdbd" :gap="28" :size="1.5" />
        <MiniMap
          v-if="cards.length > 1"
          pannable
          zoomable
          position="bottom-left"
          :node-color="minimapNodeColor"
        />

        <!-- Hub labels: screen-space, constant-size badges for parent nodes,
             shown whenever the in-circle text would be too small to read
             (below the compact tier). Like map landmark labels: the hub disc
             scales geometrically with the canvas, its label stays readable at
             any zoom. pointer-events: none — purely visual, all interaction
             passes through to the node underneath. -->
        <div v-if="showHubLabels" class="hub-label-layer">
          <div
            v-for="hub in hubLabels"
            :key="'hub-' + hub.id"
            class="hub-label"
            :style="[hub.style, { background: hub.color }]"
          >
            <span class="hub-label-type">{{ hub.type }}</span>
            <span v-if="hub.title" class="hub-label-title">{{ hub.title }}</span>
          </div>
        </div>

        <!-- Endpoint popup (click on a connection endpoint dot). Screen-space
             overlay — constant size at every zoom, no counter-scaling. -->
        <div
          v-if="endpointPopup"
          class="endpoint-popup"
          :style="endpointPopupStyle"
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
            • Press <kbd>K</kbd> contact, <kbd>Q</kbd> question<br>
            • Press <kbd>P</kbd> parent node • Drag a border dot to connect<br>
            • Paste images, URLs, or text (<kbd>Ctrl+V</kbd>)<br>
            • <kbd>Scroll</kbd> to zoom • <kbd>F</kbd> fit to screen • Drag items to reposition
          </p>
        </div>

        <!-- Drop-into-empty-space menu -->
        <div
          v-if="showDropMenu"
          class="drop-spawn-menu"
          :style="dropMenuStyle"
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
              <v-list-item @click="spawnFromDrop('contact')" prepend-icon="mdi-account-box" title="Contact"></v-list-item>
              <v-list-item @click="spawnFromDrop('question')" prepend-icon="mdi-help-circle" title="Question"></v-list-item>
              <v-divider></v-divider>
              <v-list-item
                v-for="pt in parentNodeTypes"
                :key="pt.name"
                @click="spawnFromDrop('parent', pt)"
                :title="pt.name"
              >
                <template v-slot:prepend>
                  <v-icon :color="pt.color">{{ pt.icon }}</v-icon>
                </template>
              </v-list-item>
            </v-list>
            <div class="pa-2 text-caption text-grey text-center">
              or <kbd>Ctrl+V</kbd> to paste
            </div>
          </v-card>
        </div>

        <!-- Card nodes. Every card template renders inside this slot — same
             component scope, so all handlers and helpers work unchanged.

             CONSTANT-FOOTPRINT RULE: a card occupies the same canvas-space box at
             every zoom level. The zoom tier only changes what is drawn INSIDE that
             box (full card → header+body → summary → plate). Geometric zoom then
             handles all sizing and spacing proportionally — no counter-scaled
             fonts, no position spreading, no per-zoom size math. -->
        <template #node-card="{ data: { card } }">
        <div
          :ref="el => { if (el) cardElements[card.id] = el }"
          class="card-node"
          :class="{
            'card-flash-blue': flashingCards.has(card.id) && card.type !== 'parent',
            'parent-flash-blue': flashingCards.has(card.id) && card.type === 'parent',
            'doomed-node': showDeleteConfirm && deleteTargetIds.includes(card.id),
            'reparent-target': reparentDrag?.targetId === card.id,
            'reparent-source': reparentDrag?.cardId === card.id,
            'subtree-member': subtreeDrag && subtreeDrag.offsets.some(o => o.id === card.id)
          }"
          @mousedown.capture="maybeBlockNodeDrag"
          @mousemove="trackConnectDot($event, card)"
          @mouseleave="clearConnectDot"
        >
        <!-- Connection affordance. The .connect-band is a generous invisible hot
             zone extending well past the card edge; while the pointer is inside
             it (or within the inner rim of the card), a single connection dot
             clings to the nearest point on the border and FOLLOWS the mouse —
             press it and drag to draw a link. The dot is a real Vue Flow source
             Handle, so the drag hands straight off to Vue Flow's connection
             machinery. The full-card target surface only accepts events while a
             connection is in flight (drop anywhere on a card to connect). -->
        <div class="connect-band connect-band-top" :style="connectBandStyle"></div>
        <div class="connect-band connect-band-bottom" :style="connectBandStyle"></div>
        <div class="connect-band connect-band-left" :style="connectBandStyle"></div>
        <div class="connect-band connect-band-right" :style="connectBandStyle"></div>
        <Handle
          v-if="liveDot && liveDot.cardId === card.id"
          id="live"
          type="source"
          :position="Position.Top"
          class="connect-dot-live"
          :style="{
            left: liveDot.x + 'px',
            top: liveDot.y + 'px',
            width: liveDot.size + 'px',
            height: liveDot.size + 'px',
            borderWidth: Math.max(2, Math.round(liveDot.size / 9)) + 'px'
          }"
        />
        <Handle id="target" type="target" :position="Position.Top" class="connect-target-surface" />

        <!-- MARKER tier (zoomed far out): a type-coloured plate filling the card's
             own footprint. It scales down geometrically with the zoom — at this
             range the board is read by colour and structure, not text.
             PARENTS render as a solid-colour hub disc at BOTH summary and marker
             tiers (never the generic summary card) — they are the board's
             landmarks, and their readable text rides in the screen-space hub
             label layer so it stays legible at any zoom. -->
        <div
          v-if="(card.type === 'parent' ? !showCompact : !showSummary) && activeVisualizer !== 'hierarchical'"
          class="zoom-marker"
          :class="{ 'zoom-marker-parent': card.type === 'parent' }"
          :style="{
            background: card.type === 'parent' ? nodeType(card).color : nodeType(card).tint,
            borderColor: card.type === 'parent' ? 'rgba(255, 255, 255, 0.55)' : nodeType(card).color,
            width: lodBoxWidth(card) + 'px',
            height: lodBoxHeight(card) + 'px'
          }"
          :title="collapsedLabel(card) || nodeType(card).label"
        >
          <v-icon
            :size="Math.round(lodBoxHeight(card) * (card.type === 'parent' ? 0.3 : 0.4))"
            :color="card.type === 'parent' ? 'rgba(255,255,255,0.9)' : nodeType(card).color"
          >{{ nodeType(card).icon }}</v-icon>
          <span
            v-if="nodeType(card).label"
            class="zoom-marker-label"
            :style="{ color: nodeType(card).color }"
          >{{ nodeType(card).label }}</span>
          <span
            v-if="collapsedLabel(card) || card.title"
            class="zoom-marker-title"
          >{{ collapsedLabel(card) || card.title }}</span>
        </div>

        <!-- SUMMARY tier: thumbnail + type + title in the card's own footprint.
             Text sizes are fixed in canvas units and scale with the zoom like
             everything else. -->
        <v-card
          v-else-if="!showCompact"
          :width="summaryCardWidth(card)"
          class="card-item zoom-summary-card"
          :class="{ 'zoom-summary-wide': activeVisualizer === 'hierarchical' }"
          :style="{ borderTopColor: nodeType(card).color }"
          elevation="2"
        >
          <div class="zoom-summary-inner">
            <img
              v-if="rowMedia(card)"
              :src="rowMedia(card)"
              class="zoom-summary-thumb"
              draggable="false"
              @error="$event.target.style.display = 'none'"
            />
            <v-icon
              v-else
              class="zoom-summary-icon"
              :size="64"
              :color="nodeType(card).color"
            >{{ nodeType(card).icon }}</v-icon>
            <div class="zoom-summary-body">
              <span
                v-if="nodeType(card).label"
                class="zoom-summary-type"
                :style="{ color: nodeType(card).color }"
              >{{ nodeType(card).label }}</span>
              <span class="zoom-summary-title">{{ collapsedLabel(card) || card.title || nodeType(card).label }}</span>
              <span
                v-if="activeVisualizer === 'hierarchical' && summaryPreview(card)"
                class="zoom-summary-preview"
              >{{ summaryPreview(card) }}</span>
            </div>
          </div>
        </v-card>

        <!-- Collapsed ROW (hierarchical view): one wide line per node —
             type marker, media thumb, editable title. Replaces the per-type
             card entirely while collapsed in this view. -->
        <v-card
          v-if="isCollapsedRow(card) && showCompact"
          :width="collapsedRowWidth(card)"
          class="card-item collapsed-row"
          :style="{ borderLeftColor: nodeType(card).color }"
          elevation="2"
          @dblclick.stop="handleCardDblClick(card)"
        >
          <div class="collapsed-row-inner">
            <v-icon size="18" :color="nodeType(card).color" class="collapsed-row-icon">{{ nodeType(card).icon }}</v-icon>
            <span class="type-chip collapsed-row-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>

            <img
              v-if="rowMedia(card)"
              :src="rowMedia(card)"
              class="collapsed-row-thumb"
              draggable="false"
              @error="$event.target.style.display = 'none'"
            />

            <v-text-field
              v-model="card.title"
              variant="plain"
              density="compact"
              hide-details
              :placeholder="titlePlaceholder(card)"
              class="text-caption editable-title collapsed-row-title"
              :style="titleFieldStyle(card)"
              @focus="activeCardId = card.id"
              @click.stop
            ></v-text-field>

            <span class="collapsed-row-summary">{{ collapsedLabel(card) }}</span>

            <v-spacer></v-spacer>
            <v-btn
              size="x-small"
              icon="mdi-chevron-down"
              variant="text"
              @click.stop="toggleCollapse(card)"
            ></v-btn>
          </div>
        </v-card>

        <!-- Text Card -->
        <v-card
          v-if="card.type === 'text' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 500)"
          class="card-item text-card"
          :class="{ 'warning-card': card.isWarning }"
          :style="card.cardStyle || {}"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="card.isWarning ? 'border-color: #ff4444; background: #2d1010;' : 'border-color: #FFA726; background: #fffbcc;'">
            <v-icon size="small" :color="card.isWarning ? 'red' : 'amber-darken-2'" class="collapsed-pill-icon">{{ card.isWarning ? 'mdi-alert' : 'mdi-text' }}</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="card.isWarning ? 'color: #ff4444;' : 'color: #FFA726;'">{{ card.isWarning ? 'WARNING' : 'TEXT' }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title
              class="pa-2 d-flex align-center node-header"
              :style="card.isWarning ? 'background-color: #4a1010; color: #ff6666;' : ''"
              @dblclick.stop="handleCardDblClick(card)"
            >
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field
                v-model="card.title"
                variant="plain"
                density="compact"
                hide-details
                placeholder="Text Note"
                class="text-caption editable-title" :style="titleFieldStyle(card)"
                @focus="activeCardId = card.id"
                @click.stop
              ></v-text-field>
              <v-spacer></v-spacer>
              <v-btn
                size="x-small"
                icon="mdi-chevron-up"
                variant="text"
                @dblclick.stop="handleCardDblClick(card)"
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
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Link Card -->
        <v-card
          v-if="card.type === 'link' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, card.socialMetadata ? 300 : 260, 500)"
          class="card-item link-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill collapsed-pill-tall" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: card.socialMetadata ? '#000' : '#1976D2', background: '#e3f2fd' }">
            <img
              v-if="collapsedThumb(card)"
              :src="collapsedThumb(card)"
              class="collapsed-pill-thumb-wide"
              referrerpolicy="no-referrer"
              @error="$event.target.style.display='none'"
            />
            <v-icon v-else size="small" :color="card.socialMetadata ? socialPlatformChip(card.socialMetadata.platform).color : 'blue'" class="collapsed-pill-icon">{{ card.socialMetadata ? socialPlatformChip(card.socialMetadata.platform).icon : 'mdi-link' }}</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: card.socialMetadata ? socialPlatformChip(card.socialMetadata.platform).color : '#1976D2' }">{{ card.socialMetadata ? socialPlatformChip(card.socialMetadata.platform).label.toUpperCase() : 'LINK' }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State: Full Card -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title
              class="pa-2 d-flex align-center node-header"
              @dblclick.stop="handleCardDblClick(card)"
              style="cursor: pointer;"
            >
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field
                v-model="card.title"
                variant="plain"
                density="compact"
                hide-details
                :placeholder="card.previewTitle || card.url || 'Link'"
                class="text-caption editable-title" :style="titleFieldStyle(card)"
                @focus="activeCardId = card.id"
                @click.stop
              ></v-text-field>
              <v-spacer></v-spacer>
              <v-tooltip v-if="card.apiWarning" location="top">
                <template v-slot:activator="{ props }">
                  <v-icon v-bind="props" size="small" color="orange" class="me-1">mdi-alert</v-icon>
                </template>
                <span>API Error ({{ card.apiWarning.service }}): {{ card.apiWarning.message }}<br>Fallback data shown</span>
              </v-tooltip>
              <v-btn
                size="x-small"
                icon="mdi-chevron-up"
                variant="text"
                @dblclick.stop="handleCardDblClick(card)"
              ></v-btn>
            </v-card-title>
            <v-card-text
              class="pa-3 pb-2"
              :class="{
                'link-card-content': card.socialMetadata,
                'tree-wide-body': activeVisualizer === 'hierarchical'
              }"
            >
            <v-text-field
              v-model="card.url"
              variant="plain"
              placeholder="https://..."
              hide-details
              density="compact"
              class="text-field-no-fade mb-2"
              @focus="activeCardId = card.id"
            ></v-text-field>

            <!-- Rich Social Media Preview (Twitter, TikTok, YouTube, etc.) -->
            <div v-if="card.socialMetadata" class="twitter-preview-box mb-2">
              <div class="twitter-header pa-4 pb-2">
                <div class="d-flex align-center">
                  <v-avatar
                    v-if="card.socialMetadata.author_avatar"
                    size="48"
                    class="me-3 tweet-avatar"
                  >
                    <v-img :src="card.socialMetadata.author_avatar" />
                  </v-avatar>
                  <div class="flex-grow-1">
                    <div class="tweet-author">
                      {{ card.socialMetadata.author_name || 'Unknown Author' }}
                    </div>
                    <div class="tweet-handle">
                      <span v-if="card.socialMetadata.author_handle">@{{ card.socialMetadata.author_handle }}</span>
                      <span v-else-if="card.socialMetadata.username_from_url">@{{ card.socialMetadata.username_from_url }}</span>
                      <span v-if="card.socialMetadata.published_time" class="ms-2">
                        · {{ formatDate(card.socialMetadata.published_time) }}
                      </span>
                    </div>
                  </div>
                  <div class="d-flex gap-1 align-start">
                    <!-- The X logo, like a real embedded post. Inline SVG — the
                         pinned @mdi/font 5.9 has no X-brand glyph. -->
                    <svg
                      v-if="card.socialMetadata.platform === 'x' || card.socialMetadata.platform === 'twitter'"
                      class="x-logo"
                      viewBox="0 0 24 24"
                      width="22"
                      height="22"
                      aria-label="X"
                    ><path fill="currentColor" d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>
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
                      v-if="card.socialMetadata._locally_cached"
                      size="x-small"
                      color="green-darken-1"
                      variant="tonal"
                    >
                      <v-icon size="x-small" start>mdi-harddisk</v-icon>
                      Local
                    </v-chip>
                    <v-chip
                      v-if="card.socialMetadata.platform !== 'x' && card.socialMetadata.platform !== 'twitter'"
                      size="x-small"
                      :color="socialPlatformChip(card.socialMetadata.platform).color"
                      variant="tonal"
                    >
                      <v-icon size="x-small" start>{{ socialPlatformChip(card.socialMetadata.platform).icon }}</v-icon>
                      {{ socialPlatformChip(card.socialMetadata.platform).label }}
                    </v-chip>
                  </div>
                </div>
              </div>

              <!-- Post text (tweet_text for Twitter, post_text for others) -->
              <div v-if="card.socialMetadata.tweet_text || card.socialMetadata.post_text" class="px-4 pt-2 pb-3">
                <div class="tweet-text">{{ card.socialMetadata.tweet_text || card.socialMetadata.post_text }}</div>
              </div>

              <!-- TikTok: Sound/music info -->
              <div v-if="card.socialMetadata.track || card.socialMetadata.artist" class="px-3 pb-2">
                <v-chip size="x-small" variant="tonal" color="pink">
                  <v-icon size="x-small" start>mdi-music-note</v-icon>
                  {{ card.socialMetadata.artist ? `${card.socialMetadata.artist} - ` : '' }}{{ card.socialMetadata.track || 'Original sound' }}
                </v-chip>
              </div>

              <!-- TikTok: Hashtags -->
              <div v-if="card.socialMetadata.hashtags && card.socialMetadata.hashtags.length > 0" class="px-3 pb-2 d-flex flex-wrap gap-1">
                <v-chip v-for="tag in card.socialMetadata.hashtags" :key="tag" size="x-small" variant="outlined" color="primary">
                  #{{ tag }}
                </v-chip>
              </div>

              <!-- Thumbnail (TikTok/YouTube - shown when no media_urls) -->
              <div v-if="card.socialMetadata.thumbnail_url && (!card.socialMetadata.media_urls || card.socialMetadata.media_urls.length === 0)" class="twitter-media twitter-media-single">
                <img :src="card.socialMetadata.thumbnail_url" class="twitter-media-image" loading="eager" @error="$event.target.style.display='none'" />
              </div>

              <!-- Media -->
              <div v-if="card.socialMetadata.media_urls && card.socialMetadata.media_urls.length > 0" class="twitter-media" :class="{ 'twitter-media-single': card.socialMetadata.media_urls.length === 1 }">
                <img
                  v-for="(mediaUrl, idx) in card.socialMetadata.media_urls.slice(0, 4)"
                  :key="idx"
                  :src="mediaUrl"
                  class="twitter-media-image"
                  :style="card.socialMetadata.media_urls.length === 1 ? {} : { height: '170px' }"
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
                    {{ card.socialMetadata.platform === 'tiktok' ? 'TikTok' : card.socialMetadata.platform === 'youtube' ? 'YouTube' : 'Tweet' }} Analytics & Author Info
                  </v-expansion-panel-title>
                  <v-expansion-panel-text class="pa-3">
                    <!-- Engagement Stats -->
                    <div v-if="card.socialMetadata.likes || card.socialMetadata.retweets || card.socialMetadata.replies || card.socialMetadata.quotes || card.socialMetadata.views || card.socialMetadata.comments || card.socialMetadata.reposts" class="mb-3">
                      <div class="text-caption font-weight-bold mb-2">Engagement</div>
                      <div class="d-flex flex-wrap gap-3">
                        <v-chip v-if="card.socialMetadata.views" size="small" variant="tonal" prepend-icon="mdi-eye">
                          {{ card.socialMetadata.views.toLocaleString() }} Views
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.likes" size="small" variant="tonal" prepend-icon="mdi-heart">
                          {{ card.socialMetadata.likes.toLocaleString() }} Likes
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.retweets" size="small" variant="tonal" prepend-icon="mdi-repeat">
                          {{ card.socialMetadata.retweets.toLocaleString() }} Retweets
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.reposts" size="small" variant="tonal" prepend-icon="mdi-repeat">
                          {{ card.socialMetadata.reposts.toLocaleString() }} Reposts
                        </v-chip>
                        <v-chip v-if="card.socialMetadata.comments" size="small" variant="tonal" prepend-icon="mdi-comment">
                          {{ card.socialMetadata.comments.toLocaleString() }} Comments
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
                  <v-chip size="small" variant="outlined" class="tweet-media-chip">
                    <svg class="x-logo me-1" viewBox="0 0 24 24" width="14" height="14" aria-label="X"><path fill="currentColor" d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>
                    Media
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
          <v-card-actions v-if="showDetail" class="pa-2 pt-0">
            <v-spacer></v-spacer>
            <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
          </v-card-actions>
          </template>
        </v-card>

        <!-- Image Card -->
        <v-card
          v-if="card.type === 'image' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 240, 600)"
          class="card-item image-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-img v-if="card.imageUrl" :src="card.imageUrl" width="48" height="48" cover class="collapsed-pill-thumb"></v-img>
            <v-icon v-else size="small" :color="nodeType(card).color" class="collapsed-pill-icon">{{ nodeType(card).icon }}</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title
              class="pa-2 d-flex align-center node-header"
              @dblclick.stop="handleCardDblClick(card)"
              style="cursor: pointer;"
            >
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field
                v-model="card.title"
                variant="plain"
                density="compact"
                hide-details
                :placeholder="card.caption || 'Image'"
                class="text-caption editable-title" :style="titleFieldStyle(card)"
                @focus="activeCardId = card.id"
                @click.stop
              ></v-text-field>
              <v-spacer></v-spacer>
              <v-btn
                size="x-small"
                icon="mdi-chevron-up"
                variant="text"
                @dblclick.stop="handleCardDblClick(card)"
              ></v-btn>
            </v-card-title>
            <div>
              <v-img
                :src="card.imageUrl"
                :max-width="600"
                cover
                draggable="false"
              ></v-img>
              <!-- Compact metadata line: format · dimensions · size · source -->
              <div v-if="showDetail && imageMetaLine(card)" class="image-meta-line">
                {{ imageMetaLine(card) }}
              </div>
              <div v-if="showDetail && imageExifLine(card)" class="image-meta-line image-meta-exif">
                <v-icon size="10" class="me-1">mdi-camera</v-icon>{{ imageExifLine(card) }}<span v-if="imageTakenAt(card)"> · {{ imageTakenAt(card) }}</span>
              </div>
              <div v-if="showDetail && card.mediaMetadata?.source_title" class="image-meta-source">
                {{ card.mediaMetadata.source_title }}
              </div>
              <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
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
                <!-- Source URL, present when the image was dragged in from the web -->
                <div v-if="card.url" class="image-source-row mt-2">
                  <v-icon size="x-small" class="me-1" color="grey-darken-1">mdi-link-variant</v-icon>
                  <a
                    :href="card.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="image-source-link"
                    :title="card.url"
                    @click.stop
                    @mousedown.stop
                  >{{ card.url }}</a>
                </div>
              </v-card-text>
            </div>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-btn
                v-if="card.url"
                size="x-small"
                variant="text"
                prepend-icon="mdi-link-variant"
                @click.stop="convertImageToLinkCard(card)"
              >Make link card</v-btn>
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Video Card -->
        <v-card
          v-if="card.type === 'video' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 640)"
          class="card-item video-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" color="red-darken-1" class="collapsed-pill-icon">mdi-video</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Video" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <div>
              <video v-if="card.videoUrl" :src="card.videoUrl" controls style="width: 100%; max-height: 400px;"></video>
              <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
                <v-textarea v-model="card.notes" variant="outlined" label="Notes" auto-grow rows="2" hide-details placeholder="Add notes..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-chip v-if="card.assetId" size="x-small" variant="outlined">{{ card.assetId }}</v-chip>
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Audio Card -->
        <v-card
          v-if="card.type === 'audio' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 500)"
          class="card-item audio-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" color="purple-darken-1" class="collapsed-pill-icon">mdi-music-note</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Audio" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <div>
              <audio v-if="card.audioUrl" :src="card.audioUrl" controls style="width: 100%;"></audio>
              <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
                <v-textarea v-model="card.notes" variant="outlined" label="Notes" auto-grow rows="2" hide-details placeholder="Add notes..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-chip v-if="card.assetId" size="x-small" variant="outlined">{{ card.assetId }}</v-chip>
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- HTML Card -->
        <v-card
          v-if="card.type === 'html' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 600)"
          class="card-item html-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" color="orange-darken-1" class="collapsed-pill-icon">mdi-code-tags</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="HTML" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
                <v-textarea v-model="card.htmlContent" variant="outlined" label="HTML Content" auto-grow rows="8" hide-details placeholder="<div>Paste HTML here...</div>" font-family="monospace" @focus="activeCardId = card.id"></v-textarea>
                <div v-if="card.htmlContent" class="mt-3 pa-3 bg-grey-lighten-4 rounded" style="max-height: 300px; overflow: auto;">
                  <div v-html="card.htmlContent"></div>
                </div>
              </v-card-text>
            </div>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Code Card -->
        <v-card
          v-if="card.type === 'code' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 700)"
          class="card-item code-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" color="green-darken-1" class="collapsed-pill-icon">mdi-code-braces</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Code Snippet" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-select v-model="card.codeLanguage" :items="['javascript', 'python', 'html', 'css', 'json', 'bash', 'sql']" variant="outlined" density="compact" hide-details class="ms-2" style="max-width: 120px;" @click.stop></v-select>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
                <v-textarea v-model="card.codeContent" variant="outlined" label="Code" auto-grow rows="12" hide-details placeholder="// Paste code here..." font-family="monospace" @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Markdown Card -->
        <v-card
          v-if="card.type === 'markdown' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 600)"
          class="card-item markdown-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" color="indigo-darken-1" class="collapsed-pill-icon">mdi-language-markdown</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Markdown" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
                <v-textarea v-model="card.markdownContent" variant="outlined" label="Markdown" auto-grow rows="10" hide-details placeholder="# Paste markdown here..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Contact Card -->
        <v-card
          v-if="card.type === 'contact' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 460)"
          class="card-item contact-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" :color="nodeType(card).color" class="collapsed-pill-icon">{{ nodeType(card).icon }}</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Name" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
              <v-text-field v-model="card.contactRole" variant="outlined" label="Role / Title" density="compact" hide-details class="mb-2" @focus="activeCardId = card.id"></v-text-field>
              <v-text-field v-model="card.contactOrg" variant="outlined" label="Organization" density="compact" hide-details class="mb-2" @focus="activeCardId = card.id"></v-text-field>
              <v-text-field v-model="card.contactPhone" variant="outlined" label="Phone" density="compact" hide-details class="mb-2" prepend-inner-icon="mdi-phone" @focus="activeCardId = card.id"></v-text-field>
              <v-text-field v-model="card.contactEmail" variant="outlined" label="Email" density="compact" hide-details class="mb-2" prepend-inner-icon="mdi-email" @focus="activeCardId = card.id"></v-text-field>
              <v-textarea v-model="card.notes" variant="outlined" label="Notes" auto-grow rows="2" hide-details placeholder="Booking notes, availability, background..." @focus="activeCardId = card.id"></v-textarea>
            </v-card-text>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-btn v-if="card.contactEmail" size="x-small" variant="text" prepend-icon="mdi-email-fast" :href="`mailto:${card.contactEmail}`" @click.stop>Email</v-btn>
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Question Card -->
        <v-card
          v-if="card.type === 'question' && !isCollapsedRow(card) && showCompact"
          :width="treeCardWidth(card, 220, 500)"
          class="card-item question-card"
          :class="{ 'question-answered': card.questionAnswered }"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" class="collapsed-pill" @dblclick.stop="handleCardDblClick(card)" :style="{ borderColor: nodeType(card).color, background: nodeType(card).tint }">
            <v-icon size="small" :color="nodeType(card).color" class="collapsed-pill-icon">{{ nodeType(card).icon }}</v-icon>
            <div class="collapsed-pill-body">
              <span class="collapsed-pill-type" :style="{ color: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <span class="collapsed-pill-label">{{ collapsedLabel(card) }}</span>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <div class="type-accent" :style="{ background: nodeType(card).color }"></div>
            <v-card-title class="pa-2 d-flex align-center node-header" @dblclick.stop="handleCardDblClick(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-1" :color="nodeType(card).color">{{ nodeType(card).icon }}</v-icon>
              <span v-if="nodeType(card).label" class="type-chip" :style="{ color: nodeType(card).color, borderColor: nodeType(card).color }">{{ nodeType(card).label }}</span>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Question" class="text-caption editable-title" :style="titleFieldStyle(card)" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-tooltip location="top" text="Mark answered">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    size="x-small"
                    variant="text"
                    :icon="card.questionAnswered ? 'mdi-check-circle' : 'mdi-check-circle-outline'"
                    :color="card.questionAnswered ? 'success' : undefined"
                    @click.stop="card.questionAnswered = !card.questionAnswered"
                  ></v-btn>
                </template>
              </v-tooltip>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @dblclick.stop="handleCardDblClick(card)"></v-btn>
            </v-card-title>
            <v-card-text class="pa-3" :class="{ 'tree-wide-body': activeVisualizer === 'hierarchical' }">
              <v-textarea v-model="card.content" variant="outlined" label="Question" auto-grow rows="2" hide-details class="mb-2" placeholder="What do we still need to find out?" @focus="activeCardId = card.id"></v-textarea>
              <v-textarea v-model="card.questionAnswer" variant="outlined" label="Answer" auto-grow rows="3" hide-details placeholder="Answer / findings..." @focus="activeCardId = card.id"></v-textarea>
            </v-card-text>
            <!-- User comments (every node type) -->
            <div v-if="showDetail" class="node-comments">
              <div v-if="card.comments && card.comments.length" class="node-comment-list">
                <div v-for="c in card.comments" :key="c.id" class="node-comment">
                  <span class="comment-chip">{{ c.author }}</span>
                  <span class="comment-text">{{ c.text }}</span>
                  <span class="comment-ts">{{ commentTimestamp(c.ts) }}</span>
                  <v-icon
                    v-if="canDeleteComment(c)"
                    size="13"
                    class="comment-delete"
                    @click.stop="deleteComment(card, c.id)"
                  >mdi-close</v-icon>
                </div>
              </div>
              <div class="node-comment-entry">
                <span class="comment-chip comment-chip-me">{{ commentAuthor() }}</span>
                <input
                  v-model="commentDrafts[card.id]"
                  class="comment-input"
                  type="text"
                  placeholder="Add a comment…"
                  @keydown.enter.stop="addComment(card)"
                  @click.stop
                  @focus="activeCardId = card.id"
                />
                <v-icon
                  v-if="(commentDrafts[card.id] || '').trim()"
                  size="16"
                  color="primary"
                  class="comment-send"
                  @click.stop="addComment(card)"
                >mdi-send</v-icon>
              </div>
            </div>
            <v-card-actions v-if="showDetail" class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" variant="flat" class="delete-text-btn" @click.stop="confirmDelete(card.id)">DELETE</v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Parent Node Card (Round dark-blue circle) -->
        <div
          v-if="card.type === 'parent' && !isCollapsedRow(card) && showCompact"
          class="parent-node-circle"
          :style="{
            width: parentNodeSize(card),
            height: parentNodeSize(card),
            background: card.socialMetadata?.parentNodeColor || '#1565C0',
            boxShadow: '0 4px 16px ' + (card.socialMetadata?.parentNodeColor || '#1565C0') + '66'
          }"
          @dblclick.stop="handleCardDblClick(card)"
        >
          <!-- Collapsed State -->
          <template v-if="card.collapsed">
            <v-icon size="40" color="rgba(255,255,255,0.9)" class="mb-1">{{ card.socialMetadata?.parentNodeIcon || 'mdi-file-tree' }}</v-icon>
            <span class="parent-node-type">{{ (card.socialMetadata?.parentNodeType || 'Node').toUpperCase() }}</span>
            <span v-if="card.title" class="parent-node-slug">{{ card.title }}</span>
          </template>

          <!-- Expanded State -->
          <template v-else>
            <v-icon size="48" color="rgba(255,255,255,0.9)" class="mb-1">{{ card.socialMetadata?.parentNodeIcon || 'mdi-file-tree' }}</v-icon>
            <span class="parent-node-type">{{ (card.socialMetadata?.parentNodeType || 'Node').toUpperCase() }}</span>
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
              :text-color="card.socialMetadata?.parentNodeColor || '#1565C0'"
              inline
            ></v-badge>
            <span
              class="parent-node-delete"
              @click.stop="confirmDelete(card.id)"
            >DELETE</span>
          </template>
        </div>
        </div><!-- /card-node -->
        </template>

        <!-- Connection edges. Straight centre-to-centre lines in the web views
             (the nodes are painted on top, so the line reads as joining node to
             node); elbow routing in the hierarchical tree. Endpoint dots, the
             label, and the delete affordance render in the label layer so they
             stay above the cards and clickable. -->
        <template #edge-link="edgeProps">
          <!-- Single-item v-for: binds the computed geometry to a local name. -->
          <!-- eslint-disable-next-line vue/valid-v-for -->
          <template v-for="geo in [edgeGeometry(edgeProps)]" :key="edgeProps.id">
            <g v-if="geo">
              <BaseEdge
                :path="geo.path"
                :interaction-width="24"
                :style="{
                  stroke: edgeProps.data.link.color || '#1976d2',
                  strokeWidth: hoveredLinkId === edgeProps.data.link.id ? 7 : 5,
                  opacity: hoveredLinkId === edgeProps.data.link.id ? 1 : 0.85
                }"
              />
              <EdgeLabelRenderer>
                <!-- Endpoint dots: sit where the line meets each node's perimeter.
                     Click to open the endpoint menu. Ends anchored at a parent
                     hub's CENTRE get no dot — it would be invisible under the
                     disc and would steal clicks meant for the hub itself. -->
                <div
                  v-if="!geo.srcIsParent"
                  class="edge-endpoint"
                  :style="{
                    transform: `translate(-50%, -50%) translate(${geo.x1}px, ${geo.y1}px)`,
                    background: edgeProps.data.link.color || '#1976d2'
                  }"
                  @mouseenter="hoveredLinkId = edgeProps.data.link.id"
                  @mouseleave="hoveredLinkId = null"
                  @click.stop="openEndpointPopup(edgeProps.data.link.id, 'source', geo.x1, geo.y1)"
                ></div>
                <div
                  v-if="!geo.tgtIsParent"
                  class="edge-endpoint"
                  :style="{
                    transform: `translate(-50%, -50%) translate(${geo.x2}px, ${geo.y2}px)`,
                    background: edgeProps.data.link.color || '#1976d2'
                  }"
                  @mouseenter="hoveredLinkId = edgeProps.data.link.id"
                  @mouseleave="hoveredLinkId = null"
                  @click.stop="openEndpointPopup(edgeProps.data.link.id, 'target', geo.x2, geo.y2)"
                ></div>
                <!-- Label at the midpoint of the exposed span -->
                <div
                  v-if="edgeProps.data.link.label"
                  class="edge-label"
                  :style="{
                    transform: `translate(-50%, -100%) translate(${geo.mx}px, ${geo.my - 14}px)`,
                    color: edgeProps.data.link.color || '#1976d2'
                  }"
                >{{ edgeProps.data.link.label }}</div>
                <!-- Delete button at midpoint (on hover) -->
                <div
                  v-if="hoveredLinkId === edgeProps.data.link.id"
                  class="edge-delete"
                  :style="{ transform: `translate(-50%, -50%) translate(${geo.mx}px, ${geo.my}px)` }"
                  @mouseenter="hoveredLinkId = edgeProps.data.link.id"
                  @mouseleave="hoveredLinkId = null"
                  @click.stop="deleteLink(edgeProps.data.link.id)"
                >×</div>
              </EdgeLabelRenderer>
            </g>
          </template>
        </template>

        <!-- Rubber band while aiming a new connection -->
        <template #connection-line="{ sourceX, sourceY, targetX, targetY }">
          <g>
            <line
              :x1="sourceX" :y1="sourceY" :x2="targetX" :y2="targetY"
              class="connection-rubber-band"
            />
            <circle :cx="sourceX" :cy="sourceY" r="16" class="connection-rubber-dot" />
            <circle :cx="targetX" :cy="targetY" r="16" class="connection-rubber-dot" />
          </g>
        </template>
      </VueFlow>
    </div>

    <!-- Status Bar -->
    <v-footer height="32" class="bg-grey-lighten-4 border-t flex-grow-0">
      <span class="text-caption text-grey">
        {{ cards.length }} item{{ cards.length !== 1 ? 's' : '' }} on board
        <span v-if="nodeLinks.length > 0" class="ms-2">
          | {{ nodeLinks.length }} connection{{ nodeLinks.length !== 1 ? 's' : '' }}
        </span>
        <span v-if="connecting" class="ms-2 text-primary font-weight-bold">
          | CONNECTING...
        </span>
        <span v-if="saving" class="ms-4 text-primary">
          <v-icon size="x-small" class="me-1">mdi-loading mdi-spin</v-icon>
          Saving...
        </span>
        <span v-else-if="lastSaved" class="ms-4">
          Last saved: {{ formatTime(lastSaved) }}
        </span>
        <span v-if="zoomPct !== 100" class="ms-4">
          Zoom: {{ zoomPct }}%
        </span>
        <span v-if="!currentEpisode" class="ms-4 text-warning">
          No episode selected
        </span>
      </span>
    </v-footer>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick, toRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueFlow, Handle, Position, BaseEdge, EdgeLabelRenderer, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import { useStandardNotification, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { useWhiteboardConnections, borderIntersection } from '@/composables/useWhiteboardConnections'
import { useAuth } from '@/composables/useAuth'
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

// Current user — drives the author chip on node comments.
const { currentUser } = useAuth()

// Connections composable — the persisted link store. All connection
// INTERACTION (dragging a new link, hit-testing, the rubber band) is Vue Flow's.
const {
  nodeLinks,
  loadLinks,
  createLink,
  deleteLink,
  triggerFlash,
  deleteLinksForCard,
  getLinksForSave,
  flashingCards
} = useWhiteboardConnections()

// ─── Vue Flow: viewport, nodes, edges ───
const {
  fitView,
  zoomIn,
  zoomOut,
  zoomTo,
  setViewport,
  viewport,
  setNodes,
  setEdges,
  updateNode,
  updateNodeInternals,
  findNode,
  onNodesInitialized
} = useVueFlow()

// The board-open fit must wait until Vue Flow has MEASURED the nodes — framing
// against unmeasured (zero-size) nodes lands at an arbitrary viewport. Set by
// loadBoard, consumed by the nodes-initialized hook.
let pendingInitialFit = false

onNodesInitialized(() => {
  if (!pendingInitialFit) return
  pendingInitialFit = false
  // Positions may still be settling (overlap separation ran this tick).
  nextTick(() => { fitBoard() })
})

// nodesInitialized does not reliably re-fire when the node set is REPLACED
// (episode switch): without a fallback the viewport stays parked at the old
// board's coordinates and the new board loads off-screen.
function scheduleFitFallback() {
  setTimeout(() => {
    if (pendingInitialFit) {
      pendingInitialFit = false
      fitBoard()
    }
  }, 350)
}

// Hovered link (midpoint delete affordance + endpoint dot emphasis)
const hoveredLinkId = ref(null)

// True while the user is dragging a new connection out of a handle.
const connecting = ref(false)
// The node a pending connection started from — consumed by the spawn menu when
// the user releases over empty canvas.
const pendingConnectSource = ref(null)
// Set by onConnect so onConnectEnd can tell "landed on a card" from "landed on
// empty canvas".
let connectDidComplete = false

// Drop-into-empty-space spawn menu. Position is kept in FLOW coordinates (that
// is where the new card goes); the on-screen anchor is derived from the live
// viewport, so the menu stays glued to its canvas point at constant size.
const showDropMenu = ref(false)
const dropMenuPos = ref({ x: 0, y: 0 })

// Transient glide when a computed layout is applied or the view switches.
const layoutAnimating = ref(false)
let layoutAnimatingTimer = null

function glideLayout() {
  layoutAnimating.value = true
  if (layoutAnimatingTimer) clearTimeout(layoutAnimatingTimer)
  layoutAnimatingTimer = setTimeout(() => { layoutAnimating.value = false }, 700)
}

// Card element refs for measuring dimensions
const cardElements = ref({})

// Collapse generation counter — bumped on every collapse/expand to force line recomputation
const collapseGeneration = ref(0)

// Endpoint popup state (click on connection endpoint dot)
const endpointPopup = ref(null) // { linkId, end: 'source'|'target', x, y }

// Zoom is owned by Vue Flow's viewport. Boards open with a fit-to-content frame
// (see loadBoard), so the whole structure is visible on load.
const zoomPct = computed(() => Math.round((viewport.value?.zoom || 1) * 100))

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
// Every node id the pending delete will remove (1 for a single delete, the
// whole subtree for a branch delete). Drives the .doomed-node pulse too.
const deleteTargetIds = ref([])

// Drag state. Vue Flow owns the drag mechanics; these track the gesture's
// MEANING (which card, subtree membership, tree reparent target).
const dragCard = ref(null)
// Live reparent state while dragging a row in the hierarchical view:
// {cardId, targetId|null}. Applied on release.
const reparentDrag = ref(null)
// Ctrl-drag state: {tighten, offsets:[{id, dx, dy}]} — followers that travel
// with the grabbed node.
const subtreeDrag = ref(null)
// True while a native HTML5 drag that began inside the canvas is in flight.
// Plain let (not a ref) — nothing renders from it.
let internalDragActive = false

// Card ID counter
let nextId = 1
let saveTimeout = null
let boardLoaded = false

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

// Load whiteboard settings from API. The old default_zoom setting no longer
// applies — boards always open framed to their content (fitView), which is
// strictly more useful than a fixed zoom.
async function loadWhiteboardSettings() {
  try {
    const response = await fetchJson('/api/settings/api-configs')
    if (response?.success && response?.data?.whiteboard) {
      const wb = response.data.whiteboard
      if (wb.parent_node_types) parentNodeTypes.value = wb.parent_node_types
    }
  } catch {
    // Use defaults silently
  }
}

// Auto-save on unmount (only if board was loaded and has content)
onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
  if (saveTimeout) clearTimeout(saveTimeout)
  if (boardLoaded && cards.value.length > 0) {
    saveBoard()
  }
})

// Watch for card changes and auto-save (only after initial load completes)
watch(cards, () => {
  if (currentEpisode.value && boardLoaded) {
    debouncedSave()
  }
}, { deep: true })

// Watch for episode changes and reload board
watch(currentEpisode, async (newEpisode, oldEpisode) => {
  if (newEpisode === oldEpisode) return
  // The dialog flow orchestrates its own save/load ordering.
  if (switchingViaDialog) return
  // Save the OUTGOING board under the OLD episode. Passing the episode
  // explicitly is essential: currentEpisode has already flipped to the new
  // value by the time this watcher runs, and an unqualified saveBoard() here
  // used to overwrite the TARGET episode's board with the previous episode's
  // content — which then loaded back as "the board didn't change".
  if (saveTimeout) clearTimeout(saveTimeout)
  if (oldEpisode && boardLoaded && cards.value.length > 0) {
    await saveBoard(oldEpisode)
  }
  await loadBoard()
})

// True while confirmEpisodeSelection is orchestrating a switch, so the
// currentEpisode watcher doesn't run a second, racing save/load.
let switchingViaDialog = false

// Convert client (screen) coordinates to flow/canvas coordinates.
function toFlow(clientX, clientY) {
  const rect = canvas.value?.getBoundingClientRect()
  const vp = viewport.value || { x: 0, y: 0, zoom: 1 }
  if (!rect) return { x: clientX, y: clientY }
  return {
    x: (clientX - rect.left - vp.x) / vp.zoom,
    y: (clientY - rect.top - vp.y) / vp.zoom
  }
}

// Convert flow/canvas coordinates to a position relative to the canvas element,
// for anchoring screen-space overlays (spawn menu, endpoint popup) to a canvas
// point. Reads the live viewport, so overlays track pan/zoom.
function toScreen(flowX, flowY) {
  const vp = viewport.value || { x: 0, y: 0, zoom: 1 }
  return {
    x: flowX * vp.zoom + vp.x,
    y: flowY * vp.zoom + vp.y
  }
}

// Helper: get center of visible canvas area in canvas coordinates
function getCanvasCenter(offsetX = 0, offsetY = 0) {
  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return { x: 100 + offsetX, y: 100 + offsetY }
  const center = toFlow(rect.left + rect.width / 2, rect.top + rect.height / 2)
  return { x: center.x + offsetX, y: center.y + offsetY }
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
      cards.value.push({
        id: nextId++,
        type: 'image',
        imageUrl: e.target.result,
        caption: '',
        notes: '',
        title: '',
        x: getCanvasCenter(-300, 0).x + (index * 20),
        y: getCanvasCenter(0, -150).y + (index * 20),
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

      cards.value.push({
        id: nextId++,
        type: 'video',
        videoUrl: response.file_url,
        assetId: response.asset_id,
        title: file.name,
        notes: '',
        x: getCanvasCenter(-320, 0).x,
        y: getCanvasCenter(0, -150).y,
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

      cards.value.push({
        id: nextId++,
        type: 'audio',
        audioUrl: response.file_url,
        assetId: response.asset_id,
        title: file.name,
        notes: '',
        x: getCanvasCenter(-250, 0).x,
        y: getCanvasCenter(0, -100).y,
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
  cards.value.push({
    id: nextId++,
    type: 'html',
    htmlContent: '',
    title: '',
    x: getCanvasCenter(-300, 0).x,
    y: getCanvasCenter(0, -100).y,
    width: 600,
    collapsed: false
  })
}

// Add code card
function addCodeCard() {
  cards.value.push({
    id: nextId++,
    type: 'code',
    codeContent: '',
    codeLanguage: 'javascript',
    title: '',
    x: getCanvasCenter(-350, 0).x,
    y: getCanvasCenter(0, -150).y,
    width: 700,
    collapsed: false
  })
}

// Add markdown card
function addMarkdownCard() {
  cards.value.push({
    id: nextId++,
    type: 'markdown',
    markdownContent: '',
    title: '',
    x: getCanvasCenter(-300, 0).x,
    y: getCanvasCenter(0, -100).y,
    width: 600,
    collapsed: false
  })
}

function addContactCard() {
  const center = getCanvasCenter(-230, -140)
  cards.value.push({
    id: nextId++,
    type: 'contact',
    title: '',
    contactRole: '',
    contactOrg: '',
    contactPhone: '',
    contactEmail: '',
    notes: '',
    x: center.x,
    y: center.y,
    width: 460,
    collapsed: false
  })
}

function addQuestionCard() {
  const center = getCanvasCenter(-250, -120)
  cards.value.push({
    id: nextId++,
    type: 'question',
    title: '',
    content: '',
    questionAnswer: '',
    questionAnswered: false,
    x: center.x,
    y: center.y,
    width: 500,
    collapsed: false
  })
}

/**
 * Double-click a node (or its media): zoom in to read it.
 *
 * Expands the card, brings the canvas to 80% zoom, and centres that card. Replaces
 * the old plain collapse-toggle on double-click — at low zoom "collapse this" was
 * rarely what was wanted, whereas "let me actually read this one" always is.
 *
 * A double-click on an ALREADY expanded card at reading zoom falls back to
 * collapsing it, so the gesture stays reversible.
 */
const FOCUS_ZOOM = 0.8

async function focusCard(card) {
  if (!card) return

  const z = viewport.value?.zoom || 1
  const alreadyReadable = z >= FOCUS_ZOOM - 0.01 && !card.collapsed
  if (alreadyReadable) {
    // Nothing to zoom into — treat it as the collapse toggle it used to be.
    toggleCollapse(card)
    return
  }

  if (card.collapsed) {
    card.collapsed = false
  }

  // Wait for the expanded card to lay out, so the frame fits its real size,
  // then glide the viewport to it (smooth animated zoom-and-pan via d3).
  await nextTick()
  collapseGeneration.value++
  await nextTick()

  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return
  const pos = cardPosition(card)
  const node = findNode(String(card.id))
  const w = node?.dimensions?.width || card.width || 300
  const h = node?.dimensions?.height || 200

  // Frame the card: read at FOCUS_ZOOM, or lower if it doesn't fit.
  const zoom = Math.min(
    FOCUS_ZOOM,
    (rect.width * 0.85) / Math.max(w, 1),
    (rect.height * 0.85) / Math.max(h, 1)
  )
  setViewport({
    x: rect.width / 2 - (pos.x + w / 2) * zoom,
    y: rect.height / 2 - (pos.y + h / 2) * zoom,
    zoom
  }, { duration: 500 })
}

// ─── Auto Center ───
//
// Toggle in the top-right chip row. When ON:
//   • selecting a card (click, or focusing one of its fields) pans the viewport
//     so that card sits dead centre — the zoom is NEVER touched;
//   • double-clicking a card redistributes the whole board around it as the
//     centre of the universe (linked cards ringed by graph distance, unlinked
//     ones on the outermost ring), then centres it. Again: no zoom change.
// When OFF, double-click keeps the original zoom-to-read behaviour (focusCard).
// Persisted per browser so the preference survives reloads.
const autoCenter = ref(localStorage.getItem('wb-auto-center') === '1')
watch(autoCenter, v => localStorage.setItem('wb-auto-center', v ? '1' : '0'))

// Pan (never zoom) so the card sits in the middle of the viewport.
function centerOnCard(card, duration = 400) {
  const rect = canvas.value?.getBoundingClientRect()
  if (!rect || !card) return
  const vp = viewport.value || { x: 0, y: 0, zoom: 1 }
  const node = findNode(String(card.id))
  const pos = cardPosition(card)
  const w = node?.dimensions?.width || card.width || 300
  const h = node?.dimensions?.height || 200
  setViewport({
    x: rect.width / 2 - (pos.x + w / 2) * vp.zoom,
    y: rect.height / 2 - (pos.y + h / 2) * vp.zoom,
    zoom: vp.zoom
  }, { duration })
}

// Recentre whenever a card becomes the active one. Skipped mid-gesture: a node
// drag sets the active card at press time, and panning the canvas out from
// under an in-flight drag or connection would fight the pointer.
watch(activeCardId, (id) => {
  if (!autoCenter.value || id == null) return
  if (dragCard.value || connecting.value) return
  const card = cards.value.find(c => c.id === id)
  if (card) centerOnCard(card)
})

// Double-click dispatcher for the card templates (headers, pills, media).
function handleCardDblClick(card) {
  if (autoCenter.value) {
    redistributeAroundCard(card)
  } else {
    focusCard(card)
  }
}

/**
 * Redistribute the whole board around `focal` — it stays exactly where it is
 * and becomes the centre of the universe: directly linked cards on the first
 * ring, their neighbours on the next, and cards with no path to it on the
 * outermost ring. Positions are real free-web coordinates (this is a user
 * action, like Auto Arrange), so the result persists; if invoked from a
 * computed layout view it switches to free-web first for the same reason
 * autoArrange does. The viewport then pans to centre the focal card — the
 * zoom is left completely alone.
 */
async function redistributeAroundCard(focal) {
  if (!focal || cards.value.length < 2) {
    centerOnCard(focal)
    return
  }
  if (activeVisualizer.value !== 'free-web') {
    activeVisualizer.value = 'free-web'
    await nextTick()
  }

  // Graph distance from the focal card over the link graph.
  const adjacency = new Map(cards.value.map(c => [c.id, []]))
  for (const link of nodeLinks.value) {
    if (!adjacency.has(link.sourceCardId) || !adjacency.has(link.targetCardId)) continue
    adjacency.get(link.sourceCardId).push(link.targetCardId)
    adjacency.get(link.targetCardId).push(link.sourceCardId)
  }
  const depth = new Map([[focal.id, 0]])
  const queue = [focal.id]
  while (queue.length) {
    const id = queue.shift()
    for (const next of adjacency.get(id) || []) {
      if (!depth.has(next)) {
        depth.set(next, depth.get(id) + 1)
        queue.push(next)
      }
    }
  }
  const maxDepth = Math.max(...depth.values())

  // Group every OTHER card by ring; unreachable cards form the outermost ring.
  const byDepth = new Map()
  for (const c of cards.value) {
    if (c.id === focal.id) continue
    const d = depth.get(c.id) ?? maxDepth + 1
    if (!byDepth.has(d)) byDepth.set(d, [])
    byDepth.get(d).push(c.id)
  }

  // Glide the moves like Auto Arrange does.
  autoArranging.value = true
  await nextTick()

  const focalBox = cardBox(focal)
  const cx = focal.x + focalBox.w / 2
  const cy = focal.y + focalBox.h / 2
  const placed = [{ x: focal.x, y: focal.y, ...focalBox }]

  const fits = (x, y, box) => {
    for (const p of placed) {
      const ox = x < p.x + p.w + SNAP_GAP && x + box.w + SNAP_GAP > p.x
      const oy = y < p.y + p.h + SNAP_GAP && y + box.h + SNAP_GAP > p.y
      if (ox && oy) return false
    }
    return true
  }

  for (const d of [...byDepth.keys()].sort((a, b) => a - b)) {
    const ids = byDepth.get(d)
    // More candidates on crowded rings, so big boards still resolve.
    const sweep = Math.max(12, ids.length * 3)
    ids.forEach((id, i) => {
      const card = cards.value.find(c => c.id === id)
      if (!card) return
      const box = cardBox(card)
      const baseRadius = (Math.hypot(focalBox.w, focalBox.h) + Math.hypot(box.w, box.h)) / 2 + SNAP_GAP
      const startAngle = (i / ids.length) * Math.PI * 2
      for (let expand = 0; expand < 8; expand++) {
        const radius = baseRadius * (d + expand * 0.45)
        for (let k = 0; k < sweep; k++) {
          const angle = startAngle + (k / sweep) * Math.PI * 2
          const x = Math.round(cx + Math.cos(angle) * radius - box.w / 2)
          const y = Math.round(cy + Math.sin(angle) * radius - box.h / 2)
          if (fits(x, y, box)) {
            card.x = x
            card.y = y
            placed.push({ x, y, ...box })
            return
          }
        }
      }
    })
  }

  // Positions changed — connection geometry and layouts must re-measure.
  nextTick(() => { collapseGeneration.value++ })
  setTimeout(() => {
    autoArranging.value = false
    collapseGeneration.value++
  }, AUTO_ARRANGE_DURATION)

  centerOnCard(focal, 500)
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
  // Typed cards summarise themselves — checked first, because their fields ride in
  // social_metadata and would otherwise fall into the social-post branches below.
  if (card.type === 'contact') {
    return [card.title, card.contactOrg || card.contactRole].filter(Boolean).join(' · ') || 'Contact'
  }
  if (card.type === 'question') {
    const q = card.title || card.content || 'Question'
    return (card.questionAnswered ? '✓ ' : '') + q.substring(0, 46)
  }

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
  if (card.socialMetadata?.thumbnail_url) return card.socialMetadata.thumbnail_url
  if (card.previewImage) return card.previewImage
  if (card.imageUrl) return card.imageUrl
  return null
}

// Click on empty canvas: dismiss menus and deselect.
function onPaneClick() {
  endpointPopup.value = null
  viewSelectorOpen.value = false
  floatingMenuOpen.value = false
  closeContextMenu()
  if (showDropMenu.value) {
    closeDropMenu()
    return
  }
  canvas.value?.focus()
  activeCardId.value = null
}

// Double-click on empty canvas — open the spawn menu at the click position.
// Attached on the wrapper (zoom-on-double-click is disabled) and filtered to the
// pane so double-clicks on cards keep their own meaning (focusCard).
function handlePaneDblClick(event) {
  if (!currentEpisode.value) return
  if (connecting.value || showDropMenu.value) return
  if (!event.target.closest('.vue-flow__pane')) return
  if (event.target.closest('.vue-flow__node')) return
  dropMenuPos.value = toFlow(event.clientX, event.clientY)
  showDropMenu.value = true
}

// Pan/zoom started: screen-anchored popups would drift, so close them.
function onViewportMoveStart() {
  endpointPopup.value = null
  closeContextMenu()
}

// Close the spawn menu and clear any pending connection source.
function closeDropMenu() {
  showDropMenu.value = false
  pendingConnectSource.value = null
}

// Open endpoint popup on connection endpoint dot click. x/y are FLOW coords;
// the overlay derives its screen anchor from the live viewport.
function openEndpointPopup(linkId, end, x, y) {
  endpointPopup.value = { linkId, end, x, y }
}

// Handle "Disconnect this end" from endpoint popup. With Vue Flow owning
// connection dragging there is no re-aim-in-flight mode any more, so
// disconnecting an end simply removes the link — draw a new one from a border
// dot to reconnect elsewhere.
function handleDisconnectEnd() {
  handleDestroyConnection()
}

// Handle "Destroy connection" from endpoint popup
function handleDestroyConnection() {
  if (!endpointPopup.value) return
  const { linkId } = endpointPopup.value
  endpointPopup.value = null
  deleteLink(linkId)
  hoveredLinkId.value = null
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
        cards.value.push({
          id: nextId++,
          type: 'image',
          imageUrl: e.target.result,
          caption: '',
          notes: '',
          title: '',
          x: getCanvasCenter(-300, 0).x,
          y: getCanvasCenter(0, -150).y,
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
          cards.value.push({
            id: nextId++,
            type: 'html',
            htmlContent: text,
            title: '',
            x: getCanvasCenter(-300, 0).x,
            y: getCanvasCenter(0, -100).y,
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

          // Detect HTML tags in plain text
          if (text.match(/<[a-z][\s\S]*>/i)) {
            cards.value.push({
              id: nextId++,
              type: 'html',
              htmlContent: text,
              title: '',
              x: getCanvasCenter(-300, 0).x,
              y: getCanvasCenter(0, -100).y,
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
              x: getCanvasCenter(-250, 0).x,
              y: getCanvasCenter(0, -100).y,
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

            // Analyze URL for smart child spawning and local caching
            try {
              const analysis = await fetchJson(`/api/whiteboard/analyze-url?url=${encodeURIComponent(text)}`)

              if (analysis.spawn_children && analysis.has_media) {
                // Download media and spawn child nodes
                const downloadResult = await fetchJson(`/api/whiteboard/${identifier.value}/download-social-media?url=${encodeURIComponent(text)}`, {
                  method: 'POST'
                })

                // Check for API error - spawn warning card
                if (downloadResult.error) {
                  const err = downloadResult.error
                  const warningCard = {
                    id: nextId++,
                    type: 'text',
                    title: `API Error: ${err.service || analysis.service}`,
                    content: `**${err.message || 'Unknown error'}**\n\nStatus: ${err.status_code || 'N/A'}\nEndpoint: \`${err.endpoint || 'N/A'}\`\nFallback used: ${err.fallback_used ? 'Yes' : 'No'}${err.detail ? '\n\nDetail: ' + err.detail.substring(0, 200) : ''}`,
                    notes: '',
                    x: newCard.x + 550,
                    y: newCard.y,
                    width: 400,
                    collapsed: false,
                    parentId: newCard.id,
                    isWarning: true,
                    cardStyle: { backgroundColor: '#2d1010', borderColor: '#ff4444', borderWidth: '2px' }
                  }
                  cards.value.push(warningCard)
                  notifyUserStandard(`${err.service || analysis.service} API error: ${err.message}`, NOTIFICATION_COLORS.error)
                }

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

                // For Twitter: populate socialMetadata from API data + local URLs
                if (analysis.service === 'twitter' && downloadResult.tweet_data) {
                  const td = downloadResult.tweet_data
                  newCard.socialMetadata = {
                    ...td,
                    media_urls: downloadResult.local_media_urls || td.media_urls || [],
                    author_avatar: downloadResult.local_avatar_url || td.author_avatar,
                    _locally_cached: true,
                    _cached_at: new Date().toISOString()
                  }
                  newCard.previewTitle = td.author_name ? `${td.author_name} (@${td.author_handle})` : null
                  newCard.previewDescription = td.tweet_text || null
                  newCard.previewDomain = 'x.com'
                  newCard.previewFavicon = 'https://abs.twimg.com/favicons/twitter.3.ico'
                  newCard._analyzedUrl = text
                  return
                }

                // For TikTok/YouTube/other yt-dlp services: populate socialMetadata from content_data
                if (downloadResult.content_data) {
                  const cd = downloadResult.content_data
                  newCard.socialMetadata = {
                    ...cd,
                    media_urls: downloadResult.local_media_urls || [],
                    thumbnail_url: downloadResult.local_thumbnail_url || cd.thumbnail_url,
                    _locally_cached: true,
                    _cached_at: new Date().toISOString()
                  }
                  newCard.previewTitle = cd.author_name || cd.title || null
                  newCard.previewDescription = cd.post_text || cd.title || null
                  newCard.previewDomain = analysis.service === 'tiktok' ? 'tiktok.com' : analysis.service
                  newCard._analyzedUrl = text
                  return
                }
              }
            } catch (error) {
              console.error('Error analyzing URL:', error)
            }

            // Fetch link preview (fallback for non-Twitter or if download failed)
            fetchLinkPreview(newCard)
          }
          // Detect Markdown
          else if (text.match(/^(#{1,6}\s)|(\*\*.*\*\*)|(__.*__)|(\[.*\]\(.*\))/m)) {
            cards.value.push({
              id: nextId++,
              type: 'markdown',
              markdownContent: text,
              title: '',
              x: getCanvasCenter(-300, 0).x,
              y: getCanvasCenter(0, -100).y,
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
              x: getCanvasCenter(-350, 0).x,
              y: getCanvasCenter(0, -150).y,
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
              x: getCanvasCenter(-250, 0).x,
              y: getCanvasCenter(0, -100).y,
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

// Block the browser's native image drag anywhere on the canvas.
// Images (and links) are natively draggable. Starting a native drag on a card's
// image suppresses mousemove — so the card never follows the cursor — and the
// release then fires handleDrop, spawning a duplicate card, while the drag ghost
// keeps trailing the mouse. Cancelling dragstart keeps mousedown-based card
// dragging in charge. This is done in JS rather than CSS because the <img> lives
// inside Vuetify's v-img, which scoped styles can't reach.
function handleCanvasDragStart(event) {
  // Mark this drag as originating inside the canvas, so a drop that slips
  // through (browser variance) is still rejected by handleDrop.
  internalDragActive = true
  event.preventDefault()
}

// Handle drop
function handleDrop(event) {
  event.preventDefault()

  // Belt-and-braces: a drop whose drag started inside the canvas (a native image
  // drag that escaped handleCanvasDragStart) must never spawn a card — that is
  // the "dragging a node duplicates it" bug. Native drags suppress the mouse
  // events, so check the dragstart flag rather than the node-drag state.
  if (internalDragActive || dragCard.value) {
    internalDragActive = false
    return
  }

  const dt = event.dataTransfer
  const dropPos = toFlow(event.clientX, event.clientY)

  // 1. Local files dragged from the desktop — read as data URLs. The backend
  // extracts these to the filesystem on save (media_asset_id + media_path).
  const files = dt.files
  if (files && files.length > 0) {
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
            x: dropPos.x - 300 + (index * 20),
            y: dropPos.y - 150 + (index * 20),
            width: 600,
            collapsed: false,
            // Remember where this came from, so the card can offer the source link.
            url: null
          })
        }
        reader.readAsDataURL(file)
      }
    })
    return
  }

  // 2. Dragged from a web page. Chrome gives us text/uri-list (the image's own
  // URL) and text/html (the <img> element, whose src is the same). The page the
  // image lives on is NOT in the drag payload — only the image URL is.
  const uriList = dt.getData('text/uri-list')
  const plain = dt.getData('text/plain')
  const html = dt.getData('text/html')

  let imageSrc = null
  if (html) {
    const m = html.match(/<img[^>]+src=["']([^"']+)["']/i)
    if (m) imageSrc = m[1]
  }

  const droppedUrl = [uriList, plain, imageSrc]
    .find(u => u && /^https?:\/\//.test(u.trim()))
  if (!droppedUrl) return
  const url = droppedUrl.trim()

  // An image URL becomes an image card that remembers its source URL; anything
  // else becomes a link card with a fetched preview.
  const looksLikeImage = /\.(png|jpe?g|gif|webp|avif|bmp|svg)(\?|#|$)/i.test(url) || !!imageSrc

  if (looksLikeImage) {
    let sourceSite = null
    try { sourceSite = new URL(url).hostname.replace(/^www\./, '') } catch { /* not parseable */ }
    const imageCard = {
      id: nextId++,
      type: 'image',
      imageUrl: url,
      caption: '',
      notes: '',
      title: '',
      x: dropPos.x - 300,
      y: dropPos.y - 150,
      width: 600,
      collapsed: false,
      url: url,
      // Seed source info; the backend merges in format/dimensions/EXIF on save.
      mediaMetadata: sourceSite ? { source_url: url, source_site: sourceSite } : null
    }
    cards.value.push(imageCard)
    fetchImagePageMetadata(imageCard)
    return
  }

  const newCard = {
    id: nextId++,
    type: 'link',
    url,
    notes: '',
    title: '',
    x: dropPos.x - 250,
    y: dropPos.y - 100,
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
  fetchLinkPreview(newCard)
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
  } else if (event.key === 'f' || event.key === 'F') {
    event.preventDefault()
    fitBoard()
  } else if (event.key === 'k' || event.key === 'K') {
    // 'k' for kontact — 'c' is taken by code.
    event.preventDefault()
    addContactCard()
  } else if (event.key === 'q' || event.key === 'Q') {
    event.preventDefault()
    addQuestionCard()
  } else if (event.key === 'p' || event.key === 'P') {
    event.preventDefault()
    showParentMenu.value = !showParentMenu.value
  } else if (event.key === 'Escape') {
    event.preventDefault()
    // Close popups and cancel a pending spawn.
    closeDropMenu()
    closeContextMenu()
    endpointPopup.value = null
    showParentMenu.value = false
  } else if (event.key === 'Delete' && activeCardId.value) {
    event.preventDefault()
    deleteCard(activeCardId.value)
  }
}

// Start dragging
/**
 * Vue Flow node drag lifecycle.
 *
 * Free web: dragging moves the node live (Vue Flow internal); the stored
 * card.x/card.y are written ONCE at drag stop — the only place a visualizer-
 * rendered position is ever persisted back onto a card.
 *
 * Hierarchical: the row is dragged vertically only (X is pinned by a node
 * extent set at drag start); the Y picks the prospective new parent, applied at
 * release. Balanced/waterfall: nodes are not draggable at all (layout owns
 * positions), enforced via the global nodes-draggable prop.
 *
 * Ctrl-drag carries the whole linked subtree; adding Shift packs it into a tidy
 * cluster on release. Ctrl can be pressed mid-drag (document keydown listener —
 * mousemove only reports modifiers when the mouse moves).
 */
// Clicking a node makes it the active card (keyboard Delete target, z-order).
function onFlowNodeClick({ node }) {
  const card = node.data?.card
  if (card) activeCardId.value = card.id
}

// Double-click a node: with Auto Center ON, redistribute the board around it
// (centre of the universe, zoom untouched); otherwise zoom in to read it.
function onFlowNodeDblClick({ node }) {
  const card = node.data?.card
  if (card) handleCardDblClick(card)
}

function onFlowNodeDragStart({ event, node }) {
  const card = node.data?.card
  if (!card) return
  dragCard.value = card
  activeCardId.value = card.id
  internalDragActive = false

  // Hierarchical: pin X for the whole gesture — the drag is vertical-only.
  if (activeVisualizer.value === 'hierarchical') {
    updateNode(node.id, {
      extent: [[node.position.x, -1e9], [node.position.x, 1e9]]
    })
  }

  subtreeDrag.value = null
  if (activeVisualizer.value === 'free-web' && (event.ctrlKey || event.metaKey)) {
    attachSubtreeToDrag(card, event.shiftKey)
  }

  document.addEventListener('keydown', onDragModifierKey)
  document.addEventListener('keyup', onDragModifierKey)
}

function onFlowNodeDrag({ node }) {
  const card = node.data?.card
  if (!card) return

  // Hierarchical view: Y picks which row the node is being moved onto, which
  // becomes its new parent. Applied in onFlowNodeDragStop().
  if (activeVisualizer.value === 'hierarchical') {
    const el = cardElements.value[card.id]
    const h = el?.offsetHeight || 46
    const midY = node.position.y + h / 2
    reparentDrag.value = {
      cardId: card.id,
      targetId: hierarchyRowAtY(midY, card.id)
    }
    return
  }

  // Ctrl-drag: the subtree travels with the grabbed node, holding formation.
  if (subtreeDrag.value) {
    for (const follower of subtreeDrag.value.offsets) {
      const followerNode = findNode(String(follower.id))
      if (followerNode) {
        followerNode.position = {
          x: node.position.x + follower.dx,
          y: node.position.y + follower.dy
        }
      }
    }
  }
}

function onFlowNodeDragStop({ node }) {
  const card = node.data?.card
  document.removeEventListener('keydown', onDragModifierKey)
  document.removeEventListener('keyup', onDragModifierKey)
  if (!card) { dragCard.value = null; return }

  if (activeVisualizer.value === 'hierarchical') {
    // Commit the pending reparent (null target = become a root), then let the
    // layout re-solve pull the row back into its computed slot.
    updateNode(node.id, { extent: undefined })
    if (reparentDrag.value) {
      applyReparent(reparentDrag.value.cardId, reparentDrag.value.targetId)
    }
    reparentDrag.value = null
    dragCard.value = null
    nextTick(() => { collapseGeneration.value++ })
    return
  }

  if (activeVisualizer.value === 'free-web') {
    // Persist the final positions: the dragged card, and any subtree
    // followers. Rendered coords go back through the inverse of the Auto
    // Condense transform (identity when it is off), so stored positions stay
    // in true coordinate space.
    const t = condenseTransform.value
    const toRaw = (nx, ny, w, h) => {
      if (!t) return { x: nx, y: ny }
      const rcx = t.cx + ((nx + w / 2) - t.cx) / t.k
      const rcy = t.cy + ((ny + h / 2) - t.cy) / t.k
      return { x: rcx - w / 2, y: rcy - h / 2 }
    }
    const w = node.dimensions?.width || card.width || 300
    const h = node.dimensions?.height || 200
    const raw = toRaw(node.position.x, node.position.y, w, h)
    card.x = Math.round(raw.x)
    card.y = Math.round(raw.y)
    const state = subtreeDrag.value
    if (state) {
      for (const follower of state.offsets) {
        const c = cards.value.find(x => x.id === follower.id)
        const fn = c && findNode(String(c.id))
        if (c && fn) {
          const fw = fn.dimensions?.width || c.width || 300
          const fh = fn.dimensions?.height || 200
          const fraw = toRaw(fn.position.x, fn.position.y, fw, fh)
          c.x = Math.round(fraw.x)
          c.y = Math.round(fraw.y)
        }
      }
      // Ctrl+Shift: pack the subtree into concentric rings on release.
      if (state.tighten) {
        applyTightenGlide(card, state.offsets.map(o => o.id))
      }
    }
  }

  subtreeDrag.value = null
  dragCard.value = null
}

// ─── Border-tracking connection dot ───
//
// One dot per hovered card, clinging to the nearest point on the card's
// perimeter and following the mouse while it is inside the hot band (a
// generous ring past the card edge, plus a thin rim inside it). The dot is a
// live Vue Flow source Handle, so pressing and dragging it starts a real
// connection. Node-internals are refreshed (rAF-throttled) as the dot moves so
// Vue Flow's rubber band anchors exactly where the user grabbed.
const liveDot = ref(null) // { cardId, x, y, size } — node-local canvas px

// Hot band, in SCREEN pixels (converted per event): how far outside the edge
// the zone reaches. The band exists ONLY outside the card — over the card
// itself there is never a dot, so dragging the card is never stolen.
const CONNECT_BAND_OUT_PX = 52
// On-screen dot diameter, likewise constant.
const CONNECT_DOT_PX = 30

// Canvas-space ceiling for the band thickness: without it, far-out zooms
// would create enormous invisible frames overlapping neighbouring cards and
// stealing their presses.
const CONNECT_BAND_MAX_CANVAS = 120

function connectBandCanvas() {
  const z = viewport.value?.zoom || 1
  return Math.min(CONNECT_BAND_OUT_PX / z, CONNECT_BAND_MAX_CANVAS)
}

// The band strips reach CONNECT_BAND_OUT_PX on screen (capped in canvas units).
const connectBandStyle = computed(() => {
  void viewport.value?.zoom
  return { '--band': `${Math.round(connectBandCanvas())}px` }
})

let dotInternalsRaf = null

function trackConnectDot(event, card) {
  // While a connection is in flight the anchor is fixed — don't move it.
  if (connecting.value) return
  const el = cardElements.value[card.id]
  if (!el) return
  const r = el.getBoundingClientRect()
  const z = viewport.value?.zoom || 1
  const bandOut = connectBandCanvas()
  const px = (event.clientX - r.left) / z
  const py = (event.clientY - r.top) / z
  const w = r.width / z
  const h = r.height / z

  // The dot exists only while the pointer is OUTSIDE the card, within the
  // band. Over the card itself: no dot — the whole surface drags the card.
  const inside = px > 0 && px < w && py > 0 && py < h
  if (inside) { clearConnectDot(); return }

  // Nearest point on the perimeter, and the pointer's distance to it.
  const x = Math.max(0, Math.min(w, px))
  const y = Math.max(0, Math.min(h, py))
  if (Math.hypot(px - x, py - y) > bandOut) { clearConnectDot(); return }

  liveDot.value = {
    cardId: card.id,
    x: Math.round(x),
    y: Math.round(y),
    size: Math.round(CONNECT_DOT_PX / z)
  }

  // Refresh this node's handle bounds so a press on the dot anchors the
  // connection at the dot's CURRENT spot, not where it was last measured.
  if (!dotInternalsRaf) {
    dotInternalsRaf = requestAnimationFrame(() => {
      dotInternalsRaf = null
      updateNodeInternals([String(card.id)])
    })
  }
}

function clearConnectDot() {
  if (connecting.value) return
  liveDot.value = null
}

// Block a node drag when the press lands on a real interaction surface (text
// entry, media controls, links). One capture-phase guard on the card root
// replaces per-element opt-outs: stopping propagation here means Vue Flow's
// drag handler on the node wrapper never sees the press, while the element
// itself behaves natively.
let pressOnFocusedField = false

function maybeBlockNodeDrag(event) {
  const t = event.target
  if (!t || !t.closest) return
  // Remember whether this press landed on a field that was ALREADY focused —
  // the context-menu handler uses it to decide native-vs-custom menu.
  pressOnFocusedField = !!t.closest('input, textarea, [contenteditable="true"]') &&
    document.activeElement === t
  if (t.closest('input, textarea, select, video, audio, a, [contenteditable="true"], .v-select, .v-field__input')) {
    event.stopPropagation()
  }
}

// Which row is under this canvas point? Used as the prospective parent while
// dragging in the hierarchical view. Excludes the dragged card and any of its own
// descendants — reparenting a node under its own child would orphan the subtree.
/**
 * Which row is at this Y? Used while dragging in the tree, where movement is
 * vertical only so the X coordinate carries no information.
 *
 * Excludes the dragged node and its own descendants — reparenting a node under its
 * own child would orphan the subtree.
 */
function hierarchyRowAtY(y, draggedId) {
  const layout = hierarchyLayout.value
  if (!layout) return null

  const banned = descendantsOf(draggedId)
  banned.add(draggedId)

  for (const card of cards.value) {
    if (banned.has(card.id)) continue
    const pos = layout.get(card.id)
    if (!pos) continue
    const el = cardElements.value[card.id]
    const h = el?.offsetHeight || pos.height || 46
    if (y >= pos.y && y <= pos.y + h) return card.id
  }
  return null
}

// Offsets of every subtree member relative to an origin point, as they stand now.
function captureSubtreeOffsets(origin, memberIds) {
  return memberIds.map(id => {
    const c = cards.value.find(x => x.id === id)
    return c ? { id, dx: c.x - origin.x, dy: c.y - origin.y } : null
  }).filter(Boolean)
}

/**
 * Attach the grabbed card's linked subtree to the in-flight drag.
 *
 * Offsets are relative to the dragged NODE's current position (which equals the
 * card's stored position at drag start), so followers hold their present
 * formation. With `tighten` set, the cluster is packed into concentric rings on
 * RELEASE (see onFlowNodeDragStop).
 */
function attachSubtreeToDrag(card, tighten) {
  const members = linkedSubtreeOf(card.id)
  if (!members.size) return false
  const node = findNode(String(card.id))
  const origin = node ? node.position : { x: card.x, y: card.y }
  subtreeDrag.value = {
    tighten: !!tighten,
    offsets: captureSubtreeOffsets(origin, [...members])
  }
  return true
}

// Pack the subtree with the transient glide (shared by drag release and any
// direct callers).
function applyTightenGlide(card, memberIds) {
  autoArranging.value = true
  tightenSubtree(card, memberIds)
  setTimeout(() => {
    autoArranging.value = false
    collapseGeneration.value++
  }, AUTO_ARRANGE_DURATION)
}

/**
 * Ctrl / Shift pressed (or released) while a node drag is already running.
 *
 * Ctrl is LATCHED: once it attaches the subtree, releasing the key does not
 * detach it — a slipped finger mid-drag shouldn't silently abandon the subtree.
 * Shift toggles whether the cluster is packed on release. Escape drops the
 * subtree from the drag and puts the follower nodes back.
 */
function onDragModifierKey(event) {
  if (!dragCard.value) return
  if (activeVisualizer.value !== 'free-web') return

  if (event.key === 'Escape') {
    // Followers were only moved as NODES (cards untouched until release), so
    // putting them back is just re-syncing node positions from the cards.
    if (subtreeDrag.value) {
      for (const follower of subtreeDrag.value.offsets) {
        const c = cards.value.find(x => x.id === follower.id)
        const n = c && findNode(String(c.id))
        if (n) n.position = { x: c.x, y: c.y }
      }
      subtreeDrag.value = null
    }
    return
  }

  const ctrl = event.ctrlKey || event.metaKey
  const state = subtreeDrag.value

  if (ctrl && !state) {
    // Attach mid-drag, from the CURRENT positions, so followers keep their
    // present spacing rather than snapping to where they sat at mousedown.
    attachSubtreeToDrag(dragCard.value, event.shiftKey)
    return
  }
  if (!state) return

  // Shift is read live: it decides whether the cluster packs on release.
  state.tighten = event.shiftKey
  // Ctrl itself stays latched — releasing it keeps the subtree attached.
}

/**
 * Every node hanging off `rootId`, derived from the LINK GRAPH rather than the
 * hierarchical layout — so it works in any view.
 *
 * Links are undirected, so "child" means "reachable without passing back through
 * the root". Breadth-first from the root's neighbours; the visited set (seeded with
 * the root) both breaks cycles and stops the walk escaping back up through it.
 */
function linkedSubtreeOf(rootId) {
  const adjacency = new Map(cards.value.map(c => [c.id, []]))
  for (const link of nodeLinks.value) {
    if (!adjacency.has(link.sourceCardId) || !adjacency.has(link.targetCardId)) continue
    adjacency.get(link.sourceCardId).push(link.targetCardId)
    adjacency.get(link.targetCardId).push(link.sourceCardId)
  }

  const visited = new Set([rootId])
  const out = new Set()
  const queue = [...(adjacency.get(rootId) || [])]

  while (queue.length) {
    const id = queue.shift()
    if (visited.has(id)) continue
    visited.add(id)
    out.add(id)
    for (const next of adjacency.get(id) || []) {
      if (!visited.has(next)) queue.push(next)
    }
  }
  return out
}

function descendantsOf(rootId) {
  const out = new Set()
  const layout = hierarchyLayout.value
  if (!layout) return out
  // layout entries carry parentId, so walk the map repeatedly until stable.
  let grew = true
  while (grew) {
    grew = false
    for (const [id, pos] of layout) {
      if (out.has(id)) continue
      if (pos.parentId === rootId || out.has(pos.parentId)) {
        out.add(id)
        grew = true
      }
    }
  }
  return out
}

// Apply a hierarchical reparent: drop onto a row to become its child, or onto
// empty space to become a root. Implemented by rewriting links, since the tree is
// derived from the link graph rather than stored parent pointers.
function applyReparent(cardId, newParentId) {
  const layout = hierarchyLayout.value
  const currentParent = layout?.get(cardId)?.parentId ?? null
  if (currentParent === newParentId) return

  // Drop the link to the old parent, if there is one.
  if (currentParent != null) {
    const stale = nodeLinks.value.find(
      l => (l.sourceCardId === currentParent && l.targetCardId === cardId) ||
           (l.sourceCardId === cardId && l.targetCardId === currentParent)
    )
    if (stale) deleteLink(stale.id)
  }

  if (newParentId != null) {
    createLink(newParentId, cardId)
    triggerFlash(newParentId)
  }
  triggerFlash(cardId)
  balancedWebEpoch.value++   // tree changed; force dependent layouts to re-solve
}

// ─── Vue Flow connection lifecycle (drag a border dot to link) ───

// Reject self-links and duplicates while the user is still aiming, so invalid
// targets don't light up as connectable.
//
// CAUTION: Vue Flow runs this against EVERY edge passed to setEdges as well,
// not just interactive connection attempts — so a persisted link re-presenting
// itself (same id) must count as valid, or no stored edge ever renders.
function isValidConnection(connection) {
  const s = Number(connection.source)
  const t = Number(connection.target)
  if (!Number.isFinite(s) || !Number.isFinite(t) || s === t) return false
  const existing = nodeLinks.value.find(
    l => (l.sourceCardId === s && l.targetCardId === t) ||
         (l.sourceCardId === t && l.targetCardId === s)
  )
  if (!existing) return true
  return String(existing.id) === String(connection.id ?? '')
}

function onConnectStart(params) {
  connecting.value = true
  connectDidComplete = false
  pendingConnectSource.value = params?.nodeId ? Number(params.nodeId) : null
}

function onConnect(connection) {
  const s = Number(connection.source)
  const t = Number(connection.target)
  connectDidComplete = true
  if (createLink(s, t)) {
    triggerFlash(s)
    triggerFlash(t)
    // A first connection pulls a lone node in next to its anchor (see the
    // nodeLinks watcher) — same behaviour as before.
  }
}

// Release: over a card, onConnect already made the link. Over empty canvas,
// open the spawn menu there — choosing a type creates the card AND the link
// back to the source node (see spawnFromDrop).
function onConnectEnd(event) {
  connecting.value = false
  liveDot.value = null
  if (connectDidComplete) {
    pendingConnectSource.value = null
    return
  }
  const clientX = event?.clientX ?? event?.changedTouches?.[0]?.clientX
  const clientY = event?.clientY ?? event?.changedTouches?.[0]?.clientY
  const onPane = event?.target?.classList?.contains('vue-flow__pane')
  if (onPane && clientX != null && pendingConnectSource.value != null) {
    dropMenuPos.value = toFlow(clientX, clientY)
    showDropMenu.value = true
    // pendingConnectSource stays set — consumed by spawnFromDrop.
  } else {
    pendingConnectSource.value = null
  }
}

// ─── Zoom actions ───

// Frame every card in the viewport (F key / Fit chip / board open).
function fitBoard() {
  fitView({ padding: 0.12, maxZoom: 1, duration: 400 })
}


// Add parent node card
function addParentNode(parentType) {
  const pos = getCanvasCenter(-90, -90)

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
  } else if (type === 'contact') {
    newCard.contactRole = ''
    newCard.contactOrg = ''
    newCard.contactPhone = ''
    newCard.contactEmail = ''
    newCard.notes = ''
    newCard.width = 460
  } else if (type === 'question') {
    newCard.content = ''
    newCard.questionAnswer = ''
    newCard.questionAnswered = false
    newCard.width = 500
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
  // If this spawn ended a connection drag, link the new card back to its source.
  const sourceId = pendingConnectSource.value
  if (sourceId != null && createLink(sourceId, newCard.id)) {
    triggerFlash(sourceId)
    triggerFlash(newCard.id)
  }
  closeDropMenu()
  // The drop point is wherever the user released, which may overlap existing
  // cards. Nudge the new node clear while keeping it near its parent.
  nextTick(() => {
    const anchor = cards.value.find(c => c.id === sourceId)
    if (anchor) ensureSpawnClear(newCard, anchor)
  })
}

// Handle Ctrl+V while drop menu is open -> paste content and auto-link
function handleDropPaste(event) {
  if (!showDropMenu.value) return false

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
        const pastedAnchorId = pendingConnectSource.value
        if (pastedAnchorId != null && createLink(pastedAnchorId, newCard.id)) {
          triggerFlash(pastedAnchorId)
          triggerFlash(newCard.id)
        }
        closeDropMenu()
        nextTick(() => {
          const anchor = cards.value.find(c => c.id === pastedAnchorId)
          if (anchor) ensureSpawnClear(newCard, anchor)
        })
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
        const pastedAnchorId = pendingConnectSource.value
        if (pastedAnchorId != null && createLink(pastedAnchorId, newCard.id)) {
          triggerFlash(pastedAnchorId)
          triggerFlash(newCard.id)
        }
        closeDropMenu()
        nextTick(() => {
          const anchor = cards.value.find(c => c.id === pastedAnchorId)
          if (anchor) ensureSpawnClear(newCard, anchor)
        })

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

// Confirm delete of a single node (shows the stressed dialog)
function confirmDelete(id) {
  deleteTargetIds.value = [id]
  showDeleteConfirm.value = true
}

// Confirm delete of a node AND its whole branch (linked subtree)
function confirmDeleteBranch(id) {
  deleteTargetIds.value = [id, ...linkedSubtreeOf(id)]
  showDeleteConfirm.value = true
}

function cancelDelete() {
  showDeleteConfirm.value = false
  deleteTargetIds.value = []
}

// Execute delete (after confirmation) — removes every targeted node
function executeDelete() {
  for (const id of deleteTargetIds.value) {
    deleteLinksForCard(id)
  }
  const doomed = new Set(deleteTargetIds.value)
  cards.value = cards.value.filter(c => !doomed.has(c.id))
  if (doomed.has(activeCardId.value)) {
    activeCardId.value = null
  }
  showDeleteConfirm.value = false
  deleteTargetIds.value = []
}

// Delete via keyboard now routes through the same stressed confirmation —
// a single keypress should not be able to irreversibly destroy a node.
function deleteCard(id) {
  confirmDelete(id)
}

// ─── Node right-click context menu ───
// {cardId, x, y} — x/y are screen px relative to the canvas element.
const contextMenu = ref(null)

const contextMenuCard = computed(() =>
  contextMenu.value ? cards.value.find(c => c.id === contextMenu.value.cardId) : null
)

// "Edit Segment" / "Edit Text" / ... — the node's own type identity, title-cased.
const contextMenuTypeLabel = computed(() => {
  const label = contextMenuCard.value ? (nodeType(contextMenuCard.value).label || 'Node') : 'Node'
  return label.charAt(0).toUpperCase() + label.slice(1).toLowerCase()
})

const contextMenuBranchCount = computed(() =>
  contextMenuCard.value ? linkedSubtreeOf(contextMenuCard.value.id).size : 0
)

function onFlowNodeContextMenu({ event, node }) {
  const card = node.data?.card
  if (!card) return
  // A right-click on a field the user is ACTIVELY editing keeps the native
  // browser menu (copy/paste matters there). Any other right-click on the
  // node — including unfocused fields — opens our menu.
  if (pressOnFocusedField && event.target.closest?.('input, textarea, [contenteditable="true"]')) return
  event.preventDefault()
  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return
  contextMenu.value = {
    cardId: card.id,
    // Clamp so the menu never opens off the canvas edge.
    x: Math.min(event.clientX - rect.left, rect.width - 250),
    y: Math.min(event.clientY - rect.top, rect.height - 170)
  }
  activeCardId.value = card.id
}

function closeContextMenu() {
  contextMenu.value = null
}

// Edit: bring the node up to reading/editing zoom and drop focus into its
// first text field.
function editFromContextMenu() {
  const card = contextMenuCard.value
  closeContextMenu()
  if (!card) return
  focusCard(card)
  setTimeout(() => {
    const el = cardElements.value[card.id]
    el?.querySelector('input, textarea')?.focus()
  }, 650)
}

function deleteFromContextMenu() {
  const card = contextMenuCard.value
  closeContextMenu()
  if (card) confirmDelete(card.id)
}

function deleteBranchFromContextMenu() {
  const card = contextMenuCard.value
  closeContextMenu()
  if (card) confirmDeleteBranch(card.id)
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
async function saveBoard(episodeOverride = null) {
  const targetEpisode = episodeOverride || currentEpisode.value
  if (!targetEpisode) {
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
      // Only send image_data for genuinely new base64 payloads. Once media lives
      // on the filesystem, imageUrl is a /pool/... path — sending that as
      // image_data fails the backend's base64 decode, which nulls media_asset_id
      // and orphans the file. Send media_asset_id instead so it re-links.
      image_data: (card.imageUrl && card.imageUrl.startsWith('data:')) ? card.imageUrl : null,
      media_asset_id: card.mediaAssetId || null,
      // Client-side additions (e.g. source page metadata) are merged with the
      // backend's intrinsic/EXIF extraction on save.
      media_metadata: card.mediaMetadata || null,
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
      // Contact and question cards keep their structured fields in social_metadata
      // (already a JSON grab-bag) rather than needing new columns per type.
      social_metadata: typeFieldsForSave(card),
      comments: Array.isArray(card.comments) && card.comments.length ? card.comments : null
    }))

    // Prepare node links for save (map card IDs to array indices)
    const node_links = getLinksForSave(cards.value)

    const response = await fetchJson(`/api/whiteboard/${targetEpisode}/save`, {
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
  boardLoaded = false
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
    } finally {
      boardLoaded = true
      await nextTick()
      separateOverlappingCards()
      pendingInitialFit = cards.value.length > 0
      scheduleFitFallback()
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
        collapsed: item.collapsed || false,
        // Comments exist on every node type, so they live on the base card.
        comments: Array.isArray(item.comments) ? item.comments : []
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
        // Restore local cache status (Twitter media stored on filesystem)
        card._locallyCached = item.social_metadata?._locally_cached || false
      } else if (item.item_type === 'image') {
        // Filesystem-backed media serves via media_url (/pool/...); image_data is
        // only populated for legacy/standalone base64 cards. Prefer media_url.
        card.imageUrl = item.media_url || item.image_data || ''
        card.mediaAssetId = item.media_asset_id || null
        card.mediaMetadata = item.media_metadata || null
        card.caption = item.caption || ''
        card.notes = item.notes || ''
        // Source URL for images dragged in from a web page (blank for local files)
        card.url = item.url || ''
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
      } else if (item.item_type === 'contact') {
        // Structured fields ride in social_metadata — see typeFieldsForSave().
        const meta = item.social_metadata || {}
        card.contactRole = meta.contactRole || ''
        card.contactOrg = meta.contactOrg || ''
        card.contactPhone = meta.contactPhone || ''
        card.contactEmail = meta.contactEmail || ''
        card.notes = item.notes || ''
      } else if (item.item_type === 'question') {
        const meta = item.social_metadata || {}
        card.content = item.text_content || ''
        card.questionAnswer = meta.questionAnswer || ''
        card.questionAnswered = !!meta.questionAnswered
      }

      return card
    })

    // Load node links (map DB indices back to client card IDs). Reset the
    // snap-watcher's memory first, or every link of the incoming board reads
    // as "newly created" after an episode switch and the first-connection
    // snap starts rearranging freshly loaded cards.
    knownLinkIds = new Set()
    if (response.node_links) {
      loadLinks(response.node_links, cards.value)
    }

  } catch (error) {
    console.error('Failed to load whiteboard:', error)
    notifyUserStandard('Failed to load whiteboard', NOTIFICATION_COLORS.ERROR, 3000)
  } finally {
    boardLoaded = true
    // Stored positions can leave cards overlapping — from older boards, from
    // hand-dragging, or simply from being saved at a different zoom. Separate them
    // once the DOM has measured, so a freshly loaded board is always readable.
    await nextTick()
    separateOverlappingCards()
    // Open framed to the content — the whole structure visible, at whatever
    // zoom that takes. Deferred to nodes-initialized so the frame measures the
    // real card sizes.
    pendingInitialFit = cards.value.length > 0
    scheduleFitFallback()
  }
}

/**
 * Guarantee no card overlaps another, by EXPANDING THE WHOLE BOARD.
 *
 * Pairwise nudging was tried first and does not work: pushing two cards apart just
 * shoves each into its neighbours, so it oscillates and plateaus around 8-12
 * residual overlaps no matter how many passes run (measured 66 -> 12 at 8 passes,
 * and still 8 at 120). Biasing the push direction only collapses the board into a
 * line (a 15789x56 bounding box in testing).
 *
 * Scaling every position outward from the centroid resolves it completely, because
 * gaps grow while card sizes stay fixed. It also preserves the arrangement and the
 * board's shape — measured 66 -> 0, 435 -> 0 and 1200 -> 0, with aspect ratios
 * staying between 1.3 and 3.0.
 *
 * A board with no overlaps is left byte-identical.
 */
function separateOverlappingCards() {
  const list = cards.value
  if (list.length < 2) return

  const GAP = 60
  const box = card => {
    const el = cardElements.value[card.id]
    return {
      w: el?.offsetWidth || (card.collapsed ? 220 : (card.width || 300)),
      h: el?.offsetHeight || (card.collapsed ? 46 : 200)
    }
  }

  const positioned = list.filter(c => Number.isFinite(c.x) && Number.isFinite(c.y))
  if (positioned.length < 2) return

  const anyOverlap = () => {
    for (let i = 0; i < positioned.length; i++) {
      for (let j = i + 1; j < positioned.length; j++) {
        const a = positioned[i], b = positioned[j]
        const ba = box(a), bb = box(b)
        const overlapX = a.x < b.x + bb.w + GAP && a.x + ba.w + GAP > b.x
        const overlapY = a.y < b.y + bb.h + GAP && a.y + ba.h + GAP > b.y
        if (overlapX && overlapY) return true
      }
    }
    return false
  }

  if (!anyOverlap()) return

  // Expand outward from the centroid until nothing collides. Bounded so a
  // pathological board cannot loop forever.
  const STEP = 1.15
  for (let round = 0; round < 40 && anyOverlap(); round++) {
    let cx = 0, cy = 0
    for (const c of positioned) {
      const b = box(c)
      cx += c.x + b.w / 2
      cy += c.y + b.h / 2
    }
    cx /= positioned.length
    cy /= positioned.length

    for (const c of positioned) {
      const b = box(c)
      const centreX = c.x + b.w / 2
      const centreY = c.y + b.h / 2
      c.x = (cx + (centreX - cx) * STEP) - b.w / 2
      c.y = (cy + (centreY - cy) * STEP) - b.h / 2
    }
  }

  for (const c of positioned) {
    c.x = Math.round(c.x)
    c.y = Math.round(c.y)
  }
  nextTick(() => { collapseGeneration.value++ })
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
  const previousEpisode = currentEpisode.value
  switchingViaDialog = true
  if (saveTimeout) clearTimeout(saveTimeout)

  try {
    sessionStorage.setItem('currentEpisode', ep)
    sessionStorage.setItem('currentEpisodeId', ep)

    // Update URL query param so identifier computed picks it up
    await router.replace({ query: { ...route.query, episode: ep } })

    showEpisodeDialog.value = false
    notifyUserStandard(`Episode ${ep} selected`, NOTIFICATION_COLORS.SUCCESS, 3000)

    if (pendingSaveAfterSelect.value) {
      // Menu-save with no episode: the point is to save the CURRENT cards to
      // the episode the user just picked — do not load over them.
      pendingSaveAfterSelect.value = false
      await saveBoard(ep)
    } else {
      // Normal switch: outgoing board goes back to ITS OWN episode, then the
      // new episode's board loads.
      if (previousEpisode && boardLoaded && cards.value.length > 0) {
        await saveBoard(previousEpisode)
      }
      await loadBoard()
    }
  } finally {
    switchingViaDialog = false
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
    // The currentEpisode watcher saves the outgoing board (under its own
    // episode) and loads the new one — no extra load here.
    await router.replace({ query: { ...route.query, episode: epNum } })
    notifyUserStandard(`Episode ${epNum} created and selected`, NOTIFICATION_COLORS.SUCCESS, 3000)
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
// For a web-dropped image, ask the backend what the source URL's page says about
// itself (og:title / description / site). Populates the card's metadata panel so
// the image is described by more than its pixel dimensions. Best-effort: many
// image URLs are bare files with no page metadata, and some hosts return 403.
async function fetchImagePageMetadata(card) {
  if (!card.url || !/^https?:\/\//.test(card.url)) return
  try {
    const response = await fetchJson(
      `/api/whiteboard/fetch-link-preview?url=${encodeURIComponent(card.url)}`,
      { method: 'POST' }
    )
    if (!response || response.error) return
    const merged = { ...(card.mediaMetadata || {}) }
    if (response.title) merged.source_title = response.title
    if (response.description) merged.source_description = response.description
    if (response.domain) merged.source_site = response.domain
    card.mediaMetadata = merged
  } catch (error) {
    // Non-fatal: the card still shows intrinsic metadata from the backend.
    console.debug('No page metadata for dropped image:', error)
  }
}

// Turn an image card that remembers its source URL into a full link card,
// fetching the preview (title / description / og:image) for that URL.
function convertImageToLinkCard(card) {
  if (!card.url) return
  card.type = 'link'
  card.notes = card.notes || ''
  card.previewTitle = null
  card.previewDescription = null
  // Keep the dragged image visible until the real preview arrives.
  card.previewImage = card.imageUrl || null
  card.previewDomain = null
  card.previewFavicon = null
  card.fetchingPreview = false
  card.socialMetadata = null
  card.width = 500
  // bypassCache: we seeded previewImage above, which would otherwise short-circuit.
  fetchLinkPreview(card, true)
}

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

      // Check for API error info passed through from link preview
      if (response.x_error_service) {
        card.apiWarning = {
          service: response.x_error_service,
          status_code: response.x_error_status_code,
          message: response.x_error_message,
          endpoint: response.x_error_endpoint,
          fallback_used: response.x_error_fallback_used
        }
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

// Platform chip config for social media badges
// ─── Node type identity (single source of truth) ───
// Colors were previously duplicated inline across ~16 template sites (headers,
// collapsed pills, borders), which is why expanded and collapsed cards drifted
// apart. Everything type-colored now reads from here.
const NODE_TYPES = {
  text: { label: 'TEXT', icon: 'mdi-text', color: '#FFA726', tint: '#FFF8E1' },
  link: { label: 'LINK', icon: 'mdi-link', color: '#1976D2', tint: '#E3F2FD' },
  image: { label: 'IMAGE', icon: 'mdi-image', color: '#757575', tint: '#F5F5F5' },
  video: { label: 'VIDEO', icon: 'mdi-video', color: '#E53935', tint: '#FFEBEE' },
  audio: { label: 'AUDIO', icon: 'mdi-music', color: '#8E24AA', tint: '#F3E5F5' },
  html: { label: 'HTML', icon: 'mdi-language-html5', color: '#F57C00', tint: '#FFF3E0' },
  code: { label: 'CODE', icon: 'mdi-code-tags', color: '#43A047', tint: '#E8F5E9' },
  markdown: { label: 'MD', icon: 'mdi-language-markdown', color: '#3949AB', tint: '#E8EAF6' },
  contact: { label: 'CONTACT', icon: 'mdi-account-box', color: '#00897B', tint: '#E0F2F1' },
  question: { label: 'QUESTION', icon: 'mdi-help-circle', color: '#C2185B', tint: '#FCE4EC' },
  parent: { label: 'NODE', icon: 'mdi-file-tree', color: '#1565C0', tint: '#E3F2FD' },
  file: { label: 'FILE', icon: 'mdi-file', color: '#546E7A', tint: '#ECEFF1' }
}

const WARNING_TYPE = { label: 'WARNING', icon: 'mdi-alert', color: '#ff4444', tint: '#2d1010' }

// Concrete hexes for social platforms (socialPlatformChip returns Vuetify theme
// names, which work as :color props but not in raw CSS).
const SOCIAL_HEX = {
  x: '#000000',
  twitter: '#1DA1F2',
  tiktok: '#000000',
  youtube: '#FF0000',
  instagram: '#C13584',
  facebook: '#1877F2',
  reddit: '#FF4500'
}

// Resolve a card to its type identity. Special cases that override the raw
// item_type: warning text cards, social link cards (platform branding), and
// parent nodes (which carry their own configured color).
function nodeType(card) {
  if (!card) return NODE_TYPES.text
  if (card.type === 'text' && card.isWarning) return WARNING_TYPE

  if (card.type === 'link' && card.socialMetadata?.platform) {
    const chip = socialPlatformChip(card.socialMetadata.platform)
    return {
      label: (chip.label || 'LINK').toUpperCase(),
      icon: chip.icon || 'mdi-link',
      // socialPlatformChip returns Vuetify theme names ("primary"); those work
      // as :color props but not in raw CSS, so keep a concrete hex for styling.
      color: SOCIAL_HEX[card.socialMetadata.platform] || NODE_TYPES.link.color,
      tint: NODE_TYPES.link.tint
    }
  }

  if (card.type === 'parent') {
    const meta = card.socialMetadata || {}
    return {
      label: (meta.parentNodeType || '').toUpperCase(),
      icon: meta.parentNodeIcon || NODE_TYPES.parent.icon,
      color: meta.parentNodeColor || NODE_TYPES.parent.color,
      tint: NODE_TYPES.parent.tint
    }
  }

  return NODE_TYPES[card.type] || NODE_TYPES.file
}

// Width the header title field to its own content, so it doesn't stretch across
// the header. A full-width input swallows presses everywhere in the header and
// startDrag() refuses to drag from INPUT targets — leaving the header dead to
// drag-to-move. Sized to content, only the text itself is a text target and the
// surrounding header chrome stays draggable.
// The title input is capped at TITLE_HOTSPOT_CH characters wide regardless of how
// long the title is. Anything the input covers is a text-edit target and cannot
// drag the card, so keeping it short leaves the rest of the header draggable. The
// full title still displays — it overflows into the sibling span below.
const TITLE_HOTSPOT_CH = 7

function titleFieldStyle(card) {
  const text = (card?.title || '') || titlePlaceholder(card)
  // Width is in ch units so it tracks the header font (0.95rem/700) directly,
  // rather than needing a magic em ratio per font size.
  const ch = Math.max(3, Math.min(TITLE_HOTSPOT_CH, text.length + 1))
  return {
    width: `${ch}ch`,
    flex: '0 0 auto',
    fontSize: '0.95rem'
  }
}

// The placeholder is what's visible when the title is empty, so it drives the
// width in that state.
function titlePlaceholder(card) {
  if (!card) return 'Title'
  if (card.type === 'image') return card.caption || 'Image'
  if (card.type === 'link') return card.previewTitle || card.url || 'Link'
  const t = NODE_TYPES[card.type]
  return t ? t.label.charAt(0) + t.label.slice(1).toLowerCase() : 'Title'
}

// ─── Visualizers (board layout modes) ───

const VISUALIZERS = [
  {
    key: 'free-web',
    label: 'Free Web',
    icon: 'mdi-graph-outline',
    description: 'Cards sit wherever you drop them'
  },
  {
    key: 'balanced-web',
    label: 'Balanced Web',
    icon: 'mdi-vector-triangle',
    description: 'Same web, auto-spaced for even distribution'
  },
  {
    key: 'waterfall-web',
    label: 'Waterfall Web',
    icon: 'mdi-file-tree-outline',
    description: 'Parents on top, children below, siblings side by side'
  },
  {
    key: 'hierarchical',
    label: 'Hierarchical',
    icon: 'mdi-file-tree',
    description: 'Parent/child relationships as an indented tree'
  }
]

const activeVisualizer = ref('free-web')
const visualizerMenuOpen = ref(false)
const viewSelectorOpen = ref(false)

const currentVisualizer = computed(
  () => VISUALIZERS.find(v => v.key === activeVisualizer.value) || VISUALIZERS[0]
)

// Collapsed cards render as a wide horizontal ROW in the hierarchical view rather
// than the compact pill used elsewhere. A row reads as a line item in a tree and
// its full width makes the indent legible. This is a rendering state derived from
// the existing `collapsed` boolean — no schema change, and a card keeps its
// collapsed state when switching views.
function isCollapsedRow(card) {
  return card.collapsed && activeVisualizer.value === 'hierarchical'
}

// Fixed CANVAS-SPACE width for the hierarchical tree column. Rows used to derive
// their width from the viewport divided by the zoom (a screen-space rule), which
// meant row geometry changed on every zoom step. A fixed canvas width keeps the
// tree honest under geometric zoom: zooming just scales it, like everything else.
const TREE_WIDTH = 1600

// ─── Waterfall web layout ───
//
// A layered tree drawn top-down: parent hubs on the top row, each generation of
// children on the row beneath its parent, and siblings placed side by side.
//
// Unlike the hierarchical view (an indented list), this keeps the web's shape —
// children fan out horizontally under their parent rather than stepping right —
// so the structure reads as a waterfall.

const WF_LEVEL_GAP = 220   // vertical distance between generations
const WF_SIBLING_GAP = 80  // horizontal space between siblings
const WF_TREE_GAP = 260    // extra space between separate trees
const WF_ORIGIN = { x: 120, y: 120 }

const waterfallLayout = computed(() => {
  if (activeVisualizer.value !== 'waterfall-web') return null
  const list = cards.value
  if (!list.length) return null
  void collapseGeneration.value  // re-solve when card sizes change

  const elements = toRaw(cardElements.value)
  const sizeOf = card => {
    const el = elements[card.id]
    return {
      w: el?.offsetWidth || (card.collapsed ? 220 : (card.width || 300)),
      h: el?.offsetHeight || (card.collapsed ? 46 : 200)
    }
  }

  const byId = new Map(list.map(c => [c.id, c]))
  const adjacency = new Map(list.map(c => [c.id, []]))
  for (const link of nodeLinks.value) {
    if (!adjacency.has(link.sourceCardId) || !adjacency.has(link.targetCardId)) continue
    adjacency.get(link.sourceCardId).push(link.targetCardId)
    adjacency.get(link.targetCardId).push(link.sourceCardId)
  }

  // Roots: parent-type hubs, else the best-connected card of each component.
  const degree = id => adjacency.get(id)?.length || 0
  const parents = list.filter(c => c.type === 'parent')
  const visited = new Set()
  const roots = []
  for (const p of parents) roots.push(p.id)
  // Any component with no parent hub still needs a root, or it would be dropped.
  for (const c of [...list].sort((a, b) => degree(b.id) - degree(a.id))) {
    if (roots.includes(c.id)) continue
    const reachable = roots.some(r => componentContains(adjacency, r, c.id))
    if (!reachable) roots.push(c.id)
  }

  // BFS from each root: first arrival fixes a card's generation and its parent.
  const children = new Map(list.map(c => [c.id, []]))
  const depth = new Map()
  const rootOf = new Map()
  for (const rootId of roots) {
    if (visited.has(rootId)) continue
    visited.add(rootId)
    depth.set(rootId, 0)
    rootOf.set(rootId, rootId)
    const queue = [rootId]
    while (queue.length) {
      const id = queue.shift()
      // Stable sibling order so the layout doesn't reshuffle between renders.
      const next = (adjacency.get(id) || [])
        .filter(k => !visited.has(k))
        .sort((a, b) => (byId.get(a)?.y ?? 0) - (byId.get(b)?.y ?? 0) ||
          (byId.get(a)?.x ?? 0) - (byId.get(b)?.x ?? 0))
      for (const kid of next) {
        visited.add(kid)
        depth.set(kid, depth.get(id) + 1)
        rootOf.set(kid, rootId)
        children.get(id).push(kid)
        queue.push(kid)
      }
    }
  }
  // Anything still unvisited (isolated card) becomes its own root.
  for (const c of list) {
    if (visited.has(c.id)) continue
    visited.add(c.id)
    depth.set(c.id, 0)
    rootOf.set(c.id, c.id)
    roots.push(c.id)
  }

  // Width of a subtree = max(own width, sum of children's widths + gaps). This is
  // what keeps siblings adjacent without their descendants colliding.
  const subtreeWidth = new Map()
  const measure = id => {
    if (subtreeWidth.has(id)) return subtreeWidth.get(id)
    const card = byId.get(id)
    const own = card ? sizeOf(card).w : 300
    const kids = children.get(id) || []
    let total = 0
    for (const kid of kids) total += measure(kid) + WF_SIBLING_GAP
    if (kids.length) total -= WF_SIBLING_GAP
    const width = Math.max(own, total)
    subtreeWidth.set(id, width)
    return width
  }
  for (const rootId of roots) measure(rootId)

  // Place: each node is centred over the span its children occupy.
  const positions = new Map()
  const place = (id, left, top) => {
    const card = byId.get(id)
    const size = card ? sizeOf(card) : { w: 300, h: 200 }
    const span = subtreeWidth.get(id) || size.w

    positions.set(id, {
      x: Math.round(left + (span - size.w) / 2),
      y: Math.round(top),
      depth: depth.get(id) || 0
    })

    const kids = children.get(id) || []
    if (!kids.length) return
    let childLeft = left
    // Rows are spaced by the tallest card in the generation above.
    const rowGap = size.h + WF_LEVEL_GAP
    for (const kid of kids) {
      place(kid, childLeft, top + rowGap)
      childLeft += (subtreeWidth.get(kid) || 300) + WF_SIBLING_GAP
    }
  }

  let cursorX = WF_ORIGIN.x
  for (const rootId of roots) {
    place(rootId, cursorX, WF_ORIGIN.y)
    cursorX += (subtreeWidth.get(rootId) || 300) + WF_TREE_GAP
  }
  return positions
})

// Is `targetId` in the same connected component as `fromId`?
function componentContains(adjacency, fromId, targetId) {
  const seen = new Set([fromId])
  const queue = [fromId]
  while (queue.length) {
    const id = queue.shift()
    if (id === targetId) return true
    for (const next of adjacency.get(id) || []) {
      if (!seen.has(next)) {
        seen.add(next)
        queue.push(next)
      }
    }
  }
  return false
}

// Hierarchical layout geometry
const HIER_INDENT = 320      // horizontal step per depth level
const HIER_ROW_GAP = 26      // vertical gap between sibling rows
// Tree is pinned to the top-left of the canvas: the root sits at the top edge,
// left-justified, and horizontal panning is locked (see handleCanvasMouseMove) so
// the structure always starts in the same place.
const HIER_ORIGIN = { x: 24, y: 24 }

/**
 * Width of a row in the hierarchical tree.
 *
 * Rows share a fixed canvas-space right edge (TREE_WIDTH), so deeper rows are
 * SHORTER by exactly their extra indent and the tree reads as one aligned
 * column. Pure canvas geometry — zoom scales it like everything else.
 */
function treeRowWidth(card) {
  const depth = hierarchyLayout.value?.get(card?.id)?.depth || 0
  const indent = HIER_ORIGIN.x + depth * HIER_INDENT
  // Never collapse to nothing on a deeply nested row.
  return Math.max(240, TREE_WIDTH - indent)
}

function collapsedRowWidth(card) {
  return treeRowWidth(card)
}

/**
 * Width for an ordinary card. In the hierarchical tree every row spans the
 * viewport; elsewhere cards keep their own natural size.
 */
function treeCardWidth(card, collapsedWidth, expandedWidth) {
  if (activeVisualizer.value === 'hierarchical') return treeRowWidth(card)
  return card.collapsed ? collapsedWidth : (card.width || expandedWidth)
}

// Thumbnail for a collapsed row, when the card carries any media.
function rowMedia(card) {
  if (card.type === 'image') return card.imageUrl || null
  if (card.previewImage) return card.previewImage
  if (card.thumbnailUrl) return card.thumbnailUrl
  if (card.socialMetadata?.thumbnail_url) return card.socialMetadata.thumbnail_url
  return null
}

// Bumped to force the force-directed layout to re-solve (view switch, card added
// or removed, links changed). Without this the solver would either re-run on every
// position tick — fighting its own CSS transition — or never refresh at all.
const balancedWebEpoch = ref(0)

watch(
  () => [activeVisualizer.value, cards.value.length, nodeLinks.value.length].join(':'),
  () => { balancedWebEpoch.value++ }
)

// ─── Semantic zoom (level-of-detail tiers) ───
//
// The viewport applies a real geometric zoom, so a card's canvas-space footprint
// NEVER changes with zoom — spacing and sizing stay proportional at every level.
// What changes is how much detail is drawn INSIDE that footprint:
//
//   detail  (>= 0.75) — everything: body content, metadata, comments, actions
//   compact (>= 0.45) — header, media, primary field; no comments/metadata
//   summary (>= 0.20) — type, thumbnail, title in the same footprint
//   marker  (<  0.20) — a type-coloured plate filling the footprint; icon-led
//
// No counter-scaled text, no position spreading — to read something, zoom in
// (the zoom is smooth and focal-point-correct now, so that is cheap).
const ZOOM_DETAIL = 0.75
const ZOOM_COMPACT = 0.45
const ZOOM_SUMMARY = 0.2

const zoomTier = computed(() => {
  const z = viewport.value?.zoom || 1
  if (z >= ZOOM_DETAIL) return 'detail'
  if (z >= ZOOM_COMPACT) return 'compact'
  if (z >= ZOOM_SUMMARY) return 'summary'
  return 'marker'
})

// Crossing a tier boundary swaps each card's inner content for a different-sized
// element, so measured heights change — the layout solvers (tree, waterfall)
// must re-measure. Waits a frame so the new elements are measurable.
watch(zoomTier, () => {
  nextTick(() => { collapseGeneration.value++ })
})

// Convenience predicates used throughout the card templates.
const showDetail = computed(() => zoomTier.value === 'detail')
const showCompact = computed(() => zoomTier.value === 'detail' || zoomTier.value === 'compact')
const showSummary = computed(() => zoomTier.value !== 'marker')

// LOD footprint box: the summary/marker representations fill the card's own
// canvas-space box, so swapping tiers never changes the card's footprint width.
function lodBoxWidth(card) {
  if (card.type === 'parent') {
    // Mirrors parentNodeSize() — the hub disc fills the same footprint.
    if (card.collapsed) return 260
    return activeVisualizer.value === 'hierarchical' ? 340 : 520
  }
  if (activeVisualizer.value === 'hierarchical') return treeRowWidth(card)
  return card.collapsed ? 220 : (card.width || 300)
}

function lodBoxHeight(card) {
  // Parents are circles — height matches width.
  if (card.type === 'parent') return lodBoxWidth(card)
  return Math.round(lodBoxWidth(card) * 0.42)
}

// ─── Hub labels (parent nodes stay readable at every zoom) ───
//
// Below the compact tier the type/title inside a hub disc is too small to
// read, so each parent gets a SCREEN-SPACE badge ("SEGMENT" + title) anchored
// to its centre — constant on-screen size, tracking pan/zoom and live drags
// via the node's reactive position. This is the map-label pattern: geometry
// scales, landmark labels don't. It does not touch canvas geometry, so the
// constant-footprint rule stays intact.
const showHubLabels = computed(() =>
  (viewport.value?.zoom || 1) < ZOOM_COMPACT && cards.value.some(c => c.type === 'parent')
)

const hubLabels = computed(() => {
  if (!showHubLabels.value) return []
  const vp = viewport.value || { x: 0, y: 0, zoom: 1 }
  return cards.value
    .filter(c => c.type === 'parent')
    .map(c => {
      const node = findNode(String(c.id))
      const pos = node ? node.position : cardPosition(c)
      const w = node?.dimensions?.width || lodBoxWidth(c)
      const h = node?.dimensions?.height || lodBoxHeight(c)
      const t = nodeType(c)
      return {
        id: c.id,
        type: t.label || 'NODE',
        title: c.title || '',
        color: t.color,
        style: {
          left: `${Math.round((pos.x + w / 2) * vp.zoom + vp.x)}px`,
          top: `${Math.round((pos.y + h / 2) * vp.zoom + vp.y)}px`
        }
      }
    })
})

// The spawn menu and endpoint popup are SCREEN-SPACE overlays anchored to a flow
// point: constant on-screen size at every zoom (no counter-scaling), and they
// track the canvas point through pan/zoom via the live viewport.
const dropMenuStyle = computed(() => {
  const s = toScreen(dropMenuPos.value.x, dropMenuPos.value.y)
  return {
    left: `${Math.round(s.x)}px`,
    top: `${Math.round(s.y)}px`,
    transform: 'translate(-50%, 0)'
  }
})

const endpointPopupStyle = computed(() => {
  if (!endpointPopup.value) return {}
  const s = toScreen(endpointPopup.value.x, endpointPopup.value.y)
  return {
    left: `${Math.round(s.x)}px`,
    top: `${Math.round(s.y)}px`,
    transform: 'translate(-50%, -100%) translateY(-12px)'
  }
})

// Width of the summary-tier card: the card's own footprint (tree rows span the
// tree column, like every other tier there).
function summaryCardWidth(card) {
  return activeVisualizer.value === 'hierarchical' ? treeRowWidth(card) : lodBoxWidth(card)
}

// A short excerpt of the card's own content, for the wide hierarchical row.
function summaryPreview(card) {
  const raw = card.content || card.notes || card.markdownContent ||
    card.caption || card.codeContent || card.url || ''
  const text = String(raw).replace(/\s+/g, ' ').trim()
  if (!text) return ''
  // The title already shows first; don't repeat it as the preview.
  const title = (card.title || '').trim()
  if (title && text.startsWith(title)) {
    const rest = text.slice(title.length).trim()
    return rest ? rest.slice(0, 120) : ''
  }
  return text.slice(0, 120)
}


// ─── Per-node user comments ───

// Draft text per card id, keyed so several cards can hold unsent drafts at once.
const commentDrafts = ref({})

function commentAuthor() {
  return currentUser.value?.username || currentUser.value?.email || 'unknown'
}

// Deterministic-enough local id; comments are identified by it for deletion only.
let commentSeq = 0
function addComment(card) {
  const text = (commentDrafts.value[card.id] || '').trim()
  if (!text) return
  if (!Array.isArray(card.comments)) card.comments = []
  card.comments.push({
    id: `c-${Date.now()}-${commentSeq++}`,
    author: commentAuthor(),
    text,
    ts: new Date().toISOString()
  })
  commentDrafts.value[card.id] = ''
}

function deleteComment(card, commentId) {
  if (!Array.isArray(card.comments)) return
  card.comments = card.comments.filter(c => c.id !== commentId)
}

// Only the author may remove their own comment.
function canDeleteComment(comment) {
  return comment.author === commentAuthor()
}

function commentTimestamp(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

// Contact and question cards carry extra fields with no dedicated DB columns.
// They ride along in social_metadata, which is already a JSON catch-all.
function typeFieldsForSave(card) {
  const base = card.socialMetadata ? { ...card.socialMetadata } : {}

  if (card.type === 'contact') {
    base.contactRole = card.contactRole || null
    base.contactOrg = card.contactOrg || null
    base.contactPhone = card.contactPhone || null
    base.contactEmail = card.contactEmail || null
  } else if (card.type === 'question') {
    base.questionAnswer = card.questionAnswer || null
    base.questionAnswered = !!card.questionAnswered
  }

  return Object.keys(base).length ? base : null
}

// Parent hubs anchor the board, so they read larger in the web views (free and
// balanced). The hierarchical view keeps them compact — there, depth conveys the
// same weight and vertical space is at a premium.
function parentNodeSize(card) {
  // Parents must read as the dominant element at every zoom, so they are sized
  // well above the child cards rather than merely matching them. Keep these in
  // step with lodBoxWidth() — the LOD disc fills the same footprint.
  if (card.collapsed) return '260px'
  return activeVisualizer.value === 'hierarchical' ? '340px' : '520px'
}

// True when every card is collapsed, so the toggle can flip its label/icon.
const allCollapsed = computed(
  () => cards.value.length > 0 && cards.value.every(c => c.collapsed)
)

function toggleCollapseAll() {
  const collapse = !allCollapsed.value
  for (const card of cards.value) card.collapsed = collapse
  // Card dimensions changed — connection lines must recompute against the new sizes.
  nextTick(() => { collapseGeneration.value++ })
}

function setVisualizer(key) {
  activeVisualizer.value = key
  visualizerMenuOpen.value = false
  floatingMenuOpen.value = false
  // Glide the cards into the new arrangement, then frame it.
  glideLayout()
  // The new view (and possibly a different LOD variant per card) renders first;
  // re-measure a frame later so the layout solves against the REAL row heights,
  // then frame the result.
  nextTick(() => {
    collapseGeneration.value++
    nextTick(() => { fitBoard() })
  })
}

// ─── Balanced web: force-directed layout ───
//
// Keeps the web topology (no tree, no imposed direction) but computes positions
// so nodes spread evenly: linked cards attract, all cards repel, and a mild pull
// toward the centre stops disconnected clusters drifting apart forever.
//
// Deterministic by design — seeded from each card's stored position and run to a
// fixed iteration count, so the same board always resolves to the same arrangement
// rather than shuffling on every view switch.

const FORCE_ITERATIONS = 320
const FORCE_IDEAL_LINK = 420    // preferred distance between linked cards
const FORCE_REPULSION = 190000  // strength of the all-pairs push
const FORCE_CENTER_PULL = 0.012
// Vertical gravity is stronger than horizontal, which settles the graph into a
// landscape spread instead of a tall column — measured on a real 14-node board:
// 1154x1498 (0.77) with equal pull vs 1583x1088 (1.45) at 1.6x.
const FORCE_VERTICAL_BIAS = 1.6
const FORCE_DAMPING = 0.86
const FORCE_ORIGIN = { x: 700, y: 480 }

/**
 * Run the force-directed solve and return a Map of card id -> {x, y}.
 *
 * Shared by the balanced-web visualizer and the one-shot Auto Arrange action.
 * `parentSpacing` multiplies the repulsion and minimum gap for parent hubs only,
 * so Auto Arrange can push the anchors further apart than the live visualizer does.
 */
function solveForceLayout(list, { parentSpacing = 1, clusterSpacing = 1 } = {}) {
  if (!list.length) return null

  // cardElements is written during render, so read it untracked — depending on it
  // inside a computed would let a render feed back into that computed.
  const elements = toRaw(cardElements.value)
  const nodes = list.map((card, i) => {
    const el = elements[card.id]
    const w = el?.offsetWidth || (card.collapsed ? 220 : (card.width || 300))
    const h = el?.offsetHeight || (card.collapsed ? 52 : 200)
    // Seed on a ring when a card has no meaningful stored position, so the
    // simulation never starts with everything stacked at the origin.
    const angle = (i / list.length) * Math.PI * 2
    return {
      id: card.id,
      isParent: card.type === 'parent',
      x: Number.isFinite(card.x) ? card.x : FORCE_ORIGIN.x + Math.cos(angle) * 300,
      y: Number.isFinite(card.y) ? card.y : FORCE_ORIGIN.y + Math.sin(angle) * 300,
      vx: 0,
      vy: 0,
      w,
      h,
      radius: Math.hypot(w, h) / 2
    }
  })

  const index = new Map(nodes.map((n, i) => [n.id, i]))
  const edges = []
  for (const link of nodeLinks.value) {
    const a = index.get(link.sourceCardId)
    const b = index.get(link.targetCardId)
    if (a !== undefined && b !== undefined && a !== b) edges.push([a, b])
  }

  // Assign every node to a TREE, so nodes belonging to different trees can be
  // pushed apart harder than nodes within one tree. Without this only the parent
  // hubs separate, and their children still tangle in the space between them.
  assignClusters(nodes, edges)

  for (let step = 0; step < FORCE_ITERATIONS; step++) {
    // Cooling factor: large moves early, fine settling later.
    const cooling = 1 - step / FORCE_ITERATIONS

    // Repulsion between every pair.
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i]
        const b = nodes[j]
        let dx = b.x - a.x
        let dy = b.y - a.y
        let dist = Math.hypot(dx, dy)
        if (dist < 1e-3) {
          // Coincident nodes: nudge apart deterministically by index.
          dx = (j - i) * 0.7
          dy = (i + 1) * 0.5
          dist = Math.hypot(dx, dy)
        }
        // Parent hubs get extra breathing room when asked, so the board's anchors
        // read as distinct clusters rather than crowding each other.
        let pairSpacing = (a.isParent && b.isParent) ? parentSpacing
          : (a.isParent || b.isParent) ? 1 + (parentSpacing - 1) * 0.5
            : 1
        // Different trees get interstellar space: they share no edges, so nothing
        // pulls them back together and they can be pushed well apart.
        if (a.cluster !== b.cluster) pairSpacing *= clusterSpacing
        const minGap = (a.radius + b.radius + 40) * pairSpacing
        const effective = Math.max(dist, 1)
        let force = (FORCE_REPULSION * pairSpacing) / (effective * effective)
        if (dist < minGap) force += (minGap - dist) * 1.4
        const fx = (dx / effective) * force
        const fy = (dy / effective) * force
        a.vx -= fx
        a.vy -= fy
        b.vx += fx
        b.vy += fy
      }
    }

    // Attraction along links, toward the ideal separation.
    for (const [ai, bi] of edges) {
      const a = nodes[ai]
      const b = nodes[bi]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.max(Math.hypot(dx, dy), 1)
      const force = (dist - FORCE_IDEAL_LINK) * 0.045
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      a.vx += fx
      a.vy += fy
      b.vx -= fx
      b.vy -= fy
    }

    // Gentle gravity so unconnected islands stay on-screen.
    for (const n of nodes) {
      n.vx += (FORCE_ORIGIN.x - n.x) * FORCE_CENTER_PULL
      n.vy += (FORCE_ORIGIN.y - n.y) * FORCE_CENTER_PULL * FORCE_VERTICAL_BIAS
      n.vx *= FORCE_DAMPING
      n.vy *= FORCE_DAMPING
      // Clamp per-step travel so the simulation can't explode.
      const maxStep = 60 * cooling + 4
      const speed = Math.hypot(n.vx, n.vy)
      if (speed > maxStep) {
        n.vx = (n.vx / speed) * maxStep
        n.vy = (n.vy / speed) * maxStep
      }
      n.x += n.vx
      n.y += n.vy
    }
  }

  // Normalise into positive space with a consistent margin, so the result doesn't
  // land at negative coordinates the user has to pan to find.
  const minX = Math.min(...nodes.map(n => n.x))
  const minY = Math.min(...nodes.map(n => n.y))
  const offsetX = 80 - minX
  const offsetY = 80 - minY

  // Force layout settles distances but is blind to edge crossings, which are what
  // make a web look tangled. Untangle before finalising.
  reduceEdgeCrossings(nodes, edges)

  const positions = new Map()
  for (const n of nodes) {
    positions.set(n.id, { x: Math.round(n.x + offsetX), y: Math.round(n.y + offsetY), depth: 0 })
  }
  return positions
}

// ─── Edge-crossing reduction ───

/**
 * Label each node with the connected component ("tree") it belongs to.
 *
 * Used to give different trees interstellar space in the force solve: two nodes in
 * separate trees have no reason to be near each other, so they repel much harder
 * than two nodes within the same tree.
 */
function assignClusters(nodes, edges) {
  const adjacency = nodes.map(() => [])
  for (const [a, b] of edges) {
    adjacency[a].push(b)
    adjacency[b].push(a)
  }
  for (const n of nodes) n.cluster = -1

  let cluster = 0
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i].cluster !== -1) continue
    const queue = [i]
    nodes[i].cluster = cluster
    while (queue.length) {
      const at = queue.shift()
      for (const next of adjacency[at]) {
        if (nodes[next].cluster === -1) {
          nodes[next].cluster = cluster
          queue.push(next)
        }
      }
    }
    cluster++
  }
  return cluster
}

/** Centre point of a solver node (x/y are top-left). */
function nodeCentre(n) {
  return { x: n.x + n.w / 2, y: n.y + n.h / 2 }
}

/** Do segments p1→p2 and p3→p4 properly cross? */
function segmentsCross(p1, p2, p3, p4) {
  const orient = (a, b, c) => {
    const v = (b.y - a.y) * (c.x - b.x) - (b.x - a.x) * (c.y - b.y)
    return Math.abs(v) < 1e-9 ? 0 : (v > 0 ? 1 : 2)
  }
  const o1 = orient(p1, p2, p3)
  const o2 = orient(p1, p2, p4)
  const o3 = orient(p3, p4, p1)
  const o4 = orient(p3, p4, p2)
  // Strict crossing only — shared endpoints (edges meeting at a node) don't count.
  return o1 !== o2 && o3 !== o4 && o1 !== 0 && o2 !== 0 && o3 !== 0 && o4 !== 0
}

/**
 * Does node `idx` overlap any other node?
 *
 * Uses a BOX test, not the circumscribed radius: radius is hypot(w,h)/2, a corner
 * distance, so treating it as a circle demands ~400px between two 300x200 cards
 * that would sit fine side by side — which would reject nearly every untangling
 * move and make the whole pass a no-op.
 */
function nodeOverlapsAny(nodes, idx) {
  const n = nodes[idx]
  const GAP = 40
  // x/y are TOP-LEFT (seeded from card.x/card.y), so compare edges directly.
  for (let k = 0; k < nodes.length; k++) {
    if (k === idx) continue
    const o = nodes[k]
    const overlapX = n.x < o.x + o.w + GAP && n.x + n.w + GAP > o.x
    const overlapY = n.y < o.y + o.h + GAP && n.y + n.h + GAP > o.y
    if (overlapX && overlapY) return true
  }
  return false
}

/** How many edge pairs cross, ignoring pairs that share a node? */
function countCrossings(nodes, edges) {
  let count = 0
  for (let i = 0; i < edges.length; i++) {
    const [a1, b1] = edges[i]
    for (let j = i + 1; j < edges.length; j++) {
      const [a2, b2] = edges[j]
      if (a1 === a2 || a1 === b2 || b1 === a2 || b1 === b2) continue
      // Lines are drawn centre-to-centre, so test centres — node x/y are top-left.
      if (segmentsCross(nodeCentre(nodes[a1]), nodeCentre(nodes[b1]),
        nodeCentre(nodes[a2]), nodeCentre(nodes[b2]))) count++
    }
  }
  return count
}

/**
 * Untangle the web after the force solve.
 *
 * Two moves, applied greedily and only kept when they reduce the crossing count:
 *  1. SWAP a pair of nodes' positions — the classic fix for two edges that cross
 *     because their endpoints are on the wrong sides of each other.
 *  2. ROTATE a leaf around its single neighbour — lets a child "poke out further"
 *     at a different angle instead of cutting across the web.
 *
 * Deterministic (fixed candidate order, no RNG) and bounded, so it cannot spin.
 */
function reduceEdgeCrossings(nodes, edges) {
  if (nodes.length < 4 || edges.length < 2) return

  let crossings = countCrossings(nodes, edges)
  if (crossings === 0) return

  // Degree drives which nodes are leaves (rotatable) vs structural (swap only).
  const degree = new Array(nodes.length).fill(0)
  const neighbour = new Array(nodes.length).fill(-1)
  for (const [a, b] of edges) {
    degree[a]++; degree[b]++
    neighbour[a] = b; neighbour[b] = a
  }

  const MAX_ROUNDS = 12
  for (let round = 0; round < MAX_ROUNDS && crossings > 0; round++) {
    let improved = false

    // 1. Position swaps.
    for (let i = 0; i < nodes.length && crossings > 0; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j]
        const ax = a.x, ay = a.y
        a.x = b.x; a.y = b.y
        b.x = ax; b.y = ay
        // Cards differ in size, so a swap can leave one overlapping a neighbour.
        const clean = !nodeOverlapsAny(nodes, i) && !nodeOverlapsAny(nodes, j)
        const next = clean ? countCrossings(nodes, edges) : Infinity
        if (next < crossings) {
          crossings = next
          improved = true
        } else {
          // Revert.
          b.x = a.x; b.y = a.y
          a.x = ax; a.y = ay
        }
      }
    }

    // 2. Rotate leaves around their one neighbour, and allow a longer arm — a
    //    child poking further out is preferable to an edge slicing the web.
    for (let i = 0; i < nodes.length && crossings > 0; i++) {
      if (degree[i] !== 1) continue
      const anchor = nodes[neighbour[i]]
      if (!anchor) continue
      const node = nodes[i]
      const bestX = node.x, bestY = node.y
      const dx = node.x - anchor.x
      const dy = node.y - anchor.y
      const baseRadius = Math.hypot(dx, dy) || FORCE_IDEAL_LINK
      const baseAngle = Math.atan2(dy, dx)

      let placed = false
      for (const reach of [1, 1.3, 1.7]) {
        for (let step = 1; step < 12 && !placed; step++) {
          // Alternate either side of the current angle, widening as step grows.
          const offset = (Math.ceil(step / 2) * (Math.PI / 6)) * (step % 2 === 0 ? 1 : -1)
          const angle = baseAngle + offset
          node.x = anchor.x + Math.cos(angle) * baseRadius * reach
          node.y = anchor.y + Math.sin(angle) * baseRadius * reach
          // Untangling must not create an overlap — a clean web that stacks two
          // cards on top of each other is worse than one crossing line.
          if (nodeOverlapsAny(nodes, i)) continue
          const next = countCrossings(nodes, edges)
          if (next < crossings) {
            crossings = next
            improved = true
            placed = true
          }
        }
        if (placed) break
      }
      if (!placed) {
        node.x = bestX
        node.y = bestY
      }
    }

    if (!improved) break
  }
}

// True while a transient position animation is playing (Auto Arrange or a link
// snap); gates the CSS transition on card position.
const autoArranging = ref(false)

const AUTO_ARRANGE_DURATION = 650
// Parent hubs repel each other this much harder than ordinary cards, giving the
// clusters visible separation. 1 = identical to the balanced-web visualizer.
const AUTO_ARRANGE_PARENT_SPACING = 1.9
// Separate trees push apart this much harder than nodes within one tree, so each
// tree reads as its own island rather than merging into one mass.
const AUTO_ARRANGE_CLUSTER_SPACING = 2.6

// ─── Snap-to-neighbour on link ───
//
// When a node is first connected to another, pull it in close so the board stays
// compact — but never so close that cards touch. Positions are chosen by sweeping
// a ring around the anchor and taking the first candidate that clears every other
// card, preferring the direction the node is already in so it doesn't jump across
// the board.

// Gap left between card edges when snapping. Big enough that the ~34px border
// connection zones of two cards never overlap, which would make them fight for the
// hover dot.
const SNAP_GAP = 90
// Rings are tried outward from this multiple of the ideal separation.
const SNAP_RING_STEPS = [1, 1.35, 1.75, 2.3]

function cardBox(card) {
  const el = cardElements.value[card.id]
  const w = el?.offsetWidth || (card.collapsed ? 220 : (card.width || 300))
  const h = el?.offsetHeight || (card.collapsed ? 46 : 200)
  return { w, h }
}

// Would a card of size `box` at (x, y) overlap anything other than `ignoreIds`?
function positionIsClear(x, y, box, ignoreIds) {
  for (const other of cards.value) {
    if (ignoreIds.has(other.id)) continue
    const ob = cardBox(other)
    const pos = cardPositionRaw(other)
    const overlapX = x < pos.x + ob.w + SNAP_GAP && x + box.w + SNAP_GAP > pos.x
    const overlapY = y < pos.y + ob.h + SNAP_GAP && y + box.h + SNAP_GAP > pos.y
    if (overlapX && overlapY) return false
  }
  return true
}

/**
 * Move `card` next to `anchorCard`, close but clear of every other card.
 *
 * No-op outside free-web: the computed layouts own positions there, so writing
 * x/y would be overwritten on the next solve.
 */
function snapCardNearAnchor(card, anchorCard) {
  if (!card || !anchorCard || card.id === anchorCard.id) return
  if (activeVisualizer.value !== 'free-web') return

  const box = cardBox(card)
  const anchorBox = cardBox(anchorCard)
  const anchor = cardPositionRaw(anchorCard)

  const anchorCx = anchor.x + anchorBox.w / 2
  const anchorCy = anchor.y + anchorBox.h / 2

  // Start from the direction the card already lies in, so the snap reads as
  // "pulled in" rather than "teleported to the other side".
  const currentCx = (card.x ?? anchorCx) + box.w / 2
  const currentCy = (card.y ?? anchorCy) + box.h / 2
  const preferred = Math.atan2(currentCy - anchorCy, currentCx - anchorCx)

  // Base radius: enough that the two cards' edges clear SNAP_GAP even corner-on.
  const baseRadius = (Math.hypot(anchorBox.w, anchorBox.h) + Math.hypot(box.w, box.h)) / 2 + SNAP_GAP

  const ignore = new Set([card.id])
  const SWEEP = 16   // candidate angles per ring

  for (const step of SNAP_RING_STEPS) {
    const radius = baseRadius * step
    for (let i = 0; i < SWEEP; i++) {
      // Alternate either side of the preferred direction, widening as i grows.
      const offset = (Math.ceil(i / 2) * (Math.PI * 2 / SWEEP)) * (i % 2 === 0 ? 1 : -1)
      const angle = preferred + offset
      const x = Math.round(anchorCx + Math.cos(angle) * radius - box.w / 2)
      const y = Math.round(anchorCy + Math.sin(angle) * radius - box.h / 2)
      if (positionIsClear(x, y, box, ignore)) {
        card.x = x
        card.y = y
        return true
      }
    }
  }
  // Every candidate was blocked — leave the card where it is rather than
  // deliberately overlapping something.
  return false
}

// Watch for newly created links so a FIRST connection pulls the two nodes together.
// Watching the link list rather than patching each creation site catches every path
// — drag-to-connect, force-complete, drop-menu spawn, paste-to-link, reparent.
let knownLinkIds = new Set()

watch(nodeLinks, (links) => {
  const ids = new Set(links.map(l => l.id))
  const added = links.filter(l => !knownLinkIds.has(l.id))
  const isFirstRun = knownLinkIds.size === 0 && links.length > 1
  knownLinkIds = ids

  // Skip the initial board load, which "adds" every existing link at once.
  if (isFirstRun || !added.length) return
  if (activeVisualizer.value !== 'free-web') return

  for (const link of added) {
    const source = cards.value.find(c => c.id === link.sourceCardId)
    const target = cards.value.find(c => c.id === link.targetCardId)
    if (!source || !target) continue

    // Only pull in a node that has no OTHER connection yet — an already-linked
    // node is positioned relative to its existing neighbours, and yanking it
    // would disturb an arrangement the user has already made.
    const targetDegree = links.filter(
      l => l.sourceCardId === target.id || l.targetCardId === target.id
    ).length
    if (targetDegree !== 1) continue

    // Leave it alone if it is already comfortably placed.
    const box = cardBox(target)
    const anchorBox = cardBox(source)
    const sPos = cardPositionRaw(source)
    const tPos = cardPositionRaw(target)
    const gapX = Math.max(sPos.x - (tPos.x + box.w), tPos.x - (sPos.x + anchorBox.w), 0)
    const gapY = Math.max(sPos.y - (tPos.y + box.h), tPos.y - (sPos.y + anchorBox.h), 0)
    const separation = Math.hypot(gapX, gapY)
    const tooFar = separation > SNAP_GAP * 4
    const tooClose = !positionIsClear(tPos.x, tPos.y, box, new Set([target.id]))
    if (!tooFar && !tooClose) continue

    snapWithAnimation(target, source)
  }
}, { deep: true })

/**
 * A node spawned from a dropped connection lands wherever the user released, which
 * may sit on top of existing cards. Respect that choice when it is already clear —
 * only relocate when it would overlap, and then place it near its anchor.
 */
function ensureSpawnClear(card, anchorCard) {
  if (activeVisualizer.value !== 'free-web') return
  const box = cardBox(card)
  if (positionIsClear(card.x, card.y, box, new Set([card.id]))) return
  snapWithAnimation(card, anchorCard)
}

/**
 * Ctrl+Shift release: re-pack a subtree into concentric rings around its root.
 *
 * Members are ringed by their link distance from the root, so direct children sit
 * closest and deeper descendants fan out behind them — which reads as organised
 * rather than merely close. Every placement is collision-checked against cards
 * OUTSIDE the subtree as well as those already placed, so tightening can't shove
 * the cluster on top of unrelated nodes.
 */
function tightenSubtree(rootCard, memberIds) {
  if (activeVisualizer.value !== 'free-web' || !memberIds.length) return

  // Link distance from the root, so ring assignment follows the graph.
  const adjacency = new Map(cards.value.map(c => [c.id, []]))
  for (const link of nodeLinks.value) {
    if (!adjacency.has(link.sourceCardId) || !adjacency.has(link.targetCardId)) continue
    adjacency.get(link.sourceCardId).push(link.targetCardId)
    adjacency.get(link.targetCardId).push(link.sourceCardId)
  }
  const member = new Set(memberIds)
  const depth = new Map([[rootCard.id, 0]])
  const queue = [rootCard.id]
  while (queue.length) {
    const id = queue.shift()
    for (const next of adjacency.get(id) || []) {
      if (!member.has(next) || depth.has(next)) continue
      depth.set(next, depth.get(id) + 1)
      queue.push(next)
    }
  }

  const byDepth = new Map()
  for (const id of memberIds) {
    const d = depth.get(id) ?? 1
    if (!byDepth.has(d)) byDepth.set(d, [])
    byDepth.get(d).push(id)
  }

  const rootBox = cardBox(rootCard)
  const rootCx = rootCard.x + rootBox.w / 2
  const rootCy = rootCard.y + rootBox.h / 2

  // Placed cards accumulate as we go, so later rings avoid earlier ones.
  const placed = [{ x: rootCard.x, y: rootCard.y, ...rootBox }]
  const outside = cards.value.filter(c => c.id !== rootCard.id && !member.has(c.id))

  const fits = (x, y, box) => {
    for (const p of [...placed, ...outside.map(c => ({ x: c.x, y: c.y, ...cardBox(c) }))]) {
      const ox = x < p.x + p.w + SNAP_GAP && x + box.w + SNAP_GAP > p.x
      const oy = y < p.y + p.h + SNAP_GAP && y + box.h + SNAP_GAP > p.y
      if (ox && oy) return false
    }
    return true
  }

  for (const d of [...byDepth.keys()].sort((a, b) => a - b)) {
    const ids = byDepth.get(d)
    ids.forEach((id, i) => {
      const card = cards.value.find(c => c.id === id)
      if (!card) return
      const box = cardBox(card)
      // Ring radius grows with depth; spread members evenly around it.
      const baseRadius = (Math.hypot(rootBox.w, rootBox.h) + Math.hypot(box.w, box.h)) / 2 + SNAP_GAP
      const startAngle = (i / ids.length) * Math.PI * 2

      for (let expand = 0; expand < 6; expand++) {
        const radius = baseRadius * (d + expand * 0.45)
        for (let k = 0; k < 12; k++) {
          const angle = startAngle + (k / 12) * (Math.PI * 2) / Math.max(ids.length, 1)
          const x = Math.round(rootCx + Math.cos(angle) * radius - box.w / 2)
          const y = Math.round(rootCy + Math.sin(angle) * radius - box.h / 2)
          if (fits(x, y, box)) {
            card.x = x
            card.y = y
            placed.push({ x, y, ...box })
            return
          }
        }
      }
    })
  }

  nextTick(() => { collapseGeneration.value++ })
}

// Snap with the same transient glide Auto Arrange uses.
async function snapWithAnimation(card, anchorCard) {
  autoArranging.value = true
  await nextTick()
  const moved = snapCardNearAnchor(card, anchorCard)
  nextTick(() => { collapseGeneration.value++ })
  setTimeout(() => {
    autoArranging.value = false
    collapseGeneration.value++
  }, AUTO_ARRANGE_DURATION)
  return moved
}

// Auto Arrange: a ONE-SHOT tidy-up. Runs the same force solve as the balanced-web
// visualizer (with parent hubs spaced further apart), then writes the result to the
// cards' real x/y and animates them into place.
//
// Deliberately different from switching to balanced-web: this stays in free-web, so
// the positions are genuine, persisted, and the user can immediately drag anything
// again. The animation is a transient CSS transition, not a layout mode.
async function autoArrange() {
  if (!cards.value.length || autoArranging.value) return

  // Auto Arrange is a free-web action; the computed layouts own positions in the
  // other views, so switch back before writing real coordinates.
  if (activeVisualizer.value !== 'free-web') {
    activeVisualizer.value = 'free-web'
    await nextTick()
  }

  const solved = solveForceLayout(cards.value, {
    parentSpacing: AUTO_ARRANGE_PARENT_SPACING,
    clusterSpacing: AUTO_ARRANGE_CLUSTER_SPACING
  })
  if (!solved) return

  // Turn on the transition BEFORE moving, so the cards glide rather than teleport.
  autoArranging.value = true
  await nextTick()

  for (const card of cards.value) {
    const pos = solved.get(card.id)
    if (pos) {
      card.x = pos.x
      card.y = pos.y
    }
  }

  // Card positions changed, so connection geometry must be recomputed.
  nextTick(() => { collapseGeneration.value++ })

  // Drop the transition once it has played, so ordinary dragging stays instant.
  setTimeout(() => {
    autoArranging.value = false
    collapseGeneration.value++
  }, AUTO_ARRANGE_DURATION)
}

const balancedWebLayout = computed(() => {
  if (activeVisualizer.value !== 'balanced-web') return null
  // Depend on the card set and link graph, not on live positions: the simulation
  // seeds from x/y, and re-running it on every position change would fight the
  // CSS transition. balancedWebEpoch forces a deliberate re-solve.
  void balancedWebEpoch.value
  return solveForceLayout(cards.value)
})


/**
 * Derive a forest from the connection graph.
 *
 * There is no explicit parent pointer on a card — hierarchy is implied by
 * nodeLinks, with `type: 'parent'` hub cards as natural roots. Links are
 * undirected in practice, so this walks breadth-first from the roots and treats
 * the first arrival at a card as its parent. Cycles are broken by the visited
 * set; anything unreachable becomes its own root so nothing is ever hidden.
 */
const hierarchyLayout = computed(() => {
  if (activeVisualizer.value !== 'hierarchical') return null
  // Row heights come from offsetHeight, which changes when cards collapse/expand
  // AND when a zoom tier swaps the card for a different-sized element (the wide
  // summary row is far shorter than the stacked card). collapseGeneration is
  // bumped by both, so depend on it or the tree lays out against stale heights.
  void collapseGeneration.value

  const byId = new Map(cards.value.map(c => [c.id, c]))
  const adjacency = new Map(cards.value.map(c => [c.id, []]))
  for (const link of nodeLinks.value) {
    if (!adjacency.has(link.sourceCardId) || !adjacency.has(link.targetCardId)) continue
    adjacency.get(link.sourceCardId).push(link.targetCardId)
    adjacency.get(link.targetCardId).push(link.sourceCardId)
  }

  // Roots: parent-type hubs first, then any card with connections, then orphans.
  const degree = id => adjacency.get(id)?.length || 0
  const parents = cards.value.filter(c => c.type === 'parent')
  const roots = parents.length
    ? parents
    : [...cards.value].sort((a, b) => degree(b.id) - degree(a.id)).slice(0, 1)

  const visited = new Set()
  const rows = []   // flattened, in display order: {id, depth}

  function walk(id, depth, parentId = null) {
    if (visited.has(id)) return
    visited.add(id)
    rows.push({ id, depth, parentId })
    const children = (adjacency.get(id) || [])
      .filter(childId => !visited.has(childId))
      // Stable ordering so the tree doesn't reshuffle between renders.
      .sort((a, b) => {
        const ca = byId.get(a), cb = byId.get(b)
        return (ca?.y ?? 0) - (cb?.y ?? 0) || (ca?.x ?? 0) - (cb?.x ?? 0)
      })
    for (const childId of children) walk(childId, depth + 1, id)
  }

  for (const root of roots) walk(root.id, 0)
  // Anything not reachable from a root still needs a home.
  for (const card of cards.value) if (!visited.has(card.id)) walk(card.id, 0)

  // Assign positions top-to-bottom, indenting by depth. The gap is fixed canvas
  // geometry — the zoom scales it together with the rows.
  const rowGap = HIER_ROW_GAP

  const positions = new Map()
  let cursorY = HIER_ORIGIN.y
  for (const row of rows) {
    const card = byId.get(row.id)
    const el = cardElements.value[row.id]
    // Collapsed cards render as ~46px rows in this view, not the 52px pill.
    const height = el?.offsetHeight || (card?.collapsed ? 46 : 200)
    positions.set(row.id, {
      x: HIER_ORIGIN.x + row.depth * HIER_INDENT,
      y: cursorY,
      depth: row.depth,
      parentId: row.parentId,
      height
    })
    cursorY += height + rowGap
  }
  return positions
})

/**
 * Where a card renders. In the computed layouts this overrides the stored
 * position WITHOUT mutating card.x/card.y — the free-web arrangement must
 * survive a trip through another visualizer (saveBoard persists card.x/card.y
 * directly). Node positions are synced from this resolver (see the flow-sync
 * section at the bottom of the file).
 */
function cardPositionRaw(card) {
  const layout = hierarchyLayout.value || balancedWebLayout.value || waterfallLayout.value
  if (layout) {
    const pos = layout.get(card.id)
    if (pos) return pos
  }
  return { x: card.x, y: card.y, depth: 0 }
}

/**
 * Edge geometry for the custom edge template.
 *
 * Straight centre-to-centre in the web views — the nodes are painted over the
 * line, so it reads as joining node to node. In the hierarchical tree, links are
 * drawn as ELBOWS — out of the parent's left rail, down, then across into the
 * child's left edge — so connections read as a tree instead of a web of
 * diagonals. Endpoint dots sit where the line crosses each node's perimeter
 * (or the centre, for parent hubs — hub-and-spoke anchoring).
 */
function edgeGeometry({ sourceNode, targetNode }) {
  if (!sourceNode || !targetNode) return null

  const sRect = {
    x: sourceNode.position.x,
    y: sourceNode.position.y,
    w: sourceNode.dimensions?.width || 300,
    h: sourceNode.dimensions?.height || 200
  }
  const tRect = {
    x: targetNode.position.x,
    y: targetNode.position.y,
    w: targetNode.dimensions?.width || 300,
    h: targetNode.dimensions?.height || 200
  }

  const sCenter = { x: sRect.x + sRect.w / 2, y: sRect.y + sRect.h / 2 }
  const tCenter = { x: tRect.x + tRect.w / 2, y: tRect.y + tRect.h / 2 }

  const sourceCard = sourceNode.data?.card
  const targetCard = targetNode.data?.card

  // Endpoint handle positions: card centres for parent hubs, otherwise where the
  // centre-to-centre line crosses each card's perimeter.
  let x1, y1, x2, y2
  const srcIsParent = sourceCard?.type === 'parent'
  const tgtIsParent = targetCard?.type === 'parent'
  if (srcIsParent) {
    x1 = sCenter.x; y1 = sCenter.y
  } else {
    const bp = borderIntersection(sRect, tCenter)
    x1 = bp.x; y1 = bp.y
  }
  if (tgtIsParent) {
    x2 = tCenter.x; y2 = tCenter.y
  } else {
    const bp = borderIntersection(tRect, sCenter)
    x2 = bp.x; y2 = bp.y
  }

  // Midpoint of the VISIBLE span (between the two handles), so the label and
  // delete affordance sit on the exposed part of the line, not under a card.
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2

  const straight = `M ${sCenter.x} ${sCenter.y} L ${tCenter.x} ${tCenter.y}`

  if (activeVisualizer.value !== 'hierarchical') {
    return { path: straight, x1, y1, x2, y2, mx, my, srcIsParent, tgtIsParent }
  }

  const layout = hierarchyLayout.value
  const sPos = layout?.get(sourceCard?.id)
  const tPos = layout?.get(targetCard?.id)
  if (!sPos || !tPos) return { path: straight, x1, y1, x2, y2, mx, my, srcIsParent, tgtIsParent }

  // Orient parent → child by tree depth, since links themselves are undirected.
  const [parentPos, parentRect, childPos, childRect] = sPos.depth <= tPos.depth
    ? [sPos, sRect, tPos, tRect]
    : [tPos, tRect, sPos, sRect]

  // Rail drops from under the parent, offset in from its left edge.
  const railX = parentPos.x + 24
  const parentBottom = parentPos.y + parentRect.h
  const childMidY = childPos.y + Math.min(40, childRect.h / 2)
  const childLeft = childPos.x

  let path
  if (childLeft + childRect.w < railX) {
    // A child to the LEFT of its parent can't use the rail without doubling
    // back, so route it round the near edge instead.
    const childRight = childLeft + childRect.w
    path = `M ${railX} ${parentBottom} L ${railX} ${childMidY} L ${childRight} ${childMidY}`
  } else {
    // Rounded corner where the rail turns into the child, so the tree reads
    // softly.
    const radius = Math.min(12, Math.max(0, (childLeft - railX) / 2), Math.max(0, (childMidY - parentBottom) / 2))
    if (radius < 2) {
      path = `M ${railX} ${parentBottom} L ${railX} ${childMidY} L ${childLeft} ${childMidY}`
    } else {
      path = [
        `M ${railX} ${parentBottom}`,
        `L ${railX} ${childMidY - radius}`,
        `Q ${railX} ${childMidY} ${railX + radius} ${childMidY}`,
        `L ${childLeft} ${childMidY}`
      ].join(' ')
    }
  }

  // Elbow endpoints: the dots sit at the rail mouth and the child's edge.
  return {
    path,
    x1: railX,
    y1: parentBottom,
    x2: childLeft + childRect.w < railX ? childLeft + childRect.w : childLeft,
    y2: childMidY,
    mx: railX,
    my: (parentBottom + childMidY) / 2,
    srcIsParent: false,
    tgtIsParent: false
  }
}


// ─── Image metadata display ───

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return null
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Compact one-liner shown under an image: "WEBP · 876×493 · 311 KB · nytimes.com"
function imageMetaLine(card) {
  const m = card.mediaMetadata || {}
  const parts = []
  if (m.format) parts.push(m.format)
  if (m.width && m.height) parts.push(`${m.width}×${m.height}`)
  const size = formatBytes(m.file_size)
  if (size) parts.push(size)
  if (m.source_site) parts.push(m.source_site)
  else if (card.url) {
    try { parts.push(new URL(card.url).hostname.replace(/^www\./, '')) } catch { /* not a URL */ }
  }
  return parts.join(' · ')
}

// Camera line, present only for images that actually carry EXIF.
function imageExifLine(card) {
  const e = card.mediaMetadata?.exif
  if (!e) return null
  const body = [
    [e.camera_make, e.camera_model].filter(Boolean).join(' '),
    e.lens,
    e.focal_length,
    e.aperture,
    e.shutter,
    e.iso ? `ISO ${e.iso}` : null
  ].filter(Boolean)
  return body.length ? body.join(' · ') : null
}

function imageTakenAt(card) {
  const raw = card.mediaMetadata?.exif?.taken_at
  if (!raw) return null
  // EXIF format is "YYYY:MM:DD HH:MM:SS"
  const m = raw.match(/^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2})/)
  if (!m) return raw
  const [, y, mo, d, h, mi] = m
  return `${y}-${mo}-${d} ${h}:${mi}`
}

function socialPlatformChip(platform) {
  const platforms = {
    'x': { icon: 'mdi-twitter', label: 'X', color: 'primary' },
    'twitter': { icon: 'mdi-twitter', label: 'Twitter', color: 'primary' },
    'tiktok': { icon: 'mdi-music-note-eighth', label: 'TikTok', color: 'pink' },
    'youtube': { icon: 'mdi-youtube', label: 'YouTube', color: 'red' },
    'instagram': { icon: 'mdi-instagram', label: 'Instagram', color: 'purple' },
    'rumble': { icon: 'mdi-video', label: 'Rumble', color: 'green' },
    'soundcloud': { icon: 'mdi-soundcloud', label: 'SoundCloud', color: 'orange' }
  }
  return platforms[platform] || { icon: 'mdi-web', label: platform || 'Social', color: 'grey' }
}

// Detect social media URLs that should trigger analyze + download
function isSocialMediaUrl(url) {
  return /^https?:\/\/(www\.)?(twitter\.com|x\.com|tiktok\.com|vm\.tiktok\.com|youtube\.com|youtu\.be|instagram\.com|rumble\.com|soundcloud\.com)\//i.test(url)
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
        newCard._urlChangeTimeout = setTimeout(async () => {
          // For social media URLs, trigger analyze + download flow
          if (isSocialMediaUrl(newCard.url) && !newCard._analyzedUrl) {
            newCard._analyzedUrl = newCard.url
            try {
              const analysis = await fetchJson(`/api/whiteboard/analyze-url?url=${encodeURIComponent(newCard.url)}`)
              if (analysis.spawn_children && analysis.has_media) {
                const downloadResult = await fetchJson(`/api/whiteboard/${identifier.value}/download-social-media?url=${encodeURIComponent(newCard.url)}`, {
                  method: 'POST'
                })
                // Check for API error - spawn warning card
                if (downloadResult.error) {
                  const err = downloadResult.error
                  const warningCard = {
                    id: nextId++,
                    type: 'text',
                    title: `API Error: ${err.service || analysis.service}`,
                    content: `**${err.message || 'Unknown error'}**\n\nStatus: ${err.status_code || 'N/A'}\nEndpoint: \`${err.endpoint || 'N/A'}\`\nFallback used: ${err.fallback_used ? 'Yes' : 'No'}${err.detail ? '\n\nDetail: ' + err.detail.substring(0, 200) : ''}`,
                    notes: '',
                    x: newCard.x + 550,
                    y: newCard.y,
                    width: 400,
                    collapsed: false,
                    parentId: newCard.id,
                    isWarning: true,
                    cardStyle: { backgroundColor: '#2d1010', borderColor: '#ff4444', borderWidth: '2px' }
                  }
                  cards.value.push(warningCard)
                  notifyUserStandard(`${err.service || analysis.service} API error: ${err.message}`, NOTIFICATION_COLORS.error)
                }

                if (downloadResult.assets && downloadResult.assets.length > 0) {
                  downloadResult.assets.forEach((asset, idx) => {
                    let childCard
                    if (asset.media_category === 'video') {
                      childCard = {
                        id: nextId++,
                        type: 'video',
                        videoUrl: asset.file_url,
                        assetId: asset.asset_id,
                        title: asset.source_context?.title || 'Video',
                        notes: '',
                        x: newCard.x + 550 + (idx * 20),
                        y: newCard.y + (idx * 20),
                        width: 640,
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
                        x: newCard.x + 550 + (idx * 20),
                        y: newCard.y + (idx * 20),
                        width: 600,
                        collapsed: false,
                        parentId: newCard.id
                      }
                    }
                    if (childCard) {
                      cards.value.push(childCard)
                    }
                  })
                  notifyUserStandard(`Downloaded ${downloadResult.assets.length} media file(s) from ${downloadResult.service || analysis.service}`, NOTIFICATION_COLORS.success)
                }

                // Populate socialMetadata from Twitter API data + local URLs
                if (downloadResult.tweet_data) {
                  const td = downloadResult.tweet_data
                  newCard.socialMetadata = {
                    ...td,
                    media_urls: downloadResult.local_media_urls || td.media_urls || [],
                    author_avatar: downloadResult.local_avatar_url || td.author_avatar,
                    _locally_cached: true,
                    _cached_at: new Date().toISOString()
                  }
                  newCard.previewTitle = td.author_name ? `${td.author_name} (@${td.author_handle})` : null
                  newCard.previewDescription = td.tweet_text || null
                  newCard.previewDomain = 'x.com'
                  newCard.previewFavicon = 'https://abs.twimg.com/favicons/twitter.3.ico'
                  return // Skip fetchLinkPreview
                }

                // Populate socialMetadata from yt-dlp content_data (TikTok, YouTube, etc.)
                if (downloadResult.content_data) {
                  const cd = downloadResult.content_data
                  newCard.socialMetadata = {
                    ...cd,
                    media_urls: downloadResult.local_media_urls || [],
                    thumbnail_url: downloadResult.local_thumbnail_url || cd.thumbnail_url,
                    _locally_cached: true,
                    _cached_at: new Date().toISOString()
                  }
                  newCard.previewTitle = cd.author_name || cd.title || null
                  newCard.previewDescription = cd.post_text || cd.title || null
                  newCard.previewDomain = cd.platform || analysis.service
                  return // Skip fetchLinkPreview
                }
              }
            } catch (error) {
              console.error('Error analyzing social media URL:', error)
            }
          }
          fetchLinkPreview(newCard)
        }, 1000)
      }
    }
  })
}, { deep: true })

// ─── Flow sync: cards/links (source of truth) → Vue Flow nodes/edges ───
//
// The cards array and the link store remain the single source of truth (loaded
// from and saved to the API exactly as before). Vue Flow's node/edge state is a
// projection of them: rebuilt when the card set or view changes, position-patched
// when a layout re-solves or free-web coordinates are written.

// Dragging is meaningful in free-web (moves persist) and hierarchical (vertical
// reorder). The other layouts own their positions outright.
const nodesDraggable = computed(() =>
  activeVisualizer.value === 'free-web' || activeVisualizer.value === 'hierarchical'
)

function minimapNodeColor(node) {
  return nodeType(node.data?.card)?.color || '#90a4ae'
}

function buildNode(card) {
  const pos = cardPosition(card)
  const node = {
    id: String(card.id),
    type: 'card',
    position: { x: pos.x, y: pos.y },
    data: { card }
  }
  if (activeVisualizer.value === 'hierarchical') {
    // Tree rows drag vertically only — X is owned by the depth indent.
    node.extent = [[pos.x, -1e9], [pos.x, 1e9]]
  }
  return node
}

// Full rebuild when the card SET changes (add/remove/reload) or the view
// switches. Cheap at whiteboard scale, and keeps node state trivially correct.
const cardIdsSignature = computed(
  () => activeVisualizer.value + '|' + cards.value.map(c => c.id).join(',')
)

watch(cardIdsSignature, () => {
  setNodes(cards.value.map(buildNode))
}, { immediate: true })

// Position patching: whenever the resolved positions change (a layout re-solve,
// autoArrange/snap/tighten writing card.x/y, a load-time separation pass), move
// the existing nodes to match. The node being actively dragged is skipped — Vue
// Flow owns it for the duration of the gesture.
const resolvedPositions = computed(() => {
  void collapseGeneration.value
  return cards.value.map(c => {
    const p = cardPosition(c)
    return `${c.id}:${Math.round(p.x)}:${Math.round(p.y)}`
  }).join('|')
})

watch(resolvedPositions, () => {
  for (const card of cards.value) {
    if (dragCard.value && dragCard.value.id === card.id) continue
    const node = findNode(String(card.id))
    if (!node) continue
    const pos = cardPosition(card)
    if (node.position.x !== pos.x || node.position.y !== pos.y) {
      node.position = { x: pos.x, y: pos.y }
    }
    if (activeVisualizer.value === 'hierarchical') {
      node.extent = [[pos.x, -1e9], [pos.x, 1e9]]
    }
  }
})

// ─── Auto Condense ───
//
// Toggle in the top-right chip row. When ON and the view is below the compact
// tier (the zoomed-out levels), RENDERED positions contract uniformly toward
// the board centre by the largest factor that keeps every pair of cards from
// touching — white space shrinks, the arrangement's shape is preserved, and
// nothing overlaps. Strictly view-only: stored card.x/card.y are untouched
// (free-web drags write back through the inverse transform), so zooming back
// in shows the true layout. Skipped in the hierarchical tree, which is
// already a compact column.
const autoCondense = ref(localStorage.getItem('wb-auto-condense') === '1')
watch(autoCondense, v => localStorage.setItem('wb-auto-condense', v ? '1' : '0'))

const CONDENSE_GAP = 36     // canvas px kept between card boxes
const CONDENSE_FLOOR = 0.2  // never contract below 20%

const condenseActive = computed(() =>
  autoCondense.value && !showCompact.value && activeVisualizer.value !== 'hierarchical'
)

// { cx, cy, k } — contraction centre and factor, or null when inactive/no-op.
const condenseTransform = computed(() => {
  if (!condenseActive.value) return null
  void collapseGeneration.value
  const list = cards.value
  if (list.length < 2) return null

  // Card centres and boxes in RAW coordinate space.
  const items = list.map(c => {
    const pos = cardPositionRaw(c)
    const box = cardBox(c)
    return { x: pos.x + box.w / 2, y: pos.y + box.h / 2, w: box.w, h: box.h }
  }).filter(i => Number.isFinite(i.x) && Number.isFinite(i.y))
  if (items.length < 2) return null

  let cx = 0, cy = 0
  for (const i of items) { cx += i.x; cy += i.y }
  cx /= items.length
  cy /= items.length

  // Largest safe contraction: for each pair, staying clear on EITHER axis is
  // enough, so the pair's minimum k is the cheaper of the two axis demands.
  let k = CONDENSE_FLOOR
  for (let a = 0; a < items.length; a++) {
    for (let b = a + 1; b < items.length; b++) {
      const A = items[a], B = items[b]
      const dx = Math.abs(B.x - A.x)
      const dy = Math.abs(B.y - A.y)
      const needX = (A.w + B.w) / 2 + CONDENSE_GAP
      const needY = (A.h + B.h) / 2 + CONDENSE_GAP
      const kx = dx > 0 ? needX / dx : Infinity
      const ky = dy > 0 ? needY / dy : Infinity
      const pairK = Math.min(kx, ky)
      if (Number.isFinite(pairK)) k = Math.max(k, pairK)
    }
  }
  k = Math.min(1, Math.max(CONDENSE_FLOOR, k))
  if (k >= 0.98) return null
  return { cx, cy, k }
})

// Glide the contraction/expansion when the condensed state flips.
watch(condenseActive, () => { glideLayout() })

/**
 * Where a card RENDERS: the raw resolved position (stored coords or computed
 * layout), contracted toward the board centre when Auto Condense is engaged.
 * Function declaration on purpose — hoisted, so every earlier caller sees it.
 */
function cardPosition(card) {
  const pos = cardPositionRaw(card)
  const t = condenseTransform.value
  if (!t) return pos
  const box = cardBox(card)
  const ccx = t.cx + ((pos.x + box.w / 2) - t.cx) * t.k
  const ccy = t.cy + ((pos.y + box.h / 2) - t.cy) * t.k
  return { ...pos, x: Math.round(ccx - box.w / 2), y: Math.round(ccy - box.h / 2) }
}

// Edges mirror the link store 1:1.
watch([nodeLinks, cardIdsSignature], () => {
  const ids = new Set(cards.value.map(c => c.id))
  setEdges(nodeLinks.value
    .filter(l => ids.has(l.sourceCardId) && ids.has(l.targetCardId))
    .map(l => ({
      id: String(l.id),
      source: String(l.sourceCardId),
      target: String(l.targetCardId),
      type: 'link',
      data: { link: l }
    })))
}, { deep: true, immediate: true })
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
  overflow: hidden;
  outline: none;
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
  position: relative;
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
/* Images are natively draggable in browsers. On the whiteboard that hijacks a
   card drag: the native drag suppresses mousemove (so the card never follows the
   cursor), then the release fires the canvas @drop handler, which spawns a
   duplicate card — and the drag ghost keeps trailing the mouse afterwards.
   Suppress native dragging for every image on the canvas so mousedown-based card
   dragging always wins. */
.whiteboard-canvas img {
  -webkit-user-drag: none;
  user-drag: none;
}

/* ─── Node type identity ─── */

/* Colored bar along the card's top edge, in the node type's color. */
.type-accent {
  height: 3px;
  width: 100%;
  flex: 0 0 auto;
}

/* Uppercase type label next to the icon in every card header. */
.type-chip {
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  line-height: 1;
  padding: 2px 5px;
  margin-right: 6px;
  border: 1px solid currentColor;
  border-radius: 3px;
  white-space: nowrap;
  opacity: 0.95;
}

.node-header {
  background: #fafafa;
  /* The header is drag-to-move chrome (double-click still collapses). Inline
     `cursor: pointer` on the element is overridden here so the affordance
     matches the behaviour. */
  cursor: move !important;
}

/* …except the title text itself, which is a text-entry target. */
.editable-title :deep(input) {
  cursor: text !important;
}

/* Compact metadata under an image: format · dimensions · size · source */
.image-meta-line {
  font-size: 10px;
  line-height: 1.5;
  color: #78909c;
  padding: 3px 12px 0;
  font-variant-numeric: tabular-nums;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-meta-exif {
  color: #8d6e63;
}

.image-meta-source {
  font-size: 11px;
  line-height: 1.35;
  color: #455a64;
  padding: 2px 12px 0;
  font-style: italic;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.image-source-row {
  display: flex;
  align-items: center;
  min-width: 0;
}

.image-source-link {
  font-size: 11px;
  color: #1976D2;
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-source-link:hover {
  text-decoration: underline;
}

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
/* The tweet renders as a clean white X-style bubble: black-on-white text,
   rounded (needs !important — vuetify-fixes.css flattens all radii globally),
   inset from the card edges so the card background frames it. */
.twitter-preview-box {
  border: 1px solid #cfd9de;
  border-radius: 16px !important;
  overflow: hidden;
  background: #fff;
  margin: 6px 4px 10px;
  transition: box-shadow 0.2s;
}

.tweet-author {
  font-size: 1.02rem;
  font-weight: 700;
  color: #0f1419;
  line-height: 1.25;
}

.tweet-handle {
  font-size: 0.88rem;
  color: #536471;
  line-height: 1.25;
}

.tweet-text {
  font-size: 1.05rem;
  line-height: 1.45;
  color: #0f1419;
  white-space: pre-wrap;
  word-break: break-word;
}

.x-logo {
  color: #0f1419;
  flex: 0 0 auto;
  margin-top: 2px;
}

.tweet-media-chip {
  color: #0f1419 !important;
  border-color: #cfd9de !important;
}

.tweet-avatar {
  border-radius: 50% !important;
}

.twitter-preview-box:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.twitter-header {
  background: #fff;
}

/* Media sits INSIDE the bubble as its own rounded, bordered block — like a
   real embedded post — instead of a full-bleed dark slab. */
.twitter-media {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  background: #fff;
  margin: 2px 16px 14px;
  border: 1px solid #cfd9de;
  border-radius: 16px !important;
  overflow: hidden;
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

/* Single image/thumbnail: natural aspect, capped height */
.twitter-media-single .twitter-media-image {
  max-height: 360px;
  object-fit: cover;
}

/* Editable title styling */
/* The title field must occupy only the text itself, not a full-width box.
   A stretched input swallows presses across the whole header, and startDrag()
   bails on INPUT/TEXTAREA targets — which is what made headers undraggable.
   Sizing to content leaves the rest of the header as bare, draggable chrome. */
.editable-title {
  flex: 0 0 auto !important;
  min-width: 2ch;
  max-width: 100%;
  transition: width 0.15s ease;
}

/* Once focused the field is unambiguously in edit mode, so it expands to give
   room for the full title. Collapsed again on blur to keep the drag area large. */
.editable-title:focus-within {
  width: 26ch !important;
  max-width: 60%;
}

.editable-title :deep(.v-field) {
  padding: 0 !important;
  min-height: unset !important;
}

.editable-title :deep(.v-field__input) {
  padding: 0 !important;
  min-height: unset !important;
  /* Header titles read as the card's name, so they carry real weight rather
     than inheriting the small caption styling. Font size INHERITS so the
     counter-scaled value from titleFieldStyle() applies at low zoom. */
  font-size: inherit !important;
  font-weight: 700 !important;
  letter-spacing: 0.01em;
  color: #212121 !important;
}

.editable-title :deep(input::placeholder) {
  font-weight: 600;
  color: #90a4ae !important;
  opacity: 1;
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
  /* Inputs carry a default `size` (~20 chars) that keeps them wide regardless of
     content. `field-sizing: content` shrinks to the text where supported; the
     ch-based width from titleFieldStyle() is the cross-browser fallback, applied
     here so it is measured in the input's own (larger, bold) font. */
  field-sizing: content;
  width: 100%;
  min-width: 3ch;
  max-width: 100%;
  font-size: inherit !important;
  font-weight: 700 !important;
  color: #212121 !important;
}

/* ─── Current view indicator (top-right) ─── */

.view-indicator {
  position: absolute;
  top: 16px;
  right: 20px;
  z-index: 2050;
  user-select: none;
  /* Collapse-all sits to the LEFT of the view selector, same chip styling. */
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.collapse-all-chip {
  flex: 0 0 auto;
}

.view-chip-disabled {
  opacity: 0.45;
  cursor: default;
  pointer-events: none;
}

/* The dropdown positions against this, not the whole row. */
.view-selector-anchor {
  position: relative;
  flex: 0 0 auto;
}

.view-indicator-chip {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #cfd8dc;
  border-radius: 20px;
  padding: 7px 14px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.view-indicator-chip:hover {
  border-color: #1976d2;
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.25);
}

/* ─── Hub labels: constant-size landmark badges for parent nodes ─── */
.hub-label-layer {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 45;
}

.hub-label {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 18px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.75);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
  color: #fff;
  text-align: center;
  line-height: 1.15;
  white-space: nowrap;
}

.hub-label-type {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  opacity: 0.9;
}

.hub-label-title {
  font-size: 16px;
  font-weight: 700;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Engaged toggle state (Auto Center) — filled so on/off reads at a glance */
.view-chip-active {
  background: #1976d2;
  border-color: #1976d2;
}

.view-chip-active:hover {
  border-color: #1565c0;
}

.view-chip-active .view-indicator-label {
  color: #fff;
}

.view-indicator-open {
  border-color: #1976d2;
}

.view-indicator-label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #263238;
  white-space: nowrap;
}

.view-indicator-caret {
  transition: transform 0.2s ease;
  color: #78909c;
}

.view-indicator-open .view-indicator-caret {
  transform: rotate(180deg);
}

.view-indicator-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.22);
  padding: 6px;
  min-width: 260px;
}

.view-drop-enter-active,
.view-drop-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.view-drop-enter-from,
.view-drop-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.97);
}

/* ─── Zoom readout (bottom-right of the canvas) ─── */

.zoom-readout {
  position: absolute;
  bottom: 16px;
  right: 20px;
  z-index: 2050;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #cfd8dc;
  border-radius: 20px;
  padding: 6px 14px;
  cursor: pointer;
  user-select: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
  color: #546e7a;
}

.zoom-readout:hover {
  border-color: #1976d2;
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.25);
}

/* Highlighted whenever zoom is off 100%, so it reads as actionable. */
.zoom-readout-active {
  border-color: #1976d2;
  color: #1976d2;
}

.zoom-readout-value {
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
  min-width: 4ch;
  text-align: right;
}

/* Names the active detail tier — detail / compact / summary / marker. */
.zoom-readout-tier {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #90a4ae;
  border-left: 1px solid #cfd8dc;
  padding-left: 6px;
}

/* ─── Wide tree rows: lay card bodies out horizontally ─── */
/*
 * In the hierarchical tree a row spans the viewport, so a vertically-stacked body
 * leaves most of that width empty and makes the row needlessly tall. Flow the
 * body's direct children into columns instead: the row gets shorter, and the
 * horizontal space is actually used.
 */
.tree-wide-body {
  display: flex !important;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 16px;
}

/* Each block takes a share of the row rather than the full width. */
.tree-wide-body > * {
  flex: 1 1 320px;
  min-width: 0;
  margin-bottom: 0 !important;
}

/* Text areas stay readable but don't hog the row. */
.tree-wide-body :deep(.v-textarea) {
  flex: 2 1 420px;
}

/* The social/preview box carries the most content, so give it the largest share. */
.tree-wide-body .twitter-preview-box,
.tree-wide-body .link-preview-box {
  flex: 3 1 480px;
}

/* Inside the social box, put the author block and the post body side by side. */
.tree-wide-body .twitter-preview-box {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 12px;
}

.tree-wide-body .twitter-preview-box > * {
  flex: 1 1 260px;
  min-width: 0;
}

/* Comments are a conversation log — they read as a full-width strip under the
   content, not as another column competing with it. */
.tree-wide-body ~ .node-comments,
.zoom-summary-wide .node-comments {
  width: 100%;
}

/* ─── Node comments ─── */

.node-comments {
  border-top: 1px solid #eceff1;
  padding: 6px 10px 2px;
  background: #fafbfc;
}

.node-comment-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 5px;
  max-height: 160px;
  overflow-y: auto;
}

.node-comment {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 0.72rem;
  line-height: 1.45;
}

/* Username chip preceding each comment. */
.comment-chip {
  flex: 0 0 auto;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #fff;
  background: #546e7a;
  border-radius: 3px;
  padding: 1px 6px;
  white-space: nowrap;
}

.comment-chip-me {
  background: #1976d2;
}

.comment-text {
  flex: 1 1 auto;
  min-width: 0;
  color: #37474f;
  word-break: break-word;
}

.comment-ts {
  flex: 0 0 auto;
  font-size: 0.62rem;
  color: #b0bec5;
  white-space: nowrap;
}

.comment-delete {
  flex: 0 0 auto;
  cursor: pointer;
  color: #cfd8dc;
}

.comment-delete:hover {
  color: #e53935;
}

.node-comment-entry {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 4px;
}

.comment-input {
  flex: 1 1 auto;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.75rem;
  color: #263238;
  padding: 3px 0;
}

.comment-input::placeholder {
  color: #b0bec5;
}

.comment-send {
  cursor: pointer;
}

/* An answered question recedes — it's resolved, not outstanding. */
.question-answered {
  opacity: 0.72;
}

.question-answered :deep(.node-header) {
  background: #f1f8e9;
}

/* Ctrl-drag: mark the followers so it's obvious what's coming along. */
.subtree-member :deep(.v-card),
.subtree-member :deep(.parent-node-circle) {
  outline: 2px dashed #1976d2;
  outline-offset: 2px;
}

/* Reparent drag feedback in the hierarchical view. */
.reparent-target :deep(.v-card) {
  outline: 3px solid #FFC107;
  outline-offset: 2px;
}

.reparent-source {
  opacity: 0.55;
}

/* ─── Collapsed row (hierarchical view) ─── */

.collapsed-row {
  border-left: 5px solid;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}

.collapsed-row-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  min-height: 46px;
}

.collapsed-row-icon {
  flex: 0 0 auto;
}

.collapsed-row-chip {
  flex: 0 0 auto;
  margin-right: 2px;
}

.collapsed-row-thumb {
  flex: 0 0 auto;
  width: 52px;
  height: 32px;
  object-fit: cover;
  border-radius: 3px;
  background: #eceff1;
}

.collapsed-row-title :deep(input) {
  font-size: 0.9rem !important;
  font-weight: 700 !important;
}

/* Anything past the title is context, not a control — it must never eat a drag. */
.collapsed-row-summary {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 0.75rem;
  color: #78909c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
}

/* Tree scaffolding for the hierarchical view — sits below everything. */
/* ─── Visualizer menu ─── */

.visualizer-wrapper {
  position: relative;
}

/* Pop-DOWN list of layout modes, revealed on hover. */
.visualizer-menu {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 6px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.22);
  padding: 6px;
  min-width: 260px;
  z-index: 2100;
}

/* Keeps the hover intent alive across the gap between button and menu. */
.visualizer-menu::before {
  content: '';
  position: absolute;
  top: -8px;
  left: 0;
  right: 0;
  height: 8px;
}

.visualizer-option {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s ease;
}

.visualizer-option:hover {
  background: #f0f4f8;
}

.visualizer-option-active {
  background: #e3f2fd;
}

.visualizer-option-body {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 0;
}

.visualizer-option-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: #212121;
  line-height: 1.2;
}

.visualizer-option-desc {
  font-size: 0.68rem;
  color: #78909c;
  line-height: 1.3;
}

.visualizer-drop-enter-active,
.visualizer-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.visualizer-drop-enter-from,
.visualizer-drop-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-6px);
}

/* === Connection feedback === */

/* Yellow glow on the card under the pointer while a connection is in flight —
   dropping there will connect to it. */
.canvas-dragging-connection .card-node:hover .v-card,
.canvas-dragging-connection .card-node:hover .zoom-marker {
  outline: 9px solid rgba(255, 193, 7, 0.6);
  outline-offset: 2px;
  border-radius: 6px;
}

.canvas-dragging-connection .card-node:hover .parent-node-circle {
  box-shadow: 0 0 24px 10px rgba(255, 193, 7, 0.5) !important;
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

/* Drop-into-empty-space spawn menu — screen-space overlay, constant size,
   anchored to a canvas point via dropMenuStyle (left/top/transform inline). */
.drop-spawn-menu {
  position: absolute;
  z-index: 1100;
}

/* Node right-click menu — same overlay treatment as the spawn menu. */
.node-context-menu {
  position: absolute;
  z-index: 1100;
}

/* Headline inside the delete confirmation */
.delete-warning-headline {
  color: #c62828;
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: 0.01em;
}

.drop-menu-card {
  border: 2px solid #1976d2 !important;
  border-radius: 12px !important;
  overflow: hidden;
}

.endpoint-popup {
  position: absolute;
  /* left/top/transform set inline (endpointPopupStyle) — screen-space anchor. */
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
  cursor: grab;
  box-shadow: 0 4px 16px rgba(21, 101, 192, 0.4);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
  text-align: center;
  padding: 16px;
  user-select: none;
  position: relative;
}

/* Inner dotted ring marking the drag/link boundary */
.parent-node-circle::before {
  content: '';
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  border: 2px dashed rgba(255, 255, 255, 0.35);
  pointer-events: none;
  transition: border-color 0.2s ease;
}

.parent-node-circle:hover::before {
  border-color: rgba(255, 255, 255, 0.55);
}

.parent-node-circle:hover {
  box-shadow: 0 6px 24px rgba(21, 101, 192, 0.55);
  transform: scale(1.02);
}

.parent-node-type {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.2;
}

.parent-node-slug {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  max-width: 88%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 4px;
}

.parent-node-input {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 8px;
  color: white;
  font-size: 1.9rem;
  font-weight: 800;
  text-align: center;
  padding: 6px 12px;
  width: 86%;
  margin-top: 6px;
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
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: #263238;
  font-size: 0.95rem;
  text-align: left;
  padding: 6px 10px;
  width: 74%;
  margin-top: 8px;
  outline: none;
  resize: none;
  line-height: 1.35;
}

.parent-node-desc::placeholder {
  color: rgba(21, 101, 192, 0.4);
}

.parent-node-desc:focus {
  border-color: #1565C0;
  background: white;
}

.parent-node-delete {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #fff;
  background: #d32f2f;
  border-radius: 4px;
  padding: 3px 12px;
  cursor: pointer;
  margin-top: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.parent-node-delete:hover {
  background: #b71c1c;
  color: #fff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.45);
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
/* Delete is a destructive action — filled red with white text so it reads as a
   real button, not incidental grey text. */
.delete-text-btn {
  font-size: 0.75rem !important;
  font-weight: 800;
  letter-spacing: 0.09em;
  background-color: #d32f2f !important;
  color: #fff !important;
  text-transform: uppercase !important;
  min-width: unset !important;
  height: 26px !important;
  padding: 0 16px !important;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(211, 47, 47, 0.4);
  transition: background-color 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
}

.delete-text-btn:hover {
  background-color: #b71c1c !important;
  color: #fff !important;
  box-shadow: 0 3px 10px rgba(211, 47, 47, 0.55);
}

.delete-text-btn:active {
  transform: translateY(1px);
}
</style>
<style>
/* ═══ Vue Flow canvas (unscoped: targets library internals) ═══
   All selectors are prefixed with .whiteboard-flow / .whiteboard-canvas so
   nothing leaks outside this view. */

.whiteboard-flow {
  width: 100%;
  height: 100%;
  background: #fafafa;
}

/* Nodes are transparent wrappers — the card content inside styles itself. */
.whiteboard-flow .vue-flow__node-card {
  border: none;
  background: transparent;
  padding: 0;
  cursor: move;
}

.whiteboard-flow .card-node {
  position: relative;
}

/* Card content always wins hit-tests over connect-bands — its own AND any
   overlapping neighbour's. Bands are only reachable over true empty space. */
.whiteboard-flow .card-node .card-item,
.whiteboard-flow .card-node .zoom-marker,
.whiteboard-flow .card-node .parent-node-circle {
  position: relative;
  z-index: 1;
}

/* Nodes marked for deletion while the confirmation dialog is open: dimmed,
   desaturated, and pulsing a slow red ring — the blast radius is visible
   before the user commits to an un-undoable delete. */
.whiteboard-flow .vue-flow__node .card-node.doomed-node {
  filter: grayscale(0.85) brightness(0.85);
  opacity: 0.65;
  animation: doomed-pulse 1.8s ease-in-out infinite;
  border-radius: 10px;
}

@keyframes doomed-pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(198, 40, 40, 0.25); }
  50% { box-shadow: 0 0 0 16px rgba(198, 40, 40, 0.65); }
}

/* Smooth glide when a computed layout re-solves, Auto Arrange runs, or the
   view switches. Vue Flow positions nodes via transform, so one transition
   rule covers every animated move. */
.whiteboard-canvas.layout-animating .vue-flow__node {
  transition: transform 0.65s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ─── Connection handles ─── */

/* Invisible hot zone: four strips forming a frame strictly OUTSIDE the card
   bounds (thickness --band, screen-constant via connectBandStyle). Nothing
   overlaps the card itself, so card content and dragging are untouched. */
.whiteboard-flow .connect-band {
  position: absolute;
  pointer-events: all;
  background: transparent;
  z-index: 0;
}

.whiteboard-flow .connect-band-top {
  left: calc(-1 * var(--band));
  right: calc(-1 * var(--band));
  top: calc(-1 * var(--band));
  height: var(--band);
}

.whiteboard-flow .connect-band-bottom {
  left: calc(-1 * var(--band));
  right: calc(-1 * var(--band));
  bottom: calc(-1 * var(--band));
  height: var(--band);
}

.whiteboard-flow .connect-band-left {
  left: calc(-1 * var(--band));
  top: 0;
  bottom: 0;
  width: var(--band);
}

.whiteboard-flow .connect-band-right {
  right: calc(-1 * var(--band));
  top: 0;
  bottom: 0;
  width: var(--band);
}

/* The border-tracking connection dot: clings to the nearest point on the
   card's perimeter and follows the mouse while it is in the hot zone. Press
   and drag it to draw a link. NO transition — it must track instantly. */
.whiteboard-flow .vue-flow__handle.connect-dot-live {
  position: absolute;
  min-width: 0;
  min-height: 0;
  border-style: solid;
  border-color: #fff;
  background: #1976d2;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.35), 0 0 0 6px rgba(25, 118, 210, 0.18);
  transform: translate(-50%, -50%);
  right: auto;
  bottom: auto;
  opacity: 0.95;
  pointer-events: all;
  transition: none;
  z-index: 40;
  cursor: crosshair;
}

/* Full-card target surface: inert normally; while a connection is in flight it
   covers the card so releasing anywhere on it completes the link. */
.whiteboard-flow .vue-flow__handle.connect-target-surface {
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  transform: none;
  border-radius: 0;
  background: transparent;
  border: none;
  opacity: 0;
  min-width: 0;
  min-height: 0;
  pointer-events: none;
  z-index: 20;
}

.canvas-dragging-connection .vue-flow__handle.connect-target-surface {
  pointer-events: all;
}

/* ─── Edges ─── */

/* Endpoint dots, label, and delete affordance live in the edge-label layer;
   lift it above the nodes so they stay clickable. */
.whiteboard-flow .vue-flow__edge-labels {
  z-index: 1001;
}

.whiteboard-flow .edge-endpoint {
  position: absolute;
  width: 28px;
  height: 28px;
  border: 3px solid #fff;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
  pointer-events: all;
  cursor: pointer;
}

.whiteboard-flow .edge-endpoint:hover {
  box-shadow: 0 0 0 6px rgba(25, 118, 210, 0.25);
}

.whiteboard-flow .edge-label {
  position: absolute;
  font-size: 18px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.85);
  padding: 2px 10px;
  border-radius: 6px;
  white-space: nowrap;
  pointer-events: none;
}

.whiteboard-flow .edge-delete {
  position: absolute;
  width: 32px;
  height: 32px;
  background: #fff;
  border: 2.5px solid #e53935;
  color: #e53935;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  pointer-events: all;
  cursor: pointer;
}

/* Rubber band while aiming a new connection */
.whiteboard-flow .connection-rubber-band {
  stroke: #ffc107;
  stroke-width: 4;
  stroke-dasharray: 8 5;
  stroke-linecap: round;
  opacity: 0.9;
}

.whiteboard-flow .connection-rubber-dot {
  fill: #ffc107;
  stroke: #fff;
  stroke-width: 2;
}

/* ─── Semantic zoom tiers (constant footprint) ─── */
/* All sizes are CANVAS units: they scale geometrically with the zoom, exactly
   like the full card they stand in for. No counter-scaling anywhere. */

.whiteboard-flow .zoom-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 6px solid;
  border-radius: 16px;
  overflow: hidden;
}

.whiteboard-flow .zoom-marker-parent {
  border-radius: 50%;
  border-width: 12px;
  box-shadow: 0 6px 40px rgba(0, 0, 0, 0.30);
}

/* The hub's readable text lives in the screen-space label layer; the tiny
   in-plate copies would just shimmer behind it. */
.whiteboard-flow .zoom-marker-parent .zoom-marker-label,
.whiteboard-flow .zoom-marker-parent .zoom-marker-title {
  display: none;
}

.whiteboard-flow .zoom-marker-label {
  font-weight: 800;
  letter-spacing: 0.06em;
  font-size: 30px;
  line-height: 1.1;
}

.whiteboard-flow .zoom-marker-title {
  font-size: 26px;
  color: #37474f;
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.whiteboard-flow .zoom-summary-card {
  border-top: 10px solid;
  border-radius: 14px !important;
}

.whiteboard-flow .zoom-summary-inner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 22px 26px;
}

.whiteboard-flow .zoom-summary-thumb {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: 10px;
  flex: 0 0 auto;
}

.whiteboard-flow .zoom-summary-icon {
  flex: 0 0 auto;
}

.whiteboard-flow .zoom-summary-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.whiteboard-flow .zoom-summary-type {
  font-weight: 800;
  letter-spacing: 0.05em;
  font-size: 26px;
  line-height: 1;
}

.whiteboard-flow .zoom-summary-title {
  font-size: 30px;
  font-weight: 600;
  color: #263238;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.whiteboard-flow .zoom-summary-preview {
  font-size: 22px;
  color: #607d8b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Wide hierarchical row variant: short and horizontal, so more of the tree
   fits on screen. */
.whiteboard-flow .zoom-summary-wide .zoom-summary-inner {
  padding: 8px 26px;
}

.whiteboard-flow .zoom-summary-wide .zoom-summary-body {
  flex-direction: row;
  align-items: baseline;
  gap: 24px;
}

.whiteboard-flow .zoom-summary-wide .zoom-summary-thumb {
  width: 64px;
  height: 64px;
}

/* ─── MiniMap ─── */
.whiteboard-flow .vue-flow__minimap {
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

/* ─── Circle opt-ins ───
   styles/vuetify-fixes.css flattens ALL border-radius app-wide with
   `* { border-radius: 0 !important }` (square aesthetic), and genuinely
   circular elements must opt back in with their own !important — same pattern
   the fixes file uses for avatars/radios. These whiteboard elements are
   genuinely circular: the parent hub discs, connection dots, and edge
   endpoint/delete buttons. */
.whiteboard-flow .zoom-marker-parent,
.parent-node-circle,
.parent-node-circle::before,
.whiteboard-flow .vue-flow__handle.connect-dot-live,
.whiteboard-flow .edge-endpoint,
.whiteboard-flow .edge-delete,
.whiteboard-flow .connection-rubber-dot {
  border-radius: 50% !important;
}

.hub-label {
  border-radius: 999px !important;
}
</style>
