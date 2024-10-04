# 
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# mrt_server.py - defining server APIs of the mini reliable transport protocol
#
#
# Server
#

import socket # for UDP connection
import json
from segment import Segment
from header import Header
from checksum import Checksum
from datetime import datetime, timezone
import threading
from collections import deque
import select
import datetime

ACK = {
    'SYN': 'SYN-ACK',
    'PSH': 'ACK',
    'FIN': 'FIN-ACK',
    'DATA': 'ACK'
}

buff_size = 1024

class Server:
    
    def init(self, src_port, receive_buffer_size):
        ## Class instances 
        self.segment = Segment()
        self.header = Header()
        self.checksum = Checksum()
        ## Segment buffer and lock
        self.seg_lock = threading.Lock()
        self.buff_lock = threading.Lock()
        self.seg_buff = deque() 
        self.proc_data = b''
        self.rwnd = receive_buffer_size
        ## Base parameters
        self.src_port = src_port
        self.seg_num = self.client_seg_size = 0
        ## Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.src_port))
        ## Threads 
        self.done = threading.Event()
        self.reciever = threading.Thread(target=self.read_segments)
        self.segmenter = threading.Thread(target=self.process_segments)
        self.reciever.daemon = True
        self.segmenter.daemon = True
        self.conn = None
        self.initiate_close = False 
        # Start the threads
    
    def log_to_file(self, message):
            with open(f"log_{self.src_port}.txt", "a") as log_file:
                log_file.write(message + "\n")

    def format_log_entry(self, src_port, dst_port, seq, ack, type, payload_length):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} {src_port} {dst_port} {seq} {ack} {type} {payload_length}"

    def accept(self):
        """
        accept a client request
        blocking until a client is accepted

        it should support protection against segment loss/corruption/reordering 

        return:
        the connection to the client 
        """
        ## Receive the initial SYN 
        conn = None
        while True:
            ## Getting the initial SYN
            client_req, network_addr = self.sock.recvfrom(buff_size)
            print("Got the SYN from client")
            syn_header, _ = self.segment.parse_segment(client_req, self.header.size)
            src_port, _, _, _, self.client_seg_size = self.header.parse_header(syn_header)
            
            ## Sending the SYN-ACK and wait for ACK with retry mechanism
            attempts = 0
            ack_received = False
            syn_ack_header = self.header.get_header(self.src_port, self.seg_num, 'SYN-ACK', 0, self.calc_space())
            while attempts < 3 and not ack_received:  # Limit the number of retries to 3, for example
                self.sock.sendto(self.segment.get_segment(syn_ack_header, None), network_addr)
                print("Sending the SYN-ACK")
                self.sock.settimeout(2)  # Set timeout for 5 seconds
                try:
                    syn_rsp, network_addr = self.sock.recvfrom(buff_size)
                    syn_ack_header, _ = self.segment.parse_segment(syn_rsp, self.header.size)
                    src_port, _, message_type, _, _ = self.header.parse_header(syn_ack_header)
                    if message_type == 'ACK':
                        conn = network_addr
                        ack_received = True  # ACK received, exit while loop
                except socket.timeout:
                    attempts += 1
                    print("Timeout waiting for ACK after SYN-ACK. Attempting to resend SYN-ACK...")

            if ack_received:
                break  # Exit the outer loop if ACK is successfully received
            elif attempts >= 3:
                print("Failed to receive ACK after 3 attempts. Aborting connection...")
                return None

        self.sock.settimeout(None)  # Remove the timeout for the rest of the application
        self.seg_num = 1
        self.conn = conn

        self.reciever.start()
        self.segmenter.start()
        return conn

    def check_corrupt(self, seg_header, in_data):
        """ 
        check corruption of the data according to the header
        checks checksum, seg_num, and if payload_length == recieved 
        
        arguments
        segment broken down into its elements: header and data
        a. seg_header
        b. in_data
        """
        corrupt = None
        src_port, recv_seq_num, recv_type, recv_checksum, recv_payload_length = self.header.parse_header(seg_header)
        if not self.checksum.validate_checksum(in_data, recv_checksum) and recv_type != 'FIN':
            corrupt = True
            return True, None, None
        if self.seg_num != recv_seq_num:
            corrupt = True
            return True, None, None

        if len(in_data) != recv_payload_length:
            corrupt = True
            return True, None, None
        else:
            corrupt = False
            return corrupt, recv_type, recv_seq_num
    
    def calc_space(self):
        """
        Calculates the available space, rwnd, that is available to the client
        """
        if self.rwnd > 0:
            return self.rwnd
        else:
            return 0
        
    def process_segments(self):
        """
        One of two thread functions which reads from the segment buffer (deque)
        and does the processing. First checks corruption in the segment, if corrupt segment
        then we continue to the next iteration, effectively dropping the packet
        
        Otherwise, we add the data to the final buffer, and send the acknowledgement to the 
        client 
        
        Detects a FIN response from client, to which we set the thread event which would 
        terminate the reading 
        """

        while True:
            if len(self.seg_buff) == 0:
                continue
            with self.seg_lock:
                if not self.seg_buff:
                    continue
                seg = self.seg_buff.popleft()
                
            corrupt, type, in_seg_num = self.check_corrupt(seg[0], seg[1])

            if corrupt:
                continue
            
            if in_seg_num == self.seg_num:
                with self.buff_lock:
                    self.proc_data += seg[1]
                self.seg_num += 1
                self.send_ack(self.conn, self.seg_num - 1, 'ACK')

            if type == 'FIN' or self.done.is_set() == True:
                self.send_ack(self.conn, self.seg_num, 'FIN-ACK')
                
            if type == 'TERM':
                self.initiate_close = True
                print("Trying to break")
                break
                       
    def read_segments(self):
        """
        Thread function which takes the length as parameter, and reads up until 
        the server has read that many bytes. Adds read segments to the deque 
        which the other thread will read from. 
        """        
        while True:
            if self.initiate_close == True:
                return
            ready = select.select([self.sock], [], [], 0)
            if ready[0]:
                raw_data, addr = self.sock.recvfrom(self.client_seg_size)  # Consider buff_size to be sufficiently large
                seg_header, in_data = self.segment.parse_segment(raw_data, self.header.size)
                src_port, seg_num, message_type, _, payload_length = self.header.parse_header(seg_header)
                log_entry = self.format_log_entry(src_port, 0, seg_num, 'N/A', 'DATA', payload_length)
                self.log_to_file(log_entry)
                self.seg_buff.append((seg_header, in_data))

                
    def receive(self, conn, length):
        """
        receive data from the given client
        blocking until the requested amount of data is received
        
        it should support protection against segment loss/corruption/reordering 
        the client should never overwhelsm the server given the receive buffer size

        arguments:
        conn -- the connection to the client
        length -- the number of bytes to receive

        return:
        data -- the bytes received from the client, guaranteed to be in its original order
        """
        data = None
        self.conn = conn
        while True:
            if len(self.proc_data) < length:
                continue
            else:
                with self.buff_lock:
                    data = self.proc_data[:length] 
                    self.proc_data = self.proc_data[length:]
                    self.rwnd = len(self.proc_data)
                    break
        
        return data
    
    def send_ack(self, client, seq_num, type):
        """
        sends acknowledgement to the client 
        
        client = the client connection
        seq_num = the acknowledged seq
        type =type of acknowledgement sending
        """
        ## Finds the appropriate response and create the header
        avail = self.calc_space()
        ack_header = self.header.get_header(self.src_port, seq_num, type, 0, avail)
        ack_segment = self.segment.get_segment(ack_header, None)
        self.sock.sendto(ack_segment, client)
        log_entry = self.format_log_entry(self.src_port, client, seq_num, type, 'N/A', 0)
        self.log_to_file(log_entry)
              
    def close(self):
        """
        Handles a request to close the connection from the client,
        blocking until the connection is closed properly.
        """    
        while True:
            try:
                term_ack_header = self.header.get_header(self.src_port, self.seg_num, 'TERM-ACK', 0, 0)
                term_ack_segment = self.segment.get_segment(term_ack_header, None)
                self.sock.sendto(term_ack_segment, self.conn)
                final_ack, _ = self.sock.recvfrom(buff_size)
                ack_header, _ = self.segment.parse_segment(final_ack, self.header.size)
                _, _, ack_type, _, _ = self.header.parse_header(ack_header)
                break
        
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        # Finally, close the socket
        self.sock.close()
        print("Socket closed.")
