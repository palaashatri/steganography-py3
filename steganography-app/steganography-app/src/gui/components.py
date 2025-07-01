from PyQt5.QtWidgets import (QPushButton, QLineEdit, QLabel, QFileDialog, QWidget, 
                            QVBoxLayout, QHBoxLayout, QProgressDialog,
                            QScrollArea, QGridLayout, QGroupBox,
                            QGraphicsView, QGraphicsScene)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class CustomButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px;")

class CustomLineEdit(QLineEdit):
    def __init__(self, placeholder_text, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self.setStyleSheet("font-size: 14px; padding: 5px;")

class CustomLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("font-size: 14px; font-weight: bold;")

class FileSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.label = CustomLabel("Select File:", self)
        self.line_edit = CustomLineEdit("No file selected", self)
        self.button = CustomButton("Browse", self)
        self.button.clicked.connect(self.open_file_dialog)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Image Files (*.png;*.jpg;*.jpeg)", options=options)
        if file_name:
            self.line_edit.setText(file_name)

class ImagePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Image Preview")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Graphics view for image display
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setMinimumSize(400, 300)
        layout.addWidget(self.graphics_view)
        
        # Image info
        self.image_info = QLabel("No image loaded")
        self.image_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_info)
        
    def load_image(self, image_path):
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.graphics_scene.clear()
                # Scale image to fit view
                scaled_pixmap = pixmap.scaled(
                    400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.graphics_scene.addPixmap(scaled_pixmap)
                self.graphics_view.fitInView(
                    self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio
                )
                
                # Update info
                self.image_info.setText(
                    f"Size: {pixmap.width()}x{pixmap.height()} pixels"
                )
            else:
                self.image_info.setText("Failed to load image")
        except (IOError, OSError) as e:
            self.image_info.setText(f"Error: {str(e)}")
    
    def clear_image(self):
        self.graphics_scene.clear()
        self.image_info.setText("No image loaded")

class ProgressDialog(QProgressDialog):
    def __init__(self, title="Processing", label="Please wait...", parent=None):
        super().__init__(label, "Cancel", 0, 100, parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumDuration(0)
        
    def update_progress(self, value, text=None):
        self.setValue(value)
        if text:
            self.setLabelText(text)

class AnalysisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Analysis results area
        self.results_area = QScrollArea()
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        
        # Metrics display
        self.metrics_group = QGroupBox("Quality Metrics")
        self.metrics_layout = QGridLayout(self.metrics_group)
        
        self.psnr_label = QLabel("PSNR: --")
        self.ssim_label = QLabel("SSIM: --")
        self.mse_label = QLabel("MSE: --")
        self.capacity_label = QLabel("Capacity: --")
        
        self.metrics_layout.addWidget(QLabel("Peak Signal-to-Noise Ratio:"), 0, 0)
        self.metrics_layout.addWidget(self.psnr_label, 0, 1)
        self.metrics_layout.addWidget(QLabel("Structural Similarity:"), 1, 0)
        self.metrics_layout.addWidget(self.ssim_label, 1, 1)
        self.metrics_layout.addWidget(QLabel("Mean Squared Error:"), 2, 0)
        self.metrics_layout.addWidget(self.mse_label, 2, 1)
        self.metrics_layout.addWidget(QLabel("Embedding Capacity:"), 3, 0)
        self.metrics_layout.addWidget(self.capacity_label, 3, 1)
        
        self.results_layout.addWidget(self.metrics_group)
        
        # Histogram display
        self.histogram_group = QGroupBox("Image Histogram")
        histogram_layout = QVBoxLayout(self.histogram_group)
        
        self.histogram_canvas = HistogramCanvas()
        histogram_layout.addWidget(self.histogram_canvas)
        
        self.results_layout.addWidget(self.histogram_group)
        
        self.results_area.setWidget(self.results_widget)
        layout.addWidget(self.results_area)
        
    def update_metrics(self, metrics):
        if 'psnr' in metrics:
            self.psnr_label.setText(f"{metrics['psnr']:.2f} dB")
        if 'ssim' in metrics:
            self.ssim_label.setText(f"{metrics['ssim']:.4f}")
        if 'mse' in metrics:
            self.mse_label.setText(f"{metrics['mse']:.2f}")
        if 'capacity' in metrics:
            self.capacity_label.setText(f"{metrics['capacity']} bytes")
    
    def update_histogram(self, image_array):
        self.histogram_canvas.plot_histogram(image_array)

class HistogramCanvas(FigureCanvas):
    def __init__(self):
        self.figure = Figure(figsize=(8, 4))
        super().__init__(self.figure)
        self.axes = self.figure.add_subplot(111)
        
    def plot_histogram(self, image_array):
        self.axes.clear()
        
        if len(image_array.shape) == 3:  # Color image
            colors = ['red', 'green', 'blue']
            for i, color in enumerate(colors):
                hist, bins = np.histogram(image_array[:, :, i], bins=256, range=(0, 256))
                self.axes.plot(bins[:-1], hist, color=color, alpha=0.7, label=color.upper())
            self.axes.legend()
        else:  # Grayscale image
            hist, bins = np.histogram(image_array, bins=256, range=(0, 256))
            self.axes.plot(bins[:-1], hist, color='gray')
            
        self.axes.set_xlabel('Pixel Value')
        self.axes.set_ylabel('Frequency')
        self.axes.set_title('Image Histogram')
        self.figure.tight_layout()
        self.draw()