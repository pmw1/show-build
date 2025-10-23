<template>
  <v-container fluid class="pa-0 scratchpad-container">
    <!-- Toolbar -->
    <v-app-bar flat density="compact" color="grey-lighten-4" class="border-b">
      <v-toolbar-title class="text-h6">
        <v-icon class="me-2">mdi-notebook-edit</v-icon>
        Brainstorm Whiteboard
      </v-toolbar-title>

      <v-chip v-if="identifier" size="small" color="primary" class="ms-3">
        {{ identifier }}
      </v-chip>

      <v-spacer></v-spacer>

      <!-- Quick Actions -->
      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-text"
        @click="addTextCard"
      >
        Text (T)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-link"
        @click="addLinkCard"
      >
        Link (L)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-image"
        @click="triggerImageUpload"
      >
        Image (I)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-video"
        @click="triggerVideoUpload"
      >
        Video (V)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-music-note"
        @click="triggerAudioUpload"
      >
        Audio (A)
      </v-btn>

      <v-divider vertical class="mx-2"></v-divider>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-code-tags"
        @click="addHtmlCard"
      >
        HTML (H)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-code-braces"
        @click="addCodeCard"
      >
        Code (C)
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-language-markdown"
        @click="addMarkdownCard"
      >
        Markdown (M)
      </v-btn>

      <v-divider vertical class="mx-2"></v-divider>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-delete-sweep"
        @click="clearAll"
      >
        Clear All
      </v-btn>

      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-content-save"
        @click="saveBoard"
      >
        Save
      </v-btn>
    </v-app-bar>

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

    <!-- Warning Banner - No Episode Selected -->
    <v-alert
      v-if="!currentEpisode"
      type="error"
      variant="flat"
      density="compact"
      border="start"
      class="ma-0 rounded-0 episode-warning"
    >
      <div class="font-weight-bold text-center" style="color: white; line-height: 1; font-size: 1.5em;">
        <div class="d-flex align-center justify-center">
          <v-icon size="default" class="me-2" color="white">mdi-alert</v-icon>
          No Episode Selected
        </div>
        <div style="font-size: 0.6em; margin-top: 0.1em;">
          <span style="text-decoration: underline;">You will lose all of your work</span> unless you select an episode to work in.
        </div>
      </div>
    </v-alert>

    <!-- Whiteboard Canvas -->
    <div
      ref="canvas"
      class="whiteboard-canvas"
      @click="handleCanvasClick"
      @paste="handlePaste"
      @dragover.prevent
      @drop="handleDrop"
      @keydown="handleKeyDown"
      tabindex="0"
    >
      <!-- Help Text (shown when empty) -->
      <div v-if="cards.length === 0" class="help-overlay">
        <v-icon size="64" color="grey-lighten-1">mdi-gesture-tap</v-icon>
        <p class="text-h6 text-grey-lighten-1 mt-4">Your whiteboard is empty</p>
        <p class="text-body-2 text-grey">
          <strong>Quick actions:</strong><br>
          • Press <kbd>T</kbd> text, <kbd>L</kbd> link, <kbd>I</kbd> image, <kbd>V</kbd> video, <kbd>A</kbd> audio<br>
          • Press <kbd>H</kbd> HTML, <kbd>C</kbd> code, <kbd>M</kbd> markdown<br>
          • Paste images, URLs, or text (<kbd>Ctrl+V</kbd>)<br>
          • Drag items to reposition
        </p>
      </div>

      <!-- Cards -->
      <div
        v-for="card in cards"
        :key="card.id"
        :style="{
          position: 'absolute',
          left: card.x + 'px',
          top: card.y + 'px',
          zIndex: card.id === activeCardId ? 1000 : 1
        }"
        @mousedown="startDrag($event, card)"
      >
        <!-- Text Card -->
        <v-card
          v-if="card.type === 'text'"
          :width="card.collapsed ? 160 : (card.width || 500)"
          class="card-item text-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="amber-darken-2" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">TEXT</span>
              </v-chip>
            </div>
            <div class="collapsed-icon-container" style="border: 3px solid #FFA726; background: #FFF3E0;">
              <v-icon size="x-large" color="amber-darken-2">mdi-text</v-icon>
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
                @click.stop="toggleCollapse(card)"
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
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Link Card -->
        <v-card
          v-if="card.type === 'link'"
          :width="card.collapsed ? 160 : (card.width || 500)"
          class="card-item link-card"
          elevation="2"
        >
          <!-- Collapsed State: Thumbnail Icon -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <!-- Badge above thumbnail -->
            <div class="collapsed-badge">
              <v-chip size="x-small" :color="card.socialMetadata ? 'black' : 'blue'" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">{{ card.socialMetadata ? 'X POST' : 'LINK' }}</span>
              </v-chip>
            </div>

            <v-img
              v-if="card.socialMetadata?.media_urls?.[0] || card.previewImage"
              :src="card.socialMetadata?.media_urls?.[0] || card.previewImage"
              height="160"
              width="160"
              contain
              style="border: 3px solid #1976D2;"
            ></v-img>
            <div v-else class="collapsed-icon-container" style="border: 3px solid #1976D2; background: #E3F2FD;">
              <v-icon size="x-large" color="blue">mdi-link</v-icon>
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
                @click.stop="toggleCollapse(card)"
              ></v-btn>
            </v-card-title>
            <v-card-text class="pa-3 pb-2">
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
              <div v-if="card.socialMetadata.media_urls && card.socialMetadata.media_urls.length > 0" class="twitter-media">
                <v-img
                  v-for="(mediaUrl, idx) in card.socialMetadata.media_urls.slice(0, 4)"
                  :key="idx"
                  :src="mediaUrl"
                  :max-height="card.socialMetadata.media_urls.length === 1 ? 400 : 200"
                  cover
                  class="twitter-media-image"
                />
              </div>

              <!-- Tweet Metadata Expansion -->
              <v-expansion-panels variant="accordion" flat>
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
            <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
          </v-card-actions>
          </template>
        </v-card>

        <!-- Image Card -->
        <v-card
          v-if="card.type === 'image'"
          :width="card.collapsed ? 160 : (card.width || 600)"
          class="card-item image-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="grey-darken-2" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">IMAGE</span>
              </v-chip>
            </div>
            <v-img
              v-if="card.imageUrl"
              :src="card.imageUrl"
              height="160"
              width="160"
              cover
              style="border: 3px solid #757575;"
            ></v-img>
            <div v-else class="collapsed-icon-container" style="border: 3px solid #757575; background: #F5F5F5;">
              <v-icon size="x-large" color="grey-darken-2">mdi-image</v-icon>
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
                @click.stop="toggleCollapse(card)"
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
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Video Card -->
        <v-card
          v-if="card.type === 'video'"
          :width="card.collapsed ? 160 : (card.width || 640)"
          class="card-item video-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="red-darken-1" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">VIDEO</span>
              </v-chip>
            </div>
            <div class="collapsed-icon-container" style="border: 3px solid #E53935; background: #FFEBEE;">
              <v-icon size="x-large" color="red-darken-1">mdi-video</v-icon>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-red-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-video</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Video" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @click.stop="toggleCollapse(card)"></v-btn>
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
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Audio Card -->
        <v-card
          v-if="card.type === 'audio'"
          :width="card.collapsed ? 160 : (card.width || 500)"
          class="card-item audio-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="purple-darken-1" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">AUDIO</span>
              </v-chip>
            </div>
            <div class="collapsed-icon-container" style="border: 3px solid #8E24AA; background: #F3E5F5;">
              <v-icon size="x-large" color="purple-darken-1">mdi-music-note</v-icon>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-purple-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-music-note</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Audio" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @click.stop="toggleCollapse(card)"></v-btn>
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
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- HTML Card -->
        <v-card
          v-if="card.type === 'html'"
          :width="card.collapsed ? 160 : (card.width || 600)"
          class="card-item html-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="orange-darken-1" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">HTML</span>
              </v-chip>
            </div>
            <div class="collapsed-icon-container" style="border: 3px solid #F57C00; background: #FFF3E0;">
              <v-icon size="x-large" color="orange-darken-1">mdi-code-tags</v-icon>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-orange-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-code-tags</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="HTML" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @click.stop="toggleCollapse(card)"></v-btn>
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
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Code Card -->
        <v-card
          v-if="card.type === 'code'"
          :width="card.collapsed ? 160 : (card.width || 700)"
          class="card-item code-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="green-darken-1" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">CODE</span>
              </v-chip>
            </div>
            <div class="collapsed-icon-container" style="border: 3px solid #43A047; background: #E8F5E9;">
              <v-icon size="x-large" color="green-darken-1">mdi-code-braces</v-icon>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-green-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-code-braces</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Code Snippet" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-select v-model="card.codeLanguage" :items="['javascript', 'python', 'html', 'css', 'json', 'bash', 'sql']" variant="outlined" density="compact" hide-details class="ms-2" style="max-width: 120px;" @click.stop></v-select>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @click.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.codeContent" variant="outlined" label="Code" auto-grow rows="12" hide-details placeholder="// Paste code here..." font-family="monospace" @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>

        <!-- Markdown Card -->
        <v-card
          v-if="card.type === 'markdown'"
          :width="card.collapsed ? 160 : (card.width || 600)"
          class="card-item markdown-card"
          elevation="2"
        >
          <!-- Collapsed State -->
          <div v-if="card.collapsed" @click.stop="toggleCollapse(card)" style="cursor: pointer; position: relative;">
            <div class="collapsed-badge">
              <v-chip size="x-small" color="indigo-darken-1" variant="flat">
                <span style="font-weight: bold; color: white; font-size: 0.7rem;">MARKDOWN</span>
              </v-chip>
            </div>
            <div class="collapsed-icon-container" style="border: 3px solid #3949AB; background: #E8EAF6;">
              <v-icon size="x-large" color="indigo-darken-1">mdi-language-markdown</v-icon>
            </div>
          </div>

          <!-- Expanded State -->
          <template v-else>
            <v-card-title class="pa-2 d-flex align-center bg-indigo-lighten-5" @dblclick.stop="toggleCollapse(card)" style="cursor: pointer;">
              <v-icon size="small" class="me-2">mdi-language-markdown</v-icon>
              <v-text-field v-model="card.title" variant="plain" density="compact" hide-details placeholder="Markdown" class="text-caption editable-title" @focus="activeCardId = card.id" @click.stop></v-text-field>
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-chevron-up" variant="text" @click.stop="toggleCollapse(card)"></v-btn>
            </v-card-title>
            <div>
              <v-card-text class="pa-3">
                <v-textarea v-model="card.markdownContent" variant="outlined" label="Markdown" auto-grow rows="10" hide-details placeholder="# Paste markdown here..." @focus="activeCardId = card.id"></v-textarea>
              </v-card-text>
            </div>
            <v-card-actions class="pa-2 pt-0">
              <v-spacer></v-spacer>
              <v-btn size="x-small" icon="mdi-delete" variant="text" @click="deleteCard(card.id)"></v-btn>
            </v-card-actions>
          </template>
        </v-card>
      </div>
    </div>

    <!-- Status Bar -->
    <v-footer app height="32" class="bg-grey-lighten-4 border-t">
      <span class="text-caption text-grey">
        {{ cards.length }} item{{ cards.length !== 1 ? 's' : '' }} on board
        <span v-if="saving" class="ms-4 text-primary">
          <v-icon size="x-small" class="me-1">mdi-loading mdi-spin</v-icon>
          Saving...
        </span>
        <span v-else-if="lastSaved" class="ms-4">
          Last saved: {{ formatTime(lastSaved) }}
        </span>
        <span v-if="!identifier" class="ms-4 text-warning">
          (Local only - add ?episode=0000 to URL to save whiteboard)
        </span>
      </span>
    </v-footer>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useStandardNotification, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { fetchJson } from '@/utils/apiHelpers'

