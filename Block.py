# Block.py

import struct
import hashlib
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
