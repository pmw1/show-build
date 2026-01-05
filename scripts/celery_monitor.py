#!/usr/bin/env python3
"""
Celery FFmpeg Activity Monitor
Monitors SOT processing jobs and FFmpeg activity across working directories
Uses Docker exec to query database
"""

import curses
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Directories to monitor
WORKING_DIR = Path("/mnt/sync/shared_media/preproc/working")
EPISODES_DIR = Path("/mnt/sync/disaffected/episodes")

def get_active_jobs():
    """Get active SOT processing jobs from database via Docker"""
    try:
        result = subprocess.run([
            'docker', 'exec', 'show-build-postgres',
            'psql', '-U', 'showbuild', '-d', 'showbuild', '-t', '-A', '-F', '|',
            '-c', """
                SELECT temp_job_id, episode, slug, status, current_phase,
                       working_directory, updated_at
                FROM sot_processing_jobs
                WHERE status IN ('processing', 'pending', 'uploaded')
                ORDER BY updated_at DESC
            """
        ], capture_output=True, text=True, timeout=5)

        jobs = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 7:
                jobs.append({
                    'temp_job_id': parts[0],
                    'episode': parts[1] or 'N/A',
                    'slug': parts[2] or 'uploading',
                    'status': parts[3],
                    'phase': parts[4],
                    'working_dir': parts[5],
                    'updated_at': parts[6]
                })
        return jobs
    except Exception as e:
        return []

def clear_pipeline():
    """Clear all stuck/failed jobs from the pipeline"""
    try:
        # Mark all processing/pending jobs as failed
        result = subprocess.run([
            'docker', 'exec', 'show-build-postgres',
            'psql', '-U', 'showbuild', '-d', 'showbuild', '-t', '-A',
            '-c', """
                UPDATE sot_processing_jobs
                SET status = 'failed',
                    error_message = 'Manually cleared from monitor',
                    updated_at = NOW()
                WHERE status IN ('processing', 'pending', 'uploaded')
                RETURNING temp_job_id
            """
        ], capture_output=True, text=True, timeout=5)

        # Count cleared jobs
        cleared_count = len([line for line in result.stdout.strip().split('\n') if line])
        return cleared_count
    except Exception as e:
        return -1

