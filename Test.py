import sys
import cv2
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QLabel
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

# Load the UI file
ui_file = "GUI.ui"  # Replace with your UI file path
Ui_MainWindow, _ = uic.loadUiType(ui_file)

class MainWindow(QDialog, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.show_forward_picture)
        self.pushButton_2.clicked.connect(self.show_backward_picture)
        self.image_folder = "yes"  # Path to the folder containing the images
        self.image_files = glob.glob(os.path.join(self.image_folder, "*.jpg"))
        self.current_image_index = 0

        # Replace "your_object_name" with the actual object name of the QLabel widget from your UI file
        self.image_label = self.findChild(QLabel, "your_object_name")

        # Display the first image
        if self.image_files:
            self.display_image()

    def show_forward_picture(self):
        self.current_image_index += 1
        if self.current_image_index >= len(self.image_files):
            self.current_image_index = 0
        self.display_image()

    def show_backward_picture(self):
        self.current_image_index -= 1
        if self.current_image_index < 0:
            self.current_image_index = len(self.image_files) - 1
        self.display_image()

    def display_image(self):
        image_path = self.image_files[self.current_image_index]
        image = cv2.imread(image_path)

        # Check if the image was loaded successfully
        if image is None:
            print("Failed to load image:", image_path)
            return

        # Resize the image
        dim = (500, 590)
        image = cv2.resize(image, dim)

        # Convert to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Create QImage from the image data
        qimage = QImage(image_rgb.data, image_rgb.shape[1], image_rgb.shape[0], QImage.Format_RGB888)

        # Create QPixmap from the QImage
        qpixmap = QPixmap.fromImage(qimage)

        # Scale the QPixmap to fit the label
        scaled_pixmap = qpixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)

        # Clear the label
        self.image_label.clear()

        # Set the scaled QPixmap as the label's pixmap
        self.image_label.setPixmap(scaled_pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())