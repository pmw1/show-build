import os
import subprocess
import json

def process_file(filepath: str, config_path: str):
    with open(config_path, 'r') as f:
        tasks = json.load(f)

    for task in tasks:
        if task['type'] == 'trim':
            trim_video(filepath, task)
        elif task['type'] == 'convert_to_mp3':
            convert_to_mp3(filepath, task)
        elif task['type'] == 'create_preview':
            create_low_res_preview(filepath, task)

def trim_video(video_path: str, config):
    output_file = os.path.join(
        os.path.dirname(video_path),
        f"{os.path.splitext(os.path.basename(video_path))[0]}_trimmed.mp4"
    )
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-ss", str(config['start_time']),
        "-to", str(config['end_time']),
        "-c", "copy",
        output_file
    ])
    return output_file

def convert_to_mp3(video_path: str, config):
    output_file = os.path.join(
        os.path.dirname(video_path),
        f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3"
    )
    subprocess.run([
        "ffmpeg", "-i", video_path,
        output_file
    ])
    return output_file

def create_low_res_preview(video_path: str, config):
    output_file = os.path.join(
        os.path.dirname(video_path),
        f"{os.path.splitext(os.path.basename(video_path))[0]}_preview.mp4"
    )
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"scale={config['width']}:{config['height']}, drawtext=fontsize=24:text='%{{pts\\:hms}}':x=10:y=H-th-10",
        output_file
    ])
    return output_file

# Example usage:
if __name__ == "__main__":
    file_path = "/path/to/video.mp4"
    config_path = "tasks.json"  # Path to the JSON configuration file
    process_file(file_path, config_path)