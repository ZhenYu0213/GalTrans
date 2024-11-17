import GUI
import sys


if __name__ == "__main__":
    app = GUI.QApplication(sys.argv)

    main_window = GUI.MainWindow()
    main_window.show()

    sys.exit(app.exec())
