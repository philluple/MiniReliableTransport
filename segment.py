from header import Header

class Segment:  
        
    def get_segment(self, header, data):
        if data == None:
            return header
        else: 
            return header + data
    
    def parse_segment(self, segment, header_size):
        header = segment[:header_size]
        data = segment[header_size:]
        return header, data