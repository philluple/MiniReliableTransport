import struct

class Header: 
    def __init__(self):
        # src_port, seq_num, message_type, checksum, payload_length
        self.header_format = 'H H Q I I'
        self.size = struct.calcsize(self.header_format)
        self.message_types = {'SYN': 1, 'ACK': 2, 'DATA': 3, 'FIN': 5, 'SYN-ACK': 6, 'FIN-ACK': 7, 'TERM': 8, 'TERM-ACK': 9}

    def get_message_type_code(self, message_type):
        # Convert a message type string to its corresponding integer code
        return self.message_types.get(message_type, 0)

    # For the server, size = rwnd and the client, 
    def get_header(self, src_port, seq_num, message_type, checksum, size):
        type_code = self.get_message_type_code(message_type)  # Convert to integer code
        packed_header = struct.pack(self.header_format, src_port, seq_num, type_code, checksum, size)
        return packed_header

    def parse_header(self, header):
        unpacked_header = struct.unpack(self.header_format, header)
        src_port, seq_num, type_code, checksum, payload_length = unpacked_header
        # Convert type_code back to message type string if needed
        message_type = next((k for k, v in self.message_types.items() if v == type_code), None)
        return src_port, seq_num, message_type, checksum, payload_length
