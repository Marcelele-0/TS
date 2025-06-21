#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from typing import List, Tuple

class FrameProcessor:
    def __init__(self):
        # Flaga ramki - sekwencja 01111110
        self.FLAG = "01111110"
        # Wielomian CRC-8: x^8 + x^2 + x^1 + 1 = 100000111
        self.CRC_POLY = "100000111"
        
    def crc_calculate(self, data: str) -> str:
        """Oblicza CRC dla podanych danych"""
        # Dodajemy 8 zer na końcu (długość CRC)
        dividend = data + "0" * 8
        divisor = self.CRC_POLY
        
        # Konwersja na listy dla łatwiejszej manipulacji
        dividend_bits = list(dividend)
        divisor_bits = list(divisor)
        
        for i in range(len(data)):
            if dividend_bits[i] == '1':
                # XOR operation
                for j in range(len(divisor_bits)):
                    if i + j < len(dividend_bits):
                        dividend_bits[i + j] = str(int(dividend_bits[i + j]) ^ int(divisor_bits[j]))
        
        # Zwracamy ostatnie 8 bitów jako CRC
        return ''.join(dividend_bits[-8:])
    
    def bit_stuffing(self, data: str) -> str:
        """Implementuje zasadę rozpychania bitów - wstawia 0 po pięciu kolejnych 1"""
        result = ""
        count_ones = 0
        
        for bit in data:
            result += bit
            if bit == '1':
                count_ones += 1
                if count_ones == 5:
                    result += '0'  # Wstawiamy 0 po pięciu 1
                    count_ones = 0
            else:
                count_ones = 0
                
        return result
    
    def bit_destuffing(self, data: str) -> str:
        """Usuwa bity wstawione podczas bit stuffing"""
        result = ""
        count_ones = 0
        i = 0
        
        while i < len(data):
            bit = data[i]
            result += bit
            
            if bit == '1':
                count_ones += 1
                if count_ones == 5:
                    # Sprawdzamy czy następny bit to 0 (bit stuffing)
                    if i + 1 < len(data) and data[i + 1] == '0':
                        i += 1  # Pomijamy wstawiony 0
                    count_ones = 0
            else:
                count_ones = 0
            
            i += 1
                
        return result
    
    def create_frame(self, data: str) -> str:
        """Tworzy ramkę z danymi"""
        # 1. Oblicz CRC
        crc = self.crc_calculate(data)
        
        # 2. Połącz dane z CRC
        data_with_crc = data + crc
        
        # 3. Zastosuj bit stuffing
        stuffed_data = self.bit_stuffing(data_with_crc)
        
        # 4. Dodaj flagi na początku i końcu
        frame = self.FLAG + stuffed_data + self.FLAG
        
        return frame
    
    def parse_frame(self, frame: str) -> Tuple[bool, str]:
        """Parsuje ramkę i zwraca (czy_poprawna, dane)"""
        # 1. Sprawdź czy ramka zaczyna i kończy się flagą
        if not (frame.startswith(self.FLAG) and frame.endswith(self.FLAG)):
            return False, ""
        
        # 2. Usuń flagi
        data_stuffed = frame[len(self.FLAG):-len(self.FLAG)]
        
        # 3. Usuń bit stuffing
        data_with_crc = self.bit_destuffing(data_stuffed)
        
        # 4. Sprawdź długość (musi być co najmniej 8 bitów dla CRC)
        if len(data_with_crc) < 8:
            return False, ""
        
        # 5. Podziel na dane i CRC
        data = data_with_crc[:-8]
        received_crc = data_with_crc[-8:]
        
        # 6. Oblicz CRC dla otrzymanych danych
        calculated_crc = self.crc_calculate(data)
        
        # 7. Sprawdź poprawność CRC
        if received_crc == calculated_crc:
            return True, data
        else:
            return False, ""
    
    def encode_file(self, input_filename: str, output_filename: str):
        """Koduje plik wejściowy do ramek"""
        try:
            with open(input_filename, 'r') as f:
                data = f.read().strip()
            
            # Sprawdź czy dane zawierają tylko 0 i 1
            if not all(c in '01' for c in data):
                print(f"Błąd: Plik {input_filename} zawiera nieprawidłowe znaki. Dozwolone tylko '0' i '1'.")
                return False
            
            # Podziel dane na bloki (np. 64 bity na ramkę)
            block_size = 64
            frames = []
            
            for i in range(0, len(data), block_size):
                block = data[i:i + block_size]
                frame = self.create_frame(block)
                frames.append(frame)
            
            # Zapisz ramki do pliku
            with open(output_filename, 'w') as f:
                for frame in frames:
                    f.write(frame + '\n')
            
            print(f"Zakodowano {len(frames)} ramek z pliku {input_filename} do {output_filename}")
            return True
            
        except FileNotFoundError:
            print(f"Błąd: Nie można odnaleźć pliku {input_filename}")
            return False
        except Exception as e:
            print(f"Błąd podczas kodowania: {e}")
            return False
    
    def decode_file(self, input_filename: str, output_filename: str):
        """Dekoduje ramki z pliku"""
        try:
            with open(input_filename, 'r') as f:
                lines = f.readlines()
            
            decoded_data = []
            valid_frames = 0
            invalid_frames = 0
            
            for i, line in enumerate(lines):
                frame = line.strip()
                if not frame:
                    continue
                    
                is_valid, data = self.parse_frame(frame)
                
                if is_valid:
                    decoded_data.append(data)
                    valid_frames += 1
                    print(f"Ramka {i+1}: POPRAWNA")
                else:
                    invalid_frames += 1
                    print(f"Ramka {i+1}: BŁĘDNA - pomijam")
            
            # Zapisz zdekodowane dane
            if decoded_data:
                with open(output_filename, 'w') as f:
                    f.write(''.join(decoded_data))
                
                print(f"\nZdekodowano {valid_frames} poprawnych ramek")
                print(f"Pominięto {invalid_frames} błędnych ramek")
                print(f"Wynik zapisano do {output_filename}")
                return True
            else:
                print("Błąd: Brak poprawnych ramek do zdekodowania")
                return False
                
        except FileNotFoundError:
            print(f"Błąd: Nie można odnaleźć pliku {input_filename}")
            return False
        except Exception as e:
            print(f"Błąd podczas dekodowania: {e}")
            return False

def main():
    processor = FrameProcessor()
    
    if len(sys.argv) < 4:
        print("Użycie:")
        print("  Kodowanie: python program.py encode plik_źródłowy.txt plik_wyjściowy.txt")
        print("  Dekodowanie: python program.py decode plik_wejściowy.txt plik_wynikowy.txt")
        print()
        print("Przykład:")
        print("  python program.py encode Z.txt W.txt")
        print("  python program.py decode W.txt Z_decoded.txt")
        return
    
    mode = sys.argv[1].lower()
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    
    if mode == "encode":
        print("=== KODOWANIE RAMEK ===")
        processor.encode_file(input_file, output_file)
        
    elif mode == "decode":
        print("=== DEKODOWANIE RAMEK ===")
        processor.decode_file(input_file, output_file)
        
    else:
        print("Błąd: Nieprawidłowy tryb. Użyj 'encode' lub 'decode'")

# Funkcja testowa
def create_test_file():
    """Tworzy przykładowy plik testowy"""
    test_data = "1101001010110110101110111011110111110111100101101001010110"
    with open("Z.txt", "w") as f:
        f.write(test_data)
    print(f"Utworzono plik testowy Z.txt z danymi: {test_data}")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        create_test_file()
    else:
        main()