const { notifyUserStandard } = useStandardNotification()
const route = useRoute()

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

// Drag state
const dragging = ref(false)
const dragCard = ref(null)
const dragOffset = ref({ x: 0, y: 0 })

// Card ID counter
let nextId = 1
let saveTimeout = null

// Load saved whiteboard on mount
onMounted(async () => {
  await loadBoard()
  canvas.value?.focus()
})

// Auto-save on unmount
onUnmounted(() => {
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

// Add text card
function addTextCard(x = null, y = null) {
  const rect = canvas.value?.getBoundingClientRect()
  cards.value.push({
    id: nextId++,
    type: 'text',
    content: '',
    title: '',
    x: x ?? (rect ? rect.width / 2 - 250 : 100),
    y: y ?? (rect ? rect.height / 2 - 100 : 100),
    width: 500,
    collapsed: false
  })
}

// Add link card
function addLinkCard() {
  const rect = canvas.value?.getBoundingClientRect()
  cards.value.push({
    id: nextId++,
    type: 'link',
    url: '',
    notes: '',
    title: '',
    x: rect ? rect.width / 2 - 250 : 100,
    y: rect ? rect.height / 2 - 100 : 100,
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
}

// Handle canvas click - just focus (don't spawn new cards)
function handleCanvasClick(event) {
  if (event.target === canvas.value) {
    canvas.value?.focus()
    activeCardId.value = null
  }
}

// Handle paste
function handlePaste(event) {
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
  } else if (event.key === 'Delete' && activeCardId.value) {
    event.preventDefault()
    deleteCard(activeCardId.value)
  }
}

// Start dragging
function startDrag(event, card) {
  // Don't drag if clicking on input fields
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
    return
  }

  dragging.value = true
  dragCard.value = card
  activeCardId.value = card.id

  const rect = event.currentTarget.getBoundingClientRect()
  dragOffset.value = {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

// Drag
function onDrag(event) {
  if (!dragging.value || !dragCard.value) return

  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return

  dragCard.value.x = event.clientX - rect.left - dragOffset.value.x
  dragCard.value.y = event.clientY - rect.top - dragOffset.value.y
}

// Stop dragging
function stopDrag() {
  dragging.value = false
  dragCard.value = null
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// Delete card
function deleteCard(id) {
  cards.value = cards.value.filter(c => c.id !== id)
  if (activeCardId.value === id) {
    activeCardId.value = null
  }
}

// Clear all
function clearAll() {
  if (confirm('Clear all items from the board?')) {
    cards.value = []
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
      // Link preview fields
      preview_title: card.previewTitle || null,
      preview_description: card.previewDescription || null,
      preview_image: card.previewImage || null,
      preview_domain: card.previewDomain || null,
      preview_favicon: card.previewFavicon || null,
      // Social media metadata
      social_metadata: card.socialMetadata || null
    }))

    const response = await fetchJson(`/api/whiteboard/${currentEpisode.value}/save`, {
      method: 'POST',
      body: JSON.stringify({ items })
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
        collapsed: false
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
      }

      return card
    })

  } catch (error) {
    console.error('Failed to load whiteboard:', error)
    notifyUserStandard('Failed to load whiteboard', NOTIFICATION_COLORS.ERROR, 3000)
  }
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
  height: 100vh;
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
  overflow: auto;
  outline: none;
  cursor: crosshair;
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

/* Episode warning - compact height */
.episode-warning {
  min-height: 0 !important;
  max-height: 3em !important;
  padding: 0.2em 0 !important;
  display: flex !important;
  align-items: center !important;
  overflow: hidden !important;
}

.episode-warning .v-alert__content {
  padding: 0 !important;
  margin: 0 !important;
  width: 100%;
}

.episode-warning .v-alert__prepend {
  display: none !important;
}

.episode-warning .v-alert__border {
  display: none !important;
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2px;
  background: rgba(0, 0, 0, 0.08);
}

.twitter-media-image {
  border-radius: 0;
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
</style>
