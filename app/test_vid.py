import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Media Player")
        self.setGeometry(100, 100, 800, 600)

        video_widget = QVideoWidget()
        self.setCentralWidget(video_widget)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(video_widget)

        media_url = QUrl.fromLocalFile("/home/risc3/NVRR/NVRR/nvr_project/output_0.avi")
        self.media_player.setMedia(QMediaContent(media_url))

        if not self.media_player.isAvailable():
            print("Media player is not available.")

        self.media_player.error.connect(self.handle_error)
        self.media_player.play()

    def handle_error(self, error):
        print(f"Error: {self.media_player.errorString()}")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
