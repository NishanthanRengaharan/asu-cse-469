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


# Define the Blockchain class


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


if __name__ == "__main__":
    main()