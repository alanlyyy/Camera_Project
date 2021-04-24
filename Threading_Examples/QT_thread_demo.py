from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys

class Window(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        #start thread
        self.thread = Worker()
        
        
        self.startButton = QPushButton(self.tr("&Start"))
        
        #main window screen
        self.viewer = QLabel()
        self.viewer.setFixedSize(300, 300)
        self.viewer.setText("Before revealing my age")
        
        #once thread is completed call self.updateUi function
        #self.updateUi allows the spin box to be enabled again
        self.thread.finished.connect(self.updateUi)
        #self.thread.terminated.connect(self.updateUi)
        
        #take the output of the pyqtSignal and pass the parameters into addImage function
        #write output of addImage to viewer label
        self.thread.output['int'].connect(self.addImage)
        
        #wait for start button clicked, once clicked call makePicture function
        self.startButton.clicked.connect(self.makePicture)
        
        
        layout = QGridLayout()
        layout.addWidget(self.startButton, 0, 2)
        layout.addWidget(self.viewer, 1, 0, 1, 3)
        self.setLayout(layout)        
        self.setWindowTitle(self.tr("Simple Threading Example"))
        
    def makePicture(self):
        """Starts the thread."""
        
        #enable user input again.
        self.startButton.setEnabled(False)
        #start thread with the new user input value 
        self.thread.render(5)
        
    def addImage(self, int_var):
        """Once thread is completed, output signals rect and image
        are passed into the function to be updated with self.viewer.
        """
        self.viewer.setText("After revealing my age\n My age is %d"%int_var)
        self.viewer.update()
        
    def updateUi(self):
        """
        Function used to enable user input functionality
        once thread is completed.
        """
        self.startButton.setEnabled(True)
        
class Worker(QThread):
    output = pyqtSignal(int)
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.user_val = 0
        self.stars = 0
        
    def __del__(self):    
        self.exiting = True
        self.wait()
        
    def render(self, user_int):    
        self.user_val= user_int
        self.start()
        
    def run(self):        
        # Note: This is never called directly. It is called by Qt once the
        # thread environment has been set up.
            
        self.output.emit(self.user_val)
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())