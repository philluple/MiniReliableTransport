# MiniReliableTransport

**MiniReliableTransport** is a custom implementation of a reliable data transport layer using the **Go-Back-N protocol** for efficient data transmission and retransmission. This protocol ensures that lost or corrupted packets are detected and retransmitted, maintaining reliable communication even over unreliable channels.

### Features

- **Go-Back-N Protocol**: Implements sliding window mechanism for packet transmission, allowing multiple packets to be sent before waiting for an acknowledgment, improving throughput. Lost or unacknowledged packets are retransmitted.
- **UDP Sockets**: The transport layer is built on **UDP**, a connectionless protocol, while implementing reliability principles typically found in **TCP** (e.g., sequencing, acknowledgment, and retransmission).
  
### Key Concepts

- **Sliding Window**: Manages a window of sent but unacknowledged packets, retransmitting only when necessary to optimize data flow.
- **Retransmission on Timeout**: If an acknowledgment is not received within a certain timeframe, the Go-Back-N protocol initiates retransmission for the unacknowledged packet and all subsequent ones.

### Development

Developed by **Phillip Le**, this project serves as a lightweight transport protocol, combining the flexibility of **UDP** with essential reliability features inspired by **TCP**.
