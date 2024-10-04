import hashlib

class Checksum:
    def validate_checksum(self, data, checksum):
        test_checksum = self.calc_checksum(data)
        if checksum != test_checksum:
            return False 
        else:
            return True
        
    def calc_checksum(self, data):
        hash_digest = hashlib.sha256(data).hexdigest()
        hash_int = int(hash_digest, 16)  # Convert hex digest to integer
        truncated_hash = hash_int & 0xFFFFFFFF # Truncate to 32-bit
        return truncated_hash
