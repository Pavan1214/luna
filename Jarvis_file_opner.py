import os
import subprocess
import sys
import logging
from fuzzywuzzy import process
import asyncio
try:
    import pygetwindow as gw
except ImportError:
    gw = None

from langchain.tools import tool

sys.stdout.reconfigure(encoding='utf-8')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow not available")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"🪟 Window focused: {window.title}")
            return True
    logger.warning("⚠ Window not found for focusing.")
    return False

async def index_files(base_dirs):
    file_index = []
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, _, files in os.walk(base_dir):
                for f in files:
                    file_index.append({
                        "name": f,
                        "path": os.path.join(root, f),
                        "type": "file"
                    })
        else:
            logger.warning(f"⚠ Directory not found: {base_dir}")
    logger.info(f"✅ Indexed {len(file_index)} files from {base_dirs}.")
    return file_index

async def search_file(query, index):
    choices = [item["name"] for item in index]
    if not choices:
        logger.warning("⚠ No files available for matching.")
        return None

    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' (Score: {score})")
    if score > 70:
        for item in index:
            if item["name"] == best_match:
                return item
    return None

async def open_file(item):
    try:
        logger.info(f"📂 Opening file: {item['path']}")
        if os.name == 'nt':
            # Use subprocess instead of os.startfile for better reliability
            subprocess.Popen(f'"{item["path"]}"', shell=True)
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', item["path"]])
        
        # Wait a bit for the file to open before trying to focus
        await asyncio.sleep(2)
        await focus_window(item["name"])
        return f"✅ File opened: {item['name']}"
    except Exception as e:
        logger.error(f"❌ Error opening file: {e}")
        return f"❌ Failed to open file: {e}"

async def handle_command(command, index):
    item = await search_file(command, index)
    if item:
        return await open_file(item)
    else:
        logger.warning("❌ File not found.")
        return "❌ File not found."

@tool
async def Play_file(name: str) -> str:
    """
    Searches for and opens a file by name from the C:/ drive.

    Use this tool when the user wants to open a file like a video, PDF, document, image, etc.
    Example prompts:
    - "c drive నుండి my resume తెరవండి"
    - "Open c:/project report"
    - "MP4 file play చేయండి"
    """

    folders_to_index = ["C:/", "D:/"]  # Search both C and D drives
    index = await index_files(folders_to_index)
    command = name.strip()
    return await handle_command(command, index)