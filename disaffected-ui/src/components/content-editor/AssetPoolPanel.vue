<template>
  <div class="asset-pool-panel">
    <div class="asset-pool-header">
      <router-link
        v-if="episodeNumber"
        :to="{ name: 'whiteboard', query: { episode: episodeNumber } }"
        class="jump-to-wb-link ml-auto"
      >[jump to whiteboard]</router-link>
    </div>

    <!-- Category Tabs -->
    <v-tabs
      v-model="activeTab"
      density="compact"
      show-arrows
      height="32"
      class="asset-pool-tabs"
    >
      <v-tab
        v-for="cat in categories"
        :key="cat.value"
        :value="cat.value"
        size="small"
        class="asset-pool-tab"
      >
        {{ cat.label }}
      </v-tab>
    </v-tabs>

    <!-- Search -->
    <div class="asset-pool-search-row">
      <v-icon size="small" color="grey">mdi-magnify</v-icon>
      <input
        v-model="searchQuery"
        placeholder="Search..."
        class="asset-pool-search-input"
      />
      <v-icon v-if="searchQuery" size="x-small" color="grey" class="search-clear" @click="searchQuery = ''">mdi-close</v-icon>
    </div>

    <!-- Items List -->
    <div class="asset-pool-items">
      <div v-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate size="24" width="2" color="primary" />
      </div>

      <!-- Whiteboard Tree View -->
      <template v-else-if="activeTab === 'whiteboard'">
        <div v-if="whiteboardTree.length === 0" class="text-center py-4">
          <p class="text-caption text-grey">No whiteboard items found</p>
        </div>
        <div v-else class="wb-tree">
          <template v-for="(node, nodeIdx) in filteredTree" :key="node.id">
            <!-- Parent node -->
            <div
              v-if="node.isParent"
              class="wb-parent-node"
              :class="{ 'drop-into': dropTarget && dropTarget.parentId === node.id && dropTarget.type === 'into' }"
              draggable="true"
              @dragstart="onDragStart($event, 'top', nodeIdx, null, node)"
              @dragover.prevent="onParentDragOver($event, node)"
              @dragleave="onDragLeave"
              @drop="onDropIntoParent($event, node)"
              @dragend="onDragEnd"
              @click="toggleParentExpand(node.id)"
            >
              <v-icon size="x-small" class="drag-handle mr-1">mdi-drag-vertical</v-icon>
              <v-icon size="x-small" class="mr-1">
                {{ expandedParents[node.id] ? 'mdi-chevron-down' : 'mdi-chevron-right' }}
              </v-icon>
              <span class="wb-type-badge wb-parent-badge" :style="{ background: parentBadgeBg(node), color: parentBadgeColor(node) }">
                <v-icon size="x-small" class="wb-badge-icon">{{ parentBadgeIcon(node) }}</v-icon>
                {{ parentBadgeLabel(node) }}
              </span>
              <span class="wb-parent-title">{{ node.title || 'Untitled Group' }}</span>
              <v-chip size="x-small" variant="tonal" color="grey" class="ml-auto wb-count-chip">
                {{ node.children.length }}
              </v-chip>
            </div>
            <!-- Children of parent -->
            <template v-if="node.isParent && expandedParents[node.id]">
              <div
                v-for="(child, childIdx) in node.children"
                :key="child.id"
                class="wb-child-node"
                :class="{ 'drop-into': dropTarget && dropTarget.parentId === node.id && dropTarget.type === 'into' }"
                draggable="true"
                @dragstart="onDragStart($event, 'child', childIdx, node.id, child)"
                @dragover.prevent="onChildDragOver($event, node)"
                @dragleave="onDragLeave"
                @drop="onDropIntoParent($event, node)"
                @dragend="onDragEnd"
              >
                <v-icon size="x-small" class="drag-handle mr-1">mdi-drag-vertical</v-icon>
                <span class="wb-type-badge" :style="{ background: resolveBadgeBg(child), color: resolveBadgeFg(child) }">
                  <v-icon size="x-small" class="wb-badge-icon">{{ resolveBadgeIcon(child) }}</v-icon>
                  {{ resolveBadgeLabel(child) }}
                </span>
                <span class="wb-child-title" :title="child.title">{{ child.title }}</span>
              </div>
            </template>
            <!-- Top-level non-parent (orphan) -->
            <div
              v-if="!node.isParent"
              class="wb-orphan-node"
              :class="{ 'drag-over-reorder': dropTarget && dropTarget.orphanIdx === nodeIdx && dropTarget.type === 'reorder' }"
              draggable="true"
              @dragstart="onDragStart($event, 'top', nodeIdx, null, node)"
              @dragover.prevent="onOrphanDragOver($event, nodeIdx)"
              @dragleave="onDragLeave"
              @drop="onDropReorder($event, nodeIdx)"
              @dragend="onDragEnd"
            >
              <v-icon size="x-small" class="drag-handle mr-1">mdi-drag-vertical</v-icon>
              <span class="wb-type-badge" :style="{ background: resolveBadgeBg(node), color: resolveBadgeFg(node) }">
                <v-icon size="x-small" class="wb-badge-icon">{{ resolveBadgeIcon(node) }}</v-icon>
                {{ resolveBadgeLabel(node) }}
              </span>
              <span class="wb-child-title" :title="node.title">{{ node.title }}</span>
            </div>
          </template>
        </div>
      </template>

      <!-- Flat list for scheduled/other -->
      <template v-else>
        <div v-if="filteredItems.length === 0" class="text-center py-4">
          <p class="text-caption text-grey">No {{ activeCategoryLabel }} found</p>
          <v-btn
            size="x-small"
            variant="text"
            color="primary"
            @click="$emit('create-new-item', { itemType: activeTab })"
          >
            <v-icon left size="small">mdi-plus</v-icon>
            Create New
          </v-btn>
        </div>

        <v-list v-else density="compact" class="asset-pool-list pa-0">
          <v-list-item
            v-for="item in filteredItems"
            :key="item.asset_id || item.id"
            class="asset-pool-item"
          >
            <template v-slot:prepend>
              <v-btn
                icon
                size="x-small"
                variant="tonal"
                color="success"
                @click.stop="placeItem(item)"
                class="place-btn mr-2"
              >
                <v-icon size="small">mdi-plus</v-icon>
                <v-tooltip activator="parent" location="left">Add to rundown</v-tooltip>
              </v-btn>
            </template>

            <v-list-item-title class="text-body-2 asset-item-title">
              {{ item.title || item.slug || 'Untitled' }}
            </v-list-item-title>
            <v-list-item-subtitle class="text-caption asset-item-sub">
              <v-chip v-if="item._subtype" size="x-small" :color="item._subtype === 'ad' ? 'orange' : 'purple'" variant="tonal" class="mr-1" style="height: 14px; font-size: 0.55rem;">{{ item._subtype }}</v-chip>
              <span v-if="item.customer">{{ item.customer }} &bull; </span>
              <span v-if="item.duration">{{ item.duration }}</span>
            </v-list-item-subtitle>

            <template v-slot:append>
              <v-chip
                v-if="isPlaced(item)"
                size="x-small"
                color="info"
                variant="tonal"
                class="placed-chip"
              >
                Placed
              </v-chip>
            </template>
          </v-list-item>
        </v-list>
      </template>
    </div>
  </div>
