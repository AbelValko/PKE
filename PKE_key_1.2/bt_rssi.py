import subprocess
import time

def monitor_rssi(stop, addr, parent, sleep=1, debug=False):
    """Scans for RSSI value of addr
    Assumes already connected device, presumably hci0. Rfcomm. BT 4.0. hictool.
    Parent must contain rssi_callback method
    """
    hcitool_cmd = ['sudo', 'hcitool', 'rssi', str(addr)]    #hcitool command to check rssi of device addr
    rssi_int = 0
    #Monitor runs until stop called from main thread
    while True :
        if stop():  #Called from main frame if connection abruptly ended
            break
        try:
            rssi = subprocess.check_output(hcitool_cmd) #Send command and get response
            rssi = rssi.decode('utf-8')
            rssi_int = None
            #Parse for numerical value of rssi
            for s in rssi.split():
                try:
                    rssi_int = int(s)
                except ValueError:
                    pass
            parent.rssi_callback(rssi_int)  #Callback to parent for rssi update
            if debug == True:
                print("RSSI: " + str(rssi_int))
            if rssi_int == None:
                if debug == True:
                    print("RSSI_DEBUG1: rssi none")
                break
        #Errors handled gracefully
        except subprocess.CalledProcessError as e:
            rssi_int = None
            parent.rssi_callback(rssi_int)
            if debug == True:
                print("RSSI_DEBUG2: rssi error")
            break
        time.sleep(sleep)