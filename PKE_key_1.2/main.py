import bluetooth
import time

import btconfig
import bt
import bt_rssi
import acc

def main():
    bt.set_up_bluetooth()                                   #Make sure that bluetoothctl service is running and power is on
    idle = False
    print("Socket setup complete")
    sleep_mod = acc.sleep_mode_control_module()
    sleep_mod.start_acc_monitor()
    while True:
        attack_warning = False
        bt_module = bt.Bt_module_server()                   #Allocate resources and initialize bt module
        if bt_module.connect():
            bt_module.start_rssi_monitor_thread()           #Start rssi monitor
            while True:
                #Do not print log if in idle
                if idle == True:
                    received, error = bt_module.listen(timeout=1, printing=False)
                else:
                    received, error = bt_module.listen()
                #Legacy?
                if received == None:
                    idle = False
                    if error <= 0:
                        break
                    else:
                        time.sleep(0.1)

                elif received == bytearray("keep_alive", btconfig.ENCODING):
                    lifesign = "alive"
                    #Only respond to keep-alive if in rssi range
                    if bt_module.in_range:
                        if bt_module.send(lifesign, False):
                            if idle == False:
                                idle = True
                                print("Vehicle unlocked. Entering idle. Responding to keep-alive periodically")
                            continue
                        else:
                            idle = False
                            break
                elif received == bytearray("Wake up!", btconfig.ENCODING):
                    #Only reply to wake-up if in rssi range
                    if bt_module.in_range:
                        print("Key in range")
                        if sleep_mod.sleep:
                            if attack_warning == False:
                                attack_warning == True
                                print("WARNING! ACCESS REQUESTED WHILE SLEEPING")
                        else:
                            attack_warning = False
                            print("Sending wake-up confirmation...")
                            wakeup_confirm = "confirm_wakeup"
                            idle = False
                            if bt_module.send(wakeup_confirm):
                                continue
                            else:
                                break
                elif received[0:9] == bytearray("challenge", btconfig.ENCODING):
                    print("Calculating challenge response")
                    response = "response"
                    print("Sending challenge response")
                    idle = False
                    if bt_module.send(response):
                        continue
                    else:
                        break
                else:
                    idle = False
                    print("Invalid message received. Ignoring and proceeding")

if __name__ == "__main__":
    main()
