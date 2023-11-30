import os
import struct
import sys
from Block import Block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.ids = set()

    def add_block(self, block):
        self.chain.append(block)
        self.ids.add(block.item_id)

    def save_to_file(self, filename):
        with open(filename, 'wb') as file:
            for block in self.chain:
                file.write(block.pack_into_binary())

    @staticmethod
    def load_from_file(filename):
        blockchain = Blockchain()
        try:
            with open(filename, 'rb') as file:
                while True:
                    # Adjust the size according to your structure (116 bytes for the header)
                    header_data = file.read(116)
                    if not header_data:
                        break  # End of file
                    
                    # Debug printing
                    # print(f"Read Header Data: {header_data.hex()}")
                    
                    data_len = struct.unpack('I', header_data[-4:])[0]
                    data = file.read(data_len)
                    
                    # Debug printing
                    # print(f"Read Data: {data.hex()}")
                    
                    block = Block.unpack_from_binary(header_data + data)
                    blockchain.add_block(block)

            return blockchain
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading blockchain from file: {e}")
            sys.exit(1)