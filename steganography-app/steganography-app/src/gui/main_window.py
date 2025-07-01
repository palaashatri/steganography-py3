from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QFileDialog, QProgressBar, QGroupBox,
                            QGridLayout, QComboBox, QCheckBox, QSpinBox,
                            QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from core.steganography import SteganographyEngine
from core.encryption import EncryptionManager
from analysis.quality_metrics import QualityAnalyzer
from gui.components import ImagePreviewWidget, AnalysisWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stego_engine = SteganographyEngine()
        self.encryption_manager = EncryptionManager()
        self.quality_analyzer = QualityAnalyzer()
        
        # Initialize timer references
        self._encode_timer = None
        self._decode_timer = None
        self._encode_future = None
        self._decode_future = None
        self._encode_callback = None
        self._decode_callback = None
        
        self.init_ui()
        self.setup_drag_drop()
        
    def init_ui(self):
        self.setWindowTitle("steganography-py3 GUI")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setStyleSheet(self.get_modern_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_preview_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([500, 900])
        
        self.statusBar().showMessage("Ready")
        self.create_menu_bar()
        
    def create_control_panel(self):
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)
        
        self.tab_widget = QTabWidget()
        
        encode_tab = self.create_encode_tab()
        self.tab_widget.addTab(encode_tab, "🔒 Encode")
        
        decode_tab = self.create_decode_tab()
        self.tab_widget.addTab(decode_tab, "🔓 Decode")
        
        batch_tab = self.create_batch_tab()
        self.tab_widget.addTab(batch_tab, "📦 Batch")
        
        analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(analysis_tab, "📊 Analysis")
        
        layout.addWidget(self.tab_widget)
        return control_widget
    
    def create_encode_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        image_group = QGroupBox("📷 Image Selection")
        image_layout = QVBoxLayout(image_group)
        
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("Select or drag & drop an image...")
        self.image_path_edit.setReadOnly(True)
        
        browse_btn = QPushButton("Browse Image")
        browse_btn.clicked.connect(self.browse_image)
        
        image_layout.addWidget(self.image_path_edit)
        image_layout.addWidget(browse_btn)
        layout.addWidget(image_group)
        
        message_group = QGroupBox("📝 Secret Message")
        message_layout = QVBoxLayout(message_group)
        
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText("Enter your secret message here...")
        self.message_text.setMaximumHeight(150)
        
        self.message_stats = QLabel("Characters: 0 | Bytes: 0")
        self.message_text.textChanged.connect(self.update_message_stats)
        
        message_layout.addWidget(self.message_text)
        message_layout.addWidget(self.message_stats)
        layout.addWidget(message_group)
        
        security_group = QGroupBox("🔐 Security Options")
        security_layout = QGridLayout(security_group)
        
        self.encryption_enabled = QCheckBox("Enable Encryption")
        self.encryption_enabled.setChecked(True)
        security_layout.addWidget(self.encryption_enabled, 0, 0, 1, 2)
        
        security_layout.addWidget(QLabel("Password:"), 1, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter encryption password")
        security_layout.addWidget(self.password_edit, 1, 1)
        
        security_layout.addWidget(QLabel("Algorithm:"), 2, 0)
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["AES-256", "ChaCha20", "Fernet"])
        security_layout.addWidget(self.algorithm_combo, 2, 1)
        
        layout.addWidget(security_group)
        
        stego_group = QGroupBox("🎨 Steganography Options")
        stego_layout = QGridLayout(stego_group)
        
        stego_layout.addWidget(QLabel("Method:"), 0, 0)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["LSB", "DCT", "DWT", "Adaptive LSB"])
        stego_layout.addWidget(self.method_combo, 0, 1)
        
        stego_layout.addWidget(QLabel("Quality:"), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["High (Slower)", "Medium", "Fast"])
        stego_layout.addWidget(self.quality_combo, 1, 1)
        
        stego_layout.addWidget(QLabel("Compression:"), 2, 0)
        self.compression_spin = QSpinBox()
        self.compression_spin.setRange(0, 9)
        self.compression_spin.setValue(6)
        stego_layout.addWidget(self.compression_spin, 2, 1)
        
        layout.addWidget(stego_group)
        
        self.encode_progress = QProgressBar()
        self.encode_progress.setVisible(False)
        layout.addWidget(self.encode_progress)
        
        self.encode_btn = QPushButton("🔒 Encode Message")
        self.encode_btn.setMinimumHeight(40)
        self.encode_btn.clicked.connect(self.encode_message)
        layout.addWidget(self.encode_btn)
        
        layout.addStretch()
        return widget
    
    def create_decode_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        decode_image_group = QGroupBox("📷 Steganographic Image")
        decode_image_layout = QVBoxLayout(decode_image_group)
        
        self.decode_image_path_edit = QLineEdit()
        self.decode_image_path_edit.setPlaceholderText("Select steganographic image...")
        self.decode_image_path_edit.setReadOnly(True)
        
        decode_browse_btn = QPushButton("Browse Image")
        decode_browse_btn.clicked.connect(self.browse_decode_image)
        
        decode_image_layout.addWidget(self.decode_image_path_edit)
        decode_image_layout.addWidget(decode_browse_btn)
        layout.addWidget(decode_image_group)
        
        decrypt_group = QGroupBox("🔓 Decryption Options")
        decrypt_layout = QGridLayout(decrypt_group)
        
        decrypt_layout.addWidget(QLabel("Password:"), 0, 0)
        self.decode_password_edit = QLineEdit()
        self.decode_password_edit.setEchoMode(QLineEdit.Password)
        self.decode_password_edit.setPlaceholderText("Enter decryption password")
        decrypt_layout.addWidget(self.decode_password_edit, 0, 1)
        
        decrypt_layout.addWidget(QLabel("Algorithm:"), 1, 0)
        self.decode_algorithm_combo = QComboBox()
        self.decode_algorithm_combo.addItems(["Auto-detect", "AES-256", "ChaCha20", "Fernet"])
        decrypt_layout.addWidget(self.decode_algorithm_combo, 1, 1)
        
        decrypt_layout.addWidget(QLabel("Method:"), 2, 0)
        self.decode_method_combo = QComboBox()
        self.decode_method_combo.addItems(["Auto-detect", "LSB", "DCT", "DWT", "Adaptive LSB"])
        decrypt_layout.addWidget(self.decode_method_combo, 2, 1)
        
        layout.addWidget(decrypt_group)
        
        message_output_group = QGroupBox("📋 Extracted Message")
        message_output_layout = QVBoxLayout(message_output_group)
        
        self.extracted_message = QTextEdit()
        self.extracted_message.setReadOnly(True)
        self.extracted_message.setPlaceholderText("Extracted message will appear here...")
        
        message_output_layout.addWidget(self.extracted_message)
        layout.addWidget(message_output_group)
        
        self.decode_progress = QProgressBar()
        self.decode_progress.setVisible(False)
        layout.addWidget(self.decode_progress)
        
        self.decode_btn = QPushButton("🔓 Decode Message")
        self.decode_btn.setMinimumHeight(40)
        self.decode_btn.clicked.connect(self.decode_message)
        layout.addWidget(self.decode_btn)
        
        self.export_btn = QPushButton("💾 Export Message")
        self.export_btn.clicked.connect(self.export_message)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        layout.addStretch()
        return widget
    
    def create_batch_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        batch_group = QGroupBox("📦 Batch Operations")
        batch_layout = QVBoxLayout(batch_group)
        
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel("Operation:"))
        self.batch_operation_combo = QComboBox()
        self.batch_operation_combo.addItems(["Batch Encode", "Batch Decode", "Batch Analysis"])
        operation_layout.addWidget(self.batch_operation_combo)
        batch_layout.addLayout(operation_layout)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Folder:"))
        self.batch_input_edit = QLineEdit()
        self.batch_input_edit.setReadOnly(True)
        input_browse_btn = QPushButton("Browse")
        input_browse_btn.clicked.connect(self.browse_batch_input)
        input_layout.addWidget(self.batch_input_edit)
        input_layout.addWidget(input_browse_btn)
        batch_layout.addLayout(input_layout)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self.batch_output_edit = QLineEdit()
        self.batch_output_edit.setReadOnly(True)
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.clicked.connect(self.browse_batch_output)
        output_layout.addWidget(self.batch_output_edit)
        output_layout.addWidget(output_browse_btn)
        batch_layout.addLayout(output_layout)
        
        layout.addWidget(batch_group)
        
        settings_group = QGroupBox("⚙️ Batch Settings")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Thread Count:"), 0, 0)
        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 16)
        self.thread_count_spin.setValue(4)
        settings_layout.addWidget(self.thread_count_spin, 0, 1)
        
        settings_layout.addWidget(QLabel("Progress Updates:"), 1, 0)
        self.progress_updates_check = QCheckBox("Real-time updates")
        self.progress_updates_check.setChecked(True)
        settings_layout.addWidget(self.progress_updates_check, 1, 1)
        
        layout.addWidget(settings_group)
        
        self.batch_progress = QProgressBar()
        self.batch_status = QLabel("Ready for batch processing")
        layout.addWidget(self.batch_progress)
        layout.addWidget(self.batch_status)
        
        self.batch_start_btn = QPushButton("🚀 Start Batch Processing")
        self.batch_start_btn.setMinimumHeight(40)
        self.batch_start_btn.clicked.connect(self.start_batch_processing)
        layout.addWidget(self.batch_start_btn)
        
        layout.addStretch()
        return widget
    
    def create_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.analysis_widget = AnalysisWidget()
        layout.addWidget(self.analysis_widget)
        
        return widget
    
    def create_preview_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.image_preview = ImagePreviewWidget()
        layout.addWidget(self.image_preview)
        
        return widget
    
    def setup_drag_drop(self):
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                self.image_path_edit.setText(file_path)
                self.load_image_preview(file_path)
    
    def get_modern_stylesheet(self):
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QPushButton {
            background-color: #0078d4;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QLineEdit, QTextEdit {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #0078d4;
        }
        
        QComboBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
            min-width: 6em;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e1e1e1;
            border: 1px solid #cccccc;
            padding: 8px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom-color: white;
        }
        
        QTabBar::tab:hover {
            background-color: #f0f0f0;
        }
        
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }
        """
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')
        file_menu.addAction('New Project', self.new_project)
        file_menu.addAction('Open Project', self.open_project)
        file_menu.addAction('Save Project', self.save_project)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        
        tools_menu = menubar.addMenu('Tools')
        tools_menu.addAction('Settings', self.open_settings)
        tools_menu.addAction('Benchmark', self.run_benchmark)
        tools_menu.addAction('Security Audit', self.run_security_audit)
        
        help_menu = menubar.addMenu('Help')
        help_menu.addAction('Documentation', self.open_documentation)
        help_menu.addAction('About', self.show_about)
    
    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if file_path:
            self.image_path_edit.setText(file_path)
            self.load_image_preview(file_path)
    
    def update_message_stats(self):
        text = self.message_text.toPlainText()
        char_count = len(text)
        byte_count = len(text.encode('utf-8'))
        self.message_stats.setText(f"Characters: {char_count} | Bytes: {byte_count}")
    
    def encode_message(self):
        if not self.image_path_edit.text():
            QMessageBox.warning(self, "Warning", "Please select an image file.")
            return
        
        if not self.message_text.toPlainText():
            QMessageBox.warning(self, "Warning", "Please enter a message to encode.")
            return
            
        # Check if an encoding operation is already in progress
        if hasattr(self, '_encode_timer') and self._encode_timer and self._encode_timer.isActive():
            QMessageBox.warning(self, "Warning", "Encoding operation already in progress.")
            return
        
        self.encode_progress.setVisible(True)
        self.encode_btn.setEnabled(False)
        
        def encode_progress_callback(progress):
            self.encode_progress.setValue(progress)
        
        future = self.stego_engine.encode_async(
            self.image_path_edit.text(),
            self.message_text.toPlainText(),
            self.password_edit.text() if self.encryption_enabled.isChecked() else "",
            self.method_combo.currentText(),  # steganography algorithm (LSB, DCT, etc.)
            self.algorithm_combo.currentText(),  # encryption method (AES-256, etc.)
            self.compression_spin.value(),
            encode_progress_callback
        )
        
        def on_encode_complete():
            try:
                result = future.result()
                self.encode_progress.setVisible(False)
                self.encode_btn.setEnabled(True)
                
                # Stop and clean up the timer
                if hasattr(self, '_encode_timer') and self._encode_timer:
                    self._encode_timer.stop()
                    self._encode_timer.deleteLater()
                    self._encode_timer = None
                
                if result['success']:
                    # Process any pending events before showing dialog
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    save_path, _ = QFileDialog.getSaveFileName(
                        self, "Save Steganographic Image", "", 
                        "PNG Files (*.png);;JPEG Files (*.jpg)"
                    )
                    
                    # Process events after dialog closes
                    QApplication.processEvents()
                    
                    if save_path:
                        # Convert numpy array to PIL Image for saving
                        import numpy as np
                        from PIL import Image
                        
                        stego_image = result['stego_image']
                        if isinstance(stego_image, np.ndarray):
                            # Ensure values are in valid range and convert to uint8
                            stego_image = np.clip(stego_image, 0, 255).astype(np.uint8)
                            pil_image = Image.fromarray(stego_image)
                            pil_image.save(save_path)
                        else:
                            # If it's already a PIL Image
                            stego_image.save(save_path)
                        
                        QMessageBox.information(self, "Success", 
                            f"Message encoded successfully!\nPSNR: {result['analysis']['psnr']:.2f} dB\n"
                            f"Capacity used: {result['capacity_used']:.1f}%")
                        
                        # Process events and restore focus after success dialog
                        QApplication.processEvents()
                        self.activateWindow()
                        self.raise_()
                        if hasattr(self, 'tab_widget'):
                            self.tab_widget.setFocus()
                else:
                    QMessageBox.critical(self, "Error", f"Encoding failed: {result['error']}")
                    # Process events and restore focus after error dialog
                    QApplication.processEvents()
                    self.activateWindow()
                    self.raise_()
                    if hasattr(self, 'tab_widget'):
                        self.tab_widget.setFocus()
                    
            except Exception as e:
                self.encode_progress.setVisible(False)
                self.encode_btn.setEnabled(True)
                if hasattr(self, '_encode_timer') and self._encode_timer:
                    self._encode_timer.stop()
                    self._encode_timer.deleteLater()
                    self._encode_timer = None
                QMessageBox.critical(self, "Error", f"Encoding error: {str(e)}")
        
        # Use instance variable for timer to prevent garbage collection
        self._encode_timer = QTimer()
        self._encode_timer.timeout.connect(self._check_encode_completion)
        self._encode_timer.start(100)
        
        # Store the future and callback for the timer check
        self._encode_future = future
        self._encode_callback = on_encode_complete
    
    def _check_encode_completion(self):
        """Check if encoding operation is complete and handle result"""
        if hasattr(self, '_encode_future') and self._encode_future and self._encode_future.done():
            # Stop the timer first
            if self._encode_timer:
                self._encode_timer.stop()
                
            # Call the completion callback
            if hasattr(self, '_encode_callback') and self._encode_callback:
                self._encode_callback()
                
            # Clean up references
            self._encode_future = None
            self._encode_callback = None
    
    def browse_decode_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Steganographic Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if file_path:
            self.decode_image_path_edit.setText(file_path)
    
    def decode_message(self):
        if not self.decode_image_path_edit.text():
            QMessageBox.warning(self, "Warning", "Please select a steganographic image.")
            return
            
        # Check if a decoding operation is already in progress
        if hasattr(self, '_decode_timer') and self._decode_timer and self._decode_timer.isActive():
            QMessageBox.warning(self, "Warning", "Decoding operation already in progress.")
            return
        
        self.decode_progress.setVisible(True)
        self.decode_btn.setEnabled(False)
        
        def decode_progress_callback(progress):
            self.decode_progress.setValue(progress)
        
        # Handle auto-detect by trying algorithms in order
        selected_method = self.decode_method_combo.currentText()
        if selected_method == "Auto-detect":
            # Try algorithms in order of popularity/likelihood
            algorithms_to_try = ["LSB", "DCT", "DWT", "Adaptive LSB"]
            self._decode_algorithms_to_try = algorithms_to_try
            self._decode_current_algorithm_index = 0
            algorithm = algorithms_to_try[0]
        else:
            self._decode_algorithms_to_try = [selected_method]
            self._decode_current_algorithm_index = 0
            algorithm = selected_method
        
        future = self.stego_engine.decode_async(
            self.decode_image_path_edit.text(),
            self.decode_password_edit.text(),
            algorithm,
            decode_progress_callback
        )
        
        def on_decode_complete():
            try:
                # Get result from the current future (stored in instance variable)
                result = self._decode_future.result()
                self.decode_progress.setVisible(False)
                self.decode_btn.setEnabled(True)
                
                # Stop and clean up the timer
                if hasattr(self, '_decode_timer') and self._decode_timer:
                    self._decode_timer.stop()
                    self._decode_timer.deleteLater()
                    self._decode_timer = None
                
                if result['success']:
                    self.extracted_message.setPlainText(result['message'])
                    self.export_btn.setEnabled(True)
                    
                    # Process events before showing dialog
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    QMessageBox.information(self, "Success", "Message decoded successfully!")
                    
                    # Process events and restore focus after dialog
                    QApplication.processEvents()
                    self.activateWindow()
                    self.raise_()
                    if hasattr(self, 'tab_widget'):
                        self.tab_widget.setFocus()
                else:
                    # If we're in auto-detect mode and have more algorithms to try
                    if (hasattr(self, '_decode_algorithms_to_try') and 
                        len(self._decode_algorithms_to_try) > 1 and
                        self._decode_current_algorithm_index < len(self._decode_algorithms_to_try) - 1):
                        
                        # Try next algorithm
                        self._decode_current_algorithm_index += 1
                        next_algorithm = self._decode_algorithms_to_try[self._decode_current_algorithm_index]
                        
                        # Restart the decoding process with the next algorithm
                        def decode_progress_callback(progress):
                            self.decode_progress.setValue(progress)
                        
                        next_future = self.stego_engine.decode_async(
                            self.decode_image_path_edit.text(),
                            self.decode_password_edit.text(),
                            next_algorithm,
                            decode_progress_callback
                        )
                        
                        # Store the new future and restart the timer
                        self._decode_future = next_future
                        self._decode_callback = on_decode_complete  # Set the callback for retry too
                        self._decode_timer = QTimer()
                        self._decode_timer.timeout.connect(self._check_decode_completion)
                        self._decode_timer.start(100)
                        
                        return  # Don't show error message yet, try next algorithm
                    
                    # All algorithms failed or not in auto-detect mode
                    # Process events before showing error dialog
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    QMessageBox.critical(self, "Error", f"Decoding failed: {result['error']}")
                    
                    # Process events and restore focus after error dialog
                    QApplication.processEvents()
                    self.activateWindow()
                    self.raise_()
                    
            except Exception as e:
                self.decode_progress.setVisible(False)
                self.decode_btn.setEnabled(True)
                if hasattr(self, '_decode_timer') and self._decode_timer:
                    self._decode_timer.stop()
                    self._decode_timer.deleteLater()
                    self._decode_timer = None
                
                # Process events before showing error dialog
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                QMessageBox.critical(self, "Error", f"Decoding error: {str(e)}")
                
                # Process events and restore focus after error dialog
                QApplication.processEvents()
                self.activateWindow()
                self.raise_()
        
        # Use instance variable for timer to prevent garbage collection
        self._decode_timer = QTimer()
        self._decode_timer.timeout.connect(self._check_decode_completion)
        self._decode_timer.start(100)
        
        # Store the future and callback for the timer check
        self._decode_future = future
        self._decode_callback = on_decode_complete
    
    def _check_decode_completion(self):
        """Check if decoding operation is complete and handle result"""
        if hasattr(self, '_decode_future') and self._decode_future and self._decode_future.done():
            # Stop the timer first
            if self._decode_timer:
                self._decode_timer.stop()
                
            # Call the completion callback
            if hasattr(self, '_decode_callback') and self._decode_callback:
                self._decode_callback()
                
            # Clean up references
            self._decode_future = None
            self._decode_callback = None
    
    def export_message(self):
        if not self.extracted_message.toPlainText():
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Extracted Message", "", "Text Files (*.txt)"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.extracted_message.toPlainText())
            QMessageBox.information(self, "Success", "Message exported successfully!")
    
    def browse_batch_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.batch_input_edit.setText(folder)
    
    def browse_batch_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.batch_output_edit.setText(folder)
    
    def start_batch_processing(self):
        if not self.batch_input_edit.text() or not self.batch_output_edit.text():
            QMessageBox.warning(self, "Warning", "Please select input and output folders.")
            return
        
        QMessageBox.information(self, "Info", "Batch processing feature will be implemented.")
    
    def load_image_preview(self, file_path):
        if hasattr(self, 'image_preview'):
            self.image_preview.load_image(file_path)
    
    def new_project(self):
        pass
    
    def open_project(self):
        pass
    
    def save_project(self):
        pass
    
    def open_settings(self):
        pass
    
    def run_benchmark(self):
        pass
    
    def run_security_audit(self):
        pass
    
    def open_documentation(self):
        pass
    
    def show_about(self):
        QMessageBox.about(self, "About", 
            "steganography-py3 GUI\n\n"
            "A comprehensive steganography application with encryption,\n"
            "analysis, and batch processing capabilities.")
    
    def closeEvent(self, event):
        """Handle application close event with proper cleanup"""
        # Clean up any running timers
        if hasattr(self, '_encode_timer') and self._encode_timer:
            self._encode_timer.stop()
            self._encode_timer.deleteLater()
            self._encode_timer = None
            
        if hasattr(self, '_decode_timer') and self._decode_timer:
            self._decode_timer.stop()
            self._decode_timer.deleteLater()
            self._decode_timer = None
            
        # Clean up future references
        self._encode_future = None
        self._decode_future = None
        self._encode_callback = None
        self._decode_callback = None
            
        # Accept the close event
        event.accept()