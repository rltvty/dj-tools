import json
from typing import Any
import pandas as pd
from pathlib import Path
from datetime import datetime

import hashlib


def md5(data: bytes | None) -> str:
    """
    Create an MD5 hash from binary data.

    :param data: Binary data to hash
    :return: Hexadecimal MD5 hash
    """
    if data is None:
        return ""
    md5_hash = hashlib.md5()  # Create an MD5 hash object
    md5_hash.update(data)  # Update the hash object with the binary data
    return md5_hash.hexdigest()  # Return the hash as a hexadecimal string


class VersionHistory:
    def __init__(self, history_dir: str):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history: pd.DataFrame | None = self._load_existing_history()
        self.new_data: list[dict[str, Any]] = []

    def _load_existing_history(self) -> pd.DataFrame | None:
        """Load all existing Parquet files and combine them into a single DataFrame."""
        files = list(self.history_dir.glob("*.parquet"))
        if not files:
            return None
        files.sort()
        print("Loading files in this order:")
        for file in files:
            print(f"\t{file}")
        return pd.concat([pd.read_parquet(file) for file in files], ignore_index=True)

    def _get_current_versions(self, id: str) -> list[dict[str, Any]]:
        if self.history is None:
            return []

        # Filter rows by the id
        filtered_rows = self.history[self.history["id"] == id].reset_index()
        # Convert rows to dictionaries and replace NaN with None
        return [
            {k: (None if pd.isna(v) else v) for k, v in row.items()}
            for row in filtered_rows.to_dict(orient="records")
        ]

    def convert_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Reformats metadata for history comparison."""
        item = {}
        for k, v in metadata.items():
            if k in ["key_bpm", "rating", "search", "index"]:
                continue
            elif v is None:
                continue
            elif k == "cover_art":
                item["cover_art_md5"] = md5(v)
            else:
                item[k] = v
        return item

    def _str_equals(self, one: dict[str, Any], two: dict[str, Any]) -> bool:
        if one.keys() != two.keys():
            print("keys don't match")
            return False
        for key in one.keys():
            if f"{one[key]}" != f"{two[key]}":
                print("values don't match")
                return False
        return True

    def get_create_version(self, item: dict[str, Any]) -> tuple[bool, int]:
        """Gets or creates a new version for the item.

        Returns:
           (True, #) if its a new version
           (False, #) if its an existing version
        """

        id = item["id"]
        current_versions = self._get_current_versions(id=id)
        for i, version in enumerate(current_versions):
            ver = self.convert_metadata(version)
            v = ver.pop("rev", i + 1)
            if self._str_equals(ver, item):
                return (False, v)
        new_v = len(current_versions) + 1
        return (True, new_v)

    def add_new_version(self, item: dict[str, Any]) -> None:
        self.new_data.append(item)

    def save_new_versions(self, timestamp: str) -> bool:
        """Saves new versions (if they exist) to parquet."""
        if len(self.new_data) == 0:
            return False
        df = pd.DataFrame(self.new_data)
        df["release_date"] = df["release_date"].astype(str)
        file_path = Path.joinpath(self.history_dir, f"{timestamp}.parquet")
        df.to_parquet(file_path)
        # file_path = Path.joinpath(self.history_dir, f"{timestamp}.jsonl")
        # df.to_json(file_path, orient="records", lines=True)
        print(f"New version saved to {file_path}")
        return True


{
    "duration": "6:28",
    "file": "Pastiche - It-s Wavy (Original Mix).mp3",
    "id": "esp-8e0f18e7",
    "title": "It's Wavy (Original Mix)",
    "artist": "Pastiche",
    "album": "Black Lights EP",
    "genre": "Minimal / Deep Tech",
    "label": "Phobos Records",
    "file_type": "MP3",
    "release_date": "2021-02-08",
    "starting_key": "4B",
    "user_comment": "LYRICS from 3, fun, bouncy, start out at 6",
    "user_comment_2": "Purchased at Traxsource.com",
    "bpm": "125",
    "stars": 4,
    "cover_art_md5": "b473b4ef7e1f774b310cd410458dba89",
    "additional_artists": "AQUO",
}
{
    "duration": "6:28",
    "file": "Pastiche - It-s Wavy (Original Mix).mp3",
    "id": "esp-8e0f18e7",
    "title": "It's Wavy (Original Mix)",
    "artist": "Pastiche",
    "album": "Black Lights EP",
    "genre": "Minimal / Deep Tech",
    "label": "Phobos Records",
    "file_type": "MP3",
    "release_date": "2021-02-08",
    "starting_key": "4B",
    "user_comment": "LYRICS from 3, fun, bouncy, start out at 6",
    "user_comment_2": "Purchased at Traxsource.com",
    "bpm": "125",
    "stars": 4,
    "cover_art_md5": "b473b4ef7e1f774b310cd410458dba89",
    "additional_artists": "AQUO",
}
