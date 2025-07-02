Stuff to do

Note to Copiolot: Please change the font style to strikethrough when the task is completed.

~~1. In the rundown folder of each episode there is a file called info.md which contains all of the information for that episode. The frontmatter looks like this:
---
type: full_show
airdate: 2025-06-29
episode_number: 229
title: Fuck New York
subtitle: Undecided Subtitle
duration: 01:00:00
guest: 
tags: 
slug: Fuck New York
status: production
---
I think the frontmatter portion of this markdown file can be used as a central source of truth for the episode information.  Some of the fields must be calculated: episode number, duration.  There could be a very breif overview of this data in the rundown editor with a button to "edit show details" or something like that~~

**COMPLETED**: Enhanced with inline editing - episode info is now prominently displayed at the top of the rundown editor with all fields directly editable (title, subtitle, duration, air date, guests, status, tags) and a save button for immediate updates without requiring a dialog.  




2. Editing the rundown items
I would like to be able to edit the rundown items in a more efficient way. But this comes with a whole bunch of issues that need to be addressed first:
  - The current obsidian vault uses a custom plugin that was created to insert custom "cue clock" code.  Many of these cues call on the director or software to role out elements (graphics, video/audio media)  When you are ready, I am going to show you the custom obhsidiant plugin and you can translate the logic. 