# Project Proposals

This file holds proposed additions, subtractions, and modifications to
this project. Each proposal is shaped via the /propose skill, which runs
an adaptive Q&A and conflict-checks the idea against the project's spec
files and locked principles.

**Statuses:** `draft` · `under-discussion` · `accepted` · `rejected` ·
`demoted` (to future-development.md) · `superseded`

**Lifecycle commands:** `/propose`, `/propose list`,
`/propose review <ID>`, `/propose accept <ID>`, `/propose reject <ID>`,
`/propose demote <ID>`, `/propose milestone`.

---

## P-001 — Content-Editor meta-panel tweaks (omnibus)

- **Status:** draft
- **Created:** 2026-05-30
- **Author:** kevin (session prefect-claude-bb8f4a)
- **Risk tags:** safe-additive
- **Milestone target:** — (small UI polish; no milestone)

### Problem
The right-side **MetadataPanel** ("meta panel") of the ContentEditor has
two small ergonomic issues:

1. In the always-on **Segment Info** block, the **slug** field sits above
   the **title** field. Title is the more important / more-often-read
   identifier and should come first.
2. The accordion sections below Segment Info open one-at-a-time in
   practice, and the two operator-action panels (**Asset Pool**,
   **Workflow Tools**) are buried mid-list, collapsed by default — so the
   operator must hunt and click before doing anything.

### Proposal
A bundle of small, low-risk meta-panel changes. Sub-items:

- [ ] **1. Swap title ↔ slug field order** in the Segment Info block.
  Currently rendered slug-then-title; render **title first, slug second**.
  Both are plain `v-text-field`s emitting `update-segment-field`; this is
  a two-line reorder.
  - `MetadataPanel.vue:75` (slug field) and `:76` (title field) — swap.

- [ ] **2. Open multiple accordion panels by default + reorder.**
  **Confirmed possible:** every accordion already uses
  `<v-expansion-panels v-model="expandedPanels" multiple>`
  (`MetadataPanel.vue:255,272,292,323,357`), so more than one panel *can*
  be open simultaneously. Therefore we take the "if possible" branch (the
  fallback of demoting them to plain sections is **not** needed):
  - **Default-open** Asset Pool (`assetpool`) and Workflow Tools
    (`assetgen`) in addition to the always-on Segment Info, by extending
    the `expandedPanels` default (`MetadataPanel.vue:750`,
    currently `ref(['segmentinfo'])`).
  - **Reorder** so **Workflow Tools is first**, directly under Segment
    Info, by moving `{ key: 'assetgen' }` to the top of `panelOrder`
    (`MetadataPanel.vue:751-757`). Resulting order:
    `assetgen` (Workflow Tools) → `assetpool` → `people` → `speaker` →
    `versions`.

- [ ] **3. Make the segment title editable inline in the script editor.**
  At the top of the (new visual) script editor, the segment title is
  rendered as a **read-only display div** — `class="segment-title-header"`,
  showing `item.title` or the placeholder "Enter a segment title"
  (`EditorPanel.vue:290-292`). Make it **editable in place** so the
  operator can rename the segment directly from the editor without going
  to the meta panel.
  - Convert the static div into an inline-editable field (e.g. an
    underlined `v-text-field` / contenteditable styled to match the
    current heading) bound to `item.title`.
  - On commit, call the **existing** `updateMetadata('title', value)`
    handler (`EditorPanel.vue:4262`), which emits `metadata-change` — the
    same path already used by the in-panel title editor
    (`EditorPanel.vue:999`) and wired up by ContentEditor at
    `@update-segment-field`/metadata handling (`ContentEditor.vue:251`).
    **No new event contract or save path needed.**
  - Keep the placeholder behavior: when title is empty or matches
    `^Segment-\d+$`, show "Enter a segment title" as placeholder.
  - This is the same `item.title` edited by sub-item 1's title field —
    the two stay in sync automatically since both write through
    `metadata-change` → the shared rundown item.

> **Note for implementer:** "Workflow Tools" is the panel whose
> `element.key === 'assetgen'` (label text "Workflow Tools",
> `MetadataPanel.vue:357,362`). Don't confuse it with the `assetgen`
> *backend* generation queue — here it's just the panel key.

