# 
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# mrt_client.py - defining client APIs of the mini reliable transport protocol
#

import socket # for UDP connection
import threading
from datetime import datetime, timezone
from segment import Segment
from header import Header
from timer import Timer
from checksum import Checksum
import select 
import datetime

class Client:
    def init(self, src_port, dst_addr, dst_port, segment_size):
        """
        initialize the client and create the client UDP channel

        arguments:
        src_port -- the port the client is using to send segments
        dst_addr -- the address of the server/network simulator
        dst_port -- the port of the server/network simulator
        segment_size -- the maximum size of a segment (including the header)
        """
        
        ## Class instances
        self.header = Header()
        self.segment = Segment()
        self.checksum = Checksum()
        ## Base parameters
        self.seg_num = 0
        self.src_port, self.dst_addr, self.dst_port, self.segment_size = src_port, dst_addr, dst_port, segment_size
        ## Go-Back-N 
        self.n = 4  
        self.server_rwnd = None
        self.data_buff = None
        self.segments = []
        self.temp_seg_store = []
        ## Socket and thread
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', src_port))
        self.bytes_sent = 0         
        self.worker = threading.Thread(target=self.rcv_and_sgmnt_handler)
        self.initiate_close = False

    def log_to_file(self, message):
        with open(f"log_{self.src_port}.txt", "a") as log_file:
            log_file.write(message + "\n")

    def format_log_entry(self, src_port, dst_port, seq, ack, type, payload_length):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} {src_port} {dst_port} {seq} {ack} {type} {payload_length}"

    def connect(self):
        """
        Connect to the server with a listening loop for incoming messages.
        """
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                # Send SYN message
                syn_header = self.header.get_header(self.src_port, self.seg_num, 'SYN', 0, self.segment_size)
                syn_segment = self.segment.get_segment(syn_header, None)
                self.sock.sendto(syn_segment, (self.dst_addr, self.dst_port))
                self.sock.settimeout(5)  # Timeout after 2 seconds

                encoded_resp, addr = self.sock.recvfrom(1024)
                raw_header, _ = self.segment.parse_segment(encoded_resp, self.header.size)
                _, seg_num, message_type, _, self.server_rwnd = self.header.parse_header(raw_header)

                if self.seg_num == seg_num and message_type == 'SYN-ACK':
                    final_ack = self.header.get_header(self.src_port, seg_num+1, 'ACK', 0, 0)
                    final_ack_seg = self.segment.get_segment(final_ack, None)
                    self.sock.sendto(final_ack_seg, (self.dst_addr, self.dst_port))
                    self.seg_num += 1
                    print("Connection successfully established...")
                    return True  # Exit function upon successful connection

            except socket.timeout:
                print("Timeout. Resending SYN...")
                attempts += 1  # Increment attempts after a timeout

        print("Failed to connect after maximum attempts.")
        self.sock.settimeout(None)  # Reset timeout after exiting loop
        return False

    def send(self, data):
        """
        send a chunk of data of arbitrary size to the server
        blocking until all data is sent
        it should support protection against segment loss/corruption/reordering and flow control
        
        arguments:
        data -- the bytes to be sent to the server 
        """
        # Now we want to get the size of the header 
        first_chunk = self.chunk_bytes(data)
        for chunk in self.chunk_bytes(data):
            csum = self.checksum.calc_checksum(chunk)
            seg_num = self.seg_num
            new_header = self.header.get_header(self.src_port, seg_num, 'DATA', csum, int(len(chunk)))
            new_segment = self.segment.get_segment(new_header, chunk)
            self.segments.append((self.seg_num, new_segment))
            self.seg_num += 1

        # Append the FIN segment
        fin_header = self.header.get_header(self.src_port, self.seg_num, 'FIN', 0, 0)
        self.segments.append((self.seg_num, self.segment.get_segment(fin_header, None)))
        self.seg_num += 1
        self.worker.start()
        self.worker.join()

        return self.bytes_sent

    def rcv_and_sgmnt_handler(self):
        """
        Thread function which constantly is handling sending the segments and receiving the ACK
        """
        seg_first = 0
        seg_n = 0
        timer = Timer()
        while True:
            if self.initiate_close:
               break 
            # Check if there are segments to send and if the window is not full
            d_window = min(self.n, self.server_rwnd//self.segment_size)
            if self.segments and seg_n - seg_first < d_window:
                next_seg = self.segments.pop(0)  # Using deque's popleft() for efficiency
                self.temp_seg_store.append(next_seg)  # Temporary store used for retransmission
                self.sock.sendto(next_seg[1], (self.dst_addr, self.dst_port))
                log_entry = self.format_log_entry(self.src_port, self.dst_port, next_seg[0], 'N/A', 'DATA', len(next_seg))
                self.log_to_file(log_entry)
                self.bytes_sent += (len(next_seg[1])-self.header.size)  # Update byte counter
                timer.start_timer()
                seg_n += 1 

            # Use select to check if the socket is ready to read
            ready = select.select([self.sock], [], [], 0)  # Non-blocking check
            if ready[0]:
                raw_resp, _ = self.sock.recvfrom(1024)  # Safe to call recvfrom now
                resp_header, _ = self.segment.parse_segment(raw_resp, self.header.size)
                _, ack_num, type, _, self.server_rwnd = self.header.parse_header(resp_header)
                log_entry = self.format_log_entry(self.src_port, self.dst_port, ack_num, type, 'N/A', 0)
                self.log_to_file(log_entry)
                if type == 'ACK':
                    self.temp_seg_store = [(num, seg) for num, seg in self.temp_seg_store if num != ack_num]
                    timer.stop_timer()
                    seg_first = min([num for num, _ in self.temp_seg_store], default=ack_num)
                if type in ['FIN', 'FIN-ACK']:
                    break

            if timer.timeout():
                # Retransmit logic
                for retransmit_seg in self.temp_seg_store:
                    self.sock.sendto(retransmit_seg[1], (self.dst_addr, self.dst_port))
                    self.bytes_sent += len(retransmit_seg[1])  # Update byte counter for retransmitted segments
                timer.start_timer()


    def chunk_bytes(self, data):
        """
        Takes the data that we want to send to the server and chunks it 
        according to the header size
        """
        for i in range(0, len(data), self.segment_size-self.header.size):
            yield data[i:i+self.segment_size-self.header.size]
    
    def close(self):
        """
        Request to close the connection with the server,
        blocking until the connection is closed.
        """
        print("Attempting to close...")
        while True:
            final_ack = self.header.get_header(self.src_port, self.seg_num, 'TERM', 0, 0)
            final_ack_seg = self.segment.get_segment(final_ack, None)
            self.sock.sendto(final_ack_seg, (self.dst_addr, self.dst_port))
            term_resp, _ = self.sock.recvfrom(1024)
            term_resp_header, _ = self.segment.parse_segment(term_resp, self.header.size)
            _, _, ack_type, _, _ = self.header.parse_header(term_resp_header)
            
            if ack_type == 'TERM-ACK':
                ack_seg = self.header.get_header(self.src_port, self.seg_num, 'ACK', 0, 0)
                ack_seg_head = self.segment.get_segment(ack_seg, None)
                self.sock.sendto(final_ack_seg, (self.dst_addr, self.dst_port))
                self.sock.close()
                break
            else:
                break
        
        print("Shut down the client...")


                
                