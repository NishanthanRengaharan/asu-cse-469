#Blockchain.py
import datetime
import os
import struct
import sys
import time
from uuid import UUID
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

    def show_history(self):
        history = []
        for block in self.chain:
            formatted_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(block.timestamp)) + '.' + str(int(block.timestamp * 1000000) % 1000000).zfill(6) + 'Z'
            history_entry = {
                'Case': UUID(bytes=block.case_id).hex,
                'Item': block.item_id,
                'Action': block.state.rstrip(b'\x00').decode('utf-8'),
                'Time': formatted_time
                # , time.gmtime(block.timestamp))
            }
            history.append(history_entry)
    
        return history
    
    def show_cases(self):
        cases = set()
        for block in self.chain:
            if block.case_id != b'\x00' * 16:  # Check if the case_id is not empty
                case_id_str = str(UUID(bytes=block.case_id))
                cases.add(case_id_str)
        return cases
    
    def show_items_for_case(self, case_id):
        items = set()
        for block in self.chain:
            if str(UUID(bytes=block.case_id)) == case_id:
                items.add(block.item_id)
        return items
    
    def get_last_state(self, item_id):
            for block in reversed(self.chain):
                if block.item_id == int(item_id):
                    return block
            return None
    
    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.prev_hash != bytes.fromhex(previous_block.hash):
                return False
            if current_block.hash != current_block.calculate_hash():
                return False
        return True