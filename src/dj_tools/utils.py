import os
from typing import Any

def list_mp3_files(folder_path: str) -> list[str]:
    """
    Lists all MP3 files in the specified folder and its subfolders.

    Args:
        folder_path (str): The path to the folder to scan.

    Returns:
        list[str]: A list of paths to MP3 files.
    """
    mp3_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(os.path.join(root, file))
    return mp3_files