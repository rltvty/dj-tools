from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

from .field_layout import FieldLayout

from io import BytesIO
from typing import Any

from .image_manipulation import (
    is_dark, 
    lighten_image,
    generate_qr_code,
)

PAGE_WIDTH, PAGE_HEIGHT = A4
CARD_WIDTH = PAGE_WIDTH / 2
CARD_HEIGHT = PAGE_HEIGHT / 2

def draw_field(pdf: Canvas, field: FieldLayout, data: dict, x_offset: float, y_offset: float) -> None:
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

def draw_card_border(pdf: Canvas, x_offset: float, y_offset: float) -> None:
    """Draw a border for the card with a light gray color and reset drawing properties."""
    pdf.setStrokeColor(colors.gray)  # Set the stroke color to light gray
    pdf.setLineWidth(0.5)     # Make the border thinner
    pdf.rect(x_offset, y_offset, CARD_WIDTH, CARD_HEIGHT, stroke=1, fill=0)

    # Reset to original stroke color and line width
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)

def draw_cover_art(pdf: Canvas, card: dict[str, Any], x_offset: float, y_offset: float, back: bool = False) -> None:
    """Draw cover art on the card using binary image data."""

    image_data = card.get("cover_art")

    if not image_data:
        return  # Skip if no cover art is provided
    
    cycles = 0
    while is_dark(image_data):
        cycles += 1
        # print(f"{card.get("title")}: is dark, lightening")
        image_data = lighten_image(image_data, factor=1.5)
        if cycles > 2:
            break

    if back:
        image_size = CARD_WIDTH * .41
        padding = CARD_WIDTH / 16
        image_x = x_offset + padding
        image_y = y_offset + CARD_HEIGHT - image_size - (padding * 3)  # Top of the card with padding
    else:
        image_size = CARD_WIDTH / 8 * 7  
        padding = CARD_WIDTH / 16
        image_x = x_offset + padding  # Center horizontally
        image_y = y_offset + CARD_HEIGHT - image_size - (padding * 3) + 15  # Top of the card with padding

    try:
        image_stream = BytesIO(image_data)
        image = ImageReader(image_stream)
        pdf.drawImage(image, image_x, image_y, width=image_size, height=image_size, preserveAspectRatio=True, anchor="n")
    except Exception as e:
        print(f"Error drawing image from binary data, {e}")
        exit()

# Draw the QR code on the card
def draw_qr_code(pdf: Canvas, card: dict[str, Any], x_offset: float, y_offset: float, back: bool = False) -> None:
    """
    Draws a QR code on the card.

    Args:
        qr_image (BytesIO): The file-like object containing the QR code image.
        x_offset (float): The X-coordinate of the card.
        y_offset (float): The Y-coordinate of the card.
    """
    try:
        title = card.get("search", "<missing>")
        qr_image = generate_qr_code(title)  
        image = ImageReader(qr_image)

        # Define size and position for the QR code
        qr_size = CARD_WIDTH * .5 if back else CARD_WIDTH / 3  # Scale the QR code to fit nicely
        qr_x = x_offset + (CARD_WIDTH - qr_size) / 2  # Center horizontally
        qr_y = y_offset + CARD_HEIGHT / 4  # Position in the middle of the back

        pdf.drawImage(image, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error drawing QR code: {e}")