<template>
  <v-container fluid class="dev-tools-view pa-6">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-2">Developer Tools</h1>
        <p class="text-subtitle-1 text-grey mb-6">Internal reference for Show-Build development</p>
      </v-col>
    </v-row>

    <!-- ContentEditor Wireframe Section -->
    <v-row>
      <v-col cols="12">
        <v-card class="mb-6">
          <v-card-title class="text-h5">
            <v-icon class="mr-2">mdi-view-dashboard-outline</v-icon>
            ContentEditor Wireframe
          </v-card-title>
          <v-card-subtitle>Visual reference for component regions and terminology</v-card-subtitle>

          <v-card-text>
            <!-- Wireframe Diagram -->
            <div class="wireframe-container">
              <!-- Show Info Header -->
              <div class="wireframe-row wireframe-header">
                <div class="wireframe-box header-box">
                  <div class="box-label">ShowInfoHeader</div>
                  <div class="box-content">
                    <span class="field">Show Title</span>
                    <span class="field">Episode Number</span>
                    <span class="field">Air Date/Time</span>
                    <span class="field">Production Status</span>
                    <span class="field">Duration</span>
                    <span class="field">Save Button</span>
                  </div>
                </div>
              </div>

              <!-- Main Content Area - 3 Panels -->
              <div class="wireframe-row wireframe-main">
                <!-- Rundown Panel -->
                <div class="wireframe-box rundown-panel-box">
                  <div class="box-label">RundownPanel</div>
                  <div class="box-content">
                    <div class="region-box">
                      <span class="region-label">Region: PRE-SHOW</span>
                      <div class="item-placeholder">Rundown Item</div>
                      <div class="item-placeholder selected">Rundown Item (selected)</div>
                    </div>
                    <div class="region-box">
                      <span class="region-label">Region: BLOCK A</span>
                      <div class="item-placeholder">Rundown Item</div>
                      <div class="item-placeholder">Rundown Item</div>
                    </div>
                    <div class="region-box break-region">
                      <span class="region-label">Region: BREAK 1</span>
                      <div class="item-placeholder">Ad / Break Item</div>
                    </div>
                    <div class="region-box">
                      <span class="region-label">Region: BLOCK B</span>
                      <div class="item-placeholder">Rundown Item</div>
                    </div>
                  </div>
                  <div class="box-actions">
                    <span class="action">+ New Item</span>
                    <span class="action">Sync Order</span>
                  </div>
                </div>

                <!-- Editor Panel -->
                <div class="wireframe-box editor-panel-box">
                  <div class="box-label">EditorPanel</div>
                  <div class="box-content">
                    <div class="editor-toolbar">
                      <span class="toolbar-item">Mode Toggle (Script/Markdown)</span>
                      <span class="toolbar-item">Formatting Tools</span>
                    </div>
                    <div class="script-content">
                      <div class="paragraph-box">
                        <span class="speaker-tag">JOSH</span>
                        <div class="paragraph-content">Paragraph text content (contenteditable)</div>
                      </div>
                      <div class="cue-block-box">
                        <span class="cue-type">SOT CUE</span>
                        <div class="cue-content">PlaceholderCueCard</div>
                      </div>
                      <div class="paragraph-box">
                        <span class="speaker-tag">JOSH</span>
                        <div class="paragraph-content">More paragraph content...</div>
                      </div>
                      <div class="cue-block-box fsq">
                        <span class="cue-type">FSQ CUE</span>
                        <div class="cue-content">Full Screen Quote</div>
                      </div>
                    </div>
                    <div class="segment-edit-buffer">
                      <span class="buffer-label">segmentEditBuffer (debounced changes)</span>
                    </div>
                  </div>
                </div>

                <!-- Metadata Panel -->
                <div class="wireframe-box metadata-panel-box">
                  <div class="box-label">MetadataPanel</div>
                  <div class="box-content">
                    <div class="field-group">
                      <span class="field-label">Item Type</span>
                      <span class="field-label">Title</span>
                      <span class="field-label">Slug</span>
                      <span class="field-label">Duration</span>
                      <span class="field-label">Status</span>
                    </div>
                    <div class="field-group">
                      <span class="field-label">Speaker</span>
                      <span class="field-label">WPM</span>
                    </div>
                    <div class="field-group">
                      <span class="field-label">Version History</span>
                    </div>
                  </div>
                  <div class="box-actions">
                    <span class="action">Generate Script</span>
                    <span class="action">Generate Media List</span>
                  </div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Terminology Section -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon class="mr-2">mdi-book-open-variant</v-icon>
            Component Terminology
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Term</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>ContentEditor</code></td>
                  <td>Main parent component - orchestrates all panels and state</td>
                </tr>
                <tr>
                  <td><code>ShowInfoHeader</code></td>
                  <td>Top bar with episode metadata, save button, production status</td>
                </tr>
                <tr>
                  <td><code>RundownPanel</code></td>
                  <td>Left sidebar - list of rundown items organized by region</td>
                </tr>
                <tr>
                  <td><code>EditorPanel</code></td>
                  <td>Center panel - where script content is edited (paragraphs + cues)</td>
                </tr>
                <tr>
                  <td><code>MetadataPanel</code></td>
                  <td>Right sidebar - item properties, version history, generation tools</td>
                </tr>
                <tr>
                  <td><code>PlaceholderCueCard</code></td>
                  <td>Visual card for cue blocks (SOT, IMG, GFX, FSQ, etc.)</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon class="mr-2">mdi-database</v-icon>
            Data Flow Terminology
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Term</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>rundownItems</code></td>
                  <td>Array of all items in the rundown (ContentEditor state)</td>
                </tr>
                <tr>
                  <td><code>selectedItemIndex</code></td>
                  <td>Index of currently selected item in rundownItems array</td>
                </tr>
                <tr>
                  <td><code>currentRundownItem</code></td>
                  <td>Computed property - the currently selected item object</td>
                </tr>
                <tr>
                  <td><code>rawMarkdownContent</code></td>
                  <td>The script content as raw markdown string</td>
                </tr>
                <tr>
                  <td><code>scriptContent</code></td>
                  <td>Computed property passed to EditorPanel (derived from parsedContent)</td>
                </tr>
                <tr>
                  <td><code>segmentEditBuffer</code></td>
                  <td>EditorPanel's temporary buffer for debounced edits (1.5s delay)</td>
                </tr>
                <tr>
                  <td><code>scriptSegments</code></td>
                  <td>Computed array of parsed segments (paragraphs + cues)</td>
                </tr>
                <tr>
                  <td><code>hasUnsavedChanges</code></td>
                  <td>Flag indicating pending saves needed</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Regions Section -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon class="mr-2">mdi-view-column</v-icon>
            Rundown Regions
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>PRE-SHOW</strong></td>
                  <td>Content before the show starts (cold open, teases)</td>
                </tr>
                <tr>
                  <td><strong>BLOCK A</strong></td>
                  <td>First content block after show open</td>
                </tr>
                <tr>
                  <td><strong>BREAK 1</strong></td>
                  <td>Commercial/ad break between blocks</td>
                </tr>
                <tr>
                  <td><strong>BLOCK B</strong></td>
                  <td>Second content block</td>
                </tr>
                <tr>
                  <td><strong>BREAK 2</strong></td>
                  <td>Second commercial break</td>
                </tr>
                <tr>
                  <td><strong>BLOCK C</strong></td>
                  <td>Third content block (and so on...)</td>
                </tr>
                <tr>
                  <td><strong>POST-SHOW</strong></td>
                  <td>Content after main show (outros, credits)</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon class="mr-2">mdi-card-text</v-icon>
            Cue Types
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Cue</th>
                  <th>Hotkey</th>
                  <th>Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr><td><strong>SOT</strong></td><td>Alt+S</td><td>Sound On Tape - video clip with audio</td></tr>
                <tr><td><strong>VO</strong></td><td>Alt+V</td><td>Voice Over - video with host narration</td></tr>
                <tr><td><strong>FSQ</strong></td><td>Alt+Q</td><td>Full Screen Quote - quote graphic</td></tr>
                <tr><td><strong>GFX</strong></td><td>Alt+G</td><td>Graphics - custom graphic/lower third</td></tr>
                <tr><td><strong>IMG</strong></td><td>Alt+I</td><td>Image - static image display</td></tr>
                <tr><td><strong>RIF</strong></td><td>Alt+R</td><td>Riff - music/audio bed</td></tr>
                <tr><td><strong>NAT</strong></td><td>Alt+N</td><td>Natural Sound - ambient audio</td></tr>
                <tr><td><strong>PKG</strong></td><td>Alt+P</td><td>Package - pre-produced segment</td></tr>
                <tr><td><strong>BUMP</strong></td><td>Alt+B</td><td>Bump - transition with music/video</td></tr>
                <tr><td><strong>STING</strong></td><td>-</td><td>Sting - short audio hit</td></tr>
                <tr><td><strong>VOX</strong></td><td>-</td><td>Vox Pop - person-on-street clips</td></tr>
                <tr><td><strong>MUS</strong></td><td>-</td><td>Music - music cue</td></tr>
                <tr><td><strong>LIVE</strong></td><td>-</td><td>Live - live feed/remote</td></tr>
                <tr><td><strong>DIR</strong></td><td>-</td><td>Director note/instruction</td></tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Critical Functions Section -->
    <v-row>
      <v-col cols="12">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon class="mr-2">mdi-function</v-icon>
            Critical Functions (Data Flow)
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Function</th>
                  <th>Location</th>
                  <th>Purpose</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>flushPendingChanges()</code></td>
                  <td>EditorPanel</td>
                  <td>Forces debounced edits to emit immediately</td>
                  <td><v-chip color="error" size="small">CRITICAL</v-chip></td>
                </tr>
                <tr>
                  <td><code>selectRundownItem()</code></td>
                  <td>ContentEditor</td>
                  <td>Switches to different rundown item (must flush first!)</td>
                  <td><v-chip color="error" size="small">CRITICAL</v-chip></td>
                </tr>
                <tr>
                  <td><code>saveCurrentItem()</code></td>
                  <td>ContentEditor</td>
                  <td>Persists current item to database</td>
                  <td><v-chip color="warning" size="small">HIGH</v-chip></td>
                </tr>
                <tr>
                  <td><code>handleRundownReorder()</code></td>
                  <td>ContentEditor</td>
                  <td>Handles drag-drop reordering (must flush first!)</td>
                  <td><v-chip color="error" size="small">CRITICAL</v-chip></td>
                </tr>
                <tr>
                  <td><code>updateScriptContent()</code></td>
                  <td>ContentEditor</td>
                  <td>Receives content updates from EditorPanel</td>
                  <td><v-chip color="warning" size="small">HIGH</v-chip></td>
                </tr>
                <tr>
                  <td><code>updateTextSegment()</code></td>
                  <td>EditorPanel</td>
                  <td>Handles typing - puts edits in debounce buffer</td>
                  <td><v-chip color="warning" size="small">HIGH</v-chip></td>
                </tr>
                <tr>
                  <td><code>reconstructRawContent()</code></td>
                  <td>EditorPanel</td>
                  <td>Rebuilds markdown from segment array</td>
                  <td><v-chip color="info" size="small">MEDIUM</v-chip></td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Data Loss Prevention -->
    <v-row>
      <v-col cols="12">
        <v-card class="mb-6" color="error" variant="outlined">
          <v-card-title>
            <v-icon class="mr-2">mdi-alert</v-icon>
            Data Loss Prevention Rules
          </v-card-title>
          <v-card-text>
            <v-alert type="warning" variant="tonal" class="mb-4">
              <strong>ALWAYS flush before these operations:</strong>
            </v-alert>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-check">Switching rundown items (selectRundownItem)</v-list-item>
              <v-list-item prepend-icon="mdi-check">Drag-drop reordering (handleRundownReorder)</v-list-item>
              <v-list-item prepend-icon="mdi-check">Opening modals (SOT, FSQ, GFX, IMG, etc.)</v-list-item>
              <v-list-item prepend-icon="mdi-check">Component unmount (beforeUnmount)</v-list-item>
              <v-list-item prepend-icon="mdi-check">Browser close/refresh (beforeunload)</v-list-item>
              <v-list-item prepend-icon="mdi-check">Region selection changes</v-list-item>
            </v-list>
            <v-divider class="my-4"></v-divider>
            <v-alert type="info" variant="tonal">
              <strong>Debounce timer:</strong> 1.5 seconds (reduced from 5s)<br>
              <strong>Rule:</strong> Any action that could discard the buffer must <code>await flushPendingChanges()</code> first.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script setup>
