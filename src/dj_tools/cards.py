from datetime import datetime
from dj_tools.version_history import VersionHistory
from .utils import list_mp3_files

from .field_layout import FieldLayout

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .card_layout import (
    PAGE_HEIGHT, PAGE_WIDTH, CARD_HEIGHT, CARD_WIDTH, draw_card_border, draw_cover_art, draw_field, draw_qr_code
)

from .metadata_extraction import extract_mp3_metadata

field_layouts = [
    # Front
    FieldLayout("title", "front", 10, CARD_HEIGHT - 20, justification="left", font="Helvetica-Bold", font_size=12),
    FieldLayout("artist", "front", 10, CARD_HEIGHT - 33, justification="left", font="Helvetica", font_size=10),
    
    FieldLayout("rating", "front", CARD_WIDTH - 20, CARD_HEIGHT - 20, justification="right", font="Helvetica", font_size=12),
    FieldLayout("key_bpm", "front", CARD_WIDTH - 20, CARD_HEIGHT - 34, justification="right", font="Helvetica", font_size=10),

    FieldLayout("label", "front", 10, 105, justification="left", font="Helvetica", font_size=10),
    FieldLayout("genre", "front", CARD_WIDTH - 20, 105, justification="right", font="Helvetica", font_size=10),
    FieldLayout("release_date", "front", CARD_WIDTH / 2, 105, justification="center", font="Helvetica", font_size=10),

    # Back
    FieldLayout("title", "back", 10, CARD_HEIGHT - 20, justification="left", font="Helvetica-Bold", font_size=12),
    FieldLayout("artist", "back", 10, CARD_HEIGHT - 33, justification="left", font="Helvetica", font_size=10),
    
    FieldLayout("rating", "back", CARD_WIDTH - 20, CARD_HEIGHT - 20, justification="right", font="Helvetica", font_size=12),
    FieldLayout("key_bpm", "back", CARD_WIDTH - 20, CARD_HEIGHT - 34, justification="right", font="Helvetica", font_size=10),

    FieldLayout("label", "back", 10, CARD_HEIGHT - 46, justification="left", font="Helvetica", font_size=10),
    FieldLayout("genre", "back", CARD_WIDTH - 20, CARD_HEIGHT - 46, justification="right", font="Helvetica", font_size=10),
    FieldLayout("release_date", "back", CARD_WIDTH / 2, CARD_HEIGHT - 46, justification="center", font="Helvetica", font_size=10),

    FieldLayout("user_comment", "back", 10, CARD_HEIGHT - 200, justification="left", font="Helvetica", font_size=10),
]




def create_pdf_with_layout(output_path: str, cards: list[dict], layouts: list[FieldLayout]) -> None:
    """
    Generates a PDF with A6 cards laid out on A4 paper, using layout instructions.

    Args:
        output_path (str): Path to save the generated PDF.
        cards (list[dict]): List of metadata dictionaries for each card.
        layouts (list[FieldLayout]): Layout instructions for fields.
    """
    if len(cards) == 0:
        print("No new cards to output")
        return

    pdf = canvas.Canvas(output_path, pagesize=A4)

    for i in range(0, len(cards), 4):
        current_cards = cards[i:i + 4]

        # Draw front of the cards
        for j, card in enumerate(current_cards):
            x_offset = (j % 2) * CARD_WIDTH
            y_offset = PAGE_HEIGHT - ((j // 2) + 1) * CARD_HEIGHT

            draw_card_border(pdf, x_offset, y_offset)

            draw_cover_art(pdf, card, x_offset, y_offset)

            draw_qr_code(pdf, card, x_offset + 90, y_offset - 100)

            # Draw fields on the front
            for field in layouts:
                if field.side == "front":
                    draw_field(pdf, field, card, x_offset, y_offset)

        pdf.showPage()  # Add new page for the back side

        # Draw back of the cards
        for j, card in enumerate(current_cards):
            x_offset = (j % 2) * CARD_WIDTH
            y_offset = PAGE_HEIGHT - ((j // 2) + 1) * CARD_HEIGHT

            draw_card_border(pdf, x_offset, y_offset)
            draw_cover_art(pdf, card, x_offset, y_offset, back=True)
            draw_qr_code(pdf, card, x_offset + 70, y_offset + 125, back=True)

            # Draw fields on the back
            for field in layouts:
                if field.side == "back":
                    draw_field(pdf, field, card, x_offset, y_offset)

        pdf.showPage()  # Finish the page

    pdf.save()


def main():
    files = list_mp3_files("/Users/epinzur/Desktop/Music/Traktor/")
    history = VersionHistory("data/track_history")
    data = []
    for file in files:

        metadata = extract_mp3_metadata(file)
        if metadata.get("stars", 0) < 4:
            continue

        item = history.convert_metadata(metadata)
        (new, v) = history.get_create_version(item)
        if new:
            metadata["rev"] = v
            item["rev"] = v
            history.add_new_version(item)
            data.append(metadata)

    timestamp = datetime.now().strftime("%Y-%m-%d@%H:%M")

    create_pdf_with_layout(f"new_cards_{timestamp}.pdf", data, field_layouts)

    history.save_new_versions(timestamp)

    


