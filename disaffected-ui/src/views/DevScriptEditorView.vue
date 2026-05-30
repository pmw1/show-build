<!--
  Dev harness for the migration ScriptEditor (Phase 4 first browser render).
  Route: /dev/script-editor  (dev-only; not linked from the app nav).

  Mounts the TipTap ScriptEditor with sample script content and shows the live
  serialized markdown alongside it, so the markdown<->doc round-trip and cue
  NodeView rendering can be eyeballed in a real browser, in isolation, before
  wiring into the 9,900-line ContentEditor.
-->
<template>
  <div class="dev-harness">
    <div class="dev-bar">
      <strong>ScriptEditor dev harness</strong>
      <span class="hint">edit on the left — serialized markdown updates on the right</span>
      <button @click="loadSample('mixed')">mixed</button>
      <button @click="loadSample('cues')">cues</button>
      <button @click="loadSample('bare')">bare markdown</button>
    </div>
    <div class="dev-cols">
      <div class="dev-col">
        <div class="dev-label">Editor (ProseMirror)</div>
        <script-editor
          :key="harnessKey"
          v-model:script-content="content"
        />
      </div>
      <div class="dev-col">
        <div class="dev-label">Serialized markdown (saved form)</div>
        <pre class="dev-md">{{ content }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import ScriptEditor from '@/components/content-editor/ScriptEditor.vue';

const SAMPLES = {
  mixed: [
    '<p class="josh">Welcome back to the show.</p>',
    '<p class="scott bullet">A bulleted line from Scott</p>',
    '<!-- Begin Cue -->',
    '[Type: FSQ]',
    '[AssetID: abc123]',
    '[Slug: a-quote]',
    '[Quote: "The words that matter"]',
    '[Attribution: Someone Notable]',
    '<!-- End Cue -->',
    '<p class="josh">And we are back.</p>',
  ].join('\n\n'),
  cues: [
    '<!-- Begin Cue -->',
    '[Type: GFX]',
    '[Slug: pic]',
    '[MediaURL: ../assets/graphics/pic.png]',
    '<img src="../assets/graphics/pic.png" width="200" />',
    '<!-- End Cue -->',
    '<!-- Begin Cue -->',
    '[Type: SOT]',
    '[Slug: clip-1]',
    '[Duration: 00:00:12]',
    '<!-- End Cue -->',
  ].join('\n\n'),
  bare: '## Notes\nPlain markdown with no paragraph tags.\n\n## Script\nThis text must survive the round-trip.',
};

export default {
  name: 'DevScriptEditorView',
  components: { ScriptEditor },
  setup() {
    const content = ref(SAMPLES.mixed);
    const harnessKey = ref(0);
    const loadSample = (name) => {
      content.value = SAMPLES[name];
      harnessKey.value += 1; // force a fresh editor mount with the new content
    };
    return { content, harnessKey, loadSample };
  },
};
</script>

<style scoped>
.dev-harness { height: 100vh; display: flex; flex-direction: column; font-family: system-ui, sans-serif; }
.dev-bar { padding: 8px 12px; background: #1e1e2e; color: #cdd6f4; display: flex; gap: 12px; align-items: center; }
.dev-bar .hint { color: #9399b2; font-size: 12px; }
.dev-bar button { background: #45475a; color: #cdd6f4; border: 0; padding: 4px 10px; border-radius: 4px; cursor: pointer; }
.dev-cols { flex: 1; display: flex; min-height: 0; }
.dev-col { flex: 1; display: flex; flex-direction: column; border-right: 1px solid #ccc; min-width: 0; }
.dev-label { padding: 6px 12px; background: #eee; font-size: 12px; font-weight: 600; }
.dev-md { flex: 1; margin: 0; padding: 12px; overflow: auto; background: #faf8f5; font-size: 12px; white-space: pre-wrap; word-break: break-word; }
</style>
