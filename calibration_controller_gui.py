import random

from PyQt5 import QtCore, QtGui, QtWidgets
import tcp.client_tcp as c_tcp
from calibration_gui import Ui_MainWindow
from TabsController.tab_temperature import TabTemperature
from TabsController.tab_pressure import TabPressure
from TabsController.tab_settings import TabSettings
from TabsController.tab_flow import TabFlow
from TabsController.tab_diagnostic import TabDiagnostic
from TabsController.tab_offset_zero import TabOffsetZero
from PyQt5.QtCore import QTimer
import sys


class MainDo:

    def __init__(self) -> None:
        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)

        self.tab_temperature = TabTemperature(self.ui)
        self.tab_pressure = TabPressure(self.ui)
        self.tab_flow = TabFlow(self.ui)
        self.tab_diagnostic = TabDiagnostic(self.ui)
        self.tab_diagnostic.mysignal.connect(self.append_offset_zero)
        self.tab_settings = TabSettings(self.ui)
        self.tab_offset_zero = TabOffsetZero(self.ui)
        self.timer = None
        self.MainWindow.closeEvent = self.my_close_event

    def append_offset_zero(self, value: float) -> None:
        self.tab_offset_zero.append_table([value])
        self.tab_offset_zero.redraw_graph()

    def run(self) -> None:
        self.set_timer()

        self.MainWindow.show()
        self.app.exec()

    def my_close_event(self, event: QtGui.QCloseEvent) -> None:
        self.timer.stop()
        self.timer.deleteLater()
        event.accept()

    def set_timer(self) -> None:
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_text_timer)
        self.timer.start()

    def update_text_timer(self) -> None:

        t = self.ui.tabWidget.currentIndex()
        if t == 1:
            self.tab_temperature.update_data()
        if t == 2:
            self.tab_pressure.update_data()
        if t == 3:
            self.tab_flow.update_data()
        self.tab_diagnostic.update_data()


if __name__ == "__main__":
    c_tcp.start_client_tcp_thread()

    main_do = MainDo()
    main_do.run()

    c_tcp.stop_client_tcp_thread()
