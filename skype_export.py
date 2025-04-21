import json
import re
from pathlib import Path
from datetime import datetime
import html
from tqdm import tqdm
from collections import defaultdict
from dateutil.parser import isoparse

# === Load JSON ===
with open("messages.json", encoding="utf-8") as f:
    data = json.load(f)

user_id = data["userId"]

# === Build media file lookup ===
media_files = {}
media_dir = Path("media")
media_paths = list(media_dir.glob("*"))

print("Indexing media files...")
for path in tqdm(media_paths, desc="Indexing media"):
    if path.is_file():
        media_id = path.name.split('.')[0]  # handles 0-weu-xxx.1.png
        if media_id not in media_files:
            media_files[media_id] = path.name  # ← Store just the filename!

# === Helper Functions ===
def replace_skype_emojis(text):
    return re.sub(r'<ss type="(\w+)" alt="([^"]+)">.*?</ss>', r'\2 (\1)', text)

def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip('.')

def extract_media_uriobject(content):
    match = re.search(r'<URIObject uri="https://api\.asm\.skype\.com/v1/objects/([^"]+)"[^>]*>.*?<OriginalName v="([^"]+)">', content)
    if match:
        return match.group(1), match.group(2)
    return None, None

def is_image(filename):
    return filename.lower().endswith((".jpg", ".jpeg", ".png"))

def is_video(filename):
    return filename.lower().endswith(".mp4")

def render_media_html(media_id, original_filename, relative_path):
    filename = media_files.get(media_id)
    if filename:
        rel_path = relative_path / filename
        if is_image(filename):
            return f'<img src="{rel_path.as_posix()}" style="max-width: 300px;">'
        elif is_video(filename):
            return f'''
                <video controls width="300">
                    <source src="{rel_path.as_posix()}" type="video/mp4">
                </video>
            '''
        else:
            return f'<a href="{rel_path.as_posix()}">Download {filename}</a>'
    else:
        fallback = f"{media_id}{Path(original_filename).suffix}"
        return f'<a href="{(relative_path / fallback).as_posix()}">Download {original_filename}</a>'

def format_line_html(time, sender, content, is_user):
    sender_class = "me" if is_user else "other"
    time_html = f'<span class="timestamp">[{time}]</span>'
    sender_html = f'<span class="sender {sender_class}">{html.escape(sender)}:</span>'
    message_html = f'<span class="message">{content}</span>'
    return f'<div class="line">{time_html} {sender_html} {message_html}</div>\n'

# === HTML Styling ===
css = """
<style>
body { font-family: monospace; background: #fdfdfd; color: #222; padding: 20px; max-width: 800px; margin: auto; }
.line { margin-bottom: 6px; }
.timestamp { color: #888; margin-right: 8px; }
.sender.me { color: #004aad; font-weight: bold; }
.sender.other { color: #008800; font-weight: bold; }
.message { margin-left: 5px; white-space: pre-wrap; }
img, video { display: block; margin-top: 6px; margin-bottom: 6px; }
</style>
"""

# === Counters ===
total_messages = 0
message_counts = {}
media_counts = defaultdict(int)

# === Main Loop ===
for convo in tqdm(data.get("conversations", []), desc="Processing conversations"):
    raw_name = convo.get("displayName") or convo["id"]
    name = sanitize(raw_name)
    messages = convo.get("MessageList", [])

    chat_by_week = {}
    msg_count = 0

    for msg in messages:
        content = msg.get("content", "").strip()
        sender = msg.get("from", "")
        time_str = msg.get("originalarrivaltime")
        if not time_str:
            continue

        try:
            timestamp = isoparse(time_str)
        except ValueError:
            continue

        year, week, _ = timestamp.isocalendar()
        time_formatted = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        sender_label = "You" if sender == user_id else raw_name
        is_user = sender == user_id

        media_id, original_filename = extract_media_uriobject(content)
        if media_id and original_filename:
            relative_media_path = Path("..") / ".." / "media"
            media_html = render_media_html(media_id, original_filename, relative_media_path)
            line_html = format_line_html(time_formatted, sender_label, media_html, is_user)
            media_counts[raw_name] += 1
        else:
            cleaned = html.escape(content)
            cleaned = replace_skype_emojis(cleaned)
            cleaned = cleaned.replace("\n", "<br>")
            line_html = format_line_html(time_formatted, sender_label, cleaned, is_user)

        chat_by_week.setdefault((year, week), []).append(line_html)
        msg_count += 1
        total_messages += 1

    message_counts[raw_name] = msg_count

    for (year, week), lines in chat_by_week.items():
        folder = Path(name) / str(year)
        folder.mkdir(parents=True, exist_ok=True)

        html_file = folder / f"week_{week:02}.html"
        with open(html_file, "w", encoding="utf-8") as out:
            out.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{raw_name} - week {week}</title>{css}</head><body>\n")
            out.writelines(lines)
            out.write("</body></html>")

# === Summary Output ===
print("\n--- Summary ---")
for person, count in message_counts.items():
    print(f"{person}: {count} messages")

print(f"\nTotal messages: {total_messages}")

if media_counts:
    print("\nMedia files:")
    for person, count in media_counts.items():
        print(f"{person}: {count} media items")
