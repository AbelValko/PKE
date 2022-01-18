CAR_ADDR = "B8:27:EB:99:F8:8A"  #address of car
DEFAULT_PORT = 1                #default port (legacy)
TIMEOUT = 10                    #timeout for bluetooth.BluetoothSocket.recv()
ENCODING = "utf-8"              #encoding for messages
RSSI_THRESHOLD = (-2,0)         #hysteresis for rssi
DEBUG = True
RSSI_SLEEP = 0.05               #rssi thread sleep time, due to hcitool interfacing this has little effect, the command takes too much time
RSSI_AVERAGE_LENGTH = 3         #RSSI queue length
CONNECT_TIMEOUT = 1             #Default timeout for establishing connection
LISTEN_TIMEOUT = 0.5            #Default timeout for recv

