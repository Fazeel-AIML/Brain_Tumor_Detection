import os
import cv2
import numpy as np
import glob

from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from qtpy.QtGui import QImage, QPixmap, QFont
from qtpy.QtCore import Qt

class ImageDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.current_index = 0
        self.image_files = []
        self.pixel_to_cm = 0.0001  # Example conversion factor, replace with your own
        self.max_size_cm = 15  # Example maximum size, replace with your own

        self.image_label = QLabel(self)
        self.size_label = QLabel(self)
        self.size_label.setAlignment(Qt.AlignCenter)
        self.forward_button = QPushButton('Forward', self)
        self.backward_button = QPushButton('Backward', self)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.size_label)
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.forward_button)
        self.layout.addWidget(self.backward_button)
        self.setLayout(self.layout)

        self.forward_button.clicked.connect(self.show_forward_image)
        self.backward_button.clicked.connect(self.show_backward_image)

        # Increase the font size and make the tumor size text bold
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        
        self.size_label.setFont(font)
        self.forward_button.setFont(font)
        self.backward_button.setFont(font)

    def load_image_files(self, folder):
        self.image_files = glob.glob(os.path.join(folder, "*.jpg"))
        self.current_index = 0

    def calculate_tumor_size(self, contour, pixel_to_cm):
        # Calculate the area of the contour
        area = cv2.contourArea(contour)

        # Convert the tumor size from pixels to centimeters
        tumor_size_cm = area * pixel_to_cm

        return tumor_size_cm

    def detect_tumor_size(self, image_path, pixel_to_cm, max_size_cm):
        try:
            # Load the image
            image = cv2.imread(image_path)

            if image is None:
                raise Exception("Failed to load the image")

            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Apply Canny edge detection to identify edges
            edges = cv2.Canny(blurred, 30, 150)

            # Find contours of the tumor
            contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Iterate over contours and calculate the size of the tumor
            tumor_size = 0
            tumor_contour = None
            for contour in contours:
                # Calculate the area of each contour
                area = cv2.contourArea(contour)

                # Exclude small contours and select the largest contour
                if area > tumor_size:
                    tumor_size = area
                    tumor_contour = contour

            # Convert tumor size from pixels to centimeters
            tumor_size_cm = self.calculate_tumor_size(tumor_contour, pixel_to_cm)

            # Check if tumor size exceeds the maximum allowed size
            if tumor_size_cm > max_size_cm:
                raise Exception("Tumor size exceeds the maximum allowed size")

            # Return the total tumor size in centimeters and the selected contour
            return tumor_size_cm, tumor_contour

        except Exception as e:
            print("Error:", str(e))
            return None, None

    def show_image(self, index):
        if 0 <= index < len(self.image_files):
            image_path = self.image_files[index]
            image = cv2.imread(image_path)

            if image is None:
                print("Failed to load the image:", image_path)
                return

            # Resize the image
            dim = (500, 500)
            image = cv2.resize(image, dim)

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply thresholding
            (T, thresh) = cv2.threshold(gray, 145, 155, cv2.THRESH_BINARY)
            (T, threshInv) = cv2.threshold(gray, 145, 155, cv2.THRESH_BINARY_INV)

            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            closed = cv2.erode(closed, None, iterations=19)
            closed = cv2.dilate(closed, None, iterations=19)

            # Masking
            ret, mask = cv2.threshold(closed, 145, 255, cv2.THRESH_BINARY)
            final = cv2.bitwise_and(image, image, mask=mask)

            # Canny edge detection
            def auto_canny(image, sigma=0.90):
                v = np.median(image)
                lower = int(max(0, (1.0 - sigma) * v))
                upper = int(min(255, (1.0 + sigma) * v))
                edged = cv2.Canny(image, lower, upper)
                return edged

            canny = auto_canny(closed)

            # Contour detection and drawing
            (cnts, _) = cv2.findContours(canny.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Initialize the tumor contour
            tumor_contour = None

            # Find the largest contour
            if len(cnts) > 0:
                tumor_contour = max(cnts, key=cv2.contourArea)

            if tumor_contour is not None:
                # Calculate the tumor size based on the contour
                size = self.calculate_tumor_size(tumor_contour, self.pixel_to_cm)

                # Check if tumor size exceeds the maximum allowed size
                if size > self.max_size_cm:
                    print("Tumor size exceeds the maximum allowed size")
                else:
                    # Draw the tumor contour on the image
                    cv2.drawContours(image, [tumor_contour], -1, (0, 0, 255), 6)

                    # Update the tumor size label
                    self.size_label.setText("Tumor size: {:.2f} cm".format(size))

            else:
                self.size_label.setText("No tumor contour found in the image.")

            # Convert the image to QImage
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # Convert QImage to QPixmap
            pixmap = QPixmap.fromImage(q_image)

            # Display the image
            self.image_label.setPixmap(pixmap)
            self.image_label.setScaledContents(True)

        else:
            print("Invalid image index")

    def show_forward_image(self):
        self.current_index += 1
        if self.current_index >= len(self.image_files):
            self.current_index = 0
        self.show_image(self.current_index)

    def show_backward_image(self):
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.image_files) - 1
        self.show_image(self.current_index)


# Path to the folder containing the images
image_folder = "Test_Images"

# Create the application
app = QApplication([])

# Create the main window
window = QMainWindow()
window.setWindowTitle("Tumor Image Viewer")
window.setGeometry(200, 30, 100, 150)


# Create the image display widget
image_display_widget = ImageDisplayWidget()
image_display_widget.load_image_files(image_folder)
image_display_widget.show_image(0)

# Set the image display widget as the central widget of the main window
window.setCentralWidget(image_display_widget)

# Show the main window
window.show()

# Run the application
app.exec_()