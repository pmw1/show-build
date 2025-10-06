<template>
  <v-card
    class="cue-card placeholder-cue-card"
    :class="{ 'selected': selected }"
    :style="{ borderColor: cueTypeColor }"
    variant="elevated"
    @click="$emit('select')"
  >
    <!-- Card Header -->
    <v-card-title class="cue-card-header" :style="headerStyle">
      <div class="cue-type-badge" :style="badgeStyle">
        {{ cueData.type }}
      </div>
      <div class="cue-title-text">
        {{ cueData.title }}
      </div>
      <v-spacer></v-spacer>
      <div class="cue-actions">
        <v-btn
          icon
          size="small"
          variant="text"
          @click.stop="$emit('edit')"
          class="action-btn"
        >
          <v-icon size="small">mdi-pencil</v-icon>
          <v-tooltip activator="parent" location="top">Edit Cue</v-tooltip>
        </v-btn>
        <v-btn
          icon
          size="small"
          variant="text"
          @click.stop="$emit('delete')"
          class="action-btn delete-btn"
        >
          <v-icon size="small">mdi-delete</v-icon>
          <v-tooltip activator="parent" location="top">Delete Cue</v-tooltip>
        </v-btn>
      </div>
    </v-card-title>

    <!-- Card Content -->
    <v-card-text class="cue-card-content">
      <!-- Placeholder Display -->
      <div class="placeholder-container">
        <div class="placeholder-icon-section">
          <v-icon size="48" :color="cueTypeColor" class="placeholder-icon">
            {{ getCueIcon(cueData.type) }}
          </v-icon>
        </div>

        <div class="placeholder-message">
          <div class="primary-message">
            {{ cueData.type }} / {{ cueData.slug || 'No Slug' }}
          </div>
          <div class="secondary-message">
            Display not yet implemented
          </div>
        </div>
      </div>

      <!-- Cue Information -->
      <div class="cue-info">
        <div v-if="cueData.slug" class="cue-slug">
          <v-icon size="small" class="info-icon">mdi-tag</v-icon>
          <span class="slug-text">{{ cueData.slug }}</span>
        </div>

        <div v-if="cueData.description" class="cue-description">
          <v-icon size="small" class="info-icon">mdi-text</v-icon>
          <span class="description-text">{{ cueData.description }}</span>
        </div>

        <div v-if="cueData.assetId" class="cue-asset-id">
          <v-icon size="small" class="info-icon">mdi-identifier</v-icon>
          <span class="asset-id-text">{{ cueData.assetId }}</span>
        </div>

        <div v-if="cueData.duration" class="cue-duration">
          <v-icon size="small" class="info-icon">mdi-timer</v-icon>
          <span class="duration-text">{{ cueData.duration }}</span>
        </div>

        <div v-if="cueData.mediaUrl" class="cue-media-url">
          <v-icon size="small" class="info-icon">mdi-link</v-icon>
          <span class="media-url-text">{{ truncateUrl(cueData.mediaUrl) }}</span>
        </div>
      </div>
    </v-card-text>

    <!-- Card Footer with Order Number -->
    <v-card-actions class="cue-card-footer">
      <div class="order-display">
        <v-icon size="small">mdi-numeric</v-icon>
        <span class="order-text">{{ orderNumber || 'No Order' }}</span>
      </div>
      <v-spacer></v-spacer>
      <v-chip size="small" variant="tonal" :color="cueTypeColor">
        {{ cueData.type }}
      </v-chip>
    </v-card-actions>
  </v-card>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../../utils/themeColorMap.js';

