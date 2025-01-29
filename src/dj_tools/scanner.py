import cv2
from pyzbar.pyzbar import decode
import pyperclip
import numpy as np


def scan_qr_code():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Scanning for QR codes. Press 'q' to quit.")

    last_qr_data = None  # To store the last seen QR code data

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            break

        # Decode QR codes in the frame
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")  # Extract QR code data

            # Only process and copy if it's different from the last QR code
            if qr_data != last_qr_data:
                print(f"New QR Code Data: {qr_data}")
                pyperclip.copy(qr_data)  # Copy to clipboard
                print("QR Code data copied to clipboard!")
                last_qr_data = qr_data

            # Draw a rectangle around the QR code
            points = obj.polygon
            if points:
                # Convert points to a NumPy array
                pts = np.array(
                    [(int(point.x), int(point.y)) for point in points], dtype=np.int32
                )
                cv2.polylines(
                    frame, [pts], isClosed=True, color=(0, 255, 0), thickness=3
                )

        # Display the frame
        cv2.imshow("QR Code Scanner", frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# Run the scanner
scan_qr_code()