</template>

<script>
import { fetchJson } from '@/utils/apiHelpers'

export default {
  name: 'AssetPoolPanel',
  props: {
    episodeNumber: {
      type: String,
      default: null
    },
    rundownItems: {
      type: Array,
      default: () => []
    },
    panelWidth: {
      type: String,
      default: 'wide'
    }
  },
  emits: ['place-item', 'create-new-item'],
  data() {
    return {
      activeTab: 'whiteboard',
      searchQuery: '',
      loading: false,
      categories: [
        { label: 'Whiteboard', value: 'whiteboard' },
        { label: 'Scheduled', value: 'scheduled' }
      ],
      itemsCache: {},
      currentItems: [],
      whiteboardTree: [],
      expandedParents: {},
      // Drag state
      dragSource: null,
      dropTarget: null,
      dragLeaveTimer: null
    }
  },
  computed: {
    activeCategoryLabel() {
      const cat = this.categories.find(c => c.value === this.activeTab)
      return cat ? cat.label : ''
    },
    filteredItems() {
      if (!this.searchQuery) return this.currentItems
      const q = this.searchQuery.toLowerCase()
      return this.currentItems.filter(item =>
        (item.title || '').toLowerCase().includes(q) ||
        (item.slug || '').toLowerCase().includes(q) ||
        (item.customer || '').toLowerCase().includes(q) ||
        (item.url || '').toLowerCase().includes(q)
      )
    },
    filteredTree() {
      if (!this.searchQuery) return this.whiteboardTree
      const q = this.searchQuery.toLowerCase()
      return this.whiteboardTree.map(node => {
        if (node.isParent) {
          const filteredChildren = node.children.filter(c =>
            (c.title || '').toLowerCase().includes(q) ||
            (c.url || '').toLowerCase().includes(q)
          )
          const parentMatches = (node.title || '').toLowerCase().includes(q)
          if (parentMatches || filteredChildren.length > 0) {
            return { ...node, children: parentMatches ? node.children : filteredChildren }
          }
          return null
        }
        if ((node.title || '').toLowerCase().includes(q) || (node.url || '').toLowerCase().includes(q)) {
          return node
        }
        return null
      }).filter(Boolean)
    },
    placedAssetIds() {
      const ids = new Set()
      for (const ri of this.rundownItems) {
        if (ri.library_asset_id) ids.add(ri.library_asset_id)
        if (ri.asset_id) ids.add(ri.asset_id)
      }
      return ids
    }
  },
  watch: {
    activeTab: {
      handler(newVal) {
        this.loadCategory(newVal)
      },
      immediate: true
    }
  },
  methods: {
    async loadCategory(category) {
      if (this.itemsCache[category]) {
        if (category === 'whiteboard') {
          this.whiteboardTree = this.itemsCache[category]
        } else {
          this.currentItems = this.itemsCache[category]
        }
        return
      }

      this.loading = true
      this.currentItems = []

      try {
        if (category === 'whiteboard') {
          await this.loadWhiteboardItems()
          return
        }

        if (category === 'scheduled') {
          const [adsData, promosData] = await Promise.all([
            fetchJson('/api/content-library/?item_type=ad&is_active=true&limit=100'),
            fetchJson('/api/content-library/?item_type=promo&is_active=true&limit=100')
          ])
          const ads = (adsData?.items || adsData || []).map(i => ({ ...i, _subtype: 'ad' }))
          const promos = (promosData?.items || promosData || []).map(i => ({ ...i, _subtype: 'promo' }))
          const items = [...ads, ...promos]
          this.itemsCache[category] = items
          this.currentItems = items
          return
        }

        const data = await fetchJson(`/api/content-library/?item_type=${category}&is_active=true&limit=100`)
        const items = data?.items || data || []
        this.itemsCache[category] = items
        this.currentItems = items
      } catch (error) {
        console.error(`Error loading ${category} items:`, error)
        this.currentItems = []
      } finally {
        this.loading = false
      }
    },

    async loadWhiteboardItems() {
      if (!this.episodeNumber) {
        this.whiteboardTree = []
        this.loading = false
        return
      }

      try {
        const data = await fetchJson(`/api/whiteboard/${this.episodeNumber}`)

        const wbItems = data?.items || []
        const nodeLinks = data?.node_links || []

        const itemMap = {}
        for (const item of wbItems) {
          itemMap[item.id] = item
        }

        const parentChildren = {}
        const childOfParent = new Set()

        for (const link of nodeLinks) {
          const srcIdx = link.source_index != null ? link.source_index : null
          const tgtIdx = link.target_index != null ? link.target_index : null
          const src = srcIdx != null ? wbItems[srcIdx] : itemMap[link.source_item_id]
          const tgt = tgtIdx != null ? wbItems[tgtIdx] : itemMap[link.target_item_id]
          if (!src || !tgt) continue

          if (src.item_type === 'parent') {
            if (!parentChildren[src.id]) parentChildren[src.id] = new Set()
            parentChildren[src.id].add(tgt.id)
            childOfParent.add(tgt.id)
          }
          if (tgt.item_type === 'parent') {
            if (!parentChildren[tgt.id]) parentChildren[tgt.id] = new Set()
            parentChildren[tgt.id].add(src.id)
            childOfParent.add(src.id)
          }
        }

        const tree = []

        for (const item of wbItems) {
          if (item.item_type === 'parent') {
            const childIds = parentChildren[item.id] || new Set()
            const children = [...childIds].map(cid => this.transformItem(itemMap[cid])).filter(Boolean)
            tree.push({
              id: item.id,
              isParent: true,
              title: item.title || 'Untitled Group',
              description: item.text_content,
              social_metadata: item.social_metadata,
              children: children
            })
            this.expandedParents[item.id] = true
          }
        }

        for (const item of wbItems) {
          if (item.item_type !== 'parent' && !childOfParent.has(item.id)) {
            tree.push(this.transformItem(item))
          }
        }

        this.whiteboardTree = tree
        this.itemsCache['whiteboard'] = tree
      } catch (error) {
        console.error('Error loading whiteboard items:', error)
        this.whiteboardTree = []
      } finally {
        this.loading = false
      }
    },

    transformItem(item) {
      if (!item) return null
      const sm = item.social_metadata || {}
      let title = item.title || sm.author_name || sm.title || ''

      if (item.item_type === 'link') {
        const handle = sm.author_handle ? `@${sm.author_handle}` : ''
        const text = sm.tweet_text || sm.post_text || ''
        title = title || text.substring(0, 60) || item.url || 'Link'
        if (handle && !title.includes(handle)) title = `${handle}: ${title}`
      } else if (item.item_type === 'text') {
        title = title || (item.text_content || '').substring(0, 60) || 'Text note'
      } else if (item.item_type === 'image') {
        title = title || item.caption || 'Image'
      } else if (item.item_type === 'video') {
        title = title || 'Video'
      } else if (item.item_type === 'audio') {
        title = title || 'Audio'
      } else if (item.item_type === 'code') {
        title = title || 'Code snippet'
      } else if (item.item_type === 'markdown') {
        title = title || 'Markdown'
      } else if (item.item_type === 'html') {
        title = title || 'HTML embed'
      } else {
        title = title || item.item_type || 'Item'
      }

      return {
        id: item.id,
        isParent: false,
        title: title,
        item_type: item.item_type,
        url: item.url,
        media_url: item.media_url,
        asset_id: item.media_asset_id,
        social_metadata: sm
      }
    },

    toggleParentExpand(parentId) {
      this.expandedParents[parentId] = !this.expandedParents[parentId]
    },

    // ── Drag and drop ──

    onDragStart(event, level, index, parentId, node) {
      this.dragSource = { level, index, parentId, node }
      event.dataTransfer.effectAllowed = 'move'
      event.target.classList.add('dragging')
    },

    onParentDragOver(event, parentNode) {
      if (!this.dragSource) return
      if (this.dragSource.node?.id === parentNode.id) return
      clearTimeout(this.dragLeaveTimer)
      event.dataTransfer.dropEffect = 'move'
      this.dropTarget = { type: 'into', parentId: parentNode.id }
    },

    onChildDragOver(event, parentNode) {
      if (!this.dragSource) return
      clearTimeout(this.dragLeaveTimer)
      event.dataTransfer.dropEffect = 'move'
      this.dropTarget = { type: 'into', parentId: parentNode.id }
    },

    onOrphanDragOver(event, nodeIdx) {
      if (!this.dragSource) return
      clearTimeout(this.dragLeaveTimer)
      event.dataTransfer.dropEffect = 'move'
      this.dropTarget = { type: 'reorder', orphanIdx: nodeIdx }
    },

    onDragLeave() {
      clearTimeout(this.dragLeaveTimer)
      this.dragLeaveTimer = setTimeout(() => {
        this.dropTarget = null
      }, 50)
    },

    onDragEnd(event) {
      event.target.classList.remove('dragging')
      this.dragSource = null
      this.dropTarget = null
    },

    async onDropIntoParent(event, parentNode) {
      event.preventDefault()
      const src = this.dragSource
      this.dropTarget = null
      if (!src || !src.node) return
      // Don't drop parent onto itself or a child already in this parent
      if (src.node.id === parentNode.id) return
      if (src.level === 'child' && src.parentId === parentNode.id) return

      const draggedItem = src.node
      const tree = this.whiteboardTree

      // Remove from source
      if (src.level === 'top') {
        const idx = tree.findIndex(n => n.id === draggedItem.id)
        if (idx >= 0) tree.splice(idx, 1)
      } else if (src.level === 'child') {
        const srcParent = tree.find(n => n.id === src.parentId)
        if (srcParent) {
          const idx = srcParent.children.findIndex(c => c.id === draggedItem.id)
          if (idx >= 0) srcParent.children.splice(idx, 1)
        }
      }

      // Add to target parent
      parentNode.children.push(draggedItem)
      this.expandedParents[parentNode.id] = true

      // Create node_link in backend
      await this.createNodeLink(draggedItem.id, parentNode.id)

      this.dragSource = null
      this.itemsCache['whiteboard'] = [...tree]
    },

    async onDropReorder(event, targetIdx) {
      event.preventDefault()
      const src = this.dragSource
      this.dropTarget = null
      if (!src) return

      const tree = this.whiteboardTree

      if (src.level === 'top' && src.index !== targetIdx) {
        const item = tree.splice(src.index, 1)[0]
        tree.splice(targetIdx > src.index ? targetIdx : targetIdx, 0, item)
      }

      this.dragSource = null
      this.itemsCache['whiteboard'] = [...tree]
    },

    async createNodeLink(sourceItemId, targetItemId) {
      if (!this.episodeNumber) return
      try {
        await fetchJson(`/api/whiteboard/${this.episodeNumber}/link-nodes`, {
          method: 'POST',
          body: JSON.stringify({
            source_item_id: sourceItemId,
            target_item_id: targetItemId
          })
        })
        console.log(`Created node link: ${sourceItemId} -> ${targetItemId}`)
      } catch (error) {
        console.error('Failed to create node link:', error)
      }
    },

    // ── Badge resolvers ──

    parentNodeColor(node) {
      const sm = node.social_metadata || {}
      return sm.parentNodeColor || '#6A1B9A'
    },

    parentBadgeLabel(node) {
      const sm = node.social_metadata || {}
      return sm.parentNodeType || 'Group'
    },

    parentBadgeIcon(node) {
      const sm = node.social_metadata || {}
      return sm.parentNodeIcon || 'mdi-folder-outline'
    },

    parentBadgeColor(node) {
      const sm = node.social_metadata || {}
      return sm.parentNodeColor || '#6A1B9A'
    },

    parentBadgeBg(node) {
      const color = this.parentBadgeColor(node)
      const r = parseInt(color.slice(1, 3), 16)
      const g = parseInt(color.slice(3, 5), 16)
      const b = parseInt(color.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, 0.12)`
    },

    whiteboardTypeColor(type) {
      const colors = { link: 'blue', text: 'grey', image: 'green', video: 'red', audio: 'orange', markdown: 'teal', code: 'indigo', html: 'deep-purple' }
      return colors[type] || 'grey'
    },

    whiteboardTypeBg(type) {
      const bgs = {
        link: '#E3F2FD', text: '#F5F5F5', image: '#E8F5E9', video: '#FFEBEE',
        audio: '#FFF3E0', markdown: '#E0F2F1', code: '#E8EAF6', html: '#F3E5F5'
      }
      return bgs[type] || '#F5F5F5'
    },

    whiteboardTypeFg(type) {
      const fgs = {
        link: '#1565C0', text: '#616161', image: '#2E7D32', video: '#C62828',
        audio: '#E65100', markdown: '#00695C', code: '#283593', html: '#6A1B9A'
      }
      return fgs[type] || '#616161'
    },

    whiteboardTypeIcon(type) {
      const icons = {
        link: 'mdi-link', text: 'mdi-text', image: 'mdi-image', video: 'mdi-video',
        audio: 'mdi-music-note', markdown: 'mdi-language-markdown',
        code: 'mdi-code-braces', html: 'mdi-language-html5'
      }
      return icons[type] || 'mdi-card-outline'
    },

    resolveBadgeLabel(item) {
      if (item.item_type !== 'link') return item.item_type

      const url = (item.url || '').toLowerCase()
      const sm = item.social_metadata || {}
      const platform = sm.platform || ''

      if (platform === 'x' || platform === 'twitter' || /\b(x\.com|twitter\.com)\b/.test(url)) {
        if (/\/status\/\d+/.test(url)) {
          if (sm.conversation_id && sm.tweet_id && sm.conversation_id !== sm.tweet_id) return 'X-Reply'
          return 'X-Post'
        }
        if (/\/lists\//.test(url)) return 'X-List'
        if (/\/spaces\//.test(url)) return 'X-Space'
        if (/\/(x|twitter)\.com\/[^/]+\/?$/.test(url) || /\/(x|twitter)\.com\/@[^/]+\/?$/.test(url)) return 'X-Profile'
        return 'X-Link'
      }
      if (/tiktok\.com/.test(url)) {
        if (/\/video\/\d+/.test(url)) return 'TikTok'
        if (/\/@[^/]+\/?$/.test(url)) return 'TikTok-Profile'
        return 'TikTok'
      }
      if (/youtube\.com|youtu\.be/.test(url)) {
        if (/\/watch\?|youtu\.be\//.test(url)) return 'YouTube'
        if (/\/shorts\//.test(url)) return 'YT-Short'
        if (/\/@|\/channel\/|\/c\//.test(url)) return 'YT-Channel'
        if (/\/playlist/.test(url)) return 'YT-Playlist'
        return 'YouTube'
      }
      if (/instagram\.com/.test(url)) {
        if (/\/p\//.test(url)) return 'IG-Post'
        if (/\/reel\//.test(url)) return 'IG-Reel'
        if (/\/stories\//.test(url)) return 'IG-Story'
        return 'Instagram'
      }
      if (/rumble\.com/.test(url)) return 'Rumble'
      if (/soundcloud\.com/.test(url)) return 'SoundCloud'
      if (/reddit\.com/.test(url)) {
        if (/\/comments\//.test(url)) return 'Reddit-Post'
        if (/\/r\/[^/]+\/?$/.test(url)) return 'Subreddit'
        return 'Reddit'
      }
      if (url) {
        try {
          const domain = new URL(url).hostname.replace('www.', '')
          return domain.split('.')[0]
        } catch { /* ignore */ }
      }
      return 'Link'
    },

    resolveBadgeIcon(item) {
      if (item.item_type !== 'link') return this.whiteboardTypeIcon(item.item_type)
      const label = this.resolveBadgeLabel(item)
      if (label.startsWith('X-')) return 'mdi-twitter'
      if (label.startsWith('TikTok')) return 'mdi-music-note-eighth'
      if (label.startsWith('YouTube') || label.startsWith('YT-')) return 'mdi-youtube'
      if (label.startsWith('IG-') || label === 'Instagram') return 'mdi-instagram'
      if (label === 'Rumble') return 'mdi-video'
      if (label === 'SoundCloud') return 'mdi-soundcloud'
      if (label.startsWith('Reddit') || label === 'Subreddit') return 'mdi-reddit'
      return 'mdi-link'
    },

    resolveBadgeBg(item) {
      const label = this.resolveBadgeLabel(item)
      if (label.startsWith('X-')) return '#E3F2FD'
      if (label.startsWith('TikTok')) return '#FCE4EC'
      if (label.startsWith('YouTube') || label.startsWith('YT-')) return '#FFEBEE'
      if (label.startsWith('IG-') || label === 'Instagram') return '#F3E5F5'
      if (label === 'Rumble') return '#E8F5E9'
      if (label === 'SoundCloud') return '#FFF3E0'
      if (label.startsWith('Reddit') || label === 'Subreddit') return '#FFF3E0'
      return this.whiteboardTypeBg(item.item_type)
    },

    resolveBadgeFg(item) {
      const label = this.resolveBadgeLabel(item)
      if (label.startsWith('X-')) return '#1565C0'
      if (label.startsWith('TikTok')) return '#C2185B'
      if (label.startsWith('YouTube') || label.startsWith('YT-')) return '#C62828'
      if (label.startsWith('IG-') || label === 'Instagram') return '#6A1B9A'
      if (label === 'Rumble') return '#2E7D32'
      if (label === 'SoundCloud') return '#E65100'
      if (label.startsWith('Reddit') || label === 'Subreddit') return '#E65100'
      return this.whiteboardTypeFg(item.item_type)
    },

    isPlaced(item) {
      return this.placedAssetIds.has(item.asset_id) || this.placedAssetIds.has(String(item.id))
    },

    placeItem(item) {
      this.$emit('place-item', { libraryItem: item })
    },

    refreshCategory(category) {
      delete this.itemsCache[category || this.activeTab]
      this.loadCategory(category || this.activeTab)
    }
  }
}
</script>

<style scoped>
.asset-pool-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.asset-pool-header {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.03);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.asset-pool-title {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: rgba(0, 0, 0, 0.5);
}

.jump-to-wb-link {
  font-size: 0.6rem;
  color: rgba(25, 118, 210, 0.7);
  text-decoration: none;
  white-space: nowrap;
}

.jump-to-wb-link:hover {
  color: #1976D2;
  text-decoration: underline;
}

.asset-pool-tabs {
  flex-shrink: 0;
}

.asset-pool-tab {
  font-size: 0.7rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.3px !important;
  min-width: 48px !important;
  padding: 0 8px !important;
}

.asset-pool-search-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.asset-pool-search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.75rem;
  padding: 2px 0;
  background: transparent;
  line-height: 1.2;
}

.search-clear {
  cursor: pointer;
  opacity: 0.5;
}

.search-clear:hover {
  opacity: 1;
}

.asset-pool-items {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* Whiteboard Tree */
.wb-tree {
  padding: 2px 0;
}

.wb-parent-node {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  cursor: pointer;
  background: #EDE7F6;
  border-bottom: 1px solid rgba(106, 27, 154, 0.12);
  user-select: none;
  transition: padding-left 0.15s ease, background 0.15s ease;
}

.wb-parent-node:hover {
  background: #D1C4E9;
}

.wb-parent-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.8);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.wb-count-chip {
  font-size: 0.55rem !important;
  height: 16px !important;
  flex-shrink: 0;
}

.wb-child-node {
  display: flex;
  align-items: center;
  padding: 4px 8px 4px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
  min-height: 28px;
  transition: padding-left 0.15s ease, background 0.15s ease;
}

.wb-child-node:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.wb-orphan-node {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  min-height: 28px;
  transition: padding-left 0.15s ease;
}

.wb-orphan-node:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.wb-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 1px 6px 1px 3px;
  border-radius: 3px;
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-right: 6px;
}

.wb-badge-icon {
  font-size: 11px !important;
  color: inherit !important;
}

.wb-parent-badge {
  margin-right: 6px;
  font-weight: 700;
}

.wb-child-title {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.7);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Drag and drop */
.drag-handle {
  cursor: grab;
  opacity: 0.3;
  flex-shrink: 0;
}

.wb-parent-node:hover .drag-handle,
.wb-child-node:hover .drag-handle,
.wb-orphan-node:hover .drag-handle {
  opacity: 0.7;
}

.dragging {
  opacity: 0.4;
}

/* Drop into parent: highlight the parent and all its children */
.drop-into {
  background: rgba(25, 118, 210, 0.12) !important;
  border-left: 3px solid #1976D2 !important;
  padding-left: 25px;
}

.wb-parent-node.drop-into {
  padding-left: 5px;
  background: rgba(25, 118, 210, 0.2) !important;
  border-left: 4px solid #1565C0 !important;
}

/* Reorder indicator for orphans */
.drag-over-reorder {
  border-top: 2px solid #1976D2 !important;
}

/* Flat list (scheduled) */
.asset-pool-list {
  background: transparent !important;
}

.asset-pool-item {
  min-height: 36px !important;
  padding: 2px 8px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.asset-pool-item:hover {
  background: rgba(var(--v-theme-primary), 0.06);
}

.asset-item-title {
  font-size: 0.8rem !important;
  font-weight: 500;
  line-height: 1.3;
}

.asset-item-sub {
  font-size: 0.65rem !important;
  opacity: 0.7;
}

.place-btn {
  width: 22px !important;
  height: 22px !important;
}

.placed-chip {
  font-size: 0.55rem !important;
  height: 16px !important;
}
</style>
