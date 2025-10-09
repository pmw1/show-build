<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="generationSubTab"
          direction="vertical"
          color="primary"
          class="generation-vertical-tabs"
        >
          <v-tab value="fsq-generator" prepend-icon="mdi-format-quote-close">
            FSQ Quote Generator
          </v-tab>
          <v-tab value="llm-routing" prepend-icon="mdi-robot">
            AI/LLM Routing
          </v-tab>
          <v-tab value="templates" prepend-icon="mdi-file-document-multiple">
            Templates Library
          </v-tab>
          <v-tab value="media-assets" prepend-icon="mdi-folder-image">
            Media Assets
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="generationSubTab" class="pa-6">

          <!-- FSQ Quote Generator -->
          <v-tabs-window-item value="fsq-generator">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-format-quote-close</v-icon>
              FSQ Quote Generator
            </h3>
            <p class="text-body-2 mb-4">Configure settings for Full Screen Quote generation and preview.</p>

            <v-card variant="tonal" color="deep-purple" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-video</v-icon>
                Preview Background Video
              </h4>
              <v-text-field
                v-model="localSettings.fsqBackgroundVideo"
                label="Background Video Path"
                placeholder="/assets/preview-background.mp4"
                variant="outlined"
                density="comfortable"
                hint="Path to compressed video for FSQ modal preview (1920x1080 → 640x360, ~1MB)"
                persistent-hint
              />

              <v-alert type="info" variant="tonal" class="mt-4">
                <v-alert-title>Compressed Preview</v-alert-title>
                The preview uses an ultra-compressed version of your branded background.
                Current: <code>{{ localSettings.fsqBackgroundVideo }}</code>
              </v-alert>
            </v-card>

            <v-card variant="tonal" color="deep-purple" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-palette</v-icon>
                Default FSQ Style
              </h4>
              <v-row>
                <v-col cols="6">
                  <v-select
                    v-model="localSettings.fsqDefaultAlignment"
                    :items="alignmentOptions"
                    label="Default Text Alignment"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="localSettings.fsqDefaultFont"
                    :items="fontOptions"
                    label="Default Font Family"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
              </v-row>

              <v-slider
                v-model="localSettings.fsqDefaultFontSize"
                label="Default Font Size"
                min="10"
                max="50"
                step="1"
                thumb-label
                hint="Default font size for new FSQ quotes (10-50px)"
                persistent-hint
              >
                <template v-slot:append>
                  <v-chip size="small" color="primary">
                    {{ localSettings.fsqDefaultFontSize }}px
                  </v-chip>
                </template>
              </v-slider>
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-cog</v-icon>
                Generation Options
              </h4>
              <v-checkbox
                v-model="localSettings.fsqIncludeAttributionByDefault"
                label="Include attribution by default"
                hint="When enabled, the attribution radio button will be pre-selected to 'Include Attribution'"
                persistent-hint
                density="comfortable"
              />
            </v-card>

            <v-card elevation="2" class="mb-4">
              <v-card-title class="bg-indigo-lighten-1 text-white">
                <v-icon class="mr-2">mdi-scissors-cutting</v-icon>
                FSQ Quote Splitting Rules
              </v-card-title>

              <v-card-text class="pt-4">
                <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                  Configure how AI determines when and where to split long quotes for optimal TV display
                </v-alert>

                <!-- Primary Controls: Screen Capacity -->
                <div class="text-subtitle-2 mb-3 font-weight-bold">Screen Capacity Limits</div>

                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model.number="localSettings.fsqMaxLines"
                      label="Max Lines Per Screen"
                      type="number"
                      min="3"
                      max="8"
                      variant="outlined"
                      density="compact"
                      hint="Maximum lines before split (3-8)"
                      persistent-hint
                      prepend-inner-icon="mdi-format-line-spacing"
                    >
                      <template v-slot:append-inner>
                        <span class="text-caption text-grey mr-1">lines</span>
                        <v-tooltip location="top" max-width="400">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Maximum Lines Per Screen</div>
                            <div class="text-body-2 mb-2">
                              Controls the maximum number of text lines displayed on a single full-screen quote before the AI considers splitting it.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Recommended values:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li><strong>3-4 lines:</strong> Best for maximum readability on TV (viewer sitting 8-10 feet away)</li>
                              <li><strong>5-6 lines:</strong> Good balance between content and readability</li>
                              <li><strong>7-8 lines:</strong> Maximum before quotes feel cluttered or overwhelming</li>
                            </ul>
                            <div class="text-body-2">
                              <strong>How it works:</strong> This value is multiplied by "Characters Per Line" to calculate the total character limit for a single screen.
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-text-field>
                  </v-col>

                  <v-col cols="6">
                    <v-text-field
                      v-model.number="localSettings.fsqCharsPerLine"
                      label="Characters Per Line"
                      type="number"
                      min="40"
                      max="90"
                      variant="outlined"
                      density="compact"
                      hint="Average characters at default font (40-90)"
                      persistent-hint
                      prepend-inner-icon="mdi-format-text"
                    >
                      <template v-slot:append-inner>
                        <span class="text-caption text-grey mr-1">chars</span>
                        <v-tooltip location="top" max-width="400">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Characters Per Line</div>
                            <div class="text-body-2 mb-2">
                              Defines the approximate number of characters that fit comfortably on one line at the default font size for 1920x1080 full-screen display.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Typography guidelines:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li><strong>40-50 chars:</strong> Optimal for TV viewing from 8-10 feet, excellent readability</li>
                              <li><strong>50-60 chars:</strong> Good balance, standard for most quotes</li>
                              <li><strong>60-75 chars:</strong> Still readable but approaching the limit</li>
                              <li><strong>75-90 chars:</strong> Maximum - viewers may lose their place between lines</li>
                            </ul>
                            <div class="text-body-2">
                              <strong>Note:</strong> This is based on average character width. Words with more narrow letters (like "illill") fit more per line than wide letters (like "WWWWW").
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-text-field>
                  </v-col>
                </v-row>

                <v-divider class="my-4"></v-divider>

                <!-- Secondary Controls: Split Behavior -->
                <div class="text-subtitle-2 mb-3 font-weight-bold">Split Behavior</div>

                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model.number="localSettings.fsqMinSecondScreen"
                      label="Minimum Second Screen Length"
                      type="number"
                      min="40"
                      max="150"
                      variant="outlined"
                      density="compact"
                      hint="Prevents orphan text (40-150 chars)"
                      persistent-hint
                      prepend-inner-icon="mdi-text-box-remove-outline"
                    >
                      <template v-slot:append-inner>
                        <span class="text-caption text-grey mr-1">chars</span>
                        <v-tooltip location="top" max-width="450">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Minimum Second Screen Length (Orphan Prevention)</div>
                            <div class="text-body-2 mb-2">
                              Prevents creating a second screen with very little text ("orphan" text) that looks awkward or unprofessional.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>How it works:</strong>
                            </div>
                            <div class="text-body-2 mb-2">
                              If splitting at the max limit would leave less than this value on the second screen, the AI will instead split closer to the middle to balance the content evenly.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Example with Max=250, Min=80:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li><strong>280 char quote:</strong> Normal split at 250 would leave only 30 chars (too short). System splits at 140/140 instead.</li>
                              <li><strong>400 char quote:</strong> Split at 250 leaves 150 chars (adequate). Normal split applies.</li>
                            </ul>
                            <div class="text-body-2 mb-2">
                              <strong>Recommended values:</strong>
                            </div>
                            <ul class="text-body-2">
                              <li><strong>60-70 chars:</strong> Aggressive - allows shorter second screens (~1 line)</li>
                              <li><strong>80-100 chars:</strong> Recommended - ensures ~1.5-2 lines minimum</li>
                              <li><strong>100-150 chars:</strong> Conservative - guarantees substantial second screen</li>
                            </ul>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-text-field>
                  </v-col>

                  <v-col cols="6">
                    <v-select
                      v-model="localSettings.fsqSplitStrategy"
                      label="Split Strategy"
                      :items="splitStrategyOptions"
                      variant="outlined"
                      density="compact"
                      hint="How to handle borderline quotes"
                      persistent-hint
                      prepend-inner-icon="mdi-call-split"
                    >
                      <template v-slot:append-inner>
                        <v-tooltip location="top" max-width="450">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Split Strategy</div>
                            <div class="text-body-2 mb-2">
                              Controls how the AI decides when and where to split quotes that are close to the character limit.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Strategy Options:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li class="mb-1">
                                <strong>Smart Balance (Recommended):</strong> Uses intelligent logic - splits at max limit for long quotes, but balances quotes near the threshold to prevent orphans. Best overall approach.
                              </li>
                              <li class="mb-1">
                                <strong>Always Balance:</strong> Always splits quotes near the middle point, even if one screen could fit. More conservative, ensures similar-length screens.
                              </li>
                              <li class="mb-1">
                                <strong>Strict Limit:</strong> Always splits exactly at the max character limit, no balancing. May create short second screens.
                              </li>
                              <li class="mb-1">
                                <strong>AI Decides:</strong> Lets the AI service make all split decisions without using your threshold settings. Most flexible but least predictable.
                              </li>
                            </ul>
                            <div class="text-body-2">
                              <strong>Recommendation:</strong> Use "Smart Balance" for the best combination of readability and orphan prevention.
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-select>
                  </v-col>
                </v-row>

                <v-divider class="my-4"></v-divider>

                <!-- Tertiary Controls: Fine-tuning -->
                <v-expansion-panels variant="accordion" class="mb-3">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon class="mr-2">mdi-tune</v-icon>
                      Advanced Split Tuning
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="localSettings.fsqBalanceThresholdPercent"
                            label="Balance Threshold"
                            type="number"
                            min="10"
                            max="50"
                            suffix="%"
                            variant="outlined"
                            density="compact"
                            hint="Extra capacity % before forcing split"
                            persistent-hint
                          >
                            <template v-slot:append-inner>
                              <v-tooltip location="top" max-width="450">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                                </template>
                                <div class="pa-2">
                                  <div class="text-subtitle-2 mb-2">Balance Threshold Percentage</div>
                                  <div class="text-body-2 mb-2">
                                    Defines the "gray zone" where quotes are close enough to the limit that balancing makes more sense than strict splitting.
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>How it works:</strong>
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    This percentage is added to your minimum second screen value to create a threshold. Quotes within this range will be balanced instead of split at the max limit.
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>Calculation:</strong> Balance Threshold = Max Screen 1 + (Min Second Screen × Percent)
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>Example with 30%:</strong>
                                  </div>
                                  <ul class="text-body-2 mb-2">
                                    <li>Max Screen 1: 250 chars</li>
                                    <li>Min Second: 80 chars</li>
                                    <li>Balance Threshold: 250 + (80 × 0.30) = 274 chars</li>
                                    <li>Quotes 251-274 chars → balanced split</li>
                                    <li>Quotes 275+ chars → standard split at 250</li>
                                  </ul>
                                  <div class="text-body-2">
                                    <strong>Higher %</strong> = larger gray zone, more balancing. <strong>Lower %</strong> = stricter adherence to max limit.
                                  </div>
                                </div>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>

                        <v-col cols="6">
                          <div class="d-flex align-center">
                            <v-switch
                              v-model="localSettings.fsqPreferSentenceBoundaries"
                              label="Prefer Sentence Boundaries"
                              color="primary"
                              density="compact"
                              hint="Split at periods/punctuation when possible"
                              persistent-hint
                              hide-details="auto"
                            ></v-switch>
                            <v-tooltip location="top" max-width="400">
                              <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" size="small" color="info" class="ml-2">mdi-information</v-icon>
                              </template>
                              <div class="pa-2">
                                <div class="text-subtitle-2 mb-2">Prefer Sentence Boundaries</div>
                                <div class="text-body-2 mb-2">
                                  When enabled, the AI will try to split quotes at natural sentence endings (periods, exclamation points, question marks) rather than in the middle of a sentence.
                                </div>
                                <div class="text-body-2 mb-2">
                                  <strong>Benefits:</strong>
                                </div>
                                <ul class="text-body-2 mb-2">
                                  <li>More natural reading flow - complete thoughts on each screen</li>
                                  <li>Viewers can absorb complete ideas before moving to next screen</li>
                                  <li>Professional presentation quality</li>
                                </ul>
                                <div class="text-body-2 mb-2">
                                  <strong>How it works:</strong> The AI searches within ±50 characters of the target split point for sentence-ending punctuation.
                                </div>
                                <div class="text-body-2">
                                  <strong>Recommendation:</strong> Keep this enabled for best readability.
                                </div>
                              </div>
                            </v-tooltip>
                          </div>
                        </v-col>
                      </v-row>

                      <v-row class="mt-2">
                        <v-col cols="6">
                          <div class="d-flex align-center">
                            <v-switch
                              v-model="localSettings.fsqAllowMidSentenceSplit"
                              label="Allow Mid-Sentence Splits"
                              color="primary"
                              density="compact"
                              hint="Split at commas/clauses if needed"
                              persistent-hint
                              hide-details="auto"
                            ></v-switch>
                            <v-tooltip location="top" max-width="400">
                              <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" size="small" color="info" class="ml-2">mdi-information</v-icon>
                              </template>
                              <div class="pa-2">
                                <div class="text-subtitle-2 mb-2">Allow Mid-Sentence Splits</div>
                                <div class="text-body-2 mb-2">
                                  When enabled, if no sentence boundary is found near the split point, the AI can split at commas, semicolons, or dashes (natural pause points within sentences).
                                </div>
                                <div class="text-body-2 mb-2">
                                  <strong>Fallback hierarchy:</strong>
                                </div>
                                <ol class="text-body-2 mb-2">
                                  <li>Sentence endings (. ! ?) - within ±50 chars</li>
                                  <li>Clause breaks (, ; -) - within ±30 chars (if enabled)</li>
                                  <li>Word boundaries (spaces) - within ±20 chars</li>
                                  <li>Exact position (last resort)</li>
                                </ol>
                                <div class="text-body-2 mb-2">
                                  <strong>When to use:</strong> Enable for long, complex sentences where waiting for a period would exceed limits by too much.
                                </div>
                                <div class="text-body-2">
                                  <strong>Trade-off:</strong> More flexible splitting vs. potentially breaking mid-thought.
                                </div>
                              </div>
                            </v-tooltip>
                          </div>
                        </v-col>

                        <v-col cols="6">
                          <v-select
                            v-model="localSettings.fsqOverflowHandling"
                            label="Overflow Handling"
                            :items="overflowOptions"
                            variant="outlined"
                            density="compact"
                            hint="What to do with very long quotes"
                            persistent-hint
                          >
                            <template v-slot:append-inner>
                              <v-tooltip location="top" max-width="400">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                                </template>
                                <div class="pa-2">
                                  <div class="text-subtitle-2 mb-2">Overflow Handling</div>
                                  <div class="text-body-2 mb-2">
                                    Controls what happens when quotes are extremely long and would require more than 2 screens.
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>Options:</strong>
                                  </div>
                                  <ul class="text-body-2 mb-2">
                                    <li class="mb-1">
                                      <strong>Multiple Segments (Recommended):</strong> Creates 3, 4, or more FSQ screens as needed. Best for preserving complete quotes.
                                    </li>
                                    <li class="mb-1">
                                      <strong>Compress Text:</strong> Attempts to fit quote by reducing font size or line spacing. May impact readability.
                                    </li>
                                    <li class="mb-1">
                                      <strong>Truncate with Ellipsis:</strong> Cuts quote short with "..." to fit 2 screens max. Use only when full quote isn't essential.
                                    </li>
                                  </ul>
                                  <div class="text-body-2">
                                    <strong>Recommendation:</strong> Use "Multiple Segments" to preserve quote integrity.
                                  </div>
                                </div>
                              </v-tooltip>
                            </template>
                          </v-select>
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

                <!-- Live Calculation Display -->
                <v-card variant="tonal" color="indigo-lighten-5" class="pa-4">
                  <div class="text-subtitle-2 mb-2 font-weight-bold">
                    <v-icon size="small" class="mr-1">mdi-calculator</v-icon>
                    Live Split Calculation
                  </div>

                  <v-row dense>
                    <v-col cols="4">
                      <div class="text-caption text-grey">Max Screen 1</div>
                      <div class="text-h6 text-primary">
                        {{ maxCharsScreen1 }}
                        <span class="text-caption">chars</span>
                      </div>
                    </v-col>

                    <v-col cols="4">
                      <div class="text-caption text-grey">Balance Threshold</div>
                      <div class="text-h6 text-orange">
                        {{ balanceThreshold }}
                        <span class="text-caption">chars</span>
                      </div>
                    </v-col>

                    <v-col cols="4">
                      <div class="text-caption text-grey">Min Screen 2</div>
                      <div class="text-h6 text-green">
                        {{ localSettings.fsqMinSecondScreen || 80 }}
                        <span class="text-caption">chars</span>
                      </div>
                    </v-col>
                  </v-row>

                  <v-divider class="my-3"></v-divider>

                  <!-- Visual Split Ranges -->
                  <div class="text-caption mb-2">Quote Length Behavior:</div>
                  <div class="split-behavior-guide">
                    <div class="behavior-range single">
                      <v-chip size="small" color="green" class="mr-2">Single Screen</v-chip>
                      <span class="text-caption">0 - {{ maxCharsScreen1 }} chars</span>
                    </div>
                    <div class="behavior-range balanced mt-1">
                      <v-chip size="small" color="orange" class="mr-2">Balanced Split</v-chip>
                      <span class="text-caption">
                        {{ maxCharsScreen1 + 1 }} - {{ balanceThreshold }} chars
                      </span>
                    </div>
                    <div class="behavior-range standard mt-1">
                      <v-chip size="small" color="blue" class="mr-2">Standard Split</v-chip>
                      <span class="text-caption">{{ balanceThreshold + 1 }}+ chars</span>
                    </div>
                  </div>
                </v-card>

                <!-- Example/Test Section -->
                <v-divider class="my-4"></v-divider>

                <v-expansion-panels variant="accordion">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon class="mr-2">mdi-test-tube</v-icon>
                      Test Your Settings
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-textarea
                        v-model="testQuote"
                        label="Paste a test quote"
                        variant="outlined"
                        rows="3"
                        placeholder="Enter a quote to see how it would be split..."
                        @input="previewSplit"
                      ></v-textarea>

                      <div v-if="splitPreview" class="mt-3">
                        <v-alert :type="splitPreview.type" variant="tonal" density="compact">
                          <div class="text-subtitle-2 mb-1">
                            {{ splitPreview.title }}
                          </div>
                          <div class="text-caption">
                            Quote length: <strong>{{ testQuote.length }}</strong> chars |
                            Strategy: <strong>{{ splitPreview.strategy }}</strong> |
                            Segments: <strong>{{ splitPreview.segments.length }}</strong>
                          </div>
                        </v-alert>

                        <div v-for="(segment, idx) in splitPreview.segments" :key="idx" class="mt-2">
                          <v-card variant="outlined" class="pa-3">
                            <div class="text-caption text-grey mb-1">Screen {{ idx + 1 }}/{{ splitPreview.segments.length }}</div>
                            <div class="quote-preview">{{ segment }}</div>
                            <div class="text-caption text-grey mt-1">{{ segment.length }} characters</div>
                          </v-card>
                        </div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- LLM Routing -->
          <v-tabs-window-item value="llm-routing">
            <LLMRoutingSettings
              v-model="llmSettings"
              @save="handleLLMSave"
            />
          </v-tabs-window-item>

          <!-- Templates Library -->
          <v-tabs-window-item value="templates">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-file-document-multiple</v-icon>
              Templates Library
            </h3>
            <p class="text-body-2 mb-4">Manage paths to reusable content templates stored on the media drive.</p>

            <v-card variant="tonal" color="primary" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-folder-multiple</v-icon>
                Template Library Root
              </h4>
              <v-text-field
                v-model="localSettings.templateLibraryPath"
                label="Template Library Path"
                placeholder="/mnt/sync/disaffected/templates"
                variant="outlined"
                density="comfortable"
                hint="Root path for all template categories"
                persistent-hint
              />
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3">Template Categories</h4>
              <v-list density="compact">
                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-text-box</v-icon>
                  </template>
                  <v-list-item-title>Rundown Templates</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.templateLibraryPath }}/rundown/</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-script-text</v-icon>
                  </template>
                  <v-list-item-title>Script Templates</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.templateLibraryPath }}/scripts/</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-image-multiple</v-icon>
                  </template>
                  <v-list-item-title>Graphic Templates</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.templateLibraryPath }}/graphics/</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card>

            <v-alert type="info" variant="tonal">
              <v-alert-title>Storage Location</v-alert-title>
              Templates are stored on the media drive (<code>/mnt/sync/disaffected/</code>) for persistence and backup via Syncthing.
            </v-alert>
          </v-tabs-window-item>

          <!-- Media Assets -->
          <v-tabs-window-item value="media-assets">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-folder-image</v-icon>
              Media Assets
            </h3>
            <p class="text-body-2 mb-4">Configure paths to shared media library for backgrounds, graphics, and audio.</p>

            <v-card variant="tonal" color="primary" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-folder-image</v-icon>
                Media Assets Root
              </h4>
              <v-text-field
                v-model="localSettings.mediaAssetsPath"
                label="Media Assets Path"
                placeholder="/mnt/sync/disaffected/media assets"
                variant="outlined"
                density="comfortable"
                hint="Root path for all shared media assets"
                persistent-hint
              />
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3">Media Asset Categories</h4>
              <v-list density="compact">
                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-video</v-icon>
                  </template>
                  <v-list-item-title>Video Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/video/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Video Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-video-outline</v-icon>
                  </template>
                  <v-list-item-subtitle>Backgrounds: {{ localSettings.mediaAssetsPath }}/video/backgrounds/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-video-outline</v-icon>
                  </template>
                  <v-list-item-subtitle>Templates: {{ localSettings.mediaAssetsPath }}/video/templates/</v-list-item-subtitle>
                </v-list-item>

                <v-divider class="my-2" />

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-music</v-icon>
                  </template>
                  <v-list-item-title>Audio Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/audio/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Audio Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-music-note</v-icon>
                  </template>
                  <v-list-item-subtitle>Music: {{ localSettings.mediaAssetsPath }}/audio/music/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-waveform</v-icon>
                  </template>
                  <v-list-item-subtitle>SFX: {{ localSettings.mediaAssetsPath }}/audio/sfx/</v-list-item-subtitle>
                </v-list-item>

                <v-divider class="my-2" />

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-image</v-icon>
                  </template>
                  <v-list-item-title>Graphics Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/graphics/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Graphics Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-format-quote-close</v-icon>
                  </template>
                  <v-list-item-subtitle>FSQ Templates: {{ localSettings.mediaAssetsPath }}/graphics/fsq-templates/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-text-box</v-icon>
                  </template>
                  <v-list-item-subtitle>Lower Thirds: {{ localSettings.mediaAssetsPath }}/graphics/lower-thirds/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-transition</v-icon>
                  </template>
                  <v-list-item-subtitle>Transitions: {{ localSettings.mediaAssetsPath }}/graphics/transitions/</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card>

            <v-alert type="success" variant="tonal">
              <v-alert-title>Source Video</v-alert-title>
              Current background source: <code>/mnt/sync/disaffected/media assets/video/backgrounds/background-branded-slow.mp4</code>
            </v-alert>
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>

    <!-- Save Button (Fixed at bottom of card) -->
    <v-card-actions class="px-4 pb-4 border-t">
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="save" variant="elevated">
        <v-icon left>mdi-content-save</v-icon>
        Save Generation Settings
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import LLMRoutingSettings from './LLMRoutingSettings.vue'

