from io import BytesIO
import qrcode
import os

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, POPM
from typing import  Any

from .field_layout import FieldLayout

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


from reportlab.lib import colors

from PIL import Image, ImageEnhance
from io import BytesIO
import numpy as np

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
        "TCOM", # Composer
        "TXXX:ALBUM ARTIST",
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
            metadata["file"] = file_path
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

    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")

    return metadata





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

field_layouts = [
    FieldLayout("title", "front", 10, 130, justification="left", font="Helvetica-Bold", font_size=14),
    FieldLayout("artist", "front", 10, 110, justification="left", font="Helvetica", font_size=12),
    FieldLayout("bpm", "front", 10, 90, justification="left", font="Helvetica", font_size=10),
    FieldLayout("starting_key", "front", 10, 70, justification="left", font="Helvetica", font_size=10),
    FieldLayout("genre", "back", 10, 130, justification="left", font="Helvetica", font_size=10),
    FieldLayout("label", "back", 10, 110, justification="left", font="Helvetica", font_size=10),
    FieldLayout("release_date", "back", 10, 90, justification="left", font="Helvetica", font_size=10),
    FieldLayout("rating", "back", 10, 70, justification="left", font="Helvetica", font_size=10),
]

def is_dark(image_data: bytes, threshold: float = 100.0) -> bool:
    """
    Determines if an image is dark based on its average brightness.

    Args:
        image_data (bytes): The binary image data.
        threshold (float): Brightness threshold (0-255) to classify as dark.

    Returns:
        bool: True if the image is dark, False otherwise.
    """
    # Load the image from binary data
    image = Image.open(BytesIO(image_data)).convert("RGB")
    
    # Convert to a NumPy array for pixel-level manipulation
    pixels = np.array(image)
    
    # Calculate perceived brightness for each pixel
    brightness = 0.299 * pixels[..., 0] + 0.587 * pixels[..., 1] + 0.114 * pixels[..., 2]
    avg_brightness = brightness.mean()

    return avg_brightness < threshold

def lighten_image(image_data: bytes, factor: float = 1.5) -> bytes:
    """
    Lightens an image by a specified factor.

    Args:
        image_data (bytes): The binary image data.
        factor (float): Brightness enhancement factor (>1.0 for brighter, <1.0 for darker).

    Returns:
        bytes: The binary data of the lightened image.
    """
    # Load the image from binary data
    image = Image.open(BytesIO(image_data))
    
    # Enhance the brightness
    enhancer = ImageEnhance.Brightness(image)
    lightened_image = enhancer.enhance(factor)
    
    # Save the lightened image to a BytesIO object
    lightened_data = BytesIO()
    lightened_image.save(lightened_data, format=image.format)
    lightened_data.seek(0)

    return lightened_data.getvalue()


