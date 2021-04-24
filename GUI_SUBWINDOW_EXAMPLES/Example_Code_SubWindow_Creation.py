"""
#Codersarts python Assignment Help by top rated Expert
#If you need any help then contact to codersarts offcial website

This code shows an example of creating a subwindow in a mainwindow object.
Afterwards we utilize the exit button to quit properly derived from base classes: MainWindow & SubWindow.

for creating multiple windows in gui (example 2)
#source:https://www.codersarts.com/post/multiple-windows-in-pyqt5-codersarts

for properly creatin the closeEvent method and using the X buton to exit the GUI
https://stackoverflow.com/questions/40622095/pyqt5-closeevent-method

"""
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, uic

class SubWindow_Overload(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(SubWindow_Overload, self).__init__(parent)
        label = QLabel("Sub Window",  self)
    
    def closeEvent(self, event):
                close = QtWidgets.QMessageBox.question(self,
                                             "QUIT",
                                             "Are you sure want to stop process?",
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                
                #SubWindow Base class event: X button
                #
                #
                #If X button is pressed a text box pops up.
                #if user selects Yes, we accept clicking the X button. (SubWindow base class exits)
                #If user selects No, we ignore the X button click of the base class SubWindow base class.
                #
                #
                if close == QtWidgets.QMessageBox.Yes:
                    #calls an exit function for the window
                    event.accept()
                else:
                    #ignores the exit function for the window and goes back to SubWindow
                    event.ignore()
    

class MainWindow_Overload(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(MainWindow_Overload, self).__init__(parent)
        openButton = QPushButton("Open Sub Window",  self)
        openButton.clicked.connect(self.openSub)
        
    def openSub(self):
        self.sub = SubWindow_Overload()
        self.sub.show()


    def closeEvent(self, event):
                close = QtWidgets.QMessageBox.question(self,
                                             "QUIT",
                                             "Are you sure want to stop process?",
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if close == QtWidgets.QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()

app = QApplication(sys.argv)
mainWin =MainWindow_Overload()
mainWin.show()
sys.exit(app.exec_())