// Future: Add interactive dev tools here
</script>

<style scoped>
.dev-tools-view {
  background: #1a1a2e;
  min-height: 100vh;
}

/* Wireframe Styles */
.wireframe-container {
  background: #0d0d1a;
  border: 2px solid #333;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.wireframe-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.wireframe-row.wireframe-header {
  margin-bottom: 16px;
}

.wireframe-row.wireframe-main {
  min-height: 400px;
}

.wireframe-box {
  border: 2px dashed #555;
  border-radius: 6px;
  padding: 12px;
  position: relative;
}

.box-label {
  position: absolute;
  top: -10px;
  left: 12px;
  background: #1a1a2e;
  padding: 0 8px;
  font-size: 12px;
  font-weight: bold;
  color: #64b5f6;
}

.header-box {
  flex: 1;
  border-color: #4caf50;
  min-height: 60px;
}

.header-box .box-label { color: #4caf50; }

.header-box .box-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 8px;
}

.header-box .field {
  background: #2a2a3e;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #aaa;
}

.rundown-panel-box {
  width: 220px;
  flex-shrink: 0;
  border-color: #ff9800;
  display: flex;
  flex-direction: column;
}

.rundown-panel-box .box-label { color: #ff9800; }

.editor-panel-box {
  flex: 1;
  border-color: #2196f3;
  display: flex;
  flex-direction: column;
}

.editor-panel-box .box-label { color: #2196f3; }

.metadata-panel-box {
  width: 200px;
  flex-shrink: 0;
  border-color: #9c27b0;
  display: flex;
  flex-direction: column;
}

.metadata-panel-box .box-label { color: #9c27b0; }

.box-content {
  flex: 1;
  padding-top: 8px;
}

.box-actions {
  border-top: 1px solid #333;
  padding-top: 8px;
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action {
  background: #333;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  color: #888;
}

/* Region styles */
.region-box {
  border: 1px solid #444;
  border-radius: 4px;
  padding: 6px;
  margin-bottom: 8px;
  background: #1a1a2e;
}

.region-box.break-region {
  background: #2a1a1a;
  border-color: #663333;
}

.region-label {
  font-size: 9px;
  font-weight: bold;
  color: #888;
  display: block;
  margin-bottom: 4px;
}

.item-placeholder {
  background: #2a2a3e;
  padding: 4px 8px;
  margin: 4px 0;
  border-radius: 3px;
  font-size: 10px;
  color: #777;
}

.item-placeholder.selected {
  background: #1565c0;
  color: #fff;
}

/* Editor content */
.editor-toolbar {
  background: #252535;
  padding: 6px;
  border-radius: 4px;
  margin-bottom: 8px;
  display: flex;
  gap: 12px;
}

.toolbar-item {
  font-size: 10px;
  color: #888;
}

.script-content {
  flex: 1;
  background: #151520;
  border-radius: 4px;
  padding: 8px;
  overflow-y: auto;
}

.paragraph-box {
  background: #1a1a2e;
  border-left: 3px solid #1565c0;
  padding: 8px;
  margin-bottom: 8px;
  border-radius: 0 4px 4px 0;
}

.speaker-tag {
  background: #1565c0;
  color: #fff;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: bold;
  margin-right: 8px;
}

.paragraph-content {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.cue-block-box {
  background: #2a2a1a;
  border: 1px solid #ffc107;
  padding: 8px;
  margin-bottom: 8px;
  border-radius: 4px;
}

.cue-block-box.fsq {
  background: #1a2a2a;
  border-color: #00bcd4;
}

.cue-type {
  background: #ffc107;
  color: #000;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: bold;
}

.cue-block-box.fsq .cue-type {
  background: #00bcd4;
}

.cue-content {
  font-size: 10px;
  color: #888;
  margin-top: 4px;
}

.segment-edit-buffer {
  background: #3a2020;
  border: 1px dashed #f44336;
  padding: 6px;
  border-radius: 4px;
  margin-top: 8px;
}

.buffer-label {
  font-size: 9px;
  color: #f44336;
}

/* Metadata fields */
.field-group {
  background: #252535;
  padding: 6px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.field-label {
  display: block;
  font-size: 10px;
  color: #888;
  padding: 2px 0;
}

/* Table styling */
code {
  background: #2a2a3e;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  color: #64b5f6;
}
</style>
