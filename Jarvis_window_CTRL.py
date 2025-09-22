import os
import subprocess
import logging
import sys
import asyncio
from fuzzywuzzy import process

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

from langchain.tools import tool

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App command map
APP_MAPPINGS = {
    "notepad": "notepad",
    "calculator": "calc",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "command prompt": "cmd",
    "control panel": "control",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "vs code": "C:\\Users\\gaura\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "postman": "C:\\Users\\gaura\\AppData\\Local\\Postman\\Postman.exe",
    "Jio shpare browser": "C:\\Users\\Gaurav\\AppData\\Local\\JIO\\JioSphere\\Application\\JioSphere.exe"
}

# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow not available")
        return False

    await asyncio.sleep(1.5)  # Give time for window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for d in dirs:
                    item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
                for f in files:
                    item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
        else:
            logger.warning(f"⚠ Directory not found: {base_dir}")
    logger.info(f"✅ Indexed {len(item_index)} items.")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
        return f"✅ Folder opened: {os.path.basename(path)}"
    except Exception as e:
        logger.error(f"❌ Error opening folder: {e}")
        return f"❌ Failed to open folder: {e}"

async def play_file(path):
    try:
        if os.name == 'nt':
            subprocess.Popen(f'"{path}"', shell=True)
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
        
        await asyncio.sleep(2)
        await focus_window(os.path.basename(path))
        return f"✅ File opened: {os.path.basename(path)}"
    except Exception as e:
        logger.error(f"❌ Error opening file: {e}")
        return f"❌ Failed to open file: {e}"

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder created: {path}"
    except Exception as e:
        return f"❌ Error creating folder: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ Renamed to {new_path}"
    except Exception as e:
        return f"❌ Failed to rename: {e}"

async def delete_item(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ Deleted: {path}"
    except Exception as e:
        return f"❌ Failed to delete: {e}"

# App control
@tool
async def open_app(app_title: str) -> str:
    """
    Opens a desktop app like Notepad, Chrome, VLC, etc.

    Use this tool when the user asks to launch an application on their computer.
    Example prompts:
    - "Notepad తెరవండి"
    - "Chrome open చేయండి"
    - "VLC media player ప్లే చేయండి"
    - "Calculator launch చేయండి"
    """

    app_title = app_title.lower().strip()
    app_command = APP_MAPPINGS.get(app_title, app_title)
    try:
        await asyncio.create_subprocess_shell(f'start "" "{app_command}"', shell=True)
        focused = await focus_window(app_title)
        if focused:
            return f"🚀 App launched and focused: {app_title}."
        else:
            return f"🚀 {app_title} launched, but could not focus on window."
    except Exception as e:
        return f"❌ Failed to launch {app_title}: {e}"

@tool
async def close_app(window_title: str) -> str:
    """
    Closes the applications window by its title.

    Use this tool when the user wants to close any app or window on their desktop.
    Example prompts:
    - "Notepad మూసివేయండి"
    - "Close VLC"
    - "Chrome window మూసివేయండి"
    - "Calculator ని మూసివేయండి"
    """

    if not win32gui:
        return "❌ win32gui not available"

    def enumHandler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

    win32gui.EnumWindows(enumHandler, None)
    return f"✅ Window closed: {window_title}"

# Jarvis command logic
@tool
async def folder_file(command: str) -> str:
    """
    Handles folder and file actions like open, create, rename, or delete based on user command.

    Use this tool when the user wants to manage folders or files using natural language.
    Example prompts:
    - "Projects folder సృష్టించండి"
    - "OldName ని NewName గా మార్చండి"
    - "xyz.mp4 delete చేయండి"
    - "Music folder తెరవండి"
    - "Resume.pdf ప్లే చేయండి"
    """

    folders_to_index = ["C:/", "D:/"]
    index = await index_items(folders_to_index)
    command_lower = command.lower()

    if "create folder" in command_lower or "folder create" in command_lower:
        folder_name = command.replace("create folder", "").replace("folder create", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder") or await search_item(old_name, index, "file")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ Invalid rename command."

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ Item not found for deletion."

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            result = await open_folder(item["path"])
            return result
        return "❌ Folder not found."

    item = await search_item(command, index, "file")
    if item:
        result = await play_file(item["path"])
        return result

    return "⚠ Nothing matched."