### Why now
Operator is actively working in the content-editor and finds the current
field order and collapsed action-panels slow. Pure front-end polish, no
data-model or save-path impact, safe to land immediately.

### Layer & module impact
- **Layer:** UI only
- **Modules touched:**
  `disaffected-ui/src/components/content-editor/MetadataPanel.vue`
  (items 1–2),
  `disaffected-ui/src/components/content-editor/EditorPanel.vue`
  (item 3)
- **New modules:** none
- **Files likely changed:**
  - `MetadataPanel.vue` — template lines 75–76; script `expandedPanels`
    ~750 and `panelOrder` ~751-757
  - `EditorPanel.vue` — `segment-title-header` block (lines 290–292);
    reuses existing `updateMetadata('title', …)` at ~4262 (no new wiring)
- **Post-change action:** `cd disaffected-ui && npm run lint -- --fix`
  (mandatory per CLAUDE.md). No backend restart (no Python touched).

### Edge-out analysis (mandatory)
None. These are purely client-side layout/default-state changes in a Vue
component; nothing can or should run at the edge.

### Conflicts found
None detected against scanned spec files
(`CLAUDE.md`, `docs/EDITOR_PANEL_ARCHITECTURE.md`,
`docs/SAVE_RELOAD_SPEC.md`).

- The CLAUDE.md **MetadataPanel LLM-field highlighting** rules
  (§ "MetadataPanel LLM-Generated Field Highlighting") are **not**
  affected: the LLM-color scanner matches by input `.value` vs
  `item[field]` and queries all `.sidebar-field` descendants regardless of
  order, so swapping the title/slug rows or changing which panels are open
  does not break it. No per-field `:class` bindings are added (which the
  rules forbid).
- No save-ownership / debounce paths touched (`SAVE_RELOAD_SPEC.md`),
  since the fields still emit the same `update-segment-field` event.

### Settings vs. preferences impact
None. The default-open set and panel order are hard-coded component
defaults, not user-configurable knobs. (Possible future enhancement:
persist per-operator panel open-state — out of scope here.)

### Failure modes
Negligible. Worst case a panel renders open when its content is empty
(e.g. Asset Pool with no `episodeNumber` — already guarded by
`v-if="... && episodeNumber"`, so it simply won't render). No mid-show
data risk.

### Open questions
- [ ] Should the default-open set also include `people`/`speaker`, or keep
      it to just Segment Info + Workflow Tools + Asset Pool? (Current
      proposal: just the latter three.)
- [ ] Persist operator's manual open/close choices across reloads, or
      always reset to these defaults on item switch? (Current proposal:
      always reset to defaults — simplest.)

### Related
- Proposals: none
- Future-dev: none
- ICKB: search "editor cue rundown fix" → 0 hits; no prior art
- Spec sections: `CLAUDE.md` § "MetadataPanel LLM-Generated Field
  Highlighting"; `docs/EDITOR_PANEL_ARCHITECTURE.md`

### Q&A transcript
<details>
<summary>Verbatim Q&A from the /propose session</summary>

**Scope of session (user):** "until notified, we'll be talking about
updates within the content-editor."

**Item 1 (user):** "in the right side panel (also called the 'meta panel')
swap title field and swap field position."

**Item 2 (user):** "in the right side panel, in the accordion-style menu,
can more than one sub-item be opened by default? if so, default to asset
pool being open, and workflow tools being open. also move workflow tools
to top of accordion, just under segment info. If it is not possible to
have more than one of them open, then remove workflow tools and asset pool
and add them as normal sections just below segment info."

**Omnibus form (AskUserQuestion):** "One proposal, sub-items."

**Resolution (Claude, from code inspection):** The accordions already use
`multiple`, so multiple-open IS possible → take the "if so" branch; the
removal fallback is not needed.

**Item 3 (user, 2026-05-30):** "At the top of the editor, the new editor,
the title of the segment shows up, and I want that to be editable right in
the script editor."

**Resolution (Claude, from code inspection):** The top title is a
read-only `segment-title-header` div (`EditorPanel.vue:290-292`). Make it
inline-editable, wired to the existing `updateMetadata('title', …)`
(`:4262`) → `metadata-change` emit, which ContentEditor already handles.
No new contract.

</details>

---
