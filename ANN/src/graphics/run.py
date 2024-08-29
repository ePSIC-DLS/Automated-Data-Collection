from ._page import *
from PyQt5 import QtWidgets as widgets

app = widgets.QApplication([])


class Main(widgets.QMainWindow):

    def __init__(self):
        widgets.QMainWindow.__init__(self)
        blank = widgets.QTabWidget()
        main = Sweeper(512)
        spec = Setup(main)
        fine_tune = Manual(512, spec)
        correct = Tester()
        main.current_updated.connect(correct.add_grid)
        blank.addTab(main, "Running Sweep")
        blank.addTab(spec, "Sweep Parameters")
        blank.addTab(fine_tune, "Manual Mode")
        blank.addTab(correct, "Filter Application")
        main.start.connect(lambda: blank.setCurrentIndex(0))
        self.setCentralWidget(blank)


def run():
    window = Main()
    window.show()
    app.exec()
