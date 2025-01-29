from datetime import datetime
from dj_tools.version_history import VersionHistory
from .utils import list_mp3_files

from .field_layout import FieldLayout

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .card_layout import (
    PAGE_HEIGHT, PAGE_WIDTH, CARD_HEIGHT, CARD_WIDTH, CardLayout
)

from .metadata_extraction import extract_mp3_metadata

DEBUG = False

left_edge = 10
right_edge = CARD_WIDTH - 20
top_edge = CARD_HEIGHT - 20
bottom_edge = 10

center = CARD_WIDTH / 2

# image x,y are from lower left corner
# 0,0 is lower left of the card
front_art_size = CARD_WIDTH * .9
front_art_x = left_edge+3
front_art_y = top_edge - front_art_size - 18
under_front_art = front_art_y - 12

front_qr_size = CARD_WIDTH * .29
front_qr_x = right_edge-front_qr_size+2
front_qr_y = bottom_edge

back_art_size = CARD_WIDTH * .41
back_art_x = left_edge + 5
back_art_y = top_edge - back_art_size - 18
under_back_art = back_art_y - 12

back_qr_size = back_art_size
back_qr_x = right_edge-back_qr_size
back_qr_y = back_art_y

datestamp = datetime.now().strftime("%Y-%m-%d")

field_layouts = [
    # Front
    FieldLayout("title", "front", x=left_edge, y=top_edge, justification="left", font="Helvetica-Bold", font_size=12, width=225, max_lines=1),
    FieldLayout("artist", "front", x=left_edge, y=top_edge - 13, justification="left", font="Helvetica", font_size=10),
    
    FieldLayout("rating", "front", x=right_edge, y=top_edge, justification="right", font="Helvetica", font_size=12),
    FieldLayout("key_bpm", "front", x=right_edge, y=top_edge - 14, justification="right", font="Helvetica", font_size=10),

    FieldLayout("label", "front", x=left_edge, y=under_front_art, justification="left", font="Helvetica", font_size=10),
    FieldLayout("genre", "front", x=right_edge, y=under_front_art, justification="right", font="Helvetica", font_size=10),
    FieldLayout("release_date", "front", x=center, y=under_front_art, justification="between_label_genre", font="Helvetica", font_size=10),

    FieldLayout("user_comment", "front", x=left_edge, y=under_front_art - 20, justification="left", font="Helvetica", font_size=10, width=CARD_WIDTH * .5),

    # Back
    FieldLayout("title", "back", x=left_edge, y=top_edge, justification="left", font="Helvetica-Bold", font_size=10, width=225, max_lines=1),
    FieldLayout("artist", "back", x=left_edge, y=top_edge - 13, justification="left", font="Helvetica", font_size=10),
    
    FieldLayout("rating", "back", x=right_edge, y=top_edge, justification="right", font="Helvetica", font_size=12),
    FieldLayout("key_bpm", "back", x=right_edge, y=top_edge - 14, justification="right", font="Helvetica", font_size=10),

    FieldLayout("label", "back", x=left_edge, y=under_back_art, justification="left", font="Helvetica", font_size=10),
    FieldLayout("genre", "back", x=right_edge, y=under_back_art, justification="right", font="Helvetica", font_size=10),
    FieldLayout("release_date", "back", x=center, y=under_back_art, justification="between_label_genre", font="Helvetica", font_size=10),

    FieldLayout("user_comment", "back", x=left_edge, y=under_back_art - 40, justification="left", font="Helvetica", font_size=14, width=CARD_WIDTH * .9),
    FieldLayout("user_comment_2", "back", x=left_edge, y=under_back_art - 80, justification="left", font="Helvetica", font_size=14, width=CARD_WIDTH * .9),

    FieldLayout("rev", "back", x=left_edge, y=bottom_edge, justification="left", font="Helvetica", font_size=8, prefix="rev_"),
    FieldLayout("datestamp", "back", x=right_edge, y=bottom_edge, justification="right", font="Helvetica", font_size=8, prefix=datestamp),
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

            layout = CardLayout(x_offset=x_offset, y_offset=y_offset, pdf=pdf, card=card)
            if DEBUG:
                layout.draw_card_border()
            layout.draw_cover_art(x=front_art_x, y=front_art_y, size=front_art_size)
            layout.draw_qr_code(x=front_qr_x, y=front_qr_y, size = front_qr_size)

            # Draw fields on the front
            for field in layouts:
                if field.side == "front":
                    lines = layout.draw_field(field)

        pdf.showPage()  # Add new page for the back side

        # Draw back of the cards
        for j, card in enumerate(current_cards):
            x_offset = (j % 2) * CARD_WIDTH
            y_offset = PAGE_HEIGHT - ((j // 2) + 1) * CARD_HEIGHT

            layout = CardLayout(x_offset=x_offset, y_offset=y_offset, pdf=pdf, card=card)
            if DEBUG:
                layout.draw_card_border()
            layout.draw_cover_art(x=back_art_x, y=back_art_y, size=back_art_size)
            layout.draw_qr_code(x=back_qr_x, y=back_qr_y, size = back_qr_size)

            # Draw fields on the back
            for field in layouts:
                if field.side == "back":
                    lines = layout.draw_field(field)

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

        if not metadata.get("cover_art"):
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

    if not DEBUG:
        history.save_new_versions(timestamp)

    


