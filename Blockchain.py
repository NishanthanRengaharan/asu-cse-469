# Blockchain.py

import pickle
import os
import time
import sys
from uuid import UUID

class Blockchain:
    def __init__(self):
        self.chain = []
        self.item_ids = set()

    def add_block(self, block):
        if block.item_id not in self.item_ids or block.state == b'INITIAL':
            self.chain.append(block)
            self.item_ids.add(block.item_id)
            return True
        return False

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.prev_hash != bytes.fromhex(previous_block.hash):
                return False
            if current_block.hash != current_block.calculate_hash():
                return False
        return True

    def save_to_file(self, filename):
        temp_filename = filename + '.temp'
        with open(temp_filename, 'wb') as file:
            pickle.dump(self, file, protocol=pickle.HIGHEST_PROTOCOL)
        os.rename(temp_filename, filename)

    @staticmethod
    def load_from_file(filename):
        try:
            with open(filename, 'rb') as file:
                return pickle.load(file)
        except FileNotFoundError:
            return None
        except pickle.UnpicklingError as e:
            print(f"Error loading blockchain from file: {e}")
            sys.exit(1)
    
    def show_cases(self):
        cases = set()
        for block in self.chain:
            if block.case_id:
                cases.add(UUID(bytes=block.case_id).hex)
        return cases

    def show_items_for_case(self, case_id):
        items = set()
        for block in self.chain:
            if UUID(bytes=block.case_id).hex == case_id and block.item_id:
                items.add(block.item_id.decode('utf-8'))
        return items

    def show_history(self, case_id=None, item_id=None, num_entries=None):
        entries = []
        count = 0
        for block in reversed(self.chain):
            if case_id and UUID(bytes=block.case_id).hex != case_id:
                continue
            if item_id and block.item_id.decode('utf-8') != item_id:
                continue
            entry = {
                'Case': UUID(bytes=block.case_id).hex,
                'Item': block.item_id.decode('utf-8'),
                'Action': block.state.decode('utf-8'),
                'Time': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(block.timestamp))
            }
            entries.append(entry)
            count += 1
            if num_entries and count >= num_entries:
                break
        return entries
