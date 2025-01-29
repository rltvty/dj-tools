# Mapping from Camelot to Open Key
camelot_to_open = {
    "1A": "8d",
    "2A": "9d",
    "3A": "10d",
    "4A": "11d",
    "5A": "12d",
    "6A": "1d",
    "7A": "2d",
    "8A": "3d",
    "9A": "4d",
    "10A": "5d",
    "11A": "6d",
    "12A": "7d",
    "1B": "8m",
    "2B": "9m",
    "3B": "10m",
    "4B": "11m",
    "5B": "12m",
    "6B": "1m",
    "7B": "2m",
    "8B": "3m",
    "9B": "4m",
    "10B": "5m",
    "11B": "6m",
    "12B": "7m",
}

# Mapping from long-form keys to Camelot Wheel notation
long_to_camelot = {
    "Cmaj": "8B",
    "Cmin": "5A",
    "C#maj": "3B",
    "C#min": "12A",
    "Dmaj": "10B",
    "Dmin": "7A",
    "D#maj": "5B",
    "D#min": "2A",
    "Emaj": "12B",
    "Emin": "9A",
    "Fmaj": "7B",
    "Fmin": "4A",
    "F#maj": "2B",
    "F#min": "11A",
    "Gmaj": "9B",
    "Gmin": "6A",
    "G#maj": "4B",
    "G#min": "1A",
    "Amaj": "11B",
    "Amin": "8A",
    "A#maj": "6B",
    "A#min": "3A",
    "Bmaj": "1B",
    "Bmin": "10A",
    "Cbmaj": "7B",
    "Cbmin": "4A",  # Enharmonic equivalence
    "Ebmin": "2A",  # Additional cases
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