export default {
  name: 'PlaceholderCueCard',
  emits: ['select', 'edit', 'delete'],
  props: {
    cueData: {
      type: Object,
      required: true,
      default: () => ({})
    },
    selected: {
      type: Boolean,
      default: false
    },
    orderNumber: {
      type: [String, Number],
      default: null
    }
  },
  computed: {
    cueTypeColor() {
      if (!this.cueData.type) return 'grey';
      const colorName = getColorValue(this.cueData.type.toLowerCase());
      return resolveVuetifyColor(colorName);
    },

    cueTypeStyle() {
      const backgroundColor = this.cueTypeColor;
      return {
        backgroundColor: backgroundColor,
        color: 'white'
      };
    },

    headerStyle() {
      const backgroundColor = this.cueTypeColor;
      return {
        backgroundColor: backgroundColor,
        color: 'white'
      };
    },

    badgeStyle() {
      const baseColor = this.cueTypeColor;
      // Only lighten if we have a valid hex color string
      const lighterColor = (typeof baseColor === 'string' && baseColor.startsWith('#'))
        ? this.lightenColor(baseColor, 20)
        : baseColor;
      return {
        backgroundColor: lighterColor || '#666',
        color: 'white'
      };
    }
  },
  methods: {
    getCueIcon(cueType) {
      const iconMap = {
        'SOT': 'mdi-play-circle-outline',
        'VO': 'mdi-microphone',
        'NAT': 'mdi-volume-high',
        'PKG': 'mdi-package-variant',
        'FSQ': 'mdi-format-quote-close',
        'VOX': 'mdi-account-voice',
        'MUS': 'mdi-music',
        'LIVE': 'mdi-broadcast',
        'CG': 'mdi-text-box',
        'LOWER': 'mdi-text-box-outline',
        'TITLE': 'mdi-title',
        'CREDIT': 'mdi-account-credit-card',
        'BUMPER': 'mdi-movie-roll',
        'PROMO': 'mdi-bullhorn',
        'TEASE': 'mdi-eye',
        'BREAK': 'mdi-pause',
        'COMMERCIAL': 'mdi-currency-usd'
      };

      return iconMap[cueType?.toUpperCase()] || 'mdi-file-question-outline';
    },

    truncateUrl(url) {
      if (!url) return '';
      if (url.length <= 40) return url;

      const start = url.substring(0, 20);
      const end = url.substring(url.length - 17);
      return `${start}...${end}`;
    },

    lightenColor(color, percent) {
      // Convert hex to RGB
      let hex = color.replace('#', '');

      // Handle short hex
      if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
      }

      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);

      // Lighten each component
      const newR = Math.min(255, Math.round(r + (255 - r) * (percent / 100)));
      const newG = Math.min(255, Math.round(g + (255 - g) * (percent / 100)));
      const newB = Math.min(255, Math.round(b + (255 - b) * (percent / 100)));

      // Convert back to hex
      const toHex = (n) => {
        const hex = n.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      };

      return `#${toHex(newR)}${toHex(newG)}${toHex(newB)}`;
    }
  }
};
</script>

<style scoped>
.cue-card {
  margin: 8px 0;
  border: 4px solid;
  transition: all 0.2s ease;
  cursor: pointer;
  border-radius: 0 !important;
}

.cue-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cue-card.selected {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.placeholder-cue-card {
  max-width: 75%;
  width: 75%;
  margin-left: auto;
  margin-right: auto;
}

/* Header Styling */
.cue-card-header {
  padding: 0 16px 0 0 !important;
  display: flex;
  align-items: stretch;
  gap: 12px;
  font-family: Helvetica, Arial, sans-serif;
  min-height: 48px;
}

.cue-type-badge {
  padding: 2px 16px;
  border-radius: 0;
  font-weight: normal;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-top: 0;
  border-bottom: 0;
  border-left: 0;
  border-right: 4px solid white;
  display: flex;
  align-items: center;
  margin: 0;
}

.cue-title-text {
  font-weight: bold;
  font-size: 1.2rem;
  font-family: Helvetica, Arial, sans-serif;
  flex: 1;
  display: flex;
  align-items: center;
}

.cue-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.action-btn {
  opacity: 0.7;
  color: white;
}

.action-btn:hover {
  opacity: 1;
}

.delete-btn:hover {
  color: white;
}

/* Content Styling */
.cue-card-content {
  padding: 16px !important;
}

.placeholder-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 0;
  border: 2px dashed rgba(var(--v-theme-outline), 0.3);
  margin-bottom: 12px;
}

.placeholder-icon-section {
  flex-shrink: 0;
}

.placeholder-icon {
  opacity: 0.7;
}

.placeholder-message {
  flex: 1;
}

.primary-message {
  font-weight: 600;
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  margin-bottom: 4px;
}

.secondary-message {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-style: italic;
}

/* Info Styling */
.cue-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cue-slug,
.cue-description,
.cue-asset-id,
.cue-duration,
.cue-media-url {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.info-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.slug-text {
  font-weight: 500;
  color: rgb(var(--v-theme-primary));
}

.description-text {
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.4;
}

.asset-id-text {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.duration-text {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.media-url-text {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  word-break: break-all;
}

/* Footer Styling */
.cue-card-footer {
  padding: 8px 16px !important;
  background-color: rgba(var(--v-theme-surface-variant), 0.1);
  border-top: 1px solid rgba(var(--v-theme-outline), 0.1);
}

.order-display {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.order-text {
  font-weight: 500;
}

/* Responsive Design */
@media (max-width: 600px) {
  .cue-card-header {
    padding: 8px 12px !important;
  }

  .cue-card-content {
    padding: 12px !important;
  }

  .placeholder-container {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .primary-message {
    font-size: 0.9rem;
  }
}
</style>