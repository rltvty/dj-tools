class FieldLayout:
    def __init__(
        self, 
        field_name: str, 
        side: str, 
        x: float, 
        y: float, 
        justification: str = "left", 
        font: str = "Helvetica", 
        font_size: int = 10
    ):
        """
        Layout configuration for a metadata field.

        Args:
            field_name (str): The name of the metadata field.
            side (str): 'front' or 'back' of the card.
            x (float): X-coordinate for the field.
            y (float): Y-coordinate for the field.
            justification (str): 'left', 'center', or 'right' alignment.
            font (str): Font family for the field text.
            font_size (int): Font size for the field text.
        """
        self.field_name = field_name
        self.side = side
        self.x = x
        self.y = y
        self.justification = justification
        self.font = font
        self.font_size = font_size
