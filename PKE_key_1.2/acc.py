import smbus
import threading
import time
from math import sqrt

import accconfig

class sleep_mode_control_module:
    def __init__(self):
        self.bus =smbus.SMBus(1)            #init i2c bus
        self.sleep = False                  #Sleep mode, True if no motion detected for given time
        self.acc_queue = []                 #Queue of previous acc readouts
        self.acc_value = None               #Current average acc value
        self.sleep_timer_start = None       #Start of most recent sleep timer
        self.sleep_timer_active = False
        self.mpu_init()

    def start_acc_monitor(self):
            #create thread and start it
            thread = threading.Thread(
                target = monitor_acc,
                args = (),
                kwargs = {
                'bus' : self.bus,
                'parent' : self,
                'sleep' : 0.1,
                'debug' : False
                })
            thread.daemon = True
            thread.start()

    def acc_callback(self, acc):
        acc_abs = sqrt((acc[0]-1)**2 + (acc[1]-1)**2 + (acc[2]-1)**2) #Get abs acceleration
        self.acc_queue.append(acc_abs)
        
        if len(self.acc_queue) > accconfig.ACC_QUEUE_LEN:
            self.acc_queue = self.acc_queue[1:]
        
        if self.acc_value != None:
            #If acc too different from previous sleep false
            if abs((self.acc_value-acc_abs)/self.acc_value) > accconfig.ACC_TOLERANCE:
                if self.sleep == True:
                    print("Sleep mode off")
                    self.sleep = False
                    self.sleep_timer_active = False
            else:
                #If sleep, continue sleeping
                if self.sleep:
                    pass
                else:
                    #If not sleeping but sleep timer already on, check if timer done and sleep if so
                    if self.sleep_timer_active:
                        if (time.time() - self.sleep_timer_start) > accconfig.SLEEP_TIMEOUT:
                            self.sleep = True
                            print("Sleep mode active")
                    #Else start timer
                    else:
                        self.sleep_timer_start = time.time()
                        self.sleep_timer_active = True
        avg = 0
        for value in self.acc_queue:
            avg += value
        self.acc_value = avg/accconfig.ACC_QUEUE_LEN #will produce slow startup until queue is full, should just take a second or two

    def mpu_init(self):
        #Vodoo magic for mpu init
        self.bus.write_byte_data(accconfig.DEVICE_ADDRESS, accconfig.SMPLRT_DIV, 7)
        self.bus.write_byte_data(accconfig.DEVICE_ADDRESS, accconfig.PWR_MGMT_1, 1)
        self.bus.write_byte_data(accconfig.DEVICE_ADDRESS, accconfig.CONFIG, 0)
        self.bus.write_byte_data(accconfig.DEVICE_ADDRESS, accconfig.GYRO_CONFIG, 24)
        self.bus.write_byte_data(accconfig.DEVICE_ADDRESS, accconfig.INT_ENABLE, 1)

def monitor_acc(bus, parent, sleep=0.1, debug=False):
    #call threaded, monitors accelerometer, expects parent with acc_callback method
    while True:
        acc_x = read_raw_data(bus, accconfig.ACCEL_XOUT_H)/16384
        acc_y = read_raw_data(bus, accconfig.ACCEL_YOUT_H)/16384
        acc_z = read_raw_data(bus, accconfig.ACCEL_ZOUT_H)/16384
        if debug:
            print("Accelerometer readout: X =", str(acc_x), "Y =", str(acc_y), "Z = ", str(acc_z))
        parent.acc_callback((acc_x, acc_y, acc_z))
        time.sleep(sleep)

def read_raw_data(bus, addr):
    #read data from addr on the i2c bus
    high = bus.read_byte_data(accconfig.DEVICE_ADDRESS, addr)
    low = bus.read_byte_data(accconfig.DEVICE_ADDRESS, addr+1)
    #combine readouts
    value = ((high << 8) | low)
    #get negatives
    if value > 32768:
        value = value - 65536
    return value
