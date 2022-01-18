import bluetooth
import btconfig
import time
import os

class bt_socket:
    def __init__(self):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.setblocking(True)
    def close_socket(self):
        try:
            self.sock.close()
        except bluetooth.BluetoothError as e:
            print("Error while closing socket:")
            print(e)
            
def wait_for_locking_procedure(bt_module):
    #legacy method
    verify_key_in_range(bt_module)    

def verify_key_in_range(bt_module):
    to_send = "keep_alive"
    expected_response = bytearray("alive", btconfig.ENCODING)
    bt_module.sock.settimeout(0.2)
    strikes = 0
    while True:
        if strikes >= btconfig.KEEP_ALIVE_STRIKES:
            bt_module.close_socket()
            print("Keep-alive false")
            return
        try:
            bt_module.sock.send(to_send)
        except bluetooth.BluetoothError as e:
            try:
                time.sleep(0.1)
                bt_module.sock.send(to_send)
            except bluetooth.BluetoothError as e:
                print(e) #not needed
                print("Keep-alive false")
                bt_module.close_socket()
                return
        try:
            response = bt_module.sock.recv(1024)
        except bluetooth.BluetoothError as e:
            if e == "timed out":
                strikes += 1
                continue
            else:
                print(e)
                print("Keep-alive false")
                bt_module.close_socket()
                return
        if response == expected_response:
            pass
        else:
            strikes += 1
            continue
        time.sleep(0.2)

def unlock_authentication():
    print("Waiting for connection...")
    while True:
        bt_module = establish_connection()
        if get_wakeup(bt_module) == True:
            if authenticate_key(bt_module) == True:
                return bt_module

def authenticate_key(bt_module):
    #real challenge + ID
    challenge = "challenge"
    #error handling
    try:
        bt_module.sock.send(challenge)
    except bluetooth.BluetoothError as e:
        print(e)
        print("Retrying with new challenge")
        challenge = "challenge2" #not really implemented since no encryption is used
        try:
            bt_module.sock.send(challenge)
        except bluetooth.BluetoothError as e:
            print(e)
            print("Sending of challenge failed. Resetting socket and authentication")
            bt_module.close_socket()
            return False
    print("Challenge sent")
    #real response
    print("Calculating expected response")
    expected_response = bytearray("response", btconfig.ENCODING)
    bt_module.sock.settimeout(0.1)
    try:
        print("Awaiting response")
        response = bt_module.sock.recv(1024)
    except bluetooth.BluetoothError as e:
        print(e)
        print("Authentication failed. Resetting socket and authentication")
        bt_module.close_socket()
        return False
    #error etc handling
    #timeout if wrong reply
    if response == expected_response:
        print("Challenge response confirmed")
        return True
    else:
        print("Challenge failed. Resetting socket and authentication")
        bt_module.close_socket()
        #proper handling of failed response, this is bad parenting
        print("Key placed on timeout to think about what it has done..")
        time.sleep(10)
        return False

#implement actual protocol
def get_wakeup(bt_module):
    to_send = "Wake up!"
    expected_response = bytearray("confirm_wakeup", btconfig.ENCODING)
    bt_module.sock.settimeout(0.1)
    #error handling, close socket if needed
    while True:
        try:
            bt_module.sock.send(to_send)
            # print("Wake-up sent")
        except bluetooth.BluetoothError as e:
            print(e)
            print("retrying to send wake-up")
            try:
                bt_module.sock.send(to_send)
                print("Wake-up sent")
            except bluetooth.BluetoothError as e:
                print(e)
                print("Sending of wake-up failed. Resetting socket and authentication")
                bt_module.close_socket()
                return False
        #error handling 
        try:
            response = bt_module.sock.recv(1024)
        except bluetooth.BluetoothError as e:
            if e.args[0] == "timed out":
                continue
            else:
                print(e)
                print("Wake-up not confirmed. Resetting socket and authentication")
                bt_module.close_socket()
                return False
        if response == expected_response:
            print("Wake-up confirmed")
            return True
        else:
            print("Wake-up response incorrect. Expecting " + expected_response + " Received " + response + ". Resetting socket and authentication")
            bt_module.close_socket()
            return False

#timeout causes file descriptor in bad state in connect + doesnt actually work
def establish_connection():
    current_error = None
    print("Trying to connect...")
    while True:
        bt_module = bt_socket()
        try:
            bt_module.sock.connect((btconfig.KEY_ADDR, btconfig.PORT))
            print("Connection with key established")
            return bt_module
        except bluetooth.btcommon.BluetoothError as e:
            errno = e.args[0]
            if errno != current_error:
                if errno == 112:
                    print(str(e) + " - Key is out of range or down")
                elif errno == 111:
                    print(str(e) + " - Key detected but is not ready to receive connection, program may not be started")
                elif errno == 113:
                    print(str(e) + " - Bluetoothctl power may be off")
                    print("Attempting to turn on power")
                    os.system("echo 'power on\nquit' | bluetoothctl")
                elif errno == 77:
                    print(str(e) + " - Unexpected socket failiure, verify settings and socket-protocol sync")
                else:
                    print(e)
                current_error = errno
                print("Trying to connect...")
            pass
        #already connected exeption handling (might not be needed)
def set_up_bluetooth():
    print("Resetting bluetoothctl")
    os.system("sudo systemctl stop bluetooth")
    os.system("sudo systemctl start bluetooth")
    os.system("echo 'power on\nquit' | bluetoothctl")
    time.sleep(0.1)
