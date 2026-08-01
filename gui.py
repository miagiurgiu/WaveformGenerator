import sys
from pathlib import Path
from main import generate_video

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio_file = None

        self.setWindowTitle("Audio Waveform Generator")
        self.setMinimumSize(500, 300)

        self.audio_label = QLabel("No audio file selected")

        self.choose_audio_button = QPushButton(
            "Choose Audio"
        )

        self.color_input = QLineEdit("#C8A96A")
        self.color_input.setPlaceholderText(
            "Waveform colour, for example #C8A96A"
        )

        self.export_button = QPushButton(
            "Export Transparent MOV"
        )

        self.status_label = QLabel(
            "Choose an audio file to begin."
        )

        layout = QVBoxLayout()
        layout.addWidget(self.audio_label)
        layout.addWidget(self.choose_audio_button)
        layout.addWidget(self.color_input)
        layout.addWidget(self.export_button)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.choose_audio_button.clicked.connect(
            self.choose_audio
        )

        self.export_button.clicked.connect(
            self.export_video
        )

    def choose_audio(self):
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose an audio file",
            "",
            (
                "Audio and video files "
                "(*.wav *.mp3 *.m4a *.aac *.flac *.mp4 *.mov)"
            ),
        )

        if selected_file:
            self.audio_file = Path(selected_file)

            self.audio_label.setText(
                self.audio_file.name
            )

            self.status_label.setText(
                "Audio file selected."
            )

    def export_video(self):
        if self.audio_file is None:
            self.status_label.setText(
                "Please choose an audio file first."
            )
            return

        color = self.color_input.text().strip()

        if not self.is_valid_hex_color(color):
            self.status_label.setText(
                "Enter a colour such as #C8A96A."
            )
            return

        suggested_name = (
                self.audio_file.stem
                + "_waveform.mov"
        )

        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Export transparent waveform",
            str(self.audio_file.parent / suggested_name),
            "QuickTime Video (*.mov)",
        )

        if not output_file:
            self.status_label.setText(
                "Export cancelled."
            )
            return

        output_path = Path(output_file)

        if output_path.suffix.lower() != ".mov":
            output_path = output_path.with_suffix(".mov")

        self.status_label.setText(
            "Exporting video..."
        )

        QApplication.processEvents()

        try:
            generate_video(
                audio_file=self.audio_file,
                output_file=output_path,
                color=color,
                duration_seconds=None
            )

        except Exception as error:
            self.status_label.setText(
                f"Export failed: {error}"
            )
            return

        self.status_label.setText(
            f"Export complete: {output_path.name}"
        )

    @staticmethod
    def is_valid_hex_color(color):
        if len(color) != 7:
            return False

        if not color.startswith("#"):
            return False

        try:
            int(color[1:], 16)
        except ValueError:
            return False

        return True


def main():
    application = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()