from datetime import datetime
from dj_tools.version_history import VersionHistory
from .utils import list_mp3_files

from .field_layout import FieldLayout

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


from .card_layout import (
    UNPRINTABLE_BORDER,
    PAGE_HEIGHT, PAGE_WIDTH, CARD_HEIGHT, CARD_WIDTH, CardLayout
)

from .metadata_extraction import extract_mp3_metadata

DEBUG = False

left_edge = 0
right_edge = CARD_WIDTH
top_edge = CARD_HEIGHT
bottom_edge = 0

center = CARD_WIDTH / 2

top_text_line_y = top_edge - 10
next_text_line_y = top_text_line_y - 14

front_art_size = CARD_WIDTH
front_art_x = left_edge
front_art_y = next_text_line_y - front_art_size - 5
under_front_art = front_art_y - 10

front_qr_size = CARD_WIDTH * .3
front_qr_x = right_edge-front_qr_size
front_qr_y = bottom_edge



back_art_size = CARD_WIDTH * .49
back_art_x = left_edge
back_art_y = next_text_line_y - back_art_size - 5
under_back_art = back_art_y - 10

back_qr_size = back_art_size
back_qr_x = right_edge-back_qr_size
back_qr_y = back_art_y

datestamp = datetime.now().strftime("%Y-%m-%d")

field_layouts = [
    # Front
    FieldLayout("title", "front", x=left_edge, y=top_text_line_y, justification="left", font="Helvetica-Bold", font_size=12, width=200, max_lines=1),
    FieldLayout("artist", "front", x=left_edge, y=next_text_line_y, justification="left", font="Helvetica", font_size=10),
    
    FieldLayout("rating", "front", x=right_edge - 2, y=top_text_line_y, justification="right", font="Helvetica", font_size=12),
    FieldLayout("key_bpm", "front", x=right_edge - 1, y=next_text_line_y, justification="right", font="Helvetica", font_size=10),
    FieldLayout("duration", "front", x=center, y=next_text_line_y, justification="between:artist&key_bpm", font="Helvetica", font_size=10),

    FieldLayout("label", "front", x=left_edge, y=under_front_art, justification="left", font="Helvetica", font_size=9),
    FieldLayout("genre", "front", x=right_edge, y=under_front_art, justification="right", font="Helvetica", font_size=9),
    FieldLayout("release_date", "front", x=center, y=under_front_art, justification="between:label&genre", font="Helvetica", font_size=9),

    FieldLayout("user_comment", "front", x=left_edge, y=under_front_art - 20, justification="left", font="Helvetica", font_size=10, width=CARD_WIDTH * .5),

    # Back
    FieldLayout("title", "back", x=left_edge, y=top_text_line_y, justification="left", font="Helvetica-Bold", font_size=10, width=200, max_lines=1),
    FieldLayout("artist", "back", x=left_edge, y=next_text_line_y, justification="left", font="Helvetica", font_size=10),
    
    FieldLayout("rating", "back", x=right_edge - 2, y=top_text_line_y, justification="right", font="Helvetica", font_size=12),
    FieldLayout("key_bpm", "back", x=right_edge - 1, y=next_text_line_y, justification="right", font="Helvetica", font_size=10),
    FieldLayout("duration", "back", x=center, y=next_text_line_y, justification="between:artist&key_bpm", font="Helvetica", font_size=10),

    FieldLayout("label", "back", x=left_edge, y=under_back_art, justification="left", font="Helvetica", font_size=9),
    FieldLayout("genre", "back", x=right_edge, y=under_back_art, justification="right", font="Helvetica", font_size=9),
    FieldLayout("release_date", "back", x=center, y=under_back_art, justification="between:label&genre", font="Helvetica", font_size=9),

    FieldLayout("user_comment", "back", x=left_edge, y=under_back_art - 40, justification="left", font="Helvetica", font_size=14, width=CARD_WIDTH * .9),
    FieldLayout("user_comment_2", "back", x=left_edge, y=under_back_art - 80, justification="left", font="Helvetica", font_size=14, width=CARD_WIDTH * .9),

    FieldLayout("rev", "back", x=left_edge + 2, y=bottom_edge + 2, justification="left", font="Helvetica", font_size=8, prefix="rev_"),
    FieldLayout("datestamp", "back", x=right_edge - 2, y=bottom_edge + 2, justification="right", font="Helvetica", font_size=8, prefix=datestamp),
]


def _card_offset(j: int, front: bool) -> tuple[float, float]:
    i = j if front else j+1
    x_offset = (i % 2) * (PAGE_WIDTH / 2)
    if x_offset == 0:
        x_offset = UNPRINTABLE_BORDER
    else:
        x_offset = x_offset + UNPRINTABLE_BORDER
    
    y_offset = PAGE_HEIGHT - ((j // 2) + 1) * (PAGE_HEIGHT / 2)
    
    if y_offset == 0:
        y_offset = UNPRINTABLE_BORDER 
    else:
        y_offset = y_offset + UNPRINTABLE_BORDER
    return x_offset, y_offset


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
            x_offset, y_offset = _card_offset(j, True)

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
            x_offset, y_offset = _card_offset(j, False)

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
    files = list_mp3_files("/Users/epinzur/Desktop/Music/Traktor/dnb")
    history = VersionHistory("data/track_history")
    data = []
    for file in files:

        metadata = extract_mp3_metadata(file)
        # if metadata.get("stars", 0) < 4:
        #     continue

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

    


