import sys
import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np

port = '/dev/tty.usbmodemFA131'

class Oscilloscope(QtGui.QWidget):

    def __init__(self, port):
        QtGui.QWidget.__init__(self)

        self.monitorThread = OscilloscopeThread(port)
        self.monitorThread.sigNewData.connect(self.newData)

        # state variables
        self.lastPlotTime = None
        self.times = []
        self.values = []

        # Set up UI
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(3,3,3,3)
        self.setLayout(self.layout)

        self.startBtn = QtGui.QPushButton('Start')
        self.startBtn.setCheckable(True)
        self.startBtn.toggled.connect(self.startBtnClicked)

        self.timeSpin = pg.SpinBox(value=5.0, suffix='s', siPrefix=True, dec=True, step=0.5, bounds=(0,None))

        self.plot = pg.PlotWidget()
        self.plotCurve = self.plot.plot()

        vlayout = QtGui.QVBoxLayout()
        vlayout.addWidget(self.startBtn)
        vlayout.addWidget(self.timeSpin)
        vlayout.addStretch(0)
        self.layout.addLayout(vlayout, 0, 0)
        self.layout.addWidget(self.plot, 0, 1)
        self.layout.setColumnStretch(1,5)

        self.setGeometry(100,100,1000,600)
        self.show()


    def startBtnClicked(self, b):
        if b:
            self.startBtn.setText('Stop')
            self.clearData()
            self.monitorThread.start()
        else:
            self.startBtn.setText('Start')
            self.monitorThread.stop()

    def clearData(self):
        self.lastPlotTime = None
        self.times = []
        self.values = []

    def newData(self, data):

        # Get rid of old data
        minTime = None
        now = pg.time()
        while len(self.times) > 0 and self.times[0] < (now-self.timeSpin.value()):
            self.times.pop(0)
            self.values.pop(0)
        if len(self.times) > 0 and (minTime is None or self.times[0] < minTime):
            minTime = self.times[0]
        if minTime is None:
            minTime = data[0]

        # add new data
        draw = False
        if self.lastPlotTime is None or now - self.lastPlotTime > 0.05:
            draw = True
            self.lastPlotTime = now
            
        self.values.append(data[1])
        self.times.append(data[0])
        if draw:
            self.plotCurve.setData(np.array(self.times)-minTime, np.array(self.values))


class OscilloscopeThread(QtCore.QThread):

    sigNewData = QtCore.Signal(object) ## (time, value) - emitted when a new value is read from the serial port

    def __init__(self, port):
        self.stopped = True
        QtCore.QThread.__init__(self)

        self.port = serial.Serial(port)

    def start(self):
        self.stopped = False
        QtCore.QThread.start(self)

    def stop(self):
        self.stopped = True

    def quit(self):
        self.stop()

    def run(self):

        while True:
            if self.stopped:
                break

            try:
                n = int(self.port.readline())
                t = pg.time()
            except:
                continue

            self.sigNewData.emit((t,n))



if __name__ == '__main__':
    app = pg.mkQApp()

    scope = Oscilloscope(port)
    scope.show()

    if sys.flags.interactive == 0:
        app.exec_()