def create_pdf_with_layout(output_path: str, cards: list[dict], layouts: list[FieldLayout]) -> None:
    """
    Generates a PDF with A6 cards laid out on A4 paper, using layout instructions.

    Args:
        output_path (str): Path to save the generated PDF.
        cards (list[dict]): List of metadata dictionaries for each card.
        layouts (list[FieldLayout]): Layout instructions for fields.
    """
    PAGE_WIDTH, PAGE_HEIGHT = A4
    CARD_WIDTH = PAGE_WIDTH / 2
    CARD_HEIGHT = PAGE_HEIGHT / 2

    pdf = canvas.Canvas(output_path, pagesize=A4)

    def draw_field(field: FieldLayout, data: dict, x_offset: float, y_offset: float) -> None:
        """Draw a single field on the card."""
        value = data.get(field.field_name, "")
        if not value:
            return  # Skip empty fields

        pdf.setFont(field.font, field.font_size)
        text_x = x_offset + field.x
        text_y = y_offset + field.y

        value = str(value)

        if field.justification == "right":
            text_width = pdf.stringWidth(value, field.font, field.font_size)
            text_x -= text_width
        elif field.justification == "center":
            text_width = pdf.stringWidth(value, field.font, field.font_size)
            text_x -= text_width / 2

        pdf.drawString(text_x, text_y, value)

    def draw_card_border(x_offset: float, y_offset: float) -> None:
        """Draw a border for the card with a light gray color and reset drawing properties."""
        pdf.setStrokeColor(colors.gray)  # Set the stroke color to light gray
        pdf.setLineWidth(0.5)     # Make the border thinner
        pdf.rect(x_offset, y_offset, CARD_WIDTH, CARD_HEIGHT, stroke=1, fill=0)

        # Reset to original stroke color and line width
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(1)

    def draw_cover_art(card: dict[str, Any], x_offset: float, y_offset: float) -> None:
        """Draw cover art on the card using binary image data."""

        image_data = card.get("cover_art")

        if not image_data:
            return  # Skip if no cover art is provided
        
        cycles = 0
        while is_dark(image_data):
            cycles += 1
            print(f"{card.get("title")}: is dark, lightening")
            image_data = lighten_image(image_data, factor=1.5)
            if cycles > 2:
                break

        # Define the image size and position
        image_width = CARD_WIDTH / 2  # Fit the image to half the card width
        image_height = CARD_HEIGHT / 2
        image_x = x_offset + (CARD_WIDTH - image_width) / 2  # Center horizontally
        image_y = y_offset + CARD_HEIGHT - image_height - 10  # Top of the card with padding

        try:
            image_stream = BytesIO(image_data)
            image = ImageReader(image_stream)
            pdf.drawImage(image, image_x, image_y, width=image_width, height=image_height, preserveAspectRatio=True)
        except Exception as e:
            print(f"Error drawing image from binary data, {e}")
            exit()

    # Generate QR code for text
    def generate_qr_code(text: str, size: int = 256) -> BytesIO:
        """
        Generates a QR code for the given text with a fixed resolution.

        Args:
            text (str): The text to encode in the QR code.
            size (int): The desired pixel size of the QR code (default: 256x256).

        Returns:
            BytesIO: A file-like object containing the QR code image.
        """
        # Version 4 (33x33 grid) with error correction H 
        # Max of 50 alpha-numeric characters
        # see: https://www.qrcode.com/en/about/version.html
        qr = qrcode.QRCode(
            version=4,  
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,  # Base size of each box in the QR code
            border=4      # Minimum border size (default is 4)
        )
        qr.add_data(text[:49])
        qr.make(fit=True)

        # Render the QR code to an image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Resize the image to ensure fixed resolution
        qr_image = qr_image.resize((size, size))

        # Save the QR code to a BytesIO object
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)  # Reset file pointer to the beginning
        return qr_buffer

    # Draw the QR code on the card
    def draw_qr_code(qr_image: BytesIO, x_offset: float, y_offset: float) -> None:
        """
        Draws a QR code on the card.

        Args:
            qr_image (BytesIO): The file-like object containing the QR code image.
            x_offset (float): The X-coordinate of the card.
            y_offset (float): The Y-coordinate of the card.
        """
        try:
            image = ImageReader(qr_image)

            # Define size and position for the QR code
            qr_size = CARD_WIDTH / 3  # Scale the QR code to fit nicely
            qr_x = x_offset + (CARD_WIDTH - qr_size) / 2  # Center horizontally
            qr_y = y_offset + CARD_HEIGHT / 4  # Position in the middle of the back

            pdf.drawImage(image, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True)
        except Exception as e:
            print(f"Error drawing QR code: {e}")


    for i in range(0, len(cards), 4):
        current_cards = cards[i:i + 4]

        # Draw front of the cards
        for j, card in enumerate(current_cards):
            x_offset = (j % 2) * CARD_WIDTH
            y_offset = PAGE_HEIGHT - ((j // 2) + 1) * CARD_HEIGHT

            # Draw border for the card
            draw_card_border(x_offset, y_offset)

            draw_cover_art(card, x_offset, y_offset)

            # Draw fields on the front
            for field in layouts:
                if field.side == "front":
                    draw_field(field, card, x_offset, y_offset)

        pdf.showPage()  # Add new page for the back side

        # Draw back of the cards
        for j, card in enumerate(current_cards):
            x_offset = (j % 2) * CARD_WIDTH
            y_offset = PAGE_HEIGHT - ((j // 2) + 1) * CARD_HEIGHT

            # Draw border for the card
            draw_card_border(x_offset, y_offset)
        
            title = card.get("search", "<missing>")
            qr_image = generate_qr_code(title)  # Generate QR code for the track title
            draw_qr_code(qr_image, x_offset, y_offset)

            # Draw fields on the back
            for field in layouts:
                if field.side == "back":
                    draw_field(field, card, x_offset, y_offset)

        pdf.showPage()  # Finish the page

    pdf.save()


def main():
    files = list_mp3_files("/Users/epinzur/Desktop/Music/Traktor/")
    all_keys = set()
    data = []
    for file in files:
        # print()
        # print(file)

        metadata = extract_mp3_metadata(file)
        clean_metadata(metadata)

        # print(f"{len(metadata["search"])}: '{metadata["search"]}'")

        for key in sorted(metadata.keys()):
            if key in ["cover_art"]:
                continue
            all_keys.add(key)
            # print(f"\t{key}: {metadata[key]}")

        data.append(metadata)

    create_pdf_with_layout("output_with_layout.pdf", data, field_layouts)

    print(f"All metadata fields available: {all_keys}")
