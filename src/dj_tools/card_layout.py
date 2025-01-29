from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader, simpleSplit
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


class CardLayout:
    def __init__(
        self, x_offset: float, y_offset: float, pdf: Canvas, card: dict[str, Any]
    ):
        self.inner_widths: dict[str, float] = {}
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.card = card
        self.pdf = pdf

    def draw_field(
        self,
        field: FieldLayout,
    ) -> int:
        """Draw a single field on the card with text wrapping, returning the number of lines used.

        Args:
            pdf (Canvas): The ReportLab canvas.
            field (FieldLayout): The field layout details.
            data (dict): The data containing field values.
            x_offset (float): X position offset.
            y_offset (float): Y position offset.

        Returns:
            int: The number of lines used
        """
        value = self.card.get(field.field_name, "")
        if not value and field.field_name is not "datestamp":
            return 0  # No text drawn
        
        if value == "Purchased at Traxsource.com":
            return 0

        value = f"{field.prefix}{value}"
        self.pdf.setFont(field.font, field.font_size)

        text_x = self.x_offset + field.x
        text_y = self.y_offset + field.y

        # Wrap text using simpleSplit
        wrapped_lines = simpleSplit(value, field.font, field.font_size, field.width)

        if len(wrapped_lines) > field.max_lines:
            wrapped_lines = wrapped_lines[: field.max_lines]  # Keep only allowed lines

        max_width = 0

        # Adjust for justification and draw lines
        for line in wrapped_lines:
            text_width = self.pdf.stringWidth(line, field.font, field.font_size)
            max_width = max(max_width, text_width)
            if field.justification == "right":
                draw_x = text_x - text_width
            elif field.justification == "center":
                draw_x = text_x - text_width / 2
            elif field.justification == "left":
                draw_x = text_x
            elif field.justification.startswith("between_"):
                between = field.justification.split("_")
                left = self.inner_widths[between[1]]
                right = self.inner_widths[between[2]]
                draw_x = (left + right - text_width) / 2

            self.pdf.drawString(draw_x, text_y, line)
            text_y -= field.font_size * 1.2  # Move to the next line with spacing

            if field.justification == "right":
                self.inner_widths[field.field_name] = text_x - max_width
            elif field.justification == "left":
                self.inner_widths[field.field_name] = text_x + max_width
            else:
                draw_x = text_x

        return len(wrapped_lines)

    def draw_card_border(self) -> None:
        """Draw a border for the card with a light gray color and reset drawing properties."""
        self.pdf.setStrokeColor(colors.gray)  # Set the stroke color to light gray
        self.pdf.setLineWidth(0.5)  # Make the border thinner
        self.pdf.rect(
            self.x_offset, self.y_offset, CARD_WIDTH, CARD_HEIGHT, stroke=1, fill=0
        )

        # Reset to original stroke color and line width
        self.pdf.setStrokeColor(colors.black)
        self.pdf.setLineWidth(1)

    def _draw_image(self, image_data: bytes, x: float, y: float, size: float):
        try:
            image = ImageReader(image_data)
            x = self.x_offset + x
            y = self.y_offset + y
            self.pdf.drawImage(
                image,
                x=x,
                y=y,
                width=size,
                height=size,
                preserveAspectRatio=True,
                anchor="n",
            )
        except Exception as e:
            print(f"Error drawing image from binary data, {e}")

    def draw_cover_art(self, x: float, y: float, size: float) -> None:
        """Draw cover art on the card using binary image data."""

        image_data = self.card.get("cover_art")
        if not image_data:
            return

        cycles = 0
        while is_dark(image_data):
            cycles += 1
            # print(f"{card.get("title")}: is dark, lightening")
            image_data = lighten_image(image_data, factor=1.5)
            if cycles > 2:
                break

        self._draw_image(image_data=BytesIO(image_data), x=x, y=y, size=size)

    # Draw the QR code on the card
    def draw_qr_code(self, x: float, y: float, size: float) -> None:
        search = self.card.get("search")
        if search is None:
            return

        qr_image = generate_qr_code(search)
        self._draw_image(image_data=qr_image, x=x, y=y, size=size)
