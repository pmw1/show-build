"""
Minimal enhancement to existing main.py compile endpoint.
Adds processing coordination without breaking existing functionality.
"""

# ADD THIS TO YOUR EXISTING main.py - just before the compile_script_async function

from minimal_integration import MinimalEpisode, get_processing_status

@app.get("/episodes/{episode_number}/processing-status")
async def check_processing_status(episode_number: str):
    """Check if episode is currently being processed - minimal coordination."""
    return get_processing_status(episode_number)

# MODIFY THE EXISTING compile_script_async function to add this at the beginning:
"""
async def compile_script_async(
    episode_id: str,
    output_format: str = "html",
    include_cues: bool = True,
    validate_only: bool = False,
    current_user: dict = Depends(get_current_user_or_key),
    db = Depends(get_db)
):
    # ADD THIS BLOCK AT THE START:
    try:
        # Prevent concurrent processing of same episode
        MinimalEpisode.mark_processing(episode_id, db)
    except HTTPException:
        raise  # Re-raise if already processing or episode not found
    
    try:
        # ... existing compilation logic ...
        
        # At the end of successful compilation:
        MinimalEpisode.clear_processing(episode_id)
        
    except Exception as e:
        # Clear lock on any error
        MinimalEpisode.clear_processing(episode_id)
        raise
"""