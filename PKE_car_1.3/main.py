import fsm
import bt

def main():
    bt.set_up_bluetooth()
    print("Setting up vehicle")
    vehicle = fsm.vehicle_fsm()
    print("Vehicle setup complete")
    vehicle.run()

if __name__ == "__main__":
    main()
