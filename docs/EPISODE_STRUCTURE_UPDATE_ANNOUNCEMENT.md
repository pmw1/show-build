# Episode Directory Structure Update
## What Changed and Why It Matters

**Date**: October 14, 2025
**Status**: ✅ Implemented and Active
**Affected**: All new episodes created after this date

---

## What Happened?

We've standardized how Show-Build organizes episode files on disk. From now on, every new episode will automatically have the same, predictable folder structure.

Think of it like this: instead of everyone organizing their desk differently, we now have a company-wide filing system. Everything has its place, and everyone knows where to find things.

---

## Why Did We Do This?

### The Problem Before

- **Inconsistent organization**: Different episodes had different folder structures
- **Manual work**: Someone had to create folders by hand for each episode
- **Hard to find things**: "Was that teaser in `assets/` or `media/` or `videos/`?"
- **Two systems fighting**: Files lived in both Syncthing (local) and Google Drive, but they didn't match
- **No automation**: Couldn't build tools to help because structure was unpredictable

### The Solution Now

- **One way to organize**: Every episode folder looks the same
- **Automatic creation**: Show-Build creates the structure when you make a new episode
- **Easy to find**: Always know where files go
- **Single source of truth**: Local Syncthing folder (`/mnt/sync/disaffected/episodes/`) is official
- **Ready for automation**: Consistent structure enables future features (thumbnail generation, script export, etc.)

---

## The New Structure (What You'll See)

When you create a new episode, Show-Build automatically creates these folders:

```
📁 0244/  (your episode number)
│
├── 📁 projects/          ← Production work files
│   ├── 📁 teasers/       (After Effects teaser projects + source files)
│   └── 📁 graphics/      (Other AE projects like intros, bumpers)
│
├── 📁 captures/          ← Raw vMix recordings
│   (BLOCK-A.mov, BLOCK-B.mov, BREAK-1.mov)
│
├── 📁 thumbnails/        ← Master artwork files
│   (master-16x9.psd, master-square.psd)
│
├── 📁 assets/            ← Final media used in the show
│   ├── 📁 video/         (Rendered clips, teasers, packages)
│   ├── 📁 images/        (Photos, screenshots, graphics)
│   ├── 📁 audio/         (Sound effects, music beds)
│   └── 📁 graphics/      (Lower thirds, bugs, overlays)
│
├── 📁 rundown/           ← Show rundown organization
│   └── 📁 media-list/    (vMix playlist symlinks)
│
├── 📁 scripts/           ← Generated scripts
│   ├── 📁 versions/      (Timestamped script versions)
│   └── 📁 current/       (Symlinks to latest version)
│
└── 📁 exports/           ← Final distribution files
    (Full episode, audio, subtitles, thumbnails for upload)
```

---

## Key Concepts to Understand

### 1. **Projects vs Assets** (The Most Important Distinction)

**Projects** = Work files you use to CREATE content
- Example: After Effects project file for a teaser
- Example: Source footage used in that teaser
- Location: `projects/teasers/0244-teaser-sarahsmith/`

**Assets** = Final outputs you USE IN THE SHOW
- Example: The rendered teaser video (ready for vMix)
- Example: Exported graphic PNG file
- Location: `assets/video/050-sarah-teaser.mp4`

**Why it matters**: You can delete project files after archiving to save space, but you NEED assets to re-air the show.

### 2. **Captures vs Exports**

**Captures** = Raw recordings straight from vMix
- BLOCK-A.mov, BLOCK-B.mov (unedited, everything recorded)
- BLOCK-B2.mov (if recording was interrupted and restarted)

**Exports** = Edited, finalized content
- 0244-A.mp4 (edited Block A, ready to upload)
- 0244.mp4 (full episode)
- 0244.mp3 (audio-only version)
- 0244.srt (subtitles)

### 3. **Scripts Are Generated, Not Written Here**

The `scripts/` folder contains auto-generated scripts from the database:
- Host hardcopy (PDF for printed script)
- Host teleprompter (HTML for on-screen)
- Director script (HTML with technical cues)
- Media list (text file of all assets)
- Flat text (plain text backup)
- Source markdown (original format)

**Important**: You edit scripts in Show-Build's ContentEditor, NOT by editing these files. These are exports only.

---

## What This Means For You

### If You're Creating New Episodes

**Nothing changed!** Just click "New Episode" like always. Show-Build now creates this structure automatically.

### If You're Working With Existing Episodes

**Old episodes are NOT changed.** They keep their current structure.

We're planning a "custodian script" (coming soon) that will help migrate old episodes to the new structure when you're ready.

### If You're Looking For Files

New episodes follow the guide above. Old episodes... good luck! (Just kidding, but seriously, this is why we needed the standard.)

---

## Common Questions

**Q: Do I have to manually create these folders?**
A: No! Show-Build creates them when you make a new episode.

**Q: What if I don't use all these folders?**
A: That's fine. They exist so tools know where to put things. Empty folders don't hurt anything.

**Q: Can I add my own folders?**
A: **NO.** Stick to the standard folders so automation features work. The only exception is the `preshow/` folder if you need temporary working space.

**Q: What about Google Drive?**
A: Google Drive will MIRROR the local structure. Think of it as a backup/archive copy. The Syncthing folder (`/mnt/sync/disaffected/episodes/`) is the official source.

**Q: Why so many folders?**
A: Each folder has a specific purpose. This prevents the "where does this go?" problem and makes automation possible.

**Q: What's a symlink? (rundown/media-list/ has them)**
A: A symlink is like a shortcut. It points to the real file elsewhere. vMix can use symlinks in playlists, which means we don't duplicate files—we just create organized pointers.

---

## Technical Details (For Developers)

- **Blueprint Template Updated**: Default "Sunday Show" template now creates canonical structure
- **Database Table**: `blueprint_nodes` stores the structure definition
- **Template ID**: 1 (Sunday Show - default template)
- **Total Structure**: 7 root folders, 9 subfolders = 16 total directories
- **Metadata**: Template marked with `canonical_structure: true` flag
- **Documentation**: See `docs/EPISODE_DIRECTORY_STANDARD.md` for complete specification

---

## What's Next?

Now that we have a standard structure, we can build:

1. **Custodian Script** - Validates existing episodes, fixes naming issues, migrates old episodes
2. **Thumbnail Generator** - Auto-creates YouTube/podcast thumbnails from master PSD
3. **Script Exporter** - Generates all 6 script formats automatically
4. **Media List Builder** - Creates vMix playlists with proper symlinks
5. **Archive Manager** - Moves old episodes to Google Drive following the same structure

---

## Need Help?

- **Read the spec**: `docs/EPISODE_DIRECTORY_STANDARD.md` (complete technical reference)
- **Ask questions**: This is new for everyone, so speak up if confused
- **Report issues**: If Show-Build creates the wrong structure, that's a bug—let us know

---

**Bottom Line**: Every new episode now has the same organized folder structure, created automatically. This makes everyone's life easier and enables future automation features. Old episodes stay as-is until we migrate them later.

---

*Generated: 2025-10-14*
*Specification: EPISODE_DIRECTORY_STANDARD.md v1.0*
*Implementation: Blueprint Template Update*
