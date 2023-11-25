#!/usr/bin/env python3

import argparse
import os
import struct
import hashlib
import pickle
import time
import sys
from uuid import UUID

class Block:
    def __init__(self, prev_hash, timestamp, case_id, item_id, state, handler, organization, data=''):
        self.prev_hash = prev_hash if prev_hash is not None else b'\x00' * 32
        self.timestamp = timestamp
        self.case_id = UUID(case_id).bytes if case_id is not None else b'\x00' * 16
        self.item_id = item_id.encode('utf-8') if item_id is not None and not isinstance(item_id, bytes) else item_id
        self.state = state.encode('utf-8') if state is not None and not isinstance(state, bytes) else state
        self.handler = handler.encode('utf-8') if handler is not None and not isinstance(handler, bytes) else handler
        self.organization = organization.encode('utf-8') if organization is not None and not isinstance(organization, bytes) else organization
        self.data = data.encode('utf-8') if data is not None and not isinstance(data, bytes) else data

        self.hash = self.calculate_hash()

    def calculate_hash(self):
        # Make sure all string arguments are converted to bytes
        prev_hash_bytes = self.prev_hash if isinstance(self.prev_hash, bytes) else str(self.prev_hash).encode()
        case_id_bytes = self.case_id if isinstance(self.case_id, bytes) else str(self.case_id).encode()
        state_bytes = self.state if isinstance(self.state, bytes) else str(self.state).encode()
        handler_bytes = self.handler if isinstance(self.handler, bytes) else str(self.handler).encode()
        organization_bytes = self.organization if isinstance(self.organization, bytes) else str(self.organization).encode()

        header = struct.pack(
            "32s d 16s I 12s 20s 20s I",
            prev_hash_bytes,
            self.timestamp,
            case_id_bytes,
            len(self.item_id),
            state_bytes,
            handler_bytes,
            organization_bytes,
            len(self.data)
        )
        return hashlib.sha256(header + self.data).hexdigest()

# Define the Blockchain class
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

# Helper functions
def validate_uuid(uuid_string):
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False

def main():
    parser = argparse.ArgumentParser(description="Blockchain-based Chain of Custody", add_help=False)
    parser.add_argument('command', choices=['add', 'checkout', 'checkin', 'show', 'remove', 'init', 'verify'])
    parser.add_argument('-c', '--case_id', help="Specifies the case identifier")
    parser.add_argument('-i', '--item_id', action='append', help="Specifies the evidence item's identifier")
    parser.add_argument('-h', '--handler', help="Specifies the handler's name")
    parser.add_argument('-H', '--help', action='help', help='Show this help message and exit')
    parser.add_argument('-o', '--organization', help="Organization name")
    parser.add_argument('-y', '--why', choices=['DISPOSED', 'DESTROYED', 'RELEASED'], help="Reason for removing the evidence item")
    args = parser.parse_args()

    # Check for BCHOC_FILE_PATH environment variable
    blockchain_file_path = os.environ.get('BCHOC_FILE_PATH', 'blockchain.bchoc')

    blockchain = Blockchain.load_from_file(blockchain_file_path)

    if args.command == 'add':
        if not args.case_id or not args.item_id or not validate_uuid(args.case_id):
            print("Invalid case ID or item ID")
            sys.exit(1)

        # Check if blockchain has been initialized, if not, initialize it
        if blockchain is None:
            print("Blockchain not initialized. Creating INITIAL block.")
            blockchain = Blockchain()
            initial_block = Block(
                prev_hash=None,
                timestamp=0,
                case_id=UUID('00000000-0000-0000-0000-000000000000').hex,
                item_id='',
                state=b'INITIAL\x00\x00\x00\x00',
                handler=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                organization=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                data=b'Initial block\x00'
            )
            blockchain.add_block(initial_block)

        for item_id in args.item_id:
            prev_hash = blockchain.chain[-1].hash if blockchain.chain else None

            block = Block(
                prev_hash=prev_hash,
                timestamp=time.time(),
                case_id=args.case_id,
                item_id=item_id,
                state='CHECKEDIN',
                handler=args.handler,
                organization=args.organization
            )

            if not blockchain.add_block(block):
                print(f"Item ID {item_id} already exists in the blockchain")
                sys.exit(1)

            timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(block.timestamp))
            print(f"Case: {args.case_id}")
            print(f"Added item: {item_id}")
            print(f"Status: CHECKEDIN")
            print(f"Time of action: {timestamp_iso}")

    elif args.command == 'checkout':
        # Implement checkout logic
        pass

    elif args.command == 'checkin':
        # Implement checkin logic
        pass

    elif args.command == 'show':
        if args.case_id:
            items = blockchain.show_items_for_case(args.case_id)
            for item in items:
                print(item)
        else:
            cases = blockchain.show_cases()
            for case in cases:
                print(case)

    elif args.command == 'show history':
        if args.case_id or args.item_id or args.num_entries:
            history_entries = blockchain.show_history(args.case_id, args.item_id, args.num_entries)
            for entry in history_entries:
                print(f"Case: {entry['Case']}")
                print(f"Item: {entry['Item']}")
                print(f"Action: {entry['Action']}")
                print(f"Time: {entry['Time']}")
                print()
        else:
            print("Invalid arguments for show history command. Provide at least one of -c, -i, or -n.")
            sys.exit(1)

    elif args.command == 'remove':
        # Implement remove logic
        pass

    elif args.command == 'init':
    # Attempt to load the blockchain from file
        blockchain = Blockchain.load_from_file(blockchain_file_path)
        if blockchain is None:  # blockchain should be None if the file does not exist
            print("Blockchain file not found. Created INITIAL block.")
            blockchain = Blockchain()
            initial_block = Block(
                prev_hash=None,
                timestamp=0,
                case_id=UUID('00000000-0000-0000-0000-000000000000').hex,
                item_id='',
                state=b'INITIAL' + b'\x00' * (12 - len('INITIAL')),  # Ensure the state is 12 bytes.
                handler=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                organization=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                data=b'Initial block\x00'
            )

            blockchain.add_block(initial_block)
            blockchain.save_to_file(blockchain_file_path)
        else:
            print("Blockchain file found with INITIAL block.")

    elif args.command == 'verify':
        if blockchain.verify_chain():
            print("Blockchain verified, no errors found")
        else:
            print("Blockchain verification failed")
            sys.exit(1)

    blockchain.save_to_file(blockchain_file_path)

if __name__ == "__main__":
    main()