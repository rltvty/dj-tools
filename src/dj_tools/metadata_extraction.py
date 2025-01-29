import os
from typing import Any

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, POPM, UFID

from .key_conversion import (
    convert_long_key_to_camelot,
    convert_open_key_to_camelot,
)

def extract_mp3_metadata(file_path: str) -> dict[str, Any]:
    """
    Extracts metadata and cover art from an MP3 file.

    Args:
        file_path (str): The path to the MP3 file.

    Returns:
        dict: A dictionary containing the title, artist, album, and cover art.
    """

    keys_to_skip = [
        "APIC", # Attached (or linked) Picture
        "PRIV", # Private frame
        "TENC", # Encoder
        #"TSRC", # International Standard Recording Code (ISRC)
        "TSSE", # Encoder settings
        "UFID", # Unique file identifier
        "WOAF", # Official File Information
        "WPUB", # Official Publisher Information
        "TRCK", # Track Number
        "POPM", # Popularimeter
        "GEOB", # General Encapsulated Object (serato overview)
        "WCOM", # Commercial Information
        "RVA2", # Relative volume adjustment (serato gain)
        "TPOS", # Part of set
        "TCMP", # iTunes Compilation Flag 
        "TCOM", # Composer
        "TXXX:ALBUM ARTIST",
        "TXXX:SERATO_PLAYCOUNT",
        "TXXX:TRACK_URL",
        "TXXX:LABEL_URL",
        "TXXX:FILEOWNER",
        #"TXXX:ISRC",
        "TXXX:BPM",
        "TXXX:YEAR",
        "TXXX:FILETYPE",
        "TXXX:INITIAL_KEY",
        "TXXX:RELEASE_TIME",
        "TXXX:RECORDING_DATE",
        "TXXX:ORGANIZATION",
    ]


    metadata = {
        "cover_art": None,  # Will hold binary data of the cover art
    }

    try:
        audio = MP3(file_path, ID3=ID3)  # Load MP3 with ID3 tags
        duration_seconds = int(audio.info.length) if audio.info and audio.info.length else None
        if duration_seconds is not None:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            metadata["duration"] = f"{minutes}:{seconds:02d}"

        tags: dict[str,Any] = audio.tags
        if tags:
            def get_tag(tag: str) -> str | None:
                if tag in tags:
                    return tags.pop(tag).text[0]
                return None
            
            # Extract common metadata    
            metadata["file"] = os.path.basename(file_path)
            metadata["id"] =  get_tag("TSRC") or get_tag("TXXX:ISRC")
            metadata["title"] = get_tag("TIT2")
            metadata["artist"] = get_tag("TPE1") or get_tag("TXXX:ALBUM ARTIST")
            metadata["additional_artists"] = get_tag("TPE2")
            metadata["original_artist"] = get_tag("TOPE")
            metadata["remixer"] = get_tag("TPE4") or get_tag("TXXX:TraktorRemixer")
            metadata["album"] = get_tag("TALB")
            metadata["original_album"] = get_tag("TOAL")
            metadata["genre"] = get_tag("TCON")
            metadata["label"] = get_tag("TIT1") or get_tag("TXXX:LABEL")
            metadata["publisher"] = get_tag("TPUB") or get_tag("TXXX:ORGANIZATION")
            metadata["file_type"] = get_tag("TFLT") or get_tag("TXXX:FILETYPE")
            metadata["release_year"] = get_tag("TDRL") or get_tag("TXXX:YEAR")
            metadata["release_date"] = get_tag("TDOR") or get_tag("TXXX:RELEASE_TIME")
            metadata["recording_date"] = get_tag("TDRC") or get_tag("TXXX:RECORDING_DATE")
            metadata["starting_key"] = get_tag("TKEY") or get_tag("TXXX:INITIAL_KEY")
            metadata["user_comment"] = get_tag("COMM::eng") or get_tag("TXXX:COMMENT")
            metadata["user_comment_2"] = get_tag("COMM:ID3v1 Comment:eng")
            metadata["bpm"] = get_tag("TBPM") or get_tag("TXXX:BPM")

            for key, value in tags.items():
                skip_key = False
                for skip in keys_to_skip:
                    if skip in key:
                        skip_key = True
                        continue
                if skip_key:
                    continue
                print(f"unextracted tag: '{key}', value: '{value}'")

            for tag in tags.values():
                if isinstance(tag, APIC):  # APIC contains cover art
                    metadata["cover_art"] = tag.data
                elif isinstance(tag, POPM):  # Popularimeter
                    metadata["rating"] = tag.rating
                elif isinstance(tag, UFID): # Unique file identifier.
                    ufid = tag.owner.strip()
                    if len(ufid) > 0:
                        metadata["id"] = ufid

    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")

    return clean_metadata(metadata)

def clean_metadata(metadata:dict[str, Any]):
    keys_to_remove = {key for key, value in metadata.items() if value is None}

    if metadata["original_album"] == metadata["album"]:
        keys_to_remove.add("original_album")

    if metadata["original_artist"] and metadata["original_artist"] in metadata["artist"]:
        keys_to_remove.add("original_artist")

    if metadata["additional_artists"] == metadata["artist"]:
        keys_to_remove.add("additional_artists")

    if metadata["publisher"] == metadata["label"]:
        keys_to_remove.add("publisher")

    if metadata["recording_date"] == metadata["release_date"]:
        keys_to_remove.add("recording_date")

    if metadata["release_year"] == metadata["release_date"]:
        keys_to_remove.add("release_year")

    if metadata["user_comment_2"] == metadata["user_comment"]:
        keys_to_remove.add("user_comment_2")

    for key in keys_to_remove:
        del metadata[key]

    if len(f"{metadata.get('recording_date', '')}") == 4:
        metadata["release_year"] = metadata.pop("recording_date")

    if not metadata.get("release_date") and metadata.get("release_year"):
        metadata["release_date"] = metadata.pop("release_year")

    if metadata.get("release_date") and metadata.get("release_year"):
        metadata.pop("release_year")

    if metadata.get("remixer") and metadata.get("remixer") in metadata.get("title"):
        metadata.pop("remixer")

    rating = metadata.get("rating", 0)
    stars = rating // 51
    metadata["stars"] = stars
    metadata["rating"] = "★" * stars if stars > 0 else ""

    if not metadata.get("label") and metadata.get("publisher"):
        metadata["label"] = metadata.pop("publisher")

    if metadata.get("additional_artists", "") == "Various Artists":
        metadata.pop("additional_artists")

    additional_artists: list[str] = metadata.pop("additional_artists", "").replace("&",",").replace("feat.", ",").split(",")
    actual_additional_artists = []
    for additional_artist in additional_artists:
        test = additional_artist.strip()
        if test == "":
            continue
        if test not in metadata["artist"]:
            actual_additional_artists.append(test)
    if len(actual_additional_artists) > 0:
        metadata["additional_artists"] = ", ".join(actual_additional_artists)

    if "starting_key" in metadata:
        metadata["starting_key"] = convert_open_key_to_camelot(convert_long_key_to_camelot(metadata["starting_key"]))

    search: str = metadata.get("title", "") + " " + metadata.get("artist", "")

    search = search.lower()

    for char in ["(", ")", ",", "-", "&", "!", "'s"]:
        search = search.replace(char, "")

    words = []
    for word in search.split():
        if word in ["mix", "of", "a", "feat.", "i", "the"]:
            continue
        words.append(word)

    metadata["search"] = " ".join(words)

    metadata["key_bpm"] = metadata.get("starting_key", "") + " - " + metadata.get("bpm", "")

    return metadata
