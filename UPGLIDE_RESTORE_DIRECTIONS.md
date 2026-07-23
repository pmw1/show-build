# How to get back to the working up-glide state

**Written by:** prefect-claude-b4391e (a separate session), 2026-06-06
**For:** the session that's been grinding on the script-editor drag-and-drop tonight
**Source of truth:** I reconstructed this by reading the full session transcript
(`draganddrop.md`, 24,298 lines) + diffing the live `BlockDragHandle.js` against it.

---

## TL;DR — you are already there. Stop digging.

**The code in commit `b9f0279` (current HEAD, clean working tree) already IS the
"Good that is working" state.** The displacement, the float bar, the universal
bar size, the FLIP glide, and the production timings are all at the exact
configuration that was in place at the moment Kevin said "Good that is working."

If up-glide still looks wrong to you, the problem is **not** that you've drifted
from the good config — you're already on it. Re-read the "If it STILL pops"
section before touching the file. Do **not** rewrite the displacement scheme
again. That rewrite is what broke it the first time.

---

## What "the working state" actually was (the float-overlay moment)

From the transcript, Kevin confirmed working **once**, right after the
**float-overlay fix**, immediately before he asked: *"can we make the 'INSERT
HERE' drop bar maintain the height of the paragraph that it is dragging?"* —
which you then implemented and which he reverted ("a universal drop bar size was
better"). So the good state is **the float-overlay fix with the universal
(hardcoded 52px) bar**, BEFORE any per-target sizing.

The four load-bearing pieces of that state:

### 1. Symmetric displacement (THE one that matters)
Every block shifts, splitting evenly around the gap:
```js
if (b.index >= gi2) classes.push('pm-shift-down');   // at/below gap → down half
else                classes.push('pm-shift-up');     // above gap   → up half
```
Applied as a **decoration class** (survives ProseMirror's in-place patch so the
CSS transition fires). `pm-shift-down = translateY(+DRAG_SHIFT_PX/2)`,
`pm-shift-up = translateY(-DRAG_SHIFT_PX/2)`.

> **This is the original symmetric scheme.** The transcript's post-mortem (Kevin
> asked "We had the upglide working. What happened?") traced the regression to
> exactly this: when Kevin reported an up-pop, the scheme was rewritten from
> symmetric → **one-directional** (only blocks between source and gap shift one
> way). That rewrite introduced "freshly-entering block pops," and the FLIP-in
> seed fix for *that* froze Chrome. **The symmetric scheme is what showed
> fractional glides in BOTH directions in the console.** Do not reintroduce
> one-directional displacement.

### 2. Float-overlay drop bar (killed the reflow "pop")
The "INSERT HERE" bar is **two elements**:
- `.pm-drop-gap-anchor` — **zero vertical layout height**, sits in flow at the
  gap. Because it takes no space, moving it between gaps causes **no reflow** →
  no instant snap of surrounding text. (The old single 52px element shoved
  between slots = the pop.)
- `.pm-drop-gap` — the visible 52px dashed box, **absolutely positioned**,
  centered on the anchor via `translateY(-50%)`.

### 3. Universal bar size (NOT matched to target)
The visible box is a **fixed `height: 52px`**. Do **not** size it from the
dragged paragraph. Kevin explicitly reverted the match-target-height version:
*"a universal drop bar size was better."*

### 4. FLIP glide drives the ANCHOR, measured via `offsetTop`
The bar glides between gaps by FLIP-ing the **anchor** (the in-flow element that
actually relocates), not the absolute box:
```js
const gapEl = view.dom.querySelector('.pm-drop-gap-anchor');
const newY = gapEl.offsetTop;   // transform-immune; reading it does NOT stomp an in-flight tween
```
Never `transform:'none'` to measure (that stomps the running tween → bar snaps
every frame, never visibly glides). The box's own transform is reserved for the
`translateY(-50%)` centering — don't drive the tween on the box.

### Production timings
- `DRAG_ANIM_MS = 200` (displacement + FLIP-settle), mirrors RundownPanel's
  SortableJS `:animation="200"`.
- `DROP_GAP_TWEEN_MS = 150` (bar glide between gaps).
- `DRAG_SHIFT_PX = 64` → each side shifts 32px.

---

## Verify you're on it (paste-and-run)

```bash
cd /home/kevin/show-build-migration
F=disaffected-ui/src/components/content-editor/prosemirror/BlockDragHandle.js
git log --oneline -1                      # expect: b9f0279 ... drag-drop polish
git status --short "$F"                   # expect: EMPTY (clean)
grep -nE "b\.index >= gi2|pm-shift-(up|down)" "$F"   # expect symmetric scheme, lines ~249-250 & 527-528
grep -nE "pm-drop-gap-anchor|height: 52px|offsetTop" "$F"  # float anchor + 52px + offsetTop measure
grep -nE "DRAG_ANIM_MS = 200|DROP_GAP_TWEEN_MS = 150" "$F"  # timings
```
All five hits present → you are at the confirmed-good state. No edits needed.

If somehow the working tree is dirty with a half-finished experiment:
```bash
git checkout b9f0279 -- disaffected-ui/src/components/content-editor/prosemirror/BlockDragHandle.js
```
This restores the exact good file. Then `npm run lint -- --fix` and redeploy dev.

---

## If it STILL pops on UP after confirming the config (read before editing)

The transcript's own honest conclusion: it's possible the up-pop was **real even
at the "Good that is working" moment**, and that "Good that is working" only
covered the **down** direction (Kevin may have only tested down right then).
Under the symmetric scheme the data DID show fractional sweeps both ways
(`tf=y-3.19`, `tf=y-28.09` on UP), so the glide math fires — but a residual pop
on up can come from a block **freshly entering** the shifted set with no
starting transform to animate FROM (it jumps straight to the shifted position).

If that's what you're chasing, the transcript's identified *correct* fix is **NOT**
more CSS hacks on the decoration classes (those led to the Chrome freeze). It's
the **NodeView approach** — give each block a NodeView so the displacement is a
stable, owned DOM transform that FLIPs cleanly on enter, instead of a decoration
class re-applied to a node PM patches in place. That's a fresh, scoped task —
**do it in daylight, not at 2am**, and commit `b9f0279` first as the safe base
(it already is committed, so you're covered).

**Hard rules learned the expensive way tonight:**
- ❌ Do NOT rewrite symmetric → one-directional displacement again.
- ❌ Do NOT seed a FLIP-in transform imperatively on entering blocks (froze Chrome).
- ❌ Do NOT size the drop bar to the target paragraph (Kevin reverted it).
- ❌ Do NOT `transform:'none'` to measure the bar (stomps the tween).
- ✅ Per-block visual effects in this editor MUST be **decorations**, not
  imperative DOM writes — a drop/edit re-renders the `<p>` and wipes imperative
  class/style even with `!important`. (This is a known project gotcha.)

---

## Bottom line
`b9f0279` = the up-glide-working state. You already reverted back to it earlier
tonight (the symmetric-scheme restore). Nothing is lost. If up still isn't
perfect, that's the *original* unsolved up-enter pop — a NodeView job for a
rested session, not another round of decoration hacks.
