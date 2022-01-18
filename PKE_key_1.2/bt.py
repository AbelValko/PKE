import os
import bluetooth
import time
import threading

import btconfig
import bt_rssi


class Bt_module_server:
    """ Class for controlling the bluetooth module, Key is Server, Car is Cient
    """

    def __init__(self):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM) #allocate resource
        self.sock.bind(("",0))              #bind any adapter and any port
        self.client_sock = None 
        self.vehicle_address = None
        self.rssi_thread = None             
        self.stop_rssi_thread = False       #flag to stop rssi thread upon disconnect or reset
        self.rssi = None                    #rolling average rssi readout
        self.rssi_queue = []                #recent rssi readouts for averaging
        self.in_range = False               #in rssi range flag

    def start_rssi_monitor_thread(self):
        """Starts a thread for monitoring rssi value of vehicle_address. 
    Thread is killed upon disconnect or error.
    Calls rssi_callback to update rssi on thread
    """
        self.stop_rssi_thread = False
        self.rssi_thread = threading.Thread(
            target=bt_rssi.monitor_rssi,
            args=(lambda : self.stop_rssi_thread,),
            kwargs={
            'addr' : self.vehicle_address[0],
            'parent' : self,
            'sleep' : btconfig.RSSI_SLEEP,
            'debug' : False
            }
        )
        self.rssi_thread.daemon = True    #dameonize
        self.rssi_thread.start()

    def rssi_callback(self, rssi):
        """Passed RSSI readouts from thread and updates rssi value. 
        """
        #Only average full queue
        if rssi == None:
            self.rssi = None
            self.in_range = False
            return
        else:
            #calculate and update rssi
            if len(self.rssi_queue) >= btconfig.RSSI_AVERAGE_LENGTH:
                self.rssi_queue.append(rssi)
                self.rssi_queue = self.rssi_queue[1:]
                avg = 0
                for i in self.rssi_queue:
                    avg += i
                self.rssi = avg/btconfig.RSSI_AVERAGE_LENGTH
            else:
                self.rssi_queue.append(rssi)
            #update self.in_range based on current rssi value
            if self.rssi == None:
                self.in_range = False
            elif self.rssi >= btconfig.RSSI_THRESHOLD[1]:
                self.in_range = True
            elif self.rssi <= btconfig.RSSI_THRESHOLD[0]:
                self.in_range = False

    def close_sockets(self):
        #graceful exit
        try:
            self.client_sock.close()
            self.sock.close()
        except bluetooth.BluetoothError as e:
            print("Error while closing socket:")
            print(e)
        self.stop_rssi_thread = True    #make sure thread is stopped
        if self.rssi_thread != None:
            self.rssi_thread.join()     #wait for thread to die
        
    def connect(self):
        """Connects to self.vehicle_address on socket
    """
        print("Waiting for connection...")
        self.sock.listen(1)     #Ready to accept 1 connection
        self.sock.settimeout(btconfig.CONNECT_TIMEOUT) #Socket timeout
        current_error = None
        while True:             #Ends only if connection is established. Key has no other job in the meantime. Could be threaded.
            try:                #Try to connect
                self.client_sock, self.vehicle_address = self.sock.accept()
                break
            except bluetooth.btcommon.BluetoothError as e:
                #Errors excepted, connection retried
                errno = e.args[0]
                if errno != current_error:
                    print(e)
                    current_error = errno
                    print("Waiting for connection...")
        print("Connection established from " + str(self.client_sock.getpeername()) + " at " + str(self.vehicle_address[0]))
        
        #Only allow connection from the paired vehicle
        if self.vehicle_address[0] != btconfig.CAR_ADDR:
            print("Address does not match vehicle. Blocking address")
            command = "echo 'block' " + str(self.vehicle_address[0]) + "'\nquit' | bluetoothctl"
            os.system(command)  #Block any unexpected devices that try to connect. Use Bluetoothctl.
            time.sleep(0.1)     #Sync
            return False        #Reloads socket and tries connection again
        return True

    def listen(self, timeout=btconfig.LISTEN_TIMEOUT, printing=True):
        """Unfortunate legacy name... listening for message
        """
        printing = False
        if printing == True:
            print("Listening on client socket...")
        self.client_sock.settimeout(timeout)
        try:
            data = self.client_sock.recv(1024)
            if printing == True:
                print("Received: " + str(data))
            return data, 0
        #timed out should be handled different to real errors
        except bluetooth.BluetoothError as e:
            if e.args[0] == "timed out":
                return None, 1
            print(e)
            print("Failed. Resetting socket and returning to main frame")
            self.close_sockets()    #cleanup
            return None, -1

    def send(self, data, printing=True):
        """Send message on socket"""
        to_send = bytearray(data, btconfig.ENCODING)
        try:
            self.client_sock.send(to_send)
        #Retry sending once, sync error may occur. Else cleanup and return
        except bluetooth.BluetoothError as e:
            if printing == True:
                print(e)
                print("Retrying to send...")
            try:
                self.client_sock.send(to_send)
            except bluetooth.BluetoothError as e:
                if printing == True:
                    print(e)
                    print("Sending failed. Resetting socket and returning to main frame")
                self.close_sockets()    
                return False
        if printing == True:
            print("Message sent")
        return True

def set_up_bluetooth():
    #Bluetoothctl setup, make sure everything is on and primed
    print("Resetting bluetoothctl")
    os.system("sudo systemctl stop bluetooth")
    os.system("sudo systemctl start bluetooth")
    os.system("echo 'power on\nquit' | bluetoothctl")
    time.sleep(0.1)
        
        
        
