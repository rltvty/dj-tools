import hashlib
from typing import Any
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, UFID

from .utils import list_mp3_files


def add_ufid_to_mp3(file_path: str) -> None:
    """
    Add a UFID to an MP3 file if it doesn't already have one.

    Args:
        file_path (str): Path to the MP3 file.
        namespace (str): Namespace identifier for the UFID.

    Raises:
        ValueError: If the MP3 file lacks necessary metadata (artist or title).
    """
    # Load the MP3 file
    audio = MP3(file_path, ID3=ID3)

    # Ensure the MP3 file has ID3 tags
    if audio.tags is None:
        audio.add_tags()
    tags: dict[str,Any] = audio.tags

    def get_tag(tag: str) -> str | None:
        if tag in audio.tags:
            return audio.tags.get(tag).text[0]
        return None
    
    artist = get_tag("TPE1")
    title = get_tag("TIT2")

    if artist is None or title is None:
        raise ValueError(f"File '{file_path}' is missing required metadata (artist and title).")

    for tag in tags.values():
        if isinstance(tag, UFID):
            if tag.owner and len(tag.owner) > 0:
                print(f"found UFID: {tag.owner.strip()} for: {artist} - {title}")
                return
                
    ufid_value = hashlib.sha1(f"{artist}|{title}".encode('utf-8')).hexdigest()[:8]
    ufid_tag = UFID(owner=f"esp-{ufid_value}")
    audio.tags.add(ufid_tag)
    print(f"added UFID: {ufid_tag.owner} for: {artist} - {title}")
    audio.save()


def main():
    files = list_mp3_files("/Users/epinzur/Desktop/Music/Traktor/")

    for file in files:
        add_ufid_to_mp3(file_path=file)
