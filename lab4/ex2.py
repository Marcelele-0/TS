#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
import sys
from typing import List, Dict, Optional, Tuple
from enum import Enum
import threading

class SignalType(Enum):
    IDLE = 0
    DATA = 1
    COLLISION = 2
    JAM = 3

class NodeState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSMITTING = "TRANSMITTING"
    COLLISION_DETECTED = "COLLISION"
    BACKOFF = "BACKOFF"
    JAMMING = "JAMMING"

class EthernetNode:
    def __init__(self, node_id: int, position: int):
        self.node_id = node_id
        self.position = position
        self.state = NodeState.IDLE
        self.data_to_send = []
        self.current_frame = None
        self.transmission_time = 0
        self.backoff_time = 0
        self.collision_count = 0
        self.successful_transmissions = 0
        self.total_attempts = 0
        self.jam_duration = 0
        
    def has_data_to_send(self) -> bool:
        return len(self.data_to_send) > 0
    
    def add_data(self, frame_data: str):
        self.data_to_send.append(frame_data)
    
    def calculate_backoff(self) -> int:
        """Oblicza czas backoff używając Binary Exponential Backoff"""
        if self.collision_count > 10:
            self.collision_count = 10  # Maksymalnie 2^10 slotów
        
        max_slots = 2 ** self.collision_count
        return random.randint(0, max_slots - 1)