export default {
  name: 'GenerationSettings',
  components: {
    LLMRoutingSettings
  },
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        fsqBackgroundVideo: '/assets/preview-background.mp4',
        fsqDefaultAlignment: 'left',
        fsqDefaultFont: 'sans-serif',
        fsqDefaultFontSize: 30,
        fsqIncludeAttributionByDefault: true,
        fsqMaxLines: 4,
        fsqCharsPerLine: 70,
        templateLibraryPath: '/mnt/sync/disaffected/templates',
        mediaAssetsPath: '/mnt/sync/disaffected/media assets'
      })
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      generationSubTab: 'fsq-generator',
      localSettings: {
        ...this.modelValue,
        // Initialize new FSQ split settings with defaults if not present
        fsqMinSecondScreen: this.modelValue.fsqMinSecondScreen || 80,
        fsqSplitStrategy: this.modelValue.fsqSplitStrategy || 'smart',
        fsqBalanceThresholdPercent: this.modelValue.fsqBalanceThresholdPercent || 30,
        fsqPreferSentenceBoundaries: this.modelValue.fsqPreferSentenceBoundaries !== undefined ? this.modelValue.fsqPreferSentenceBoundaries : true,
        fsqAllowMidSentenceSplit: this.modelValue.fsqAllowMidSentenceSplit !== undefined ? this.modelValue.fsqAllowMidSentenceSplit : false,
        fsqOverflowHandling: this.modelValue.fsqOverflowHandling || 'multi_segment'
      },
      llmSettings: {
        routing: {
          quoteSplitting: 'auto',
          slugGeneration: 'auto',
          scriptSummary: 'auto',
          titleGeneration: 'auto',
          contentExpansion: 'auto',
          entityExtraction: 'auto',
          peopleSearch: 'auto',
          socialSearch: 'auto',
          tweetComposing: 'auto',
          factChecking: 'auto',
          enableFallback: true,
          fallbackOrder: ['ollama', 'openai', 'anthropic', 'gemini', 'grok']
        },
        prompts: []
      },
      alignmentOptions: [
        { title: 'Left Aligned', value: 'left' },
        { title: 'Centered', value: 'centered' },
        { title: 'Right Aligned', value: 'right' }
      ],
      fontOptions: [
        { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
        { title: 'Serif (Georgia)', value: 'serif' },
        { title: 'Monospace (Courier)', value: 'monospace' }
      ],
      splitStrategyOptions: [
        { title: 'Smart Balance (Recommended)', value: 'smart' },
        { title: 'Always Balance', value: 'always_balance' },
        { title: 'Strict Limit', value: 'strict_limit' },
        { title: 'AI Decides', value: 'ai_only' }
      ],
      overflowOptions: [
        { title: 'Multiple Segments', value: 'multi_segment' },
        { title: 'Compress Text', value: 'compress' },
        { title: 'Truncate with Ellipsis', value: 'truncate' }
      ],
      testQuote: '',
      splitPreview: null
    }
  },
  computed: {
    maxCharsScreen1() {
      return (this.localSettings.fsqMaxLines || 5) * (this.localSettings.fsqCharsPerLine || 50)
    },
    balanceThreshold() {
      const maxChars = this.maxCharsScreen1
      const minSecond = this.localSettings.fsqMinSecondScreen || 80
      const percent = (this.localSettings.fsqBalanceThresholdPercent || 30) / 100
      return Math.round(maxChars + (minSecond * percent))
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        this.localSettings = { ...newVal }
      },
      deep: true
    }
  },
  mounted() {
    this.loadLLMSettings()
  },
  methods: {
    save() {
      this.$emit('update:modelValue', this.localSettings)
      this.$emit('save', this.localSettings)
    },
    async loadLLMSettings() {
      // Load LLM settings from database
      try {
        const response = await this.$axios.get('/settings/llm_routing')
        if (response.data && response.data.value) {
          this.llmSettings = response.data.value
          console.log('✅ Loaded LLM routing settings from database:', this.llmSettings)
        }
      } catch (error) {
        console.warn('Failed to load LLM settings from database, using defaults:', error)
      }
    },
    async handleLLMSave(settings) {
      this.llmSettings = settings

      // Save to database
      try {
        await this.$axios.post('/settings/llm_routing', {
          key: 'llm_routing',
          value: settings,
          category: 'generation'
        })
        console.log('✅ LLM routing settings saved to database:', settings)

        // Show success notification
        this.$emit('save', this.localSettings)
      } catch (error) {
        console.error('❌ Failed to save LLM settings to database:', error)
        alert('Failed to save LLM routing settings')
      }
    },

    // Preview split behavior for test quote
    previewSplit() {
      if (!this.testQuote) {
        this.splitPreview = null
        return
      }

      const config = {
        maxChars: this.maxCharsScreen1,
        minSecond: this.localSettings.fsqMinSecondScreen || 80,
        balanceThreshold: this.balanceThreshold
      }

      const length = this.testQuote.length

      if (length <= config.maxChars) {
        this.splitPreview = {
          type: 'success',
          title: '✓ Fits on single screen',
          strategy: 'Single Screen',
          segments: [this.testQuote]
        }
      } else if (length <= config.balanceThreshold) {
        const mid = Math.floor(length / 2)
        // Find nearest sentence boundary
        const splitPoint = this.findSplitPoint(this.testQuote, mid)
        this.splitPreview = {
          type: 'warning',
          title: '⚖️ Will be balanced split',
          strategy: 'Balanced',
          segments: [
            this.testQuote.substring(0, splitPoint).trim(),
            this.testQuote.substring(splitPoint).trim()
          ]
        }
      } else {
        const splitPoint = this.findSplitPoint(this.testQuote, config.maxChars)
        const remainder = this.testQuote.substring(splitPoint).trim()

        // Check if remainder is too short (orphan)
        if (remainder.length < config.minSecond) {
          this.splitPreview = {
            type: 'error',
            title: '⚠️ Would create orphan text - will rebalance',
            strategy: 'Forced Balance',
            segments: [
              this.testQuote.substring(0, Math.floor(length / 2)).trim(),
              this.testQuote.substring(Math.floor(length / 2)).trim()
            ]
          }
        } else {
          this.splitPreview = {
            type: 'info',
            title: '✂️ Will be standard split',
            strategy: 'Standard',
            segments: [
              this.testQuote.substring(0, splitPoint).trim(),
              remainder
            ]
          }
        }
      }
    },

    // Find best split point near target position
    findSplitPoint(text, target) {
      if (!this.localSettings.fsqPreferSentenceBoundaries) {
        return target
      }

      // Try to find sentence boundaries first
      const sentences = ['. ', '! ', '? ']
      for (const punct of sentences) {
        const idx = text.lastIndexOf(punct, target)
        if (idx > target - 50 && idx < target + 50) {
          return idx + 2
        }
      }

      // If mid-sentence splits allowed, try commas/semicolons
      if (this.localSettings.fsqAllowMidSentenceSplit) {
        const clauses = [', ', '; ', ' - ']
        for (const punct of clauses) {
          const idx = text.lastIndexOf(punct, target)
          if (idx > target - 30 && idx < target + 30) {
            return idx + 2
          }
        }
      }

      // Fallback to word boundary
      const spaceIdx = text.lastIndexOf(' ', target)
      if (spaceIdx > target - 20) {
        return spaceIdx + 1
      }

      return target
    }
  }
}
</script>

<style scoped>
.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.generation-vertical-tabs {
  height: 100%;
}

.v-card {
  border-radius: 8px;
}
</style>
