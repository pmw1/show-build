"""
Episode Script Compilation Tool

Compiles episode markdown files into formatted HTML scripts for production.
Uses centralized path configuration from paths.py for maintainability.

Usage:
    python compile-script-dev.py <episode_number> [--validate]

Examples:
    python compile-script-dev.py 0225              # Compile episode 0225
    python compile-script-dev.py 0225 --validate   # Validate only, no output

Path Configuration:
    All paths are imported from paths.py to ensure consistency across tools.
    See tools/README.md for more information about the configuration system.
"""

import os
import sys
import argparse
from pathlib import Path
import re
from datetime import datetime
import yaml
import html

# Import project paths
from paths import EPISODE_ROOT, BLUEPRINTS, HEADER_PATH, VALID_CUE_TYPES

def get_ordinal_day(day):
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"

def parse_yaml_frontmatter(content):
    match = re.match(r'^---\s*$(.*?)^---\s*$', content, re.DOTALL | re.MULTILINE)
    if match:
        return yaml.safe_load(match.group(1))
    return {}

def validate_cue_blocks(segment_files):
    valid = True
    cue_pattern = re.compile(r"(<<!--\s*Begin Cue\s*-->>.*?(?:<<!--\s*End Cue\s*-->>|$))", re.DOTALL | re.IGNORECASE)
    
    for file_path in segment_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            print(f"\033[31munknown\terror\t{file_path.name}: Failed to read file\033[0m")
            valid = False
            continue

        frontmatter = parse_yaml_frontmatter(content)
        segment_id = frontmatter.get("id", "unknown")

        cue_blocks = cue_pattern.findall(content)
        for block in cue_blocks:
            cue_type = re.search(r"\[Type:\s*(.*?)\]", block, re.IGNORECASE)
            slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
            asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
            media_url = re.search(r"\[MediaURL:\s*(.*?)\]", block, re.IGNORECASE)
            quote = re.search(r"\[Quote:\s*(.*?)(?=\[Attribution:|\[MediaURL:|\s*<<!--\s*End Cue\s*-->>|$)", block, re.IGNORECASE | re.DOTALL)
            attribution = re.search(r"\[Attribution:\s*(.*?)\]", block, re.IGNORECASE)

            asset_id_str = asset_id.group(1).strip() if asset_id else "unknown"
            cue_type_str = cue_type.group(1).strip().upper() if cue_type else "unknown"
            slug_str = slug.group(1).strip().lower() if slug else "unknown-slug"

            errors = []
            if not cue_type:
                errors.append("Missing [Type]")
            elif cue_type_str not in VALID_CUE_TYPES:
                errors.append(f"Invalid [Type: {cue_type_str}]")
            if not slug or not slug.group(1).strip():
                errors.append("Missing or empty [Slug]")
            if cue_type_str == "FSQ" and (not quote or not quote.group(1).strip()):
                errors.append("Missing or empty [Quote]")
            if cue_type_str == "GFX" and (not media_url or not media_url.group(1).strip()):
                errors.append("Missing or empty [MediaURL]")
            if not re.search(r"<<!--\s*End Cue\s*-->>", block, re.IGNORECASE):
                errors.append("Missing End Cue")

            color = "\033[32m" if not errors else "\033[31m"
            output = f"{asset_id_str} / {cue_type_str} / {slug_str} **{'VALID' if not errors else 'INVALID'}**"
            if errors:
                output += f" [{'; '.join(errors)}]"
            print(f"{color}{output}\033[0m")
            
            if errors:
                valid = False
    
    return valid