class EthernetSimulator:
    def __init__(self, cable_length: int = 100, num_nodes: int = 4, 
                 propagation_delay: int = 1, slot_time: int = 10):
        self.cable = [SignalType.IDLE] * cable_length
        self.cable_length = cable_length
        self.propagation_delay = propagation_delay
        self.slot_time = slot_time
        self.time_step = 0
        self.nodes = []
        self.statistics = {
            'total_transmissions': 0,
            'successful_transmissions': 0,
            'collisions': 0,
            'channel_utilization': 0
        }
        
        # Rozmieść węzły równomiernie
        positions = [i * (cable_length // (num_nodes + 1)) for i in range(1, num_nodes + 1)]
        for i in range(num_nodes):
            node = EthernetNode(i, positions[i])
            self.nodes.append(node)
    
    def sense_carrier(self, node: EthernetNode) -> bool:
        """Sprawdza czy medium jest wolne (Carrier Sense)"""
        return self.cable[node.position] == SignalType.IDLE
    
    def detect_collision(self, node: EthernetNode) -> bool:
        """Wykrywa kolizję na pozycji węzła (Collision Detection)"""
        return self.cable[node.position] == SignalType.COLLISION
    
    def propagate_signal(self):
        """Symuluje propagację sygnału w medium"""
        new_cable = [SignalType.IDLE] * self.cable_length
        
        for i in range(self.cable_length):
            signals = []
            
            # Sprawdź sygnały z sąsiednich pozycji (propagacja)
            for offset in [-self.propagation_delay, 0, self.propagation_delay]:
                pos = i + offset
                if 0 <= pos < self.cable_length:
                    if self.cable[pos] != SignalType.IDLE:
                        signals.append(self.cable[pos])
            
            # Sprawdź czy jakiś węzeł nadaje na tej pozycji
            for node in self.nodes:
                if node.position == i and node.state == NodeState.TRANSMITTING:
                    signals.append(SignalType.DATA)
                elif node.position == i and node.state == NodeState.JAMMING:
                    signals.append(SignalType.JAM)
            
            # Ustal stan medium
            if len(signals) == 0:
                new_cable[i] = SignalType.IDLE
            elif len(signals) == 1:
                new_cable[i] = signals[0]
            else:
                # Kolizja - więcej niż jeden sygnał
                new_cable[i] = SignalType.COLLISION
        
        self.cable = new_cable
    
    def update_node_states(self):
        """Aktualizuje stany wszystkich węzłów"""
        for node in self.nodes:
            if node.state == NodeState.IDLE:
                if node.has_data_to_send():
                    if self.sense_carrier(node):
                        # Medium wolne - rozpocznij transmisję
                        node.state = NodeState.TRANSMITTING
                        node.current_frame = node.data_to_send.pop(0)
                        node.transmission_time = len(node.current_frame)
                        node.total_attempts += 1
                        self.statistics['total_transmissions'] += 1
                    else:
                        # Medium zajęte - czekaj
                        node.state = NodeState.LISTENING
            
            elif node.state == NodeState.LISTENING:
                if self.sense_carrier(node):
                    # Medium się zwolniło - spróbuj nadawać
                    node.state = NodeState.TRANSMITTING
                    node.current_frame = node.data_to_send.pop(0)
                    node.transmission_time = len(node.current_frame)
                    node.total_attempts += 1
                    self.statistics['total_transmissions'] += 1
            
            elif node.state == NodeState.TRANSMITTING:
                if self.detect_collision(node):
                    # Wykryto kolizję - wyślij sygnał JAM
                    node.state = NodeState.JAMMING
                    node.jam_duration = 5  # Czas trwania sygnału JAM
                    node.collision_count += 1
                    node.data_to_send.insert(0, node.current_frame)  # Zwróć ramkę do kolejki
                    self.statistics['collisions'] += 1
                else:
                    node.transmission_time -= 1
                    if node.transmission_time <= 0:
                        # Transmisja zakończona pomyślnie
                        node.state = NodeState.IDLE
                        node.collision_count = 0
                        node.successful_transmissions += 1
                        self.statistics['successful_transmissions'] += 1
            
            elif node.state == NodeState.JAMMING:
                node.jam_duration -= 1
                if node.jam_duration <= 0:
                    # Zakończ sygnał JAM i przejdź do backoff
                    node.state = NodeState.BACKOFF
                    node.backoff_time = self.calculate_backoff_time(node)
            
            elif node.state == NodeState.BACKOFF:
                node.backoff_time -= 1
                if node.backoff_time <= 0:
                    node.state = NodeState.IDLE
    
    def calculate_backoff_time(self, node: EthernetNode) -> int:
        """Oblicza czas backoff"""
        return node.calculate_backoff() * self.slot_time
    
    def print_network_state(self):
        """Wyświetla aktualny stan sieci"""
        print(f"\n=== Krok czasowy: {self.time_step} ===")
        
        # Stan medium
        cable_display = []
        for i, signal in enumerate(self.cable):
            if signal == SignalType.IDLE:
                cable_display.append('-')
            elif signal == SignalType.DATA:
                cable_display.append('D')
            elif signal == SignalType.COLLISION:
                cable_display.append('X')
            elif signal == SignalType.JAM:
                cable_display.append('J')
        
        print("Medium: ", ''.join(cable_display))
        
        # Pozycje węzłów
        node_display = [' '] * self.cable_length
        for node in self.nodes:
            node_display[node.position] = str(node.node_id)
        print("Węzły:  ", ''.join(node_display))
        
        # Stany węzłów
        print("\nStany węzłów:")
        for node in self.nodes:
            queue_size = len(node.data_to_send)
            print(f"  Węzeł {node.node_id}: {node.state.value:12} | "
                  f"Kolejka: {queue_size} | Kolizje: {node.collision_count} | "
                  f"Udane: {node.successful_transmissions}")
    
    def print_statistics(self):
        """Wyświetla statystyki symulacji"""
        print(f"\n{'='*50}")
        print("STATYSTYKI SYMULACJI")
        print(f"{'='*50}")
        print(f"Całkowite próby transmisji: {self.statistics['total_transmissions']}")
        print(f"Udane transmisje:          {self.statistics['successful_transmissions']}")
        print(f"Kolizje:                   {self.statistics['collisions']}")
        
        if self.statistics['total_transmissions'] > 0:
            success_rate = (self.statistics['successful_transmissions'] / 
                          self.statistics['total_transmissions']) * 100
            collision_rate = (self.statistics['collisions'] / 
                            self.statistics['total_transmissions']) * 100
            print(f"Wskaźnik sukcesu:          {success_rate:.1f}%")
            print(f"Wskaźnik kolizji:          {collision_rate:.1f}%")
        
        print(f"\nStatystyki poszczególnych węzłów:")
        for node in self.nodes:
            print(f"  Węzeł {node.node_id}: {node.successful_transmissions} udanych, "
                  f"{node.total_attempts} prób")
    
    def add_random_traffic(self, probability: float = 0.1):
        """Dodaje losowy ruch do węzłów"""
        for node in self.nodes:
            if random.random() < probability and len(node.data_to_send) < 5:
                frame_size = random.randint(10, 50)  # Losowy rozmiar ramki
                frame_data = f"Frame_{self.time_step}_{node.node_id}"
                node.add_data(frame_data)
    
    def simulate_step(self):
        """Wykonuje jeden krok symulacji"""
        self.propagate_signal()
        self.update_node_states()
        self.time_step += 1
    
    def run_simulation(self, steps: int = 100, traffic_probability: float = 0.1, 
                      verbose: bool = True, print_interval: int = 10):
        """Uruchamia symulację"""
        print(f"Rozpoczynam symulację CSMA/CD")
        print(f"Długość kabla: {self.cable_length}, Węzły: {len(self.nodes)}")
        print(f"Pozycje węzłów: {[node.position for node in self.nodes]}")
        
        for step in range(steps):
            # Dodaj losowy ruch
            self.add_random_traffic(traffic_probability)
            
            # Wykonaj krok symulacji
            self.simulate_step()
            
            # Wyświetl stan co określoną liczbę kroków
            if verbose and (step % print_interval == 0 or step < 20):
                self.print_network_state()
                if step < 20:  # Pauza tylko na początku dla lepszej obserwacji
                    time.sleep(0.5)
        
        # Podsumowanie
        self.print_statistics()

def create_test_scenarios():
    """Tworzy różne scenariusze testowe"""
    print("Dostępne scenariusze testowe:")
    print("1. Podstawowy test (4 węzły, średni ruch)")
    print("2. Test wysokiego ruchu (6 węzłów, duży ruch)")
    print("3. Test niskiego ruchu (3 węzły, mały ruch)")
    print("4. Test długiego kabla (4 węzły, długi kabel)")
    
    choice = input("Wybierz scenariusz (1-4): ")
    
    if choice == "1":
        sim = EthernetSimulator(cable_length=50, num_nodes=4)
        sim.run_simulation(steps=100, traffic_probability=0.15)
    elif choice == "2":
        sim = EthernetSimulator(cable_length=60, num_nodes=6)
        sim.run_simulation(steps=150, traffic_probability=0.25)
    elif choice == "3":
        sim = EthernetSimulator(cable_length=40, num_nodes=3)
        sim.run_simulation(steps=80, traffic_probability=0.08)
    elif choice == "4":
        sim = EthernetSimulator(cable_length=100, num_nodes=4)
        sim.run_simulation(steps=120, traffic_probability=0.12)
    else:
        print("Nieprawidłowy wybór, uruchamiam scenariusz podstawowy...")
        sim = EthernetSimulator()
        sim.run_simulation()

def manual_test():
    """Pozwala na ręczne dodawanie ramek do transmisji"""
    sim = EthernetSimulator(cable_length=30, num_nodes=3)
    
    print("Test ręczny - dodaj ramki do transmisji")
    print("Węzły znajdują się na pozycjach:", [node.position for node in sim.nodes])
    
    # Dodaj ramki ręcznie
    sim.nodes[0].add_data("Frame_A")
    sim.nodes[1].add_data("Frame_B")
    sim.nodes[2].add_data("Frame_C")
    
    print("Dodano ramki: A do węzła 0, B do węzła 1, C do węzła 2")
    print("Uruchamiam symulację...")
    
    sim.run_simulation(steps=50, traffic_probability=0.0, print_interval=1)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        create_test_scenarios()
    elif len(sys.argv) > 1 and sys.argv[1] == "manual":
        manual_test()
    else:
        print("Symulator Ethernet CSMA/CD")
        print("Użycie:")
        print("  python program.py          - symulacja domyślna")
        print("  python program.py test     - scenariusze testowe")
        print("  python program.py manual   - test ręczny")
        print()
        
        # Symulacja domyślna
        sim = EthernetSimulator()
        sim.run_simulation()

if __name__ == "__main__":
    main()