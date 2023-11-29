# Block.py

import struct
import hashlib
from uuid import UUID

class Block:
    def __init__(self, prev_hash, timestamp, case_id, item_id, state, handler, organization, data=''):
        self.prev_hash = prev_hash if prev_hash is not None else b'\x00' * 32
        self.timestamp = timestamp
        self.case_id = case_id if isinstance(case_id, bytes) else UUID(case_id).bytes
        self.item_id = item_id
        self.state = state.encode('utf-8').ljust(12, b'\x00')
        self.handler = handler.encode('utf-8').ljust(20, b'\x00')
        self.organization = organization.encode('utf-8').ljust(20, b'\x00')
        self.data = data.encode('utf-8')

    def calculate_hash(self):
        header = struct.pack("32s d 16s I 12s 20s 20s I", self.prev_hash, self.timestamp, self.case_id,
                             self.item_id, self.state, self.handler, self.organization, len(self.data))
        return hashlib.sha256(header + self.data).hexdigest()

    @staticmethod
    def unpack_from_binary(binary_data):
        struct_format = struct.Struct("32s d 16s I 12s 20s 20s I")
        unpacked_data = struct_format.unpack(binary_data[:struct_format.size])
        data = binary_data[struct_format.size:]
        return Block(*unpacked_data[:-1], data=data.rstrip(b'\x00'))

    def pack_into_binary(self):
        # Debug printing
        print(f"Packing Block: {self}")
        
        header = struct.pack(
            "32s d 16s I 12s 20s 20s I",
            self.prev_hash,
            self.timestamp,
            self.case_id,
            self.item_id,
            self.state.ljust(12, b'\x00'),
            self.handler.ljust(20, b'\x00'),
            self.organization.ljust(20, b'\x00'),
            len(self.data)
        )
        
        # Debug printing
        print(f"Packed Header: {header.hex()}")
        print(f"Packed Data: {self.data.hex()}")
        
        return header + self.data

    @staticmethod
    def unpack_from_binary(binary_data):
        # Adjust the unpacking format to match the header size
        struct_format = struct.Struct("32s d 16s I 12s 20s 20s I")
        unpacked_data = struct_format.unpack(binary_data[:116])
        data = binary_data[116:]
        stripped_data = data.rstrip(b'\x00')
        # Debug printing
        print(f"Unpacking Block: {unpacked_data}")
        print(f"Unpacked Data: {stripped_data.decode()}")
        
        return Block(*unpacked_data[:-1], data=data.rstrip(b'\x00'))