def get_directory_files(dir_path):
    """Get list of files in directory with sizes"""
    try:
        path = Path(dir_path)
        if not path.exists():
            return []
        
        files = []
        for item in sorted(path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if item.is_file():
                size = item.stat().st_size
                size_mb = size / (1024 * 1024)
                files.append({
                    'name': item.name,
                    'size': size,
                    'size_mb': size_mb,
                    'mtime': item.stat().st_mtime
                })
        return files[:5]  # Top 5 most recent
    except Exception as e:
        return []

def get_ffmpeg_processes():
    """Get running FFmpeg processes from local and kairo"""
    ffmpeg_procs = []
    
    # Local FFmpeg processes
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        for line in result.stdout.split('\n'):
            if 'ffmpeg' in line.lower() and 'grep' not in line.lower():
                ffmpeg_procs.append(('LOCAL', line))
    except:
        pass
    
    # Kairo FFmpeg processes
    try:
        result = subprocess.run(
            ['ssh', 'kairo', 'ps aux'],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        for line in result.stdout.split('\n'):
            if 'ffmpeg' in line.lower() and 'grep' not in line.lower():
                ffmpeg_procs.append(('KAIRO', line))
    except:
        pass
    
    return ffmpeg_procs

def extract_ffmpeg_info(ps_line):
    """Extract useful info from ps line"""
    # Find the ffmpeg command part
    idx = ps_line.find('ffmpeg')
    if idx == -1:
        return ps_line[:60]
    
    cmd = ps_line[idx:]
    
    # Extract key parts: input file, output file, codec
    parts = []
    
    # Look for input file
    if ' -i ' in cmd:
        i_idx = cmd.find(' -i ') + 4
        end_idx = cmd.find(' -', i_idx)
        if end_idx != -1:
            input_file = cmd[i_idx:end_idx].strip()
            parts.append(f"IN:{Path(input_file).name[:15]}")
    
    # Look for output file (usually at end)
    cmd_parts = cmd.split()
    if len(cmd_parts) > 0:
        last_part = cmd_parts[-1]
        if '.' in last_part and '/' in last_part:
            parts.append(f"OUT:{Path(last_part).name[:15]}")
    
    # Look for codec
    if '-c:v' in cmd:
        codec_idx = cmd.find('-c:v') + 5
        end_idx = cmd.find(' ', codec_idx)
        if end_idx != -1:
            codec = cmd[codec_idx:end_idx].strip()
            parts.append(f"CODEC:{codec}")
    
    return ' | '.join(parts) if parts else cmd[:60]

def draw_monitor(stdscr):
    """Main ncurses drawing function"""
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(1000)

    # Setup colors
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_RED)

    # Status message tracking
    status_message = ""
    status_color = 0
    status_expire_time = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Title
        title = " CELERY FFMPEG MONITOR - Show-Build "
        try:
            stdscr.addstr(0, (width - len(title)) // 2, title, 
                         curses.color_pair(5) | curses.A_BOLD)
        except:
            pass
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            stdscr.addstr(0, width - len(timestamp) - 2, timestamp, curses.color_pair(4))
        except:
            pass
        
        # Get data
        jobs = get_active_jobs()
        ffmpeg_procs = get_ffmpeg_processes()
        
        # Column widths
        col1_width = 30
        col2_width = 45
        col3_width = max(width - col1_width - col2_width - 6, 20)
        
        # Headers
        y = 2
        try:
            stdscr.addstr(y, 1, "ACTIVE JOBS".ljust(col1_width), 
                         curses.color_pair(5) | curses.A_BOLD)
            stdscr.addstr(y, col1_width + 2, "WORKING DIR FILES".ljust(col2_width), 
                         curses.color_pair(5) | curses.A_BOLD)
            stdscr.addstr(y, col1_width + col2_width + 4, "FFMPEG ACTIVITY", 
                         curses.color_pair(5) | curses.A_BOLD)
        except:
            pass
        
        y += 1
        try:
            stdscr.addstr(y, 0, "─" * width)
        except:
            pass
        
        # Draw jobs and files
        y += 1
        max_display = min(len(jobs), (height - 7) // 4)
        
        for i, job in enumerate(jobs[:max_display]):
            if y >= height - 4:
                break
            
            # Status color
            color = curses.color_pair(1) if job['status'] == 'processing' else \
                    curses.color_pair(2) if job['status'] == 'pending' else \
                    curses.color_pair(4)
            
            # Column 1: Job info
            ep_slug = f"Ep{job['episode'][:4]}: {job['slug'][:18]}"
            status_phase = f"{job['status'][:8]}/{job['phase'][:10]}"
            job_id_short = job['temp_job_id'][-12:]
            
            try:
                stdscr.addstr(y, 1, ep_slug[:col1_width-1], color | curses.A_BOLD)
                stdscr.addstr(y+1, 1, status_phase[:col1_width-1], color)
                stdscr.addstr(y+2, 1, job_id_short[:col1_width-1], curses.color_pair(6))
            except:
                pass
            
            # Column 2: Working directory files
            working_path = f"/mnt/sync{job['working_dir']}"
            files = get_directory_files(working_path)
            
            file_y = y
            for j, file_info in enumerate(files[:3]):
                if file_y >= height - 4:
                    break
                file_str = f"{file_info['name'][:30]} {file_info['size_mb']:.1f}MB"
                try:
                    stdscr.addstr(file_y, col1_width + 2, 
                                file_str[:col2_width], curses.color_pair(4))
                except:
                    pass
                file_y += 1
            
            y += 4
        
        # Column 3: FFmpeg activity
        ffmpeg_y = 4
        for host, proc in ffmpeg_procs[:height - ffmpeg_y - 3]:
            if ffmpeg_y >= height - 3:
                break
            
            info = extract_ffmpeg_info(proc)
            label = f"[{host[:5]}] "
            full_str = label + info
            
            try:
                stdscr.addstr(ffmpeg_y, col1_width + col2_width + 4, 
                            full_str[:col3_width], curses.color_pair(1) | curses.A_BOLD)
            except:
                pass
            ffmpeg_y += 1
        
        # Status message (if active)
        if status_message and time.time() < status_expire_time:
            status_y = height - 3
            try:
                stdscr.addstr(status_y, (width - len(status_message)) // 2,
                            f" {status_message} ",
                            curses.color_pair(status_color) | curses.A_BOLD)
            except:
                pass

        # Summary footer
        footer_y = height - 2
        summary = f"Jobs: {len(jobs)} | FFmpeg: {len(ffmpeg_procs)} | Refresh: 1s | 'c'=Clear Pipeline | 'q'=Quit"
        try:
            stdscr.addstr(footer_y, 1, summary[:width-2], curses.color_pair(4))
        except:
            pass

        stdscr.refresh()

        # Check for keyboard input
        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('c') or key == ord('C'):
            # Clear pipeline
            cleared = clear_pipeline()
            if cleared > 0:
                status_message = f"✓ Cleared {cleared} job(s) from pipeline"
                status_color = 7  # Green background
                status_expire_time = time.time() + 3
            elif cleared == 0:
                status_message = "ℹ Pipeline already empty"
                status_color = 4  # Cyan
                status_expire_time = time.time() + 2
            else:
                status_message = "✗ Failed to clear pipeline"
                status_color = 8  # Red background
                status_expire_time = time.time() + 3

def main():
    """Main entry point"""
    try:
        curses.wrapper(draw_monitor)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
