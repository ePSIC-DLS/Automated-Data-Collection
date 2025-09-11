"""
Example code showing how to construct a Lens and Defs table
for a JEOL microscope. Written by Bart Marzec, PyJEM workshop
in York, 10 Jan 2024.
"""


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LensDefTable(object):
    def setupUi(self, LensDefTable):
        LensDefTable.setObjectName("LensDefTable")
        LensDefTable.resize(600, 600)
        self.label = QtWidgets.QLabel(LensDefTable)
        self.label.setGeometry(QtCore.QRect(20, 20, 561, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(LensDefTable)
        self.label_2.setGeometry(QtCore.QRect(20, 80, 68, 19))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(LensDefTable)
        self.label_3.setGeometry(QtCore.QRect(20, 110, 68, 19))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(LensDefTable)
        self.label_4.setGeometry(QtCore.QRect(20, 140, 68, 19))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(LensDefTable)
        self.label_5.setGeometry(QtCore.QRect(20, 170, 68, 19))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(LensDefTable)
        self.label_6.setGeometry(QtCore.QRect(20, 200, 68, 19))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(LensDefTable)
        self.label_7.setGeometry(QtCore.QRect(20, 270, 68, 19))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(LensDefTable)
        self.label_8.setGeometry(QtCore.QRect(20, 300, 68, 19))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(LensDefTable)
        self.label_9.setGeometry(QtCore.QRect(20, 330, 68, 19))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(LensDefTable)
        self.label_10.setGeometry(QtCore.QRect(20, 360, 68, 19))
        self.label_10.setObjectName("label_10")
        self.label_11 = QtWidgets.QLabel(LensDefTable)
        self.label_11.setGeometry(QtCore.QRect(20, 390, 68, 19))
        self.label_11.setObjectName("label_11")
        self.label_12 = QtWidgets.QLabel(LensDefTable)
        self.label_12.setGeometry(QtCore.QRect(20, 420, 68, 19))
        self.label_12.setObjectName("label_12")
        self.label_13 = QtWidgets.QLabel(LensDefTable)
        self.label_13.setGeometry(QtCore.QRect(20, 450, 68, 19))
        self.label_13.setObjectName("label_13")
        self.label_14 = QtWidgets.QLabel(LensDefTable)
        self.label_14.setGeometry(QtCore.QRect(20, 480, 68, 19))
        self.label_14.setObjectName("label_14")
        self.label_CL1 = QtWidgets.QLabel(LensDefTable)
        self.label_CL1.setGeometry(QtCore.QRect(120, 80, 68, 19))
        self.label_CL1.setObjectName("label_CL1")
        self.label_CL2 = QtWidgets.QLabel(LensDefTable)
        self.label_CL2.setGeometry(QtCore.QRect(120, 110, 68, 19))
        self.label_CL2.setObjectName("label_CL2")
        self.label_CL3 = QtWidgets.QLabel(LensDefTable)
        self.label_CL3.setGeometry(QtCore.QRect(120, 140, 68, 19))
        self.label_CL3.setObjectName("label_CL3")
        self.label_OLc = QtWidgets.QLabel(LensDefTable)
        self.label_OLc.setGeometry(QtCore.QRect(120, 170, 68, 19))
        self.label_OLc.setObjectName("label_OLc")
        self.label_OLf = QtWidgets.QLabel(LensDefTable)
        self.label_OLf.setGeometry(QtCore.QRect(120, 200, 68, 19))
        self.label_OLf.setObjectName("label_OLf")
        self.label_GunA1X = QtWidgets.QLabel(LensDefTable)
        self.label_GunA1X.setGeometry(QtCore.QRect(120, 270, 68, 19))
        self.label_GunA1X.setObjectName("label_GunA1X")
        self.label_GunA2X = QtWidgets.QLabel(LensDefTable)
        self.label_GunA2X.setGeometry(QtCore.QRect(120, 300, 68, 19))
        self.label_GunA2X.setObjectName("label_GunA2X")
        self.label_SpotAX = QtWidgets.QLabel(LensDefTable)
        self.label_SpotAX.setGeometry(QtCore.QRect(120, 330, 68, 19))
        self.label_SpotAX.setObjectName("label_SpotAX")
        self.label_CLA1X = QtWidgets.QLabel(LensDefTable)
        self.label_CLA1X.setGeometry(QtCore.QRect(120, 360, 68, 19))
        self.label_CLA1X.setObjectName("label_CLA1X")
        self.label_CLA2X = QtWidgets.QLabel(LensDefTable)
        self.label_CLA2X.setGeometry(QtCore.QRect(120, 390, 68, 19))
        self.label_CLA2X.setObjectName("label_CLA2X")
        self.label_IS1X = QtWidgets.QLabel(LensDefTable)
        self.label_IS1X.setGeometry(QtCore.QRect(120, 420, 68, 19))
        self.label_IS1X.setObjectName("label_IS1X")
        self.label_IS2X = QtWidgets.QLabel(LensDefTable)
        self.label_IS2X.setGeometry(QtCore.QRect(120, 450, 68, 19))
        self.label_IS2X.setObjectName("label_IS2X")
        self.label_PLAX = QtWidgets.QLabel(LensDefTable)
        self.label_PLAX.setGeometry(QtCore.QRect(120, 480, 68, 19))
        self.label_PLAX.setObjectName("label_PLAX")
        self.label_GunA1Y = QtWidgets.QLabel(LensDefTable)
        self.label_GunA1Y.setGeometry(QtCore.QRect(230, 270, 68, 19))
        self.label_GunA1Y.setObjectName("label_GunA1Y")
        self.label_GunA2Y = QtWidgets.QLabel(LensDefTable)
        self.label_GunA2Y.setGeometry(QtCore.QRect(230, 300, 68, 19))
        self.label_GunA2Y.setObjectName("label_GunA2Y")
        self.label_SpotAY = QtWidgets.QLabel(LensDefTable)
        self.label_SpotAY.setGeometry(QtCore.QRect(230, 330, 68, 19))
        self.label_SpotAY.setObjectName("label_SpotAY")
        self.label_CLA1Y = QtWidgets.QLabel(LensDefTable)
        self.label_CLA1Y.setGeometry(QtCore.QRect(230, 360, 68, 19))
        self.label_CLA1Y.setObjectName("label_CLA1Y")
        self.label_CLA2Y = QtWidgets.QLabel(LensDefTable)
        self.label_CLA2Y.setGeometry(QtCore.QRect(230, 390, 68, 19))
        self.label_CLA2Y.setObjectName("label_CLA2Y")
        self.label_IS1Y = QtWidgets.QLabel(LensDefTable)
        self.label_IS1Y.setGeometry(QtCore.QRect(230, 420, 68, 19))
        self.label_IS1Y.setObjectName("label_IS1Y")
        self.label_IS2Y = QtWidgets.QLabel(LensDefTable)
        self.label_IS2Y.setGeometry(QtCore.QRect(230, 450, 68, 19))
        self.label_IS2Y.setObjectName("label_IS2Y")
        self.label_PLAY = QtWidgets.QLabel(LensDefTable)
        self.label_PLAY.setGeometry(QtCore.QRect(230, 480, 68, 19))
        self.label_PLAY.setObjectName("label_PLAY")
        self.label_16 = QtWidgets.QLabel(LensDefTable)
        self.label_16.setGeometry(QtCore.QRect(20, 540, 171, 19))
        self.label_16.setObjectName("label_16")
        self.label_time = QtWidgets.QLabel(LensDefTable)
        self.label_time.setGeometry(QtCore.QRect(230, 540, 131, 19))
        self.label_time.setObjectName("label_time")

        self.retranslateUi(LensDefTable)
        QtCore.QMetaObject.connectSlotsByName(LensDefTable)

    def retranslateUi(self, LensDefTable):
        _translate = QtCore.QCoreApplication.translate
        LensDefTable.setWindowTitle(_translate("LensDefTable", "Lens and Defs table by PyQt and PyJEM"))
        self.label.setText(_translate("LensDefTable", "PyJEM and PyQt based Lens and Deflector table"))
        self.label_2.setText(_translate("LensDefTable", "CL1:"))
        self.label_3.setText(_translate("LensDefTable", "CL2:"))
        self.label_4.setText(_translate("LensDefTable", "CL3:"))
        self.label_5.setText(_translate("LensDefTable", "OLc:"))
        self.label_6.setText(_translate("LensDefTable", "OLf:"))
        self.label_7.setText(_translate("LensDefTable", "GunA1:"))
        self.label_8.setText(_translate("LensDefTable", "GunA2:"))
        self.label_9.setText(_translate("LensDefTable", "SpotA:"))
        self.label_10.setText(_translate("LensDefTable", "CLA1:"))
        self.label_11.setText(_translate("LensDefTable", "CLA2:"))
        self.label_12.setText(_translate("LensDefTable", "IS1:"))
        self.label_13.setText(_translate("LensDefTable", "IS2:"))
        self.label_14.setText(_translate("LensDefTable", "PLA:"))
        self.label_CL1.setText(_translate("LensDefTable", "XXXX"))
        self.label_CL2.setText(_translate("LensDefTable", "XXXX"))
        self.label_CL3.setText(_translate("LensDefTable", "XXXX"))
        self.label_OLc.setText(_translate("LensDefTable", "XXXX"))
        self.label_OLf.setText(_translate("LensDefTable", "XXXX"))
        self.label_GunA1X.setText(_translate("LensDefTable", "XXXX"))
        self.label_GunA2X.setText(_translate("LensDefTable", "XXXX"))
        self.label_SpotAX.setText(_translate("LensDefTable", "XXXX"))
        self.label_CLA1X.setText(_translate("LensDefTable", "XXXX"))
        self.label_CLA2X.setText(_translate("LensDefTable", "XXXX"))
        self.label_IS1X.setText(_translate("LensDefTable", "XXXX"))
        self.label_IS2X.setText(_translate("LensDefTable", "XXXX"))
        self.label_PLAX.setText(_translate("LensDefTable", "XXXX"))
        self.label_GunA1Y.setText(_translate("LensDefTable", "YYYY"))
        self.label_GunA2Y.setText(_translate("LensDefTable", "YYYY"))
        self.label_SpotAY.setText(_translate("LensDefTable", "YYYY"))
        self.label_CLA1Y.setText(_translate("LensDefTable", "YYYY"))
        self.label_CLA2Y.setText(_translate("LensDefTable", "YYYY"))
        self.label_IS1Y.setText(_translate("LensDefTable", "YYYY"))
        self.label_IS2Y.setText(_translate("LensDefTable", "YYYY"))
        self.label_PLAY.setText(_translate("LensDefTable", "YYYY"))
        self.label_16.setText(_translate("LensDefTable", "Last refresh time:"))
        self.label_time.setText(_translate("LensDefTable", "hh-mm-ss"))




from PyQt5 import QtWidgets, QtCore

from PyJEM import TEM3
import time



# Allow enough time to establish connection with the microscope
time.sleep(5)

#print(lenses.GetCL3())

# Worker will run in the background as a separate QThread.
# This way it will not block the main GUI.

class Worker(QtCore.QThread):
    execute = QtCore.pyqtSignal(dict)
    lenses = TEM3.Lens3()
    defs = TEM3.Def3()
    def run(self):
        #print(lenses.GetCL3())
        while True:      
            newData = {}
            try:
                newData['CL1'] = self.lenses.GetCL1()
                newData['CL2'] = self.lenses.GetCL2()
                newData['CL3'] = self.lenses.GetCL3()
                newData['OLc'] = self.lenses.GetOLc()
                newData['OLf'] = self.lenses.GetOLf()
                newData['GunA1X'], newData['GunA1Y'] = self.defs.GetGunA1()
                newData['GunA2X'], newData['GunA2Y'] = self.defs.GetGunA2()
                newData['SpotAX'], newData['SpotAY'] = self.defs.GetSpotA()
                newData['CLA1X'], newData['CLA1Y'] = self.defs.GetCLA1()
                newData['CLA2X'], newData['CLA2Y'] = self.defs.GetCLA2()
                newData['IS1X'], newData['IS1Y'] = self.defs.GetIS1()
                newData['IS2X'], newData['IS2Y'] = self.defs.GetIS2()
                newData['PLAX'], newData['PLAY'] = self.defs.GetPLA()
                newData['time'] = time.strftime("%H:%M:%S")
            except Exception as err:
                newData["exception"]=err
                
            self.execute.emit(newData)
            self.sleep(5)

    
# This is the main GUI class, it will run in the main thread.
# I subclassed Ui_LensDefTable created by Qt Designer and converted
# from a .ui file to a .py file with pyuic5.

class LensDefTableWidget(QtWidgets.QWidget, Ui_LensDefTable):
    def __init__(self):
        super().__init__()
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        # Create a worker object - which will run in a separate thread
        self.worker = Worker()
        # Connect signals to slots
        self.worker.execute.connect(self.update_ui)
        # Start the worker thread.
        self.worker.start()
        #print('third attempt: ', lenses.GetCL3())
    
    # Update_ui will receive a dictionary from the worker, and will need
    # to use it to populate labels in the GUI.
    # It needs to be prepared to receive corrupted dictionaries (error checking).
    def update_ui(self, data):
        try:
            #print('forth_att,emp :', lenses.GetCL3())
            self.label_CL1.setText(hex(data['CL1'])[2:].upper())
            self.label_CL2.setText(hex(data['CL2'])[2:].upper())
            self.label_CL3.setText(hex(data['CL3'])[2:].upper())
            self.label_OLc.setText(hex(data['OLc'])[2:].upper())
            self.label_OLf.setText(hex(data['OLf'])[2:].upper())
            self.label_GunA1X.setText(hex(data['GunA1X'])[2:].upper())
            self.label_GunA1Y.setText(hex(data['GunA1Y'])[2:].upper())
            self.label_GunA2X.setText(hex(data['GunA2X'])[2:].upper())
            self.label_GunA2Y.setText(hex(data['GunA2Y'])[2:].upper())  
            self.label_SpotAX.setText(hex(data['SpotAX'])[2:].upper())
            self.label_SpotAY.setText(hex(data['SpotAY'])[2:].upper())   
            self.label_CLA1X.setText(hex(data['CLA1X'])[2:].upper())
            self.label_CLA1Y.setText(hex(data['CLA1Y'])[2:].upper())   
            self.label_CLA2X.setText(hex(data['CLA2X'])[2:].upper())
            self.label_CLA2Y.setText(hex(data['CLA2Y'])[2:].upper())    
            self.label_IS1X.setText(hex(data['IS1X'])[2:].upper())
            self.label_IS1Y.setText(hex(data['IS1Y'])[2:].upper())  
            self.label_IS2X.setText(hex(data['IS2X'])[2:].upper())
            self.label_IS2Y.setText(hex(data['IS2Y'])[2:].upper())     
            self.label_PLAX.setText(hex(data['PLAX'])[2:].upper())
            self.label_PLAY.setText(hex(data['PLAY'])[2:].upper())   
            self.label_time.setText(data['time'])
            #print('forth_att,emp :', lenses.GetCL3())
        except Exception as err:
            print(data.get("exception"))
        
    

if __name__ == "__main__":
    import sys
    #print('second attempt : ', lenses.GetCL3())
    app = QtWidgets.QApplication(sys.argv)
    # Create an instance of the subclass
    lens_def_table_widget = LensDefTableWidget()
    # Show the widget
    lens_def_table_widget.show()
    sys.exit(app.exec_())
