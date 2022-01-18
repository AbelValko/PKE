import bt
import lock

#is this the best structure? Should there be an active method?
#abstract class for vehicle states
class vehicle:
    def __init__(self):
        unlocked = None
    #method for moving to next state, blocks until reqs for next state fulfilled 
    def transition(self, bt_module):
        pass
    #method for entering state, basic setup
    def enter(self):
        pass
    
#add button press and then out of range locking
class vehicle_unlocked(vehicle):
    def enter(self):
        self.unlocked = True
        lock.unlock()
        print("Vehicle unlocked")
    def transition(self, bt_module):
        print("Waiting for locking procedure. Verifying key in range periodically.")
        bt.wait_for_locking_procedure(bt_module)
        print("Locking procedure complete")
        next_state = vehicle_locked()
        return next_state, None
    
class vehicle_locked(vehicle):
    def enter(self):
        self.unlocked = False
        lock.lock()
        print("Vehicle locked")
    def transition(self, bt_module=None):
        print("Waiting for unlock authentication...")
        #unlock_authentication blocks until authentication complete and then returns bt_module with current socket fo com
        bt_module = bt.unlock_authentication()
        print("Authenticaton complete")
        next_state = vehicle_unlocked()
        return next_state, bt_module
        
def vehicle_setup():
    state = vehicle_locked()
    return state

#finite state machine for vehicle
class vehicle_fsm:
    def __init__(self):
        self.state = vehicle_setup()
        self.bt_module = bt.bt_socket()
        
    def run(self):
        while True:
            #cleanup for bt on exit?
            next_state, self.bt_module = self.state.transition(self.bt_module)
            self.state = next_state
            self.state.enter()
    