"""
Enhanced reorder endpoint that also renames files to match their new order.
This can be integrated into main.py to replace the existing reorder_rundown function.
"""

import os
import re
import yaml
import logging
from fastapi import HTTPException

async def reorder_rundown_with_rename(episode_number: str, payload: dict):
    """
    Reorder rundown items and rename files to match their new order.
    
    This function:
    1. Updates the order field in YAML frontmatter
    2. Renames files to match the new order (e.g., "10 intro.md", "20 segment.md")
    3. Preserves the slug portion of the filename
    """
    base_path = "/home/episodes"
    episode_path = os.path.join(base_path, episode_number, "rundown")
    
    if not os.path.isdir(episode_path):
        raise HTTPException(
            status_code=404, detail=f"Episode {episode_number} not found."
        )
    
    try:
        # First pass: Read all files and their content
        files_to_process = []
        for index, segment in enumerate(payload.get('segments', [])):
            filename = segment.get("filename")
            if not filename or not filename.endswith(".md"):
                raise HTTPException(
                    status_code=422, detail=f"Invalid or missing filename in segment {index}"
                )
            
            file_path = os.path.join(episode_path, filename)
            if not os.path.isfile(file_path):
                raise HTTPException(
                    status_code=404, detail=f"File {filename} not found."
                )
            
            # Read existing file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.startswith("---"):
                raise HTTPException(
                    status_code=422, detail=f"No YAML frontmatter in {filename}"
                )
            
            fm_end = content.find("\n---", 4)
            if fm_end == -1:
                raise HTTPException(
                    status_code=422, detail=f"Invalid YAML frontmatter in {filename}"
                )
            
            yaml_block = content[4:fm_end]
            body = content[fm_end + 4:]
            front_matter = yaml.safe_load(yaml_block) or {}
            
            # Extract slug from frontmatter or filename
            slug = front_matter.get("slug", "")
            if not slug:
                # Try to extract slug from filename (e.g., "10 my-slug.md" -> "my-slug")
                match = re.match(r'^\d+\s+(.+)\.md$', filename)
                if match:
                    slug = match.group(1)
                else:
                    # Remove .md and any leading numbers
                    slug = re.sub(r'^\d+\s*', '', filename.replace('.md', ''))
                    if not slug:
                        slug = f"item-{index + 1}"
            
            # Update order in frontmatter
            new_order = (index + 1) * 10
            front_matter["order"] = new_order
            
            # Generate new filename with updated order number
            new_filename = f"{new_order} {slug}.md"
            
            files_to_process.append({
                "old_path": file_path,
                "old_filename": filename,
                "new_filename": new_filename,
                "new_path": os.path.join(episode_path, new_filename),
                "front_matter": front_matter,
                "body": body,
                "order": new_order
            })
        
        # Second pass: Create a mapping to avoid naming conflicts
        # Use temporary names first
        temp_renames = []
        for file_info in files_to_process:
            # Use a UUID-like temp name to avoid any conflicts
            import uuid
            temp_name = f"_temp_{uuid.uuid4().hex[:8]}_{file_info['old_filename']}"
            temp_path = os.path.join(episode_path, temp_name)
            temp_renames.append({
                "old": file_info['old_path'],
                "temp": temp_path,
                "final": file_info['new_path'],
                "file_info": file_info
            })
        
        # Perform the renames in two stages to avoid conflicts
        # Stage 1: Rename all to temp names
        for rename_info in temp_renames:
            if os.path.exists(rename_info['old']):
                os.rename(rename_info['old'], rename_info['temp'])
        
        # Stage 2: Rename from temp to final names and update content
        for rename_info in temp_renames:
            file_info = rename_info['file_info']
            
            # Write updated content with new frontmatter
            new_yaml = yaml.safe_dump(file_info['front_matter'], sort_keys=False)
            new_content = f"---\n{new_yaml}---\n{file_info['body']}"
            
            # Write to final filename
            with open(rename_info['final'], "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Remove temp file if it still exists and is different from final
            if os.path.exists(rename_info['temp']) and rename_info['temp'] != rename_info['final']:
                os.remove(rename_info['temp'])
        
        # Log the changes
        logging.info(f"Reordered {len(files_to_process)} files in episode {episode_number}")
        for file_info in files_to_process:
            logging.info(f"  {file_info['old_filename']} -> {file_info['new_filename']} (order: {file_info['order']})")
        
        return {
            "status": "success",
            "message": f"Rundown for episode {episode_number} reordered with updated filenames",
            "files_renamed": len(files_to_process),
            "changes": [
                {
                    "old": f['old_filename'],
                    "new": f['new_filename'],
                    "order": f['order']
                }
                for f in files_to_process
            ]
        }
        
    except Exception as e:
        logging.error(f"Failed to reorder rundown: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reorder rundown: {str(e)}")


# Example of how to integrate this into main.py:
"""
# In main.py, replace the existing reorder_rundown function with:

from enhanced_reorder import reorder_rundown_with_rename

@app.post("/rundown/{episode_number}/reorder")
async def reorder_rundown(episode_number: str, payload: ReorderRequest):
    return await reorder_rundown_with_rename(episode_number, payload.dict())
"""