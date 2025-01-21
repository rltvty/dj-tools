from PIL import Image, ImageEnhance
from io import BytesIO
import numpy as np
import qrcode


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
