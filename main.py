
#!/usr/bin/env python
from datetime import datetime, timedelta
from pathlib import Path
import re
import time
import numpy as np
import sys
import PySide2
import pandas as pd
import pyqtgraph as pg
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from DataHandler import DataHandler

TEMP_GROUP = 0
PRES_GROUP = 1


class LogView(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent

        self.lt = QVBoxLayout()
        self.title = QLabel("Logs")
        self.title.setStyleSheet("QLabel{font-size: 18pt; font-weight: bold}")
        self.back_btn = QPushButton("BACK")
        self.back_btn.clicked.connect(self._parent.showMainView)
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.plot = self.graph_widget.addPlot(axisItems = {'bottom': pg.DateAxisItem()})
        self.plot.showGrid(x = True, y = True)
        self.type_sel = QComboBox()
        self.type_sel.addItems(["Temperature", "Pressure"])

        self.sensor_sel = QComboBox()
        for i in range(20):
            self.sensor_sel.addItem(str(i+1))

        validator_date = QRegExpValidator(QRegExp("[0-9\,\. ]+"), self)
        validator_time = QRegExpValidator(QRegExp("[0-9\:\. ]+"), self)

        self.begin_date_input = QLineEdit()
        self.begin_time_input = QLineEdit()
        self.end_date_input = QLineEdit()
        self.end_time_input = QLineEdit()
        self.show_btn = QPushButton("SHOW")

        self.begin_date_input.setFixedWidth(150)
        self.begin_time_input.setFixedWidth(80)
        self.end_date_input.setFixedWidth(150)
        self.end_time_input.setFixedWidth(80)

        self.begin_date_input.setValidator(validator_date)
        self.begin_time_input.setValidator(validator_time)
        self.end_date_input.setValidator(validator_date)
        self.end_time_input.setValidator(validator_time)
        self.begin_date_input.setMaxLength(8)
        self.begin_time_input.setMaxLength(5)
        self.end_date_input.setMaxLength(8)
        self.end_time_input.setMaxLength(5)

        dat = datetime.now()
        self.end_date_input.setText(dat.strftime('%d.%m.%y'))
        dat = dat + timedelta(days=-1)
        self.begin_date_input.setText(dat.strftime('%d.%m.%y'))
        self.begin_time_input.setText("00:00")
        self.end_time_input.setText("23:59")

        controls_l = QHBoxLayout()
        controls_l.addWidget(self.back_btn)
        controls_l.addStretch(8)
        controls_l.addWidget(QLabel("Begin date:"))
        controls_l.addWidget(self.begin_date_input)

        controls_l.addWidget(self.begin_time_input)
        controls_l.addStretch(1)
        controls_l.addWidget(QLabel("End date:"))
        controls_l.addWidget(self.end_date_input)

        controls_l.addWidget(self.end_time_input)
        controls_l.addStretch(1)
        controls_l.addWidget(QLabel("Sensor type:"))
        controls_l.addWidget(self.type_sel)
        controls_l.addWidget(QLabel("number:"))
        controls_l.addWidget(self.sensor_sel)
        controls_l.addStretch(2)
        controls_l.addWidget(self.show_btn)

        self.lt.addWidget(self.title)
        self.lt.addWidget(self.graph_widget)
        self.lt.addLayout(controls_l)

        self.setLayout(self.lt)


    def set_data(self, data):
        self.plot.setData(data)
        self.update()



class LogViewController(QObject):

    def setView(self, view:LogView):
        self.view = view
        self.view.show_btn.clicked.connect(self.loadLog)

    def loadLog(self):
        begin_date = self.view.begin_date_input.text()
        begin_time = self.view.begin_time_input.text()
        end_date = self.view.end_date_input.text()
        end_time = self.view.end_time_input.text()
        sensor_type = self.view.type_sel.currentText()
        sensor_num = self.view.sensor_sel.currentText()
        sensor = ''
        the_pen = pg.mkPen((255,255,255), width=2)
        symbol=''
        if sensor_type == 'Temperature':
            sensor = 'T'
            the_pen = pg.mkPen((0,255,255), width=2)
            symbol='+'
        elif sensor_type == 'Pressure':
            sensor = 'P'
            the_pen = pg.mkPen((255,127,0), width=2)
            symbol = '+'
        sensor += sensor_num

        t = self.get_logs(begin_date, end_date, begin_time, end_time, sensor)
        self.view.plot.clear()
        self.view.plot.plot(x=[x.timestamp() for x in t[0]], y=t[1], pen=the_pen, symbol=symbol)

    def get_logs(self, begin_date, end_date, begin_time, end_time, sensor):

        df = pd.DataFrame({
            'time': [],
            'sensor': [],
            'value': []
        })

        def processDate(d):
            raw_date = re.sub('[^0-9]', ' ', d)
            dt = time.strptime(raw_date, "%d %m %y")
            f_date = time.strftime('%d%b%y', dt)
            return f_date

        def processTime(d):
            raw_date = re.sub('[^0-9]', ' ', d)
            # dt = time.strptime(raw_date, "%H %M")
            return raw_date

        bd = time.strptime(processDate(begin_date), "%d%b%y")
        ed = time.strptime(processDate(end_date), "%d%b%y")
        bt = time.strptime(processTime(begin_time), "%H %M")
        et = time.strptime(processTime(end_time), "%H %M")
        dat = datetime(int(time.strftime('%Y', bd)), int(time.strftime('%m', bd)), int(time.strftime('%d', bd)), int(time.strftime('%H', bt)), int(time.strftime('%M', bt)))
        dat_i = dat
        end = datetime(int(time.strftime('%Y', ed)), int(time.strftime('%m', ed)), int(time.strftime('%d', ed)), int(time.strftime('%H', et)), int(time.strftime('%M', et)))
        print(dat, end)
        files = []
        times = []
        values = []
        d = []
        while dat_i <= end:
            # try:
            dd = dat_i.strftime('%d%b%y')
            the_path = dd + ".csv"
            the_log = Path(the_path)
            if the_log.is_file():
                print('Path:', the_path)
                print('Date:', dat_i)
                df = pd.read_csv(the_log, index_col=None)
                print(df)
                for i in df.index:
                    ti = time.strptime(df['time'][i], "%H:%M:%S")
                    tti = datetime(int(dat_i.strftime('%Y')), int(dat_i.strftime('%m')), int(dat_i.strftime('%d')), int(time.strftime('%H', ti)), int(time.strftime('%M', ti)))
                    if tti > end or tti < dat:
                        df.drop(index=i)
                    else:
                        current_line = df.iloc[[i]]
                        d.append(current_line)
                        current_sensor = current_line.iloc[-1]['sensor']
                        if current_sensor == sensor:
                            current_value = current_line.iloc[-1]['value']
                            full_time = datetime(year=int(dat_i.strftime('%Y')), 
                                            month=int(dat_i.strftime('%m')), 
                                            day=int(dat_i.strftime('%d')), 
                                            hour=int(time.strftime('%H', ti)), 
                                            minute=int(time.strftime('%M', ti)), 
                                            second=int(time.strftime('%S', ti)))

                            times.append(full_time)
                            values.append(current_value)
                files.append(the_path)
            dat_i = dat_i + timedelta(days=1)
        print("INFO/Menu: Found logs")
        return [times, values] # df



class ImageView(QWidget):
    def __init__(self):
        super().__init__()
        self.pixmap = QPixmap()

    def setImage(self, im_path):
        self.pixmap.load(im_path)
        self.update()

    def sizeHint(self):
        return QSize(600,600)

    def paintEvent(self, e):
        painter = QPainter(self)
        rect = QRect(0, 0, painter.device().width(), painter.device().height())
        painter.drawPixmap(rect, self.pixmap)

class GraphsView(QWidget):

    plots_temp = []
    plots_pres = []
    plots = [plots_temp, plots_pres]

    def __init__(self, parent):
        super().__init__()
        self._parent = parent

        # creating graphics layout widget
        win = pg.GraphicsLayoutWidget()
        for group in range(2):
            for i in range(20):
                if i % 4 == 0:
                    win.nextRow()
                p = win.addPlot(enableMenu=False, enableMouse = False, invertY = True)
                p.showAxis('bottom', False)
                p.showGrid(x = True, y = True)
                if group == TEMP_GROUP:
                    the_pen = pg.mkPen((0,255,255), width=2)
                elif group == PRES_GROUP:
                    the_pen = pg.mkPen((255,127,0), width=2)
                else:
                    the_pen = pg.mkPen((255,0,0), width=2)
                self.plots[group].append(p.plot([0], pen=the_pen))

        self.title = QLabel("Sensor Graphs")
        self.title.setStyleSheet("QLabel{font-size: 18pt;font-weight: bold}")

        self.back_btn = QPushButton("BACK")
        btm_l = QHBoxLayout()
        btm_l.addWidget(self.back_btn)
        self.back_btn.clicked.connect(self._parent.showAllSensorsView)
        btm_l.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(win)
        layout.addLayout(btm_l)

        self.setLayout(layout)

    def set_data(self, data: list, group=0, view=0):
        self.plots[group][view].setData(data)
        self.update()


class GraphsViewController(QObject):

    view = None

    def set_view(self, view:GraphsView):
        self.view = view

    def set_handler(self, handler:DataHandler):
        self.handler = handler
        self.handler.new_data_available.connect(self.update)

    def update(self, data):
        group_s = data['sensor'][0]
        num = int(data['sensor'][1:])

        if group_s == 'T':
            group = TEMP_GROUP
        elif group_s == 'P':
            group = PRES_GROUP
        else:
            print('Got bad sensor name!')
            return
        
        if num > 20 or num < 0:
            print('Got bad sensor number!')
            return

        the_data = self.handler.last_values_for_sensor(data['sensor'])
        if the_data is not None and self.view is not None:
            self.view.set_data(the_data, group = group, view = num-1)
        else:
            print("Couldn't update plot, bad data given!")



class SensorValueView(QWidget):
    def __init__(self):
        super().__init__()
        self.name_lbl = QLabel("Sensor")
        self.value_lbl = QLabel("N/A")
        self.value_lbl.setFixedWidth(80)
        self.value_lbl.setFrameShape(QFrame.Panel)
        self.value_lbl.setFrameShadow(QFrame.Sunken)
        l = QHBoxLayout()
        l.addWidget(self.name_lbl)
        l.addWidget(self.value_lbl)
        self.setLayout(l)

    def setName(self, name):
        self.name = name
        self.name_lbl.setText(self.name)

    def setValue(self, value):
        self.value = value
        self.value_lbl.setText(value)

    def setValueColor(self, color):
        self.value_lbl.setStyleSheet("background-color: " + str(color))

    def sizeHint(self) -> QSize:
        return QSize(40,160)

class AllSensorValuesView(QWidget):

    sensor_amount = 40
    views_amount = 20
    temp_views = []
    pres_views = []
    views = [temp_views, pres_views]

    def __init__(self, parent):
        super().__init__()
        self._parent = parent

        layout = QVBoxLayout()
        cols_l = QHBoxLayout()
        col1_l = QVBoxLayout()
        col2_l = QVBoxLayout()

        # Headers
        temp_header_lbl = QLabel("TEMPERATURE")
        pres_header_lbl = QLabel("PRESSURE")
        col1_l.addWidget(temp_header_lbl)
        col2_l.addWidget(pres_header_lbl)

        grid1 = QGridLayout()
        grid1.setSpacing(10)
        grid2 = QGridLayout()
        grid2.setSpacing(10)
        
        # Add views to list of views 
        for i in range(self.views_amount):
            v = SensorValueView()
            v.setName("Sensor " + str(i+1))
            v.setStyleSheet("QLabel{font-size: 18pt;}")
            v.setValueColor("#041f1e")
            self.temp_views.append(v)
        for i in range(self.views_amount):
            v = SensorValueView()
            v.setName("Sensor " + str(i+1))
            v.setStyleSheet("QLabel{font-size: 18pt;}")
            v.setValueColor("#241006")
            self.pres_views.append(v)

        # Display views to grid 1
        column = 0
        row = 0
        for view in self.temp_views:
            if column >= 2:
                column = 0
                row = row + 1
            if row >= 10:
                row = 0
            grid1.addWidget(view, row, column)
            column = column + 1
            

        # Display views to grid 2
        column = 0 
        row = 0
        for view in self.pres_views:
            if column >= 2:
                column = 0
                row = row + 1
            if row >= 10:
                row = 0
            grid2.addWidget(view, row, column)
            column = column + 1
                    
        col1_l.addLayout(grid1)
        col2_l.addLayout(grid2)

        cols_l.addLayout(col1_l)
        cols_l.addLayout(col2_l)

        self.title = QLabel("Sensor values")
        self.title.setStyleSheet("QLabel{font-size: 18pt; font-weight: bold}")

        self.back_btn = QPushButton("BACK")
        self.graphs_btn = QPushButton("SHOW GRAPHS")
        btm_l = QHBoxLayout()
        btm_l.addWidget(self.back_btn)
        self.back_btn.clicked.connect(self._parent.showMainView)
        btm_l.addStretch()
        btm_l.addWidget(self.graphs_btn)
        self.graphs_btn.clicked.connect(self._parent.showGraphsView)

        layout.addWidget(self.title)
        layout.addLayout(cols_l)
        layout.addLayout(btm_l)

        self.setLayout(layout)

    def set_handler(self, handler):
        self.handler = handler
        self.handler.new_data_available.connect(self.update_values)

    def update_values(self, data):
        if data is  None:
            return
            
        group_s = data['sensor'][0]
        num = int(data['sensor'][1:])

        if group_s == 'T':
            group = TEMP_GROUP
        elif group_s == 'P':
            group = PRES_GROUP
        else:
            print('Got bad sensor name!')
            return
        
        if num > 20 or num < 0:
            print('Got bad sensor number!')
            return

        the_data = self.handler.last_values_for_sensor(data['sensor'])
        # print('Last data', the_data)
        if the_data is not None:
            self.views[group][num-1].setValue(str(data['value']))
        else:
            print("Couldn't update plot, bad data given!")

class MainView(QWidget):

    def __init__(self, parent):
        super().__init__()
        self._parent = parent

        menu_l = QVBoxLayout()
        self.sensors_btn = QPushButton("Show sensors")
        self.log_btn = QPushButton("Show log")
        self.sensors_btn.setFixedSize(120, 42)
        self.log_btn.setFixedSize(120, 42)
        self.dummy1_btn = QPushButton()
        self.dummy2_btn = QPushButton()
        self.dummy3_btn = QPushButton()
        self.dummy1_btn.setFixedSize(120, 42)
        self.dummy2_btn.setFixedSize(120, 42)
        self.dummy3_btn.setFixedSize(120, 42)
        self.dummy1_btn.setDisabled(True)
        self.dummy2_btn.setDisabled(True)
        self.dummy3_btn.setDisabled(True)
        menu_l.addStretch()
        menu_l.addWidget(self.sensors_btn)
        menu_l.addWidget(self.log_btn)
        menu_l.addWidget(self.dummy1_btn)
        menu_l.addWidget(self.dummy2_btn)
        menu_l.addWidget(self.dummy3_btn)
        menu_l.addStretch()

        self.sensors_btn.clicked.connect(self._parent.showAllSensorsView)
        self.log_btn.clicked.connect(self._parent.showLogView)

        self.l = QHBoxLayout()

        self.l.addStretch()
        self.l.addLayout(menu_l)

        self.setLayout(self.l)

    

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.handler = DataHandler()
        self.handler_thread = QThread()
        self.handler.moveToThread(self.handler_thread)
        self.handler_thread.start()
        self.handler.run()

        # self.setFixedSize(QSize(800, 600))
        self.setWindowTitle("Sensor Dashboard")
        self.lt = QStackedLayout()

        self.main_view = MainView(self)
        self.sensors_view = AllSensorValuesView(self)
        self.sensors_view.set_handler(self.handler)

        self.graphs_view_controller = GraphsViewController()
        self.graphs_view_controller.set_handler(self.handler)

        self.log_view = LogView(self)
        self.log_view_controller = LogViewController()
        self.log_view_controller.setView(self.log_view)

        self.graphs_view = GraphsView(self)
        self.graphs_view_controller.set_view(self.graphs_view)


        self.lt.addWidget(self.main_view)
        self.lt.addWidget(self.sensors_view)
        self.lt.addWidget(self.graphs_view)
        self.lt.addWidget(self.log_view)

        

        widget = QWidget()
        widget.setLayout(self.lt)
        self.setCentralWidget(widget)

        self.showMainView()
        self.showFullScreen()

    def showMainView(self):
        self.lt.setCurrentWidget(self.main_view)

    def showAllSensorsView(self):
        self.lt.setCurrentWidget(self.sensors_view)
    
    def showGraphsView(self):
        self.lt.setCurrentWidget(self.graphs_view)
    
    def showLogView(self):
        self.lt.setCurrentWidget(self.log_view)

    def hideGraphsView(self):
        pass
        
        

if __name__ == '__main__':

    app = QApplication(sys.argv)

    with open('styles.qss', 'r') as f:
        style = f.read()

    # Set the stylesheet of the application
    app.setStyleSheet(style)

    window = MainWindow()
    window.show()

    app.exec_()