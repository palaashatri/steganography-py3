from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox

class FileSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super(FileSelectionDialog, self).__init__(parent)
        self.setWindowTitle("Select File")
        self.setGeometry(100, 100, 300, 150)
        layout = QVBoxLayout()

        self.label = QLabel("No file selected.")
        layout.addWidget(self.label)

        self.select_button = QPushButton("Select File")
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)

        self.setLayout(layout)

    def select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Image Files (*.png;*.jpg;*.jpeg)", options=options)
        if file_name:
            self.label.setText(file_name)

class ConfirmationDialog(QDialog):
    def __init__(self, message, parent=None):
        super(ConfirmationDialog, self).__init__(parent)
        self.setWindowTitle("Confirmation")
        self.setGeometry(100, 100, 250, 100)
        layout = QVBoxLayout()

        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.confirm_button = QPushButton("OK")
        self.confirm_button.clicked.connect(self.accept)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)

def show_error_message(message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText(message)
    msg_box.setWindowTitle("Error")
    msg_box.exec_()