def format_cue_block(block):
    cue_type = re.search(r"\[Type:\s*(.*?)\]", block, re.IGNORECASE)
    slug = re.search(r"\[Slug:\s*(.*?)\]", block, re.IGNORECASE)
    asset_id = re.search(r"\[AssetID:\s*(.*?)\]", block, re.IGNORECASE)
    media_url = re.search(r"\[MediaURL:\s*(.*?)\]", block, re.IGNORECASE)
    quote = re.search(r"\[Quote:\s*(.*?)(?=\[Attribution:|\[MediaURL:|\s*<<!--\s*End Cue\s*-->>|$)", block, re.IGNORECASE | re.DOTALL)
    attribution = re.search(r"\[Attribution:\s*(.*?)\]", block, re.IGNORECASE)
    duration = re.search(r"\[Duration:\s*(.*?)\]", block, re.IGNORECASE)
    transcription = re.search(r"\[Transcription:\s*(.*?)\]", block, re.IGNORECASE)

    if not cue_type:
        return ""

    slug_str = slug.group(1).strip().lower() if slug else "unknown-slug"
    cue_type_str = cue_type.group(1).strip().upper()
    asset_id_str = asset_id.group(1).strip() if asset_id else "unknown"
    print(f"{asset_id_str}\t{cue_type_str}\t{slug_str}")

    entry = (
        "<div class='cue'>\n"
        "<p class='cue-header' style='font-weight:bold; font-size:1em;'>[[ {cue_type_str} / {slug_str} ]]</p>\n"
    ).format(cue_type_str=cue_type_str, slug_str=slug_str)

    if cue_type_str == "GFX":
        if media_url:
            media_url_str = media_url.group(1).strip()
            entry += (
                "<div class='gfx'>\n"
                "<img src='{media_url}' style='max-width:350px; max-height:350px; border:1px solid #ccc;' />\n"
                "</div>\n"
            ).format(media_url=media_url_str)

    elif cue_type_str == "SOT":
        entry += "<div class='sot'>\n"
        if duration and duration.group(1).strip():
            entry += (
                "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>Duration: {duration}</p>\n"
            ).format(duration=duration.group(1).strip())
        if transcription and transcription.group(1).strip():
            entry += (
                "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>Trans: {transcription}</p>\n"
            ).format(transcription=html.escape(transcription.group(1).strip()))
        else:
            entry += "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>No Transcript</p>\n"
        entry += "</div>\n"

    elif cue_type_str == "FSQ":
        if quote:
            quote_text = quote.group(1).strip().rstrip(']')  # Remove trailing ']'
            if not quote_text:
                return ""
            attribution_text = re.sub(r'^\W+', '', attribution.group(1).strip()) if attribution else ""
            entry += (
                "<div class='fsq'>\n"
                "<blockquote>{0}</blockquote>\n"
                "<p>— {1}</p>\n"
                "</div>\n"
            ).format(html.escape(quote_text), html.escape(attribution_text))
            # Debug: Log raw and cleaned attribution
            if attribution:
                attr_text = attribution.group(1).strip()
                attr_clean = re.sub(r'^\W+', '', attr_text)
                print(f"Debug: Attribution raw='{attr_text}', cleaned='{attr_clean}'")
        else:
            return ""

    entry += "</div>\n"
    return entry

def process_segment(file_path, para_counter):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return [], para_counter

    frontmatter = parse_yaml_frontmatter(content)
    slug = frontmatter.get("slug", file_path.stem).strip().lower()
    segment_id = frontmatter.get("id", "unknown")
    print(f"{segment_id}\tsegment\t{slug}")

    content = re.sub(r'^\s*---\s*.*?---\s*', '', content, flags=re.DOTALL)
    content = re.sub(r'##\s*Notes\s*.*?($|\n##|\n---)', '', content, flags=re.DOTALL)
    content = re.sub(r'##\s*Description\s*.*?($|\n##|\n---)', '', content, flags=re.DOTALL)

    if not content.strip() and not slug:
        return [(
            "<p style='text-align:left; font-weight:bold; font-size:2em; color:red; font-family:Helvetica,sans-serif;'>"
            "COMPILE ERROR29278: Missing Slug; Fatal output \\/\\ can not compile</p>\n"
        )], para_counter

    if not content.strip():
        return [], para_counter

    header_html = (
        "<p style='text-align:left; font-weight:bold; font-size:1.5em; font-family:Helvetica,sans-serif;'>"
        "{slug}</p>\n"
    ).format(slug=slug)

    output = [header_html]
    seen_slugs = set()
    processed_cues = set()  # Track processed cue blocks by asset_id and slug
    sot_pattern = r"(?:\{SOT/[^}]+\})"
    cue_pattern = re.compile(r"(?=(<<!--\s*Begin Cue\s*-->>.*?<<!--\s*End Cue\s*-->>))", re.DOTALL | re.IGNORECASE)
    parts = re.split(r"(?=(?:{}|{}))".format(cue_pattern.pattern, sot_pattern), content, flags=re.DOTALL | re.IGNORECASE)

    for part in parts:
        if not isinstance(part, str):
            continue
        part = part.strip()
        if not part:
            continue
        if re.match(r"<<!--\s*Begin Cue\s*-->>", part, re.IGNORECASE):
            asset_id = re.search(r"\[AssetID:\s*(.*?)\]", part, re.IGNORECASE)
            slug = re.search(r"\[Slug:\s*(.*?)\]", part, re.IGNORECASE)
            if asset_id and slug:
                cue_key = (asset_id.group(1).strip(), slug.group(1).strip().lower())
                if cue_key in processed_cues:
                    continue
                processed_cues.add(cue_key)
            cue_output = format_cue_block(part)
            if cue_output:
                slug_match = re.search(r"\[\[ [A-Z]+ / ([^\]]+) \]\]", cue_output)
                if slug_match:
                    cue_slug = slug_match.group(1).strip()
                    if cue_slug in seen_slugs:
                        continue
                    seen_slugs.add(cue_slug)
                output.append(cue_output)
        elif re.match(r"\{SOT/[^}]+\}", part):
            if len(part) < 7:
                continue
            sot_name = part[5:-1]
            if sot_name in seen_slugs:
                continue
            seen_slugs.add(sot_name)
            print(f"unknown\tSOT\t{sot_name}")
            output.append(
                "<div class='cue'>\n"
                "<p class='cue-header' style='font-weight:bold; font-size:1em;'>[[ SOT / {sot_name} ]]</p>\n"
                "<div class='sot'>\n"
                "<p style='margin-top: 0.1em; margin-bottom: 0; font-size: 0.72em;'>No Transcript</p>\n"
                "</div>\n"
                "</div>\n"
            )
        else:
            paragraphs = part.strip().split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if not para or re.match(r"\[MediaURL:[^\]]+\]", para, re.IGNORECASE):
                    continue
                para = html.escape(para).replace("\n", "<br>")
                if '%' in para:
                    para = para.replace('%', '%%')
                para_counter += 1
                output.append(
                    "<p id='para-{0}' style='text-align:justify; width:100%; font-family:Helvetica,sans-serif; line-height:1.5;'>{1}</p>\n".format(para_counter, para)
                )
    return output, para_counter

def compile_script(episode_number, validate_only=False):
    episode_path = EPISODE_ROOT / episode_number
    info_path = episode_path / "info.md"
    if not episode_path.exists():
        print(f"\033[31munknown\terror\tepisode_{episode_number}: Episode folder does not exist\033[0m")
        return

    rundown_path = episode_path / "rundown"
    if not rundown_path.exists():
        print(f"\033[31munknown\terror\tepisode_{episode_number}: Rundown folder does not exist\033[0m")
        return

    segment_files = sorted(rundown_path.glob("*.md"))
    if not segment_files:
        print(f"\033[31munknown\terror\tepisode_{episode_number}: No markdown files found\033[0m")
        return

    if not validate_cue_blocks(segment_files):
        print(f"\033[31munknown\terror\tepisode_{episode_number}: Validation failed, aborting\033[0m")
        return

    if validate_only:
        return

    info_data = {}
    if info_path.exists():
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                info_data = parse_yaml_frontmatter(f.read())
        except Exception:
            print(f"\033[31munknown\terror\tinfo.md: Failed to read info file\033[0m")

    episode_num = info_data.get("episode_number", episode_number)
    title = info_data.get("title", f"EPISODE NUMBER {episode_number}")
    subtitle = info_data.get("subtitle", "")
    status = info_data.get("status", "unknown")
    airdate = info_data.get("airdate", "")
    date_str = ""
    mm, dd, yy = "", "", ""
    print(f"Debug: Raw airdate = '{airdate}'")  # Debug raw value
    print(f"Debug: Airdate repr = {repr(airdate)}")  # Inspect string representation
    try:
        if not airdate:
            raise ValueError("Airdate is not set in info.md")
        if isinstance(airdate, (datetime.date, datetime.datetime)):
            airdate = airdate.strftime("%Y-%m-%d")  # Convert date object to string
        print(f"Debug: Airdate bytes = {[hex(ord(c)) for c in airdate]}")  # Inspect byte values after conversion
        airdate = str(airdate).strip()  # Ensure string, remove whitespace
        cleaned = ''.join(c for c in airdate if c.isascii() and not c.isspace())  # ASCII-only, no spaces
        print(f"Debug: Cleaned airdate = '{cleaned}'")  # Debug cleaned value
        date_part = cleaned.split("T")[0]  # Take date part
        print(f"Debug: Date part = '{date_part}', length = {len(date_part)}")  # Debug final date part
        airdate_date = datetime.strptime(date_part, "%Y-%m-%d").replace(hour=21, minute=0, second=0)
        date_str = airdate_date.strftime("%B %dth, %Y at 9:00 PM")
        mm, dd, yy = airdate_date.strftime("%m-%d-%y").split("-")
    except (ValueError, TypeError, AttributeError) as e:
        print(f"\033[31mError parsing airdate: {e}\033[0m")
        print(f"\033[33mPlease verify that 'airdate' in {info_path} is a valid 'YYYY-MM-DD' string.\033[0m")
        sys.exit(1)

    base_filename = f"script-{'-'.join(filter(None, [mm, dd, yy]))}-{status}-1.html"
    output_path = rundown_path / base_filename
    version = 1
    while output_path.exists():
        version += 1
        output_path = rundown_path / f"script-{'-'.join(filter(None, [mm, dd, yy]))}-{status}-{version}.html"

    cover_html = (
        "<div style='text-align: center; font-size: 2.5em'>DISAFFECTED</div>\n"
        "<div style='text-align: center; font-size: 1em'>EPISODE: {episode_num}</div>\n"
        "<div style='text-align: center; font-size: 1.2em'>{date_str}</div>\n"
        "<br><br>\n"
        "<div style='text-align: center; font-size: 1.2em'>Title:</div>\n"
        "<div style='text-align: center; font-size: 1.5em'>{title}</div>\n"
    )
    if subtitle:
        cover_html += "<br><br>\n<div style='text-align: center; font-size: 1.2em'>Subtitle</div>\n<div style='text-align: center; font-size: 1.2em'>{subtitle}</div>\n"
    cover_html += "<br><br>\n"

    script_output = []
    para_counter = 0

    script_output.append(
        "<!DOCTYPE html>\n<html>\n<head>\n"
        "<style>\n"
        "body { font-family: Helvetica, sans-serif; font-size: 18px; }\n"
        ".container { width: 95%; max-width: 800px; margin: 0 auto; border-left: 1px dotted rgba(128, 128, 128, 0.5); border-right: 1px dotted rgba(128, 128, 128, 0.5); padding: 1em; }\n"
        ".cue { margin-top: 2em; }\n"
        ".cue-header { font-weight: bold; font-size: 1em; margin-bottom: 0.5em; }\n"
        ".gfx { text-align: left; }\n"
        ".sot { text-align: left; font-size: 0.9em; }\n"
        ".fsq { text-align: left; max-width: 100%; }\n"
        ".fsq blockquote { width: 100%; max-width: 100%; margin: 0; padding: 1.65em; border-left: 9px solid #ccc; border-right: 9px solid #ccc; line-height: 1.5; color: rgba(0, 0, 0, 0.75); box-sizing: border-box; }\n"
        ".fsq p { font-size: 0.9em; margin-top: 0.5em; }\n"
        "</style>\n"
        "</head>\n<body>\n<div class='container'>\n"
    )
    script_output.append(cover_html.format(episode_num=episode_num, date_str=date_str, title=title, subtitle=subtitle))

    if HEADER_PATH.exists():
        try:
            with open(HEADER_PATH, "r", encoding="utf-8") as f:
                header_html = f.read()
        except Exception:
            print(f"\033[31munknown\terror\theader: Failed to read header file\033[0m")
            header_html = ""
    else:
        header_html = ""
    script_output.append(header_html)

    for segment in segment_files:
        segment_html, para_counter = process_segment(segment, para_counter)
        script_output.extend(segment_html)

    script_output.append("</div>\n</body>\n</html>")

    if output_path.exists():
        output_path.unlink()
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(script_output))
    except Exception:
        print(f"\033[31munknown\terror\t{output_path.name}: Failed to write output file\033[0m")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile script or validate cue blocks")
    parser.add_argument("episode_number", help="4-digit episode number (e.g., 0224)")
    parser.add_argument("--validate", action="store_true", help="Run validate only")
    args = parser.parse_args()

    if not re.match(r"^\d{4}$", args.episode_number):
        print("Usage: python compile_script.py <episode_number> [--validate] (episode_number: 4-digit, e.g., 0224)")
        sys.exit(1)

    compile_script(args.episode_number, validate_only=args.validate)
