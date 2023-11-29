#!/usr/bin/env python3

# bchoc.py
import maya
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
        blockchain = Blockchain.load_from_file(blockchain_file_path)
        if blockchain is None:
            print("Blockchain file not found. Creating INITIAL block.")
            initial_block = Block(
                prev_hash=b'\x00' * 32,
                timestamp=time.time(),
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
            print("Initial block created and saved to the blockchain.")
        else:
            print("Blockchain file found with INITIAL block.")

    if args.command == 'verify':
        exit(1)

if __name__ == "__main__":
    main()