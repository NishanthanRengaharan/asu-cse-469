#!/usr/bin/env python3

# bchoc.py
import argparse
import os
import struct
import hashlib
import time
import sys
from uuid import UUID
from Block import Block
from Blockchain import Blockchain
from datetime import datetime, timezone


# Helper functions
def validate_uuid(uuid_string):
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False
    
def initialize_blockchain_if_needed(blockchain_file_path):
    blockchain = Blockchain.load_from_file(blockchain_file_path)
    if blockchain is None:
        print("Blockchain file not found. Creating INITIAL block.")
        initial_block = Block(
            prev_hash=b'\x00' * 32,
            timestamp=0,
            case_id=UUID(int=0).bytes,
            item_id=0,
            state='INITIAL',
            handler='',
            organization='',
            data='Initial block\x00'
        )
        blockchain = Blockchain()
        blockchain.add_block(initial_block)
        blockchain.save_to_file(blockchain_file_path)
    return blockchain

def create_initial_block():
    return Block(
        prev_hash=b'\x00' * 32,
        timestamp=time.time(),
        case_id=UUID(int=0).bytes,
        item_id=0,
        state='INITIAL',
        handler='',
        organization='',
        data='Initial block\x00'
    )

def get_last_block_hash(blockchain):
    if blockchain.chain:
        return blockchain.chain[-1].hash
    else:
        # Handle the case where the blockchain is empty
        return None

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
    parser.add_argument('-r', '--reverse',action='store_true', help="Reverses the history list")
    args = parser.parse_args()

    # Check for BCHOC_FILE_PATH environment variable
    blockchain_file_path = os.environ.get('BCHOC_FILE_PATH', 'blockchain.bchoc')
    blockchain = Blockchain.load_from_file(blockchain_file_path)

    

    if args.command == 'init':
        blockchain = initialize_blockchain_if_needed(blockchain_file_path)
        if blockchain:
            print("Blockchain file found with INITIAL block.")

    elif args.command == 'add':
        blockchain = initialize_blockchain_if_needed(blockchain_file_path)
        
        # Validate case_id and item_id
        if not args.case_id or not args.item_id:
            print("Case ID and Item ID are required.")
            sys.exit(1)

        if not validate_uuid(args.case_id):
            print("Invalid case ID format.")
            sys.exit(1)


        for item_id in args.item_id:
            if int(item_id) in blockchain.ids:
                print("Evidence with {item_id} already present in the record")
                exit(1)
            last_block_hash = get_last_block_hash(blockchain)
            # Create a new block with the provided information
            new_block = Block(
                prev_hash=last_block_hash,
                timestamp=time.time(),
                case_id=args.case_id,
                item_id=int(item_id),
                state='CHECKEDIN',
                handler=args.handler or '',
                organization=args.organization or '',
                data=''
            )

            blockchain.add_block(new_block)

            timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(new_block.timestamp))
            print(f"Case: {args.case_id}")
            print(f"Added item: {item_id}")
            print(f"Status: CHECKEDIN")
            print(f"Time of action: {timestamp_iso}")
        blockchain.save_to_file(blockchain_file_path)
        
    elif args.command == 'checkout':
        
        if not args.item_id or not args.handler or not args.organization:
            print("Item ID, handler, and organization are mandatory for checkout.")
            sys.exit(1)
        item_id = args.item_id[0]
        # Check if blockchain has been initialized
        if blockchain is None:
            print("Blockchain not initialized. Cannot perform checkout.")
            sys.exit(1)
        # Get the last state block of the item
        last_state_block = blockchain.get_last_state(item_id)

        if last_state_block is None:
            print(f"Item ID {item_id} must be checkedin before performing checkout.")
            sys.exit(1)
        

        if last_state_block.state.rstrip(b'\x00').decode('utf-8') != 'CHECKEDIN':
            print(f"Item ID {item_id} must be checked in before performing  checkout.")
            sys.exit(1)

        last_block_hash = get_last_block_hash(blockchain)
            # Create a new block with the provided information
        new_block = Block(
                prev_hash=last_block_hash,
                timestamp=time.time(),
                case_id=last_state_block.case_id,
                item_id=int(item_id),
                state='CHECKEDOUT',
                handler=args.handler or '',
                organization=args.organization or '',
                data=''
            )

        blockchain.add_block(new_block)
        blockchain.save_to_file(blockchain_file_path)

        timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(new_block.timestamp))
        print(f"Checked out item: {item_id}")
        print(f"Status: CHECKEDOUT")
        print(f"Time of action: {timestamp_iso}")
        
    elif args.command == 'checkin':
        if not args.item_id or not args.handler or not args.organization:
            print("Item ID, handler, and organization are mandatory for checkin.")
            sys.exit(1)
        # Assuming only one item is checked in at a time
        item_id = args.item_id[0]
        # Check if blockchain has been initialized
        if blockchain is None:
            print("Blockchain not initialized. Cannot perform checkin.")
            sys.exit(1)
        # Check if the item's last state is checked out

        last_block = blockchain.get_last_state(item_id)
        if last_block is None:
            print(f"Item ID {item_id} must be checked out before performing checkin.")
            sys.exit(1)

        if last_block.state.rstrip(b'\x00').decode('utf-8') != 'CHECKEDOUT':
            print(f"Item ID {item_id} must be checked out before performing checkin.")
            sys.exit(1)

        last_block_hash = get_last_block_hash(blockchain)
        # Create a new block with the provided information
        new_block = Block(
                prev_hash=last_block_hash,
                timestamp=time.time(),
                case_id=last_block.case_id,
                item_id=int(item_id),
                state='CHECKEDIN',
                handler=args.handler or '',
                organization=args.organization or '',
                data=''
            )
        

        blockchain.add_block(new_block)
        blockchain.save_to_file(blockchain_file_path)


        timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(new_block.timestamp))
        print(f"Checked in item: {item_id}")
        print(f"Status: CHECKEDIN")
        print(f"Time of action: {timestamp_iso}")

    elif args.command == 'show' and args.subcommand == 'history':
        # if not args.item_id:
        #     print("Item ID is required for showing history.")
        #     sys.exit(1)

        blockchain = Blockchain.load_from_file(blockchain_file_path)
        if blockchain is None:
            print("Blockchain not initialized. No history available.")
            sys.exit(1)

        history = blockchain.show_history()
        temp = history
        if args.case_id is not None:
            history = []
            for entry in temp:
                if entry['Case'] == args.case_id:
                    history.add(entry)
        
        temp = history
        if args.item_id is not None:
            for entry in temp:
                if entry['Item'] not in  args.item_id:
                    history.remove(entry)
        if args.num_entries is not None:
            history = history[:int(args.num_entries)]
        for entry in history:
            print(f"Case: {entry['Case']}")
            print(f"Item: {entry['Item']}")
            print(f"Action: {entry['Action']}")
            # print(f"Time: {entry['Time']}")
            print("\n")

    elif args.command == 'show' and args.subcommand == 'cases':
        blockchain = Blockchain.load_from_file(blockchain_file_path)
        if blockchain is None:
            print("Blockchain not initialized. No cases available.")
            sys.exit(1)

        cases = blockchain.show_cases()
        if cases:
            for case_id in cases:
                print(case_id)
        else:
            print("No cases found in the blockchain.")

    elif args.command == 'show' and args.subcommand == 'items':
        if not args.case_id:
            print("Case ID is required for showing items.")
            sys.exit(1)

        blockchain = Blockchain.load_from_file(blockchain_file_path)
        if blockchain is None:
            print("Blockchain not initialized. No items available.")
            sys.exit(1)

        items = blockchain.show_items_for_case(args.case_id)
        for item in items:
            print(item)

    elif args.command == 'remove':
        if not args.item_id:
            print("Invalid item ID")
            sys.exit(1)
        # Check if blockchain has been initialized
        if blockchain is None:
            print("Blockchain not initialized. Cannot perform removal.")
            sys.exit(1)
        
        # Ensure 'why' is provided as it is not optional
        if not args.why:
            print("Removal reason is required. Please provide the '-y' or '--why' argument.")
            sys.exit(1)
        if args.why == "RELEASED" and not args.organization:
            print("Removal reason - RELEASED requires organization.")
            sys.exit(1)

        item_id = args.item_id[0]  # Assuming only one item is removed at a time
        last_state_block = blockchain.get_last_state(item_id)
        if not last_state_block:
            print(f"Item ID {item_id} must be checked in before performing remove.")
            sys.exit(1)

        if last_state_block.state.rstrip(b'\x00').decode('utf-8') != 'CHECKEDIN':
            print(f"Item ID {item_id} must be checked in before performing remove.")
            sys.exit(1)

        last_block_hash = get_last_block_hash(blockchain)
            # Create a new block with the provided information
        new_block = Block(
                prev_hash=last_block_hash,
                timestamp=time.time(),
                case_id=last_state_block.case_id,
                item_id=int(item_id),
                state=args.why,
                handler=args.handler or '',
                organization=args.organization or '',
                data=''
            )

        blockchain.add_block(new_block)
        blockchain.save_to_file(blockchain_file_path)

        timestamp_iso = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(new_block.timestamp))
        print(f"Case: {UUID(bytes=last_state_block.case_id).hex if last_state_block.case_id else None}")
        print(f"Removed item: {item_id}")
        print(f"Status: REMOVED")
        print(f"Removal Reason: {args.why}")
        print(f"Time of action: {timestamp_iso}")
        # Exit with code 0 after successful removal
        # sys.exit(0)

    elif args.command == 'verify':
        if blockchain.verify_chain():
            print("Blockchain verified, no errors found")
        else:
            print("Blockchain verification failed")
            sys.exit(1)

if __name__ == "__main__":
    main()