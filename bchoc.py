#!/usr/bin/env python3

# bchoc.py
import argparse
import os
import struct
import hashlib
import pickle
import time
import sys
from uuid import UUID
from Block import Block
from Blockchain import Blockchain


# Define the Blockchain class


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
    parser.add_argument('subcommand', nargs='?', choices=['cases', 'items', 'history'])
    parser.add_argument('-c', '--case_id', nargs='?', help="Specifies the case identifier")
    parser.add_argument('-i', '--item_id', nargs='?', action='append', help="Specifies the evidence item's identifier")
    parser.add_argument('-h', '--handler', help="Specifies the handler's name")
    parser.add_argument('-H', '--help', action='help', help='Show this help message and exit')
    parser.add_argument('-o', '--organization', help="Organization name")
    parser.add_argument('-y', '--why', choices=['DISPOSED', 'DESTROYED', 'RELEASED'], help="Reason for removing the evidence item")
    parser.add_argument('-n', '--num_entries', help="Number of entries")
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
        if not args.item_id:
            print("Invalid item ID")
            sys.exit(1)

        # Check if blockchain has been initialized
        if blockchain is None:
            print("Blockchain not initialized. Cannot perform checkout.")
            sys.exit(1)

        item_id = args.item_id[0]  # Assuming only one item is checked out at a time

        # Iterate through the blockchain in reverse to find the last state of the item ID
        last_state = None
        for block in reversed(blockchain.chain):
            if block.item_id == item_id:
                last_state = block.state
                break

        if last_state == 'CHECKEDIN':
            prev_hash = blockchain.chain[-1].hash if blockchain.chain else None

            checkout_block = Block(
                prev_hash=prev_hash,
                timestamp=time.time(),
                case_id=None,  # Since checkout doesn't require case_id
                item_id=item_id,
                state='CHECKEDOUT',
                handler=args.handler,
                organization=args.organization
            )

            if not blockchain.add_block(checkout_block):
                print(f"Item ID {item_id} is already checked out or does not exist in the blockchain")
                sys.exit(1)

            timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(checkout_block.timestamp))
            print(f"Checked out item: {item_id}")
            print(f"Status: CHECKEDOUT")
            print(f"Time of action: {timestamp_iso}")

        elif last_state in ['CHECKEDOUT', 'REMOVED', 'DESTROYED', 'DISPOSED']:
            print(f"Cannot perform action. Item ID {item_id} has been {last_state.lower()}")
            sys.exit(1)

        else:
            print(f"Item ID {item_id} is not checked in or does not exist in the blockchain")
            sys.exit(1)

    elif args.command == 'checkin':
        if not args.case_id or not args.item_id or not validate_uuid(args.case_id):
            print("Invalid case ID or item ID")
            sys.exit(1)

        # Check if blockchain has been initialized
        if blockchain is None:
            print("Blockchain not initialized. Cannot perform checkin.")
            sys.exit(1)

        # Implement checkin logic
        item_id = args.item_id[0]  # Assuming only one item is checked in at a time
        prev_hash = blockchain.chain[-1].hash if blockchain.chain else None

        checkin_block = Block(
            prev_hash=prev_hash,
            timestamp=time.time(),
            case_id=args.case_id,
            item_id=item_id,
            state='CHECKEDIN',
            handler=args.handler,
            organization=args.organization
        )

        if not blockchain.add_block(checkin_block):
            print(f"Item ID {item_id} is not checked out or does not exist in the blockchain")
            sys.exit(1)

        timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(checkin_block.timestamp))
        print(f"Case: {args.case_id}")
        print(f"Checked in item: {item_id}")
        print(f"Status: CHECKEDIN")
        print(f"Time of action: {timestamp_iso}")

    elif args.command == 'show' and args.subcommand == 'cases':
        cases = blockchain.show_cases()
        for case in cases:
            print(case)

    elif args.command == 'show' and args.subcommand == 'items':
        if not args.case_id or not validate_uuid(args.case_id):
            print("Invalid case ID")
            sys.exit(1)

        items = blockchain.show_items_for_case(args.case_id)
        for item in items:
            print(item)

    elif args.command == 'show' and args.subcommand == 'history':
        # if not args.case_id and not args.item_id:
        #     print("At least one of -c or -i is required for the show history command.")
        #     sys.exit(1)

        history_entries = blockchain.show_history(case_id=args.case_id, item_id=args.item_id, num_entries=args.num_entries)
        for entry in history_entries:
            print(f"Case: {entry['Case']}")
            print(f"Item: {entry['Item']}")
            print(f"Action: {entry['Action']}")
            print(f"Time: {entry['Time']}")
            print()


    elif args.command == 'remove':
        if not args.item_id:
            print("Invalid item ID")
            sys.exit(1)

        # Check if blockchain has been initialized
        if blockchain is None:
            print("Blockchain not initialized. Cannot perform removal.")
            sys.exit(1)

        item_id = args.item_id[0]  # Assuming only one item is removed at a time

        # Check if the item is checked in
        is_checked_in = False
        for block in blockchain.chain[::-1]:
            if block.item_id == item_id and block.state == 'CHECKEDIN':
                is_checked_in = True
                break

        if not is_checked_in:
            print(f"Item ID {item_id} is not checked in or does not exist in the blockchain")
            sys.exit(1)

        prev_hash = blockchain.chain[-1].hash if blockchain.chain else None

        # Ensure 'why' is provided as it is not optional
        if not args.why:
            print("Removal reason is required. Please provide the '-y' or '--why' argument.")
            sys.exit(1)

        removal_reason = args.why.encode('utf-8')

        remove_block = Block(
            prev_hash=prev_hash,
            timestamp=time.time(),
            case_id=args.case_id,
            item_id=item_id,
            state='REMOVED',
            handler=args.handler,
            organization=args.organization,
            data=removal_reason
        )

        if not blockchain.add_block(remove_block):
            print(f"Not able to remove Item ID {item_id}")
            sys.exit(1)

        timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(remove_block.timestamp))
        print(f"Case: {args.case_id}")
        print(f"Removed item: {item_id}")
        print(f"Status: REMOVED")
        print(f"Removal Reason: {args.why}")
        print(f"Time of action: {timestamp_iso}")

        # Exit with code 0 after successful removal
        sys.exit(0)

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