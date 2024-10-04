[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/KQFw0QXH)
# CSEE 4119 Spring 2024, Assignment 2
## Phillip Le 
## GitHub username: philluple


Code Structure:
On top of the given structure, I have implemented various classes to help with both the server and client functionalities. 

1. header.py 
2. segment.py
3. timer.py
4. checksum.py 

### header.py
This class is responsible for headers. The format I have chosen is 'H H Q I I'.

1. H - src_port
Though not super neccessary for this assignment as the server can only handle one client at a time. If I were to expand this use for multiple clients. This would be useful for matching server buffers designated for each client identified by the src_port 

2. H - seg_num/ack_num
For the server, this element represents the segment number that the client sent. For the client, this is the ack_number which also corresponds with the segment number they are expecting an ACK for 

3. Q - message type 

4. I - checksum 

5. I - payload_length/rwnd
For the server, this would be the rwnd – advertising how much more data that the client can send. In the client, this value represents the number of bytes that they are sending 

Functions:

1. get_message_type_code: gets the corresponding message type given the int that was sent in header
2. get_header: constructs the header 
3. parse_header: returns the components of the header after unpacking it 


### segment.py
This class is responsible for all things segments. 

1. get_segment: gets the header constructed from the header class as well as the data and constructs a segment 
2. parse_segment: seperates the header from the data according to the header_size

### timer.py

1. start_timer – updates the start_time 
2. stop_timer – stops the timer 
3. timeout – timeout is defined to be 5 seconds, returns whether or not there has been a timeout

### checksum.py

1. validate_checksum – takes the checksum from the header as well as the data, and verifies the checksum value 
2. calc_checksum – calculates the checksum according to data. 


Client-server handle transfers using Go-Back-N protocol













