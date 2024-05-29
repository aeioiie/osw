import os
import sys
import queue
import platform

from PyQt5 import QtWidgets, QtGui, QtCore
import vlc

class MiniPlayer(QtWidgets.QMainWindow):
    """Stripped-down PyQt5-based media player class to sync with "master" video.
    """

    def __init__(self, data_queue, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.setWindowTitle("Mini Player")
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Ready")

        # Create a basic vlc instance
        self.instance = vlc.Instance()

        self.video_media = None
        self.audio_media = None

        # Create an empty vlc media player for video
        self.video_player = self.instance.media_player_new()
        # Create an empty vlc media player for audio
        self.audio_player = self.instance.media_player_new()

        self.init_ui()
        self.open_file()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_ui)

        self.data_queue = data_queue
        self.timer.start()

    def init_ui(self):
        """Set up the user interface
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        if platform.system() == "Darwin":  # for MacOS
            self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.videoframe = QtWidgets.QFrame()

        self.palette = self.videoframe.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        self.widget.setLayout(self.vboxlayout)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

    def open_file(self):
        """Open a media file in a MediaPlayer
        """
        video_dialog_txt = "Choose Video File"
        audio_dialog_txt = "Choose Audio File"

        video_filename = QtWidgets.QFileDialog.getOpenFileName(self, video_dialog_txt, os.path.expanduser('~'))
        if not video_filename[0]:
            return

        audio_filename = QtWidgets.QFileDialog.getOpenFileName(self, audio_dialog_txt, os.path.expanduser('~'))
        if not audio_filename[0]:
            return

        # getOpenFileName returns a tuple, so use only the actual file names
        self.video_media = self.instance.media_new(video_filename[0])
        self.audio_media = self.instance.media_new(audio_filename[0])

        # Put the media in the media players
        self.video_player.set_media(self.video_media)
        self.audio_player.set_media(self.audio_media)

        # Parse the metadata of the video file
        self.video_media.parse()

        # Set the title of the track as the window title
        self.setWindowTitle("{}".format(self.video_media.get_meta(0)))

        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in its own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux":  # for Linux using the X Server
            self.video_player.set_xwindow(int(self.videoframe.winId()))
        elif platform.system() == "Windows":  # for Windows
            self.video_player.set_hwnd(int(self.videoframe.winId()))
        elif platform.system() == "Darwin":  # for MacOS
            self.video_player.set_nsobject(int(self.videoframe.winId()))

        # Start playing the video and audio as soon as they load
        self.video_player.play()
        self.audio_player.play()

    def update_ui(self):
        self.update_statusbar()

        if self.video_player.get_state() == vlc.State.Ended:
            self.video_player.stop()
            self.video_player.play()
        if self.audio_player.get_state() == vlc.State.Ended:
            self.audio_player.stop()
            self.audio_player.play()

        try:
            val = self.data_queue.get(block=False)
        except queue.Empty:
            return

        if val == '<':
            self.video_player.set_rate(self.video_player.get_rate() * 0.5)
            self.audio_player.set_rate(self.audio_player.get_rate() * 0.5)
            return
        if val == '>':
            self.video_player.set_rate(self.video_player.get_rate() * 2)
            self.audio_player.set_rate(self.audio_player.get_rate() * 2)
            return
        if val == 'P':
            self.video_player.play()
            self.audio_player.play()
            return
        if val == 'p':
            self.video_player.pause()
            self.audio_player.pause()
            return
        if val == 'S':
            self.video_player.stop()
            self.audio_player.stop()
            return

        val = int(val)
        if val != self.video_player.get_time():
            self.video_player.set_time(val)
            self.audio_player.set_time(val)

    def update_statusbar(self):
        mtime = QtCore.QTime(0, 0, 0, 0)
        time = mtime.addMSecs(self.video_player.get_time())
        self.statusbar.showMessage(time.toString())


def main():
    """Entry point for our simple vlc player
    """
    app = QtWidgets.QApplication(sys.argv)

    data_queue = queue.Queue()

    player = MiniPlayer(data_queue)
    player.show()
    player.resize(720, 720)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()