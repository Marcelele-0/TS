"""
Ethernet CSMA/CD (Carrier Sense Multiple Access with Collision Detection) Simulation

This module simulates an Ethernet network using the CSMA/CD protocol.
Multiple devices attempt to transmit data over a shared cable medium,
with collision detection and exponential backoff algorithms.

The simulation visualizes:
- Signal propagation along the cable
- Collision detection and handling
- Device transmission scheduling
- Real-time network state visualization
"""

from copy import copy
import random
import time

# Configuration constants
ETHERNET_CABLE_LENGHT = 20  # Length of the Ethernet cable in segments

class CableCell:
    """
    Represents a single segment of the Ethernet cable.
    
    Each cell can carry signals from left and right directions.
    Collisions are detected when signals from both directions meet.
    
    Attributes:
        pos (int): Position of this cell in the cable
        left (str|None): Signal coming from the left direction
        right (str|None): Signal coming from the right direction
    """
    
    def __init__(self, _pos_):
        """
        Initialize a cable cell at the given position.
        
        Args:
            _pos_ (int): Position of this cell in the cable (0-based index)
        """
        self.pos = _pos_
        self.left = None   # Signal from left direction
        self.right = None  # Signal from right direction

    def new_signal(self, signal):
        """
        Inject a new signal into this cable cell.
        
        The signal propagates in both directions. If there's already
        a signal present, a collision ('#') is marked.
        
        Args:
            signal (str): The signal to inject (typically device name like 'A', 'B', 'C')
        """
        self.left = signal if self.left == None else '#'
        self.right = signal if self.right == None else '#'

    def propagate(self, cable, new_cable):
        """
        Propagate signals to neighboring cells in the next time step.
        
        This method implements the core signal propagation logic:
        - Signals move from one cell to adjacent cells
        - Collisions are detected when signals meet
        - Collision markers ('#') are propagated
        
        Args:
            cable (list): Current state of the cable
            new_cable (list): Next state of the cable to be updated
        """
        new_self = new_cable[self.pos]

        # Handle left neighbor propagation
        if self.pos != 0:  # Have left neighbor
            left = cable[self.pos-1]
            new_left = new_cable[self.pos-1]
            if self.left != None and left.right != None:
                # Collision: signals meeting from both directions
                new_left.left = '#'
                new_self.right = '#'
            elif left.right != None:
                # Signal coming from left neighbor
                new_self.right = left.right
            elif self.left != None:
                # Signal going to left neighbor
                new_left.left = self.left
        
        # Handle right neighbor propagation
        if self.pos != ETHERNET_CABLE_LENGHT - 1:  # Have right neighbor
            right = cable[self.pos+1]
            new_right = new_cable[self.pos+1]
            if self.right != None and right.left != None:
                # Collision: signals meeting from both directions
                new_right.right = '#'
                new_self.left = '#'
            elif right.left != None:
                # Signal coming from right neighbor
                new_self.left = right.left
            elif self.right != None:
                # Signal going to right neighbor
                new_right.right = self.right
        
        # Handle collision in current cell
        if new_self.left != None and new_self.right != None:
            new_self.left = '#'
            new_self.right = '#'
    
    def __str__(self):
        """
        Return visual representation of the cable cell state.
        
        Returns:
            str: '_' for empty cell, signal character for active transmission,
                 or the signal from right direction if left is empty
        """
        if self.left == None and self.right == None:
            return '_'  # Empty cell
        return self.right if self.left == None else self.left
    
class Transmission:
    """
    Represents a data transmission from a device.
    
    Implements CSMA/CD behavior including:
    - Carrier sense (checking if medium is free)
    - Collision detection
    - Exponential backoff algorithm
    - Packet transmission tracking
    
    Attributes:
        src (str): Source device identifier (e.g., 'A', 'B', 'C')
        pos (int): Position of the transmitting device on the cable
        len (int): Total length of the packet to transmit
        left (int): Remaining bits to transmit
        wait (int): Time to wait to ensure no collisions occurred
        sleep (int): Backoff time after a collision
    """
    
    def __init__(self, _src_, _pos_, _len_):
        """
        Initialize a new transmission.
        
        Args:
            _src_ (str): Source device identifier
            _pos_ (int): Position on the cable where transmission starts
            _len_ (int): Length of the packet in time units
        """
        self.src = _src_                        # Device identifier (A, B, C)
        self.pos = _pos_                        # Position in the cable
        self.len = _len_                        # Total packet length
        self.left = _len_                       # Remaining bits to transmit
        self.wait = ETHERNET_CABLE_LENGHT       # Wait time to detect collisions
        self.sleep = 0                          # Backoff sleep time

    def transmit(self, cable):
        """
        Attempt to transmit data on the cable using CSMA/CD protocol.
        
        The transmission process follows these steps:
        1. Check if still in backoff period (sleep > 0)
        2. Detect collisions (collision markers '#')
        3. If collision detected, enter exponential backoff
        4. If medium is clear, transmit one bit
        5. Wait for collision detection period after transmission
        
        Args:
            cable (list): Current state of the cable
            
        Returns:
            bool: True if transmission is complete, False otherwise
        """
        # Check if we're done waiting for collision detection
        if self.wait == 0:
            return True
        
        # Handle backoff period after collision
        if self.sleep > 0:
            self.sleep -= 1
            return False

        # Detect collision at our position
        if cable[self.pos].left == '#' or cable[self.pos].right == '#':
            # Collision detected! Implement exponential backoff
            self.sleep = random.choice([1, 2]) * ETHERNET_CABLE_LENGHT
            self.wait = ETHERNET_CABLE_LENGHT
            self.left = self.len  # Restart transmission
            return False

        # Continue transmission or wait for collision detection
        if self.left == 0:
            # Packet sent, now waiting to ensure no collisions
            self.wait -= 1
        elif cable[self.pos].left == None and cable[self.pos].right == None:
            # Medium is clear, transmit one bit
            cable[self.pos].new_signal(self.src)
            self.left -= 1
        
        return False

class Device:
    """
    Represents a network device connected to the Ethernet cable.
    
    Each device has a schedule of transmissions and manages its own
    transmission queue. Devices implement CSMA/CD protocol for
    media access control.
    
    Attributes:
        name (str): Device identifier (e.g., 'A', 'B', 'C')
        pos (int): Physical position on the cable
        round (int): Current simulation round counter
        transmission (Transmission|None): Currently active transmission
        transmissions (list): Queue of scheduled transmissions
    """
    
    def __init__(self, _name_, _pos_, _rounds_):
        """
        Initialize a network device.
        
        Args:
            _name_ (str): Device identifier
            _pos_ (int): Position on the cable (0-based index)
            _rounds_ (list): List of rounds when device should start transmission
        """
        self.name = _name_
        self.pos = _pos_
        self.round = 0
        self.transmission = None
        # Create transmission queue with random packet lengths
        self.transmissions = [
            [r, Transmission(_name_, _pos_, random.randint(5, 10))] 
            for r in _rounds_
        ]
    
    def refresh(self, cable):
        """
        Update device state for the current simulation round.
        
        This method:
        1. Increments the round counter
        2. Continues any active transmission
        3. Starts new transmissions when scheduled
        
        Args:
            cable (list): Current state of the cable
            
        Returns:
            bool: True if device has more activity, False if done
        """
        self.round += 1

        # Handle ongoing transmission
        if self.transmission != None:
            if self.transmission.transmit(cable):
                # Transmission completed
                print(f"    💚 Device {self.name} completed transmission")
                self.transmission = None
            else:
                return True  # Still transmitting
        
        # Check for new scheduled transmissions
        if self.transmissions:
            r, t = self.transmissions[0]
            if self.round >= r:
                # Start new transmission
                print(f"    📡 Device {self.name} starting new transmission (length: {t.len})")
                self.transmission = t
                self.transmissions = self.transmissions[1:]
                self.transmission.transmit(cable)
            return True
        else:
            # No more transmissions scheduled
            return False

    def __str__(self):
        """Return device identifier for display."""
        return self.name

def main():
    """
    Main simulation function.
    
    Sets up the Ethernet network simulation with:
    - A cable of specified length
    - Multiple devices with transmission schedules
    - Real-time visualization of network state
    """
    print("🌐 Starting Ethernet CSMA/CD Simulation")
    print("=" * 50)
    print(f"Cable length: {ETHERNET_CABLE_LENGHT} segments")
    print("Legend: _ = empty, A/B/C = device signal, # = collision")
    print("=" * 50)
    
    # Initialize the cable
    cable = [CableCell(i) for i in range(ETHERNET_CABLE_LENGHT)]

    # Create devices with their transmission schedules
    devices = [
        Device('A', 3, [1, 40, 41]),    # Device A at position 3
        Device('B', 9, [50]),           # Device B at position 9
        Device('C', 15, [55, 60, 80])   # Device C at position 15
    ]
    
    print(f"📱 Devices configured:")
    for dev in devices:
        schedule = [t[0] for t in dev.transmissions]
        print(f"   Device {dev.name} at position {dev.pos}: transmissions at rounds {schedule}")
    print()

    current_round = 0

    while devices:
        current_round += 1

        # Propagate signals through the cable
        new_cable = [CableCell(i) for i in range(ETHERNET_CABLE_LENGHT)]
        for cell in cable:
            cell.propagate(cable, new_cable)
        cable = new_cable
        
        # Update all devices
        print(f"🔄 ROUND {current_round}")
        devices = [d for d in devices if d.refresh(cable)]

        # Visualize current state
        print("   Cable: " + "".join([str(cell) for cell in cable]))

        # Show device positions
        device_line = [' '] * ETHERNET_CABLE_LENGHT
        for dev in devices:
            device_line[dev.pos] = str(dev)
        print("   Devs:  " + "".join(device_line))
        
        # Show active transmissions
        active_transmissions = [d for d in devices if d.transmission is not None]
        if active_transmissions:
            transmission_info = []
            for d in active_transmissions:
                t = d.transmission
                if t.sleep > 0:
                    status = f"backing off ({t.sleep} rounds)"
                elif t.left > 0:
                    status = f"transmitting ({t.left}/{t.len} left)"
                else:
                    status = f"waiting for collision detection ({t.wait} rounds)"
                transmission_info.append(f"{d.name}: {status}")
            print("   Status: " + " | ".join(transmission_info))
        
        print()
        time.sleep(0.1)
    
    print("✅ Simulation completed - all devices finished their transmissions")

if __name__ == '__main__':
    main()