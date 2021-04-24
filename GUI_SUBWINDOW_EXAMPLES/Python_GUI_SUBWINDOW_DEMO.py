# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GPS_Logging_GUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

"""
How to create  QVBoxLayout window.
https://pythonpyqt.com/pyqt-box-layout/


#Using a Timer+generator to control and exit out of an infinite for loop
https://stackoverflow.com/questions/7216087/pyqt-how-to-cancel-loop-in-my-gui-using-cancel-button

"""

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from datetime import datetime as dt
import time

class SubWindow(QtWidgets.QWidget):

    def __init__(self, parent = None):
        super(SubWindow, self).__init__(parent)
        
        vbox = QtWidgets.QVBoxLayout()
        
        #create pushbutton
        self.passive_cam_stop_button = QtWidgets.QPushButton("Stop Passive Cam")
        
        #click push button
        self.passive_cam_stop_button.clicked.connect(self.on_stop_passive_cam_button_clicked)
        
        font = QtGui.QFont()
        font.setPointSize(16)
        self.passive_cam_stop_button.setFont(font) 
        self.passive_cam_stop_button.setObjectName("stop_passive_cam_button")
        
        self.label = QtWidgets.QLabel("Before")
        
        
        vbox.addWidget(self.passive_cam_stop_button)
        vbox.addWidget(self.label)
        
        self.setLayout(vbox)
        
        #at position(150,150) create a 100x100 box
        self.setGeometry(150,150,100,100)
        self.setWindowTitle('Passive Cam Release')
        
        self.button_clicked = 0
        
    @QtCore.pyqtSlot()
    def on_stop_passive_cam_button_clicked(self):
        print("Stop")
        self.label.setText("After")
        
        #flag used to break out of passive cam loop
        self.button_clicked = 1
        

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
        
#subclass of mainwindow to customize application main window
class UI_MainWindow(QtWidgets.QMainWindow):

    def __init__(self,*args,**kwargs):
        
        #inherit all attributes from QMainWindow parent
        super(UI_MainWindow,self).__init__(*args,**kwargs)

        self.resize(1058, 750)
        self.setWindowTitle("MainWindow")


        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        
        
        self.start_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(210, 150, 231, 211))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.start_button.setFont(font)
        self.start_button.setObjectName("start_button")
        self.start_button.setStyleSheet("background-color : yellow")
        self.start_button.clicked.connect(self.on_start_button_clicked)
        
        
        self.stop_button = QtWidgets.QPushButton(self.centralwidget)
        self.stop_button.setGeometry(QtCore.QRect(540, 150, 231, 211))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.stop_button.setFont(font)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setStyleSheet("background-color : yellow")
        self.stop_button.clicked.connect(self.on_stop_button_clicked)

        self.TimeStamp_label = QtWidgets.QLabel(self.centralwidget)
        self.TimeStamp_label.setGeometry(QtCore.QRect(800, 500, 251, 41))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.TimeStamp_label.setFont(font)
        self.TimeStamp_label.setObjectName("TimeStamp_label")
        
        self.ellapsed_time_label = QtWidgets.QLabel(self.centralwidget)
        self.ellapsed_time_label.setGeometry(QtCore.QRect(800, 600, 251, 41))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.ellapsed_time_label.setFont(font)
        self.ellapsed_time_label.setObjectName("Ellapsed_Time_label")
        
        self.status_indicator = QtWidgets.QLabel(self.centralwidget)
        self.status_indicator.setGeometry(QtCore.QRect(290, 520, 361, 91))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.status_indicator.setFont(font)
        self.status_indicator.setObjectName("status_indicator")
        
        #enable widgets in the main window
        self.setCentralWidget(self.centralwidget)
        
        self.retranslateUi()

        #matches action signals like button clicks to Widget objects
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self._generator = None
        self._timerId = None

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "My Awesome GPS Logging app"))
        self.start_button.setText(_translate("MainWindow", "GPS Start"))
        self.stop_button.setText(_translate("MainWindow", "GPS Stop"))
        self.status_indicator.setText(_translate("MainWindow", "Connecting..."))

    @QtCore.pyqtSlot()
    def on_start_button_clicked(self):
        print("Start")
        self.status_indicator.setText("GPS Start Logging")
        self.status_indicator.adjustSize()

        self.stop_button.setStyleSheet("background-color : yellow")
        self.start_button.setStyleSheet("background-color : green")

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        #open subwindow
        self.sub = SubWindow()
        self.sub.show()

        #kill previous timer and reset timer details before starting the loop
        self.stop_timer()
        
        self._generator = self.loopGenerator(self.sub)  # Start the loop
        
        #timer occurs every time once there are no more window events to process (ex. passive_cam out end of loop)
        self._timerId = self.startTimer(0)   # This is the idle timer
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
    
    def stop_timer(self):
        if self._timerId is not None:
            self.killTimer(self._timerId)
        self._generator = None
        self._timerId = None
        
    def loopGenerator(self,sub_window):
        # Put the code of your loop here
        while True:
            print(1)
            time.sleep(1)
            
            if (sub_window.button_clicked ==1):
                print("Broken out of the loop")
                break
                
            # No processEvents() needed, just "pause" the loop using yield
            yield
            
            
    def timerEvent(self, event):
        # This is called every time the GUI is idle.
        
        #if self.loopGenerator is not running return None
        if self._generator is None:
            return
        
        #try to grab next iteration, if there is an error, stop the timer.
        try:
            next(self._generator)  # Run the next iteration
        except StopIteration:
            self.stop_timer()
        
    @QtCore.pyqtSlot()
    def on_stop_button_clicked(self):
        print("Stop")
        
        self.status_indicator.setText("GPS Stop Logging")
        self.status_indicator.adjustSize()
        
        self.stop_button.setStyleSheet("background-color : green")
        self.start_button.setStyleSheet("background-color : yellow")
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        print("Stop Button Clicked")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
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



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ui = UI_MainWindow()
    ui.show()

    sys.exit(app.exec_())
