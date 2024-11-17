import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton,
    QWidget, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QDialog,
    QListView, QDialogButtonBox
)
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt,QObject,pyqtSignal,pyqtSlot
import sys

import LunaHook
import utils
class DataHandler(QObject):
    pid_selected = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.pid = None

    def set_pid(self, pid):
        self.pid = pid
        self.pid_selected.emit(pid) 
    def get_pid(self):
        return self.pid
class SelectPidsPopup(QDialog):
    def __init__(self,data_handler:DataHandler):
        super().__init__()
        self.setWindowTitle("Select PIDs")
        self.setMinimumSize(400, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.data_handler = data_handler 

        layout = QVBoxLayout()

        self.table = QTableWidget(99, 2)  
        self.table.setHorizontalHeaderLabels(["PID", "Name"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)


        pids = utils.get_pids()
        for row,(pid , name) in enumerate(pids.items()):
            self.table.setItem(row,0,QTableWidgetItem(str(pid)))
            self.table.setItem(row,1,QTableWidgetItem(name))

        self.table.cellDoubleClicked.connect(self.on_double_click)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def on_double_click(self, row, column):
        pid = self.table.item(row, 0).text()
        self.data_handler.set_pid(int(pid))
        print(f"Selected PID: {pid}")  
        self.accept()


class LogHistoryPopup(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Log History")
        self.setMinimumSize(400, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout()

        self.list_view = QListView()
        layout.addWidget(self.list_view)

        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setWindowTitle("Floating Window with Tabs")
        self.setGeometry(100, 100, 800, 300)

        self.data_handler = DataHandler()
        self.data_handler.pid_selected.connect(self.on_pid_selected) 
        self.luna = None
        
        self.text = "set pid please"
        self.init_ui()
        self._is_dragging = False  
        self._start_pos = None     
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._start_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.move(event.globalPos() - self._start_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)


        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setAlignment(Qt.AlignTop)

        self.btn_select_pids = QPushButton("Select PIDs")
        self.btn_log_history = QPushButton("Log History")
        self.btn_select_pids.clicked.connect(self.show_select_pids_popup)
        self.btn_log_history.clicked.connect(self.show_log_history_popup)

        button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                font-size: 14px;
                padding: 8px 16px;
                border: 1px solid #444444;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """
        self.btn_select_pids.setStyleSheet(button_style)
        self.btn_log_history.setStyleSheet(button_style)

        button_layout.addWidget(self.btn_select_pids)
        button_layout.addWidget(self.btn_log_history)

        main_layout.addLayout(button_layout)
    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setBrush(QColor(43, 43, 43))  
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        painter.setPen(QColor(255, 255, 255))  
        painter.setFont(QFont("Arial", 16))
        text_rect = self.rect().adjusted(0, 10, 0, 0)
        painter.drawText(text_rect, Qt.AlignTop | Qt.AlignCenter,self.text)
    def show_select_pids_popup(self):
        popup = SelectPidsPopup(self.data_handler)
        popup.exec()

    def show_log_history_popup(self):
        popup = LogHistoryPopup()
        popup.exec()

    def on_pid_selected(self,pid):
        host_dll,hook_dll = utils.get_dll()
        self.luna = LunaHook.LunaHostWrapper(host_dll)
        self.luna.Luna_Inject(pid, os.path.abspath("LunaHook"))

        self.luna.xai_api.translation_finished.connect(self.on_translation_finished)
    @pyqtSlot(str)
    def on_translation_finished(self,translation):
        self.text = translation
        self.update()