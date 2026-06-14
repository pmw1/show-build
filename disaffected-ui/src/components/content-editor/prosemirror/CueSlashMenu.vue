<!--
  Inline cue picker for the slash command. Rendered into a floating popup at the
  caret by the SlashCommand extension. Keyboard-first: ↑/↓ move, Enter/Tab pick,
  Esc closes; or keep typing after "/" to filter. Mouse hover/click also work.

  Each item carries the cue type; selecting it calls command({ type }), which the
  extension turns into an insertCue transaction at the caret.
-->
<template>
  <div class="cue-slash-menu" role="listbox">
    <div v-if="items.length === 0" class="cue-slash-empty">no matching cue</div>
    <button
      v-for="(item, i) in items"
      :key="item.type"
      class="cue-slash-item"
      :class="{ 'is-active': i === selectedIndex }"
      role="option"
      :aria-selected="i === selectedIndex"
      @mousemove="selectedIndex = i"
      @click="pick(i)"
    >
      <span class="cue-chip" :style="{ background: chipColor(item) }">{{ item.type }}</span>
      <span class="cue-name">{{ item.tooltip }}</span>
      <span class="cue-key">alt+{{ item.key }}</span>
    </button>
  </div>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '../../../utils/themeColorMap.js';

export default {
  name: 'CueSlashMenu',
  props: {
    items: { type: Array, required: true },
    command: { type: Function, required: true },
  },
  data() {
    return { selectedIndex: 0 };
  },
  watch: {
    items() {
      this.selectedIndex = 0;
    },
  },
  methods: {
    // #39: the slash-menu chip color must come from the SAME color registry as
    // the add-cue toolbar, the in-script cue card, and the insertion popup —
    // not the static hex that used to live on CUE_ITEMS (which diverged from
    // the registry, e.g. FSQ showed pale orange instead of lime). Fall back to
    // any item.color, then grey, if the type can't resolve.
    chipColor(item) {
      const name = item?.type ? getColorValue(item.type.toLowerCase()) : null;
      const resolved = name ? resolveVuetifyColor(name) : null;
      return resolved || item?.color || '#9e9e9e';
    },
    // Called by the extension's keydown handler (returns true if it consumed the key).
    onKeyDown(event) {
      if (event.key === 'ArrowUp') {
        this.selectedIndex = (this.selectedIndex + this.items.length - 1) % this.items.length;
        return true;
      }
      if (event.key === 'ArrowDown') {
        this.selectedIndex = (this.selectedIndex + 1) % this.items.length;
        return true;
      }
      if (event.key === 'Enter' || event.key === 'Tab') {
        this.pick(this.selectedIndex);
        return true;
      }
      return false;
    },
    pick(i) {
      const item = this.items[i];
      if (item) this.command({ type: item.type });
    },
  },
};
</script>

<style scoped>
.cue-slash-menu {
  background: #1e1e2e;
  color: #cdd6f4;
  border: 1px solid #45475a;
  border-radius: 8px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
  padding: 4px;
  min-width: 240px;
  max-height: 320px;
  overflow-y: auto;
  font-family: system-ui, sans-serif;
}
.cue-slash-empty { padding: 8px 10px; color: #9399b2; font-size: 13px; }
.cue-slash-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 6px 8px;
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  color: inherit;
}
.cue-slash-item.is-active { background: #313244; }
.cue-chip {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #11111b;
  padding: 2px 7px;
  border-radius: 4px;
  min-width: 42px;
  text-align: center;
}
.cue-name { flex: 1; font-size: 13px; }
.cue-key { font-size: 11px; color: #7f849c; }
</style>
