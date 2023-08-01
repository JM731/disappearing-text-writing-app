from PyQt6.QtWidgets import (QApplication,
                             QMainWindow,
                             QWidget,
                             QGridLayout,
                             QPlainTextEdit,
                             QStackedLayout,
                             QPushButton,
                             QComboBox,
                             QCheckBox,
                             QHBoxLayout,
                             QVBoxLayout,
                             QLabel,
                             QProgressBar
                             )
from PyQt6.QtCore import QTimer, Qt, pyqtSlot, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
import time
import random

PROGRESS_BAR_COLORS = ["#00ff00", "#f5d742", "#f29100", "#f54242", "#0613c4"]
PROGRESS_BAR_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background-color: 
"""
END_STRING = "; }"


def set_stylesheet(index):
    return PROGRESS_BAR_STYLE + PROGRESS_BAR_COLORS[index] + END_STRING


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl

    @pyqtSlot(int)
    def do_work(self, max_value):
        self.ctrl['break'] = False
        for n in range(max_value):
            if self.ctrl['break']:
                break
            time.sleep(0.1)
            if not self.ctrl['break']:
                self.progress.emit(n + 1)
        self.finished.emit()


class Window(QMainWindow):

    work_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.writing_time = 5
        self.stop_timeout_random = False
        self.write_timeout = 5
        self.hint = False
        self.started = False
        self.ctrl = {'break': False}
        self.current_stylesheet = set_stylesheet(0)

        self.setWindowTitle("Disappearing Text Writing App")
        self.setFixedSize(800, 600)

        self.stacked_layout = QStackedLayout()
        central_widget = QWidget()
        central_widget.setLayout(self.stacked_layout)
        self.setCentralWidget(central_widget)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)

        self.text_entry = QPlainTextEdit()
        self.text_entry.setStyleSheet(
            "QPlainTextEdit:focus { border: none; }"
            "QPlainTextEdit { border: none; outline: none; }"
        )
        self.text_entry.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

        self.timers = [QTimer() for _ in range(4)]
        for i in range(1, 4):
            self.timers[i].setInterval(1000)
        self.timers[0].timeout.connect(self.onTimeout0)
        self.timers[1].timeout.connect(self.onTimeout1)
        self.timers[2].timeout.connect(self.onTimeout2)
        self.timers[3].timeout.connect(self.onTimeout3)
        self.active_timer = self.timers[0]

        self.worker = Worker(self.ctrl)
        self.worker_thread = QThread()
        self.worker.progress.connect(self.updateProgressBarValue)
        self.worker.finished.connect(self.finish)
        self.work_requested.connect(self.worker.do_work)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.menuScreen()
        self.textScreen()

    def menuScreen(self):
        self.setContentsMargins(300, 230, 300, 230)

        initial_widget = QWidget()
        layout = QVBoxLayout()
        combobox_layout = QHBoxLayout()

        start_button = QPushButton("Start")
        start_button_font = QFont()
        start_button_font.setPointSize(16)
        start_button.setFont(start_button_font)
        timer_combobox_label = QLabel("Total writing time (min)")
        timer_combobox = QComboBox()
        timer_combobox.addItem("5")
        timer_combobox.addItem("4")
        timer_combobox.addItem("3")
        timer_combobox.addItem("2")
        timer_combobox.addItem("1")
        random_timer_checkbox = QCheckBox("Random countdown (4-7s)")
        hint_checkbox = QCheckBox("Timeout visual hint")

        layout.addWidget(start_button)
        layout.addWidget(random_timer_checkbox)
        layout.addWidget(hint_checkbox)
        combobox_layout.addWidget(timer_combobox_label)
        combobox_layout.addWidget(timer_combobox)
        layout.addLayout(combobox_layout)

        start_button.clicked.connect(self.onStartButtonPress)
        timer_combobox.textActivated[str].connect(self.onComboboxSelected)
        random_timer_checkbox.stateChanged.connect(self.randomCheckboxTick)
        hint_checkbox.stateChanged.connect(self.hintCheckboxTick)
        initial_widget.setLayout(layout)
        self.stacked_layout.addWidget(initial_widget)

    def textScreen(self):

        text_screen_widget = QWidget()
        layout = QGridLayout()

        menu_button = QPushButton("Menu")
        menu_button.clicked.connect(self.menuButtonPress)
        restart_button = QPushButton("Restart")
        restart_button.clicked.connect(self.restartButtonPress)

        layout.addWidget(self.progress_bar, 0, 0, 1, 4)
        layout.addWidget(self.text_entry, 1, 0, 1, 4)
        layout.addWidget(menu_button, 2, 1, 1, 1)
        layout.addWidget(restart_button, 2, 2, 1, 1)

        text_screen_widget.setLayout(layout)
        self.stacked_layout.addWidget(text_screen_widget)

    def hintCheckboxTick(self, state):
        self.hint = (state == 2)

    def randomCheckboxTick(self, state):
        self.stop_timeout_random = (state == 2)

    def onComboboxSelected(self, text):
        self.writing_time = int(text)

    def onStartButtonPress(self):
        self.started = False
        self.setContentsMargins(0, 0, 0, 0)
        self.text_entry.textChanged.connect(self.onTextChanged)
        self.text_entry.setEnabled(True)
        self.progress_bar.setMaximum(self.writing_time * 60 * 10)
        self.resetProgressBar()
        self.stacked_layout.setCurrentIndex(1)

    def onTextChanged(self):
        if not self.started:
            self.work_requested.emit(self.progress_bar.maximum())
            self.started = True
        self.active_timer.stop()
        self.active_timer = self.timers[0]
        self.setCurrentStyleSheet(0)
        if self.stop_timeout_random:
            self.timers[0].start(random.randint(1, 4) * 1000)
        else:
            self.timers[0].start(2000)

    def onTimeout0(self):
        self.active_timer.stop()
        self.active_timer = self.timers[1]
        self.active_timer.start()
        self.setCurrentStyleSheet(1)

    def onTimeout1(self):
        self.active_timer.stop()
        self.active_timer = self.timers[2]
        self.active_timer.start()
        self.setCurrentStyleSheet(2)

    def onTimeout2(self):
        self.active_timer.stop()
        self.active_timer = self.timers[3]
        self.active_timer.start()
        self.setCurrentStyleSheet(3)

    def onTimeout3(self):
        self.active_timer.stop()
        self.stopWorker()
        self.clearText()
        self.text_entry.setEnabled(False)

    def updateProgressBarValue(self, current_value):
        self.progress_bar.setValue(current_value)
        self.progress_bar.setStyleSheet(self.current_stylesheet)

    def finish(self):
        self.active_timer.stop()
        self.text_entry.textChanged.disconnect(self.onTextChanged)
        if not self.ctrl['break']:
            self.progress_bar.setStyleSheet(set_stylesheet(4))

    def setCurrentStyleSheet(self, index):
        if self.hint:
            self.current_stylesheet = set_stylesheet(index)
        else:
            self.current_stylesheet = set_stylesheet(0)

    def restartButtonPress(self):
        self.stopWorker()
        self.clearText()
        self.resetProgressBar()
        self.started = False
        self.text_entry.setEnabled(True)
        self.text_entry.textChanged.connect(self.onTextChanged)
        self.text_entry.setFocus()

    def menuButtonPress(self):
        self.stopWorker()
        self.setContentsMargins(300, 230, 300, 230)
        self.clearText()
        self.stacked_layout.setCurrentIndex(0)

    def resetProgressBar(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(set_stylesheet(0))

    def stopWorker(self):
        self.ctrl['break'] = True

    def clearText(self):
        self.text_entry.blockSignals(True)
        self.text_entry.clear()
        self.text_entry.blockSignals(False)

    def closeEvent(self, event):
        self.stopWorker()


if __name__ == "__main__":
    main_event_thread = QApplication([])
    window = Window()
    window.show()
    main_event_thread.exec()
