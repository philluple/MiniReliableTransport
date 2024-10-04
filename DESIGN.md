# CSEE 4119 Spring 2024, Assignment 2 Design File
## Phillip Le
## GitHub username: philluple

TYPES of MESSAGES 
1. ACK - acknowledgement 
2. DATA - sending data 
4. SYN - initiate connection
5. SYN-ACK - acknowlesge connection req
6. FIN - done sending data 
7. FIN-ACK - ack fin
8. TERM - terminate connection
9. Confirm

STEPS:
1. Network must be started 
2. Server must be started 

Handshake
3. Client sends SYN to the server, size element of header is set to the size of segments that the client wants to send 
4.  Server responds with a SYN-ACK, header includes the amount of data that the server can send according to the buffer size
4. Client sends ACK

5. After the handshake, the client begins to send the data. First chunking it using the chunk_data function

def chunk_data(data):
Returns chunks of data according to the segment size defined at initialization of client and the header size of the buffer that the 

6. After chunking, self.seg_num is effectively the number of segments that the client wants to send. Client spawns a thread and starts the thread whose target is the rcv_and_sgmnt_handler. 

7. MRT uses Go-Back-N, thus the client thread will dynamically check the window, choosing the min between the defined window size, 4, and the amount of data that the server can handle as communicated in handshake or previous ACK

8. Client adds recently sent segments into an array which stores tuples (seg_num, segment). Starts the timer. Sends the data with DATA type

10. In the server, there are two threads one for processing and one for reading. The one that reads is simply reading the incoming segments and adding them to a segment buffer. The processing thread checks for corruption in the segments and will send ACK, drop, and append data to self.proc_data accordingly. 

11. Following Go-Back-N protocol, in case where there is corruption, the server will not ACK segment. When the client checks for timeouts and sees that there are items in the temp_seg_store (unACKED) the client will retransmit. 

12. Once close(), server stops reading and starts to listen for the. Client sends TERM, server responds with TERM-ACK, client sends ACK and closes