# SkypeExport

A Python script to transform Skype message exports into organized HTML chat logs, grouped by conversation and ISO week.

## Overview

`skype_export.py` reads a `messages.json` export from Skype (with accompanying `media/` folder) and generates a set of HTML files:

- Each conversation gets its own folder, named after the contact or thread (sanitized to remove invalid characters).
- Within each conversation folder, subfolders are created for each year.
- Inside each year folder, an HTML file is created for each ISO week, named `week_<WW>.html`, containing all messages for that week.

Messages and media (images, videos, and other file links) are embedded or linked directly in the HTML.

## Prerequisites

- Python 3.x
- Install dependencies:
  ```bash
  pip install python-dateutil tqdm
  ```

## Usage

1. Place `skype_export.py` in the root of your Skype backup folder, alongside:
   - `messages.json`
   - `media/` directory (containing exported media files)

2. Run the script:
   ```bash
   python skype_export.py
   ```

3. Inspect the generated folders and HTML files.

## Output Artifacts

- **HTML chat logs**: One file per conversation per week, located at `./<ConversationName>/<Year>/week_<WW>.html`.
- **Embedded media**: Images and videos appear inline; other files are provided as download links.
- **Console summary**: After processing, the script prints counts of messages and media items per contact, and the total message count.

## Notes

- Folder and file names are sanitized to replace characters illegal in file systems.
- Skype emojis are converted to text descriptions.
- If media files are missing, the HTML will include fallback download links.

## License

This project is licensed under the MIT License.
