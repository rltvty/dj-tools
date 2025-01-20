import os

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, POPM
from typing import  Any

# Mapping from Camelot to Open Key
camelot_to_open = {
    "1A": "8d", "2A": "9d", "3A": "10d", "4A": "11d", "5A": "12d", "6A": "1d",
    "7A": "2d", "8A": "3d", "9A": "4d", "10A": "5d", "11A": "6d", "12A": "7d",
    "1B": "8m", "2B": "9m", "3B": "10m", "4B": "11m", "5B": "12m", "6B": "1m",
    "7B": "2m", "8B": "3m", "9B": "4m", "10B": "5m", "11B": "6m", "12B": "7m"
}

# Mapping from long-form keys to Camelot Wheel notation
long_to_camelot = {
    "Cmaj": "8B", "Cmin": "5A",
    "C#maj": "3B", "C#min": "12A",
    "Dmaj": "10B", "Dmin": "7A",
    "D#maj": "5B", "D#min": "2A",
    "Emaj": "12B", "Emin": "9A",
    "Fmaj": "7B", "Fmin": "4A",
    "F#maj": "2B", "F#min": "11A",
    "Gmaj": "9B", "Gmin": "6A",
    "G#maj": "4B", "G#min": "1A",
    "Amaj": "11B", "Amin": "8A",
    "A#maj": "6B", "A#min": "3A",
    "Bmaj": "1B", "Bmin": "10A",
    "Cbmaj": "7B", "Cbmin": "4A",  # Enharmonic equivalence
    "Ebmin": "2A"  # Additional cases
}

def convert_long_key_to_camelot(key: str) -> str:
    """
    Converts a musical long key into Camelot Wheel notation.
    
    Args:
        key (str): The musical key in long form (e.g., 'Bmin', 'Fmaj').
    
    Returns:
        str: The Camelot Wheel notation (e.g., '11d', '4m'), or the input if no conversion is found.
    """

    return long_to_camelot.get(key, key)

def convert_camelot_to_open_key(key: str) -> str:
    """
    Converts a key from Camelot Wheel (Rekordbox) to Open Key (Traktor) notation.

    Args:
        key (str): The key in Camelot Wheel notation.

    Returns:
        str: The converted Open Key notation, or the input if no conversion is found.
    """
    return camelot_to_open.get(key, key)

def convert_open_key_to_camelot(key: str) -> str:
    """
    Converts a key from Open Key (Traktor) to Camelot Wheel (Rekordbox) notation.

    Args:
        key (str): The key in Open Key notation.

    Returns:
        str: The converted Camelot Wheel key notation, or the input if no conversion is found.
    """
    # Reverse map from Open Key to Camelot
    open_to_camelot = {v: k for k, v in camelot_to_open.items()}

    return open_to_camelot.get(key, key)

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
        "TSRC", # International Standard Recording Code (ISRC)
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
        "TXXX:SERATO_PLAYCOUNT",
        "TXXX:TRACK_URL",
        "TXXX:LABEL_URL",
        "TXXX:FILEOWNER",
        "TXXX:ISRC",
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
            metadata["title"] = get_tag("TIT2")
            metadata["artist"] = get_tag("TPE1")
            metadata["additional_artists"] = get_tag("TPE2")
            metadata["album_artist"] = get_tag("TXXX:ALBUM ARTIST")
            metadata["original_artist"] = get_tag("TOPE")
            metadata["composer"] = get_tag("TCOM")
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

    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")

    return metadata





def clean_metadata(metadata:dict[str, Any]):
    keys_to_remove = {key for key, value in metadata.items() if value is None}

    if metadata["original_album"] == metadata["album"]:
        keys_to_remove.add("original_album")

    if metadata["original_artist"] == metadata["artist"]:
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

    rating = metadata.get("rating", 0)
    stars = rating // 51
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

def main():
    files = list_mp3_files("/Users/epinzur/Desktop/Music/Traktor/")
    for file in files:
        print()
        print(file)

        metadata = extract_mp3_metadata(file)
        clean_metadata(metadata)

        for key in sorted(metadata.keys()):
            if key in ["cover_art"]:
                continue
            print(f"\t{key}: {metadata[key]}")


    # if metadata["cover_art"]:
    #     with open("cover_art.jpg", "wb") as img_file:
    #         img_file.write(metadata["cover_art"])
    #     print("Cover art saved as 'cover_art.jpg'")
    # else:
    #     print("No cover art found.")