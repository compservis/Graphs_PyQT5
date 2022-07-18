DEBUG_TEST = False

from pathlib import Path
import random
from PySide2.QtCore import *
import pandas as pd
import time
import json
import serial

SERIAL_PORT = "/dev/ttyS0" # For USB: "/dev/tty.usbserial-1420"
BAUDRATE = 9600

class DataHandler(QObject):

    new_data_available = Signal(dict)

    last_log = pd.DataFrame({
        'time': [],
        'sensor': [],
        'value': []
    })

    cs = 0
    ts = 'T'

    def run(self):

        if self.init_serial():
            self.timer = QTimer()
            self.timer.timeout.connect(self.read_data)
            self.timer.start(500)
        else:
            print('No data reading!')

    def init_serial(self):
        if not DEBUG_TEST:
            try:
                self.ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
            except:
                print('Unable to open Serial')
                self.ser = None
                return False
        return True

    def read_data(self):
        if not DEBUG_TEST:
            try:
                reading = self.ser.readline().decode()
                print("reading:", reading)
            except:
                pass
        else:
            # --- TEST PART ------
            r = {'sensor': self.ts + str(self.cs), 'value': round(random.uniform(17.2, 23.5), 2)}
            reading = json.dumps(r)
            if (self.cs >= 20):
                if self.ts == 'T':
                    self.ts = 'P'
                else:
                    self.ts = 'T'
                self.cs = 0
            # ---------------------
        self.handle_data(reading)
        self.cs += 1

    def handle_data(self, data: str):
        if len(data) > 2:
            try:
                self.new_data = json.loads(data)
                # print(self.new_data)
                self.save_to_log()
                self.new_data_available.emit(self.new_data)
            except:
                print("Bad data provided!")
        else:
            print("Got not enough symbols!")

    def last_values_for_sensor(self, sensor):
        l = self.last_log.loc[self.last_log['sensor'] == sensor]
        # print(l)
        values = l['value']
        return values.to_numpy()

    def save_to_log(self):
        # print('New data:', self.new_data)
        # check for today's log presence
        date = time.strftime("%d%b%y", time.localtime())
        the_time = time.strftime("%H:%M:%S", time.localtime())
        todays_log_path = date + ".csv"
        todays_log = Path(todays_log_path)

        df = pd.DataFrame({
            'time': [the_time],
            'sensor': [self.new_data['sensor']],
            'value': [self.new_data['value']],
        })
        if todays_log.is_file():
            # read log
            df.to_csv(str(todays_log), mode='a', header=False, index=False)
            # if self.last_log.empty:
            log = pd.read_csv(todays_log_path)
            self.last_log = log.copy()
            # self.last_log.append(df)
            pd.concat([self.last_log, df], ignore_index=True)
        else:
            # create log file
            log = df
            log.to_csv(str(todays_log), index=False)
        self.last_log = self.last_log.tail(50 * 10) # multiplying by 10 is needed because of the bug in Pandas library