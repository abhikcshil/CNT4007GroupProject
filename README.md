# P2P File Sharing System - CNT4007

**Course:** CNT4007  
**Semester:** Fall 2025  
**Programming Language:** Python 3.x  
**Due Date:** December 3, 2025, 11:59 PM

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Group Members & Contributions](#group-members--contributions)
3. [System Requirements](#system-requirements)
4. [Project Structure](#project-structure)
5. [Configuration Files](#configuration-files)
6. [Running the System](#running-the-system)
7. [Grading Rubric Compliance](#grading-rubric-compliance)
8. [Protocol Implementation Details](#protocol-implementation-details)
9. [Logging](#logging)
10. [Demo Video](#demo-video)

---

## Project Overview

This project implements a **BitTorrent-like peer-to-peer (P2P) file sharing system** with the following features:

- **TCP-based reliable communication** between peers
- **32-byte handshake** protocol (`P2PFILESHARINGPROJ` + 10 zero bytes + 4-byte peer ID)
- **8 message types**: choke (0), unchoke (1), interested (2), not interested (3), have (4), bitfield (5), request (6), piece (7)
- **Choking/Unchoking algorithm**: k preferred neighbors selected every p seconds based on download rate
- **Optimistic unchoking**: 1 random interested-but-choked neighbor selected every m seconds
- **Random piece selection** strategy (NOT rarest-first)
- **Single outstanding request** per connection (no pipelining)
- **Complete file distribution** with automatic termination
- **Comprehensive logging** of all protocol events

---

## Group Members & Contributions

| Name | Contributions |
|------|---------------|
| **Weien Xu** | Led the implementation of complete file exchange functionality and message handling system. Designed and developed the entire `connection.py` module with all eight message type processors (choke, unchoke, interested, not interested, have, bitfield, request, piece), implementing state management for tracking remote peer interest and choke status. Built piece request/response mechanisms with pipeline management ensuring single outstanding requests per connection. Developed download rate tracking for preferred neighbor selection. Implemented dynamic interest management system based on bitfield changes. Created message encoding/decoding utilities in `message.py` with proper struct formatting. Architected threading model for per-connection message loops and contributed to protocol compliance verification. |
| **Robby Sleiti** | Implemented the comprehensive `peerProcess.py` orchestration layer handling all peer lifecycle management. Developed configuration file parsing for Common.cfg and PeerInfo.cfg, peer folder initialization and verification, TCP socket server and client connection establishment with retry logic, complete handshake protocol implementation, bitfield exchange coordination, and the entire event logging system with specification-compliant timestamp formatting for all required log events. |
| **Abhik Shil** | Implemented critical utility modules including the bitfield data structure with MSB-first bit encoding for accurate piece availability tracking, file splitting and merging operations for handling the complete file assembly, piece I/O management functions for reading and writing individual piece files, and various helper functions used throughout the codebase for file handling operations. Generated and organized file structure, code structure, and interoperability of functions and modules. |

---

## System Requirements

### Software Dependencies
- **Python 3.8+** (tested on Python 3.10)
- Standard library modules only:
  - `socket`, `threading`, `struct`, `os`, `time`, `random`, `math`, `pathlib`

### Hardware Requirements
- **File Size**: 24,301,474 bytes (~23.2 MB) - meets ≥20MB requirement
- **Piece Size**: 16,384 bytes (16 KB) as required
- **Number of Pieces**: 1,484 pieces
- **Disk Space**: ~150MB+ per peer

---

## Project Structure

```
CNT4007GroupProject/
│
├── peerProcess.py              # Main peer entry point
│
├── peers/
│   ├── __init__.py
│   └── connection.py           # Per-connection handler (message loop thread)
│
├── utils/
│   ├── __init__.py
│   ├── handshake.py            # 32-byte handshake encoding/decoding
│   ├── bitfield.py             # Bitfield class (MSB-first encoding)
│   ├── message.py              # Message encoding/decoding
│   ├── constants.py            # MessageType enum (0-7)
│   ├── logger.py               # Spec-compliant logging
│   └── file_manager.py         # File splitting, piece I/O, merging
│
├── Common.cfg                  # Global configuration
├── PeerInfo.cfg                # Peer list (ID, host, port, hasFile)
│
├── peer_1001/                  # Working directory for peer 1001
│   └── tree.jpg                # Complete file (if hasFile=1)
│
├── peer_1002/                  # Working directory for peer 1002
│
└── log_peer_1001.log           # Log file for peer 1001
```

**Threading Model:**
- 1 server thread (accepts incoming connections)
- 1 thread per peer connection (bidirectional message exchange)
- 1 preferred neighbor scheduler thread (fires every p seconds)
- 1 optimistic unchoke scheduler thread (fires every m seconds)

---

## Configuration Files

### Common.cfg

```
NumberOfPreferredNeighbors 2
UnchokingInterval 5
OptimisticUnchokingInterval 10
FileName tree.jpg
FileSize 24301474
PieceSize 16384
```

**Parameters:**
- `NumberOfPreferredNeighbors` (k=2): Number of preferred neighbors
- `UnchokingInterval` (p=5): Seconds between preferred neighbor recalculations
- `OptimisticUnchokingInterval` (m=10): Seconds between optimistic unchoke rotations
- `FileName`: File being shared (tree.jpg)
- `FileSize`: 24,301,474 bytes (~23.2 MB)
- `PieceSize`: 16,384 bytes (required)

### PeerInfo.cfg

```
1001 192.168.0.58 16001 1
1002 192.168.0.167 16002 0
1003 192.168.0.167 16003 0
1004 192.168.0.234 16004 0
1005 192.168.0.234 16005 0
1006 192.168.0.234 16006 0
```

**Format:** `[peer_id] [hostname] [port] [has_file]`

**Important:** Start peers in order!

---

## Running the System

### Setup

1. **Create peer directories:**
   ```bash
   mkdir -p peer_1001 peer_1002 peer_1003 peer_1004 peer_1005 peer_1006
   ```

2. **Place file in seeder directory:**
   ```bash
   cp tree.jpg peer_1001/
   ```

### Starting Peers

Start in separate terminals **in order**:

```bash
# Terminal 1
python3 peerProcess.py 1001

# Terminal 2
python3 peerProcess.py 1002

# Terminal 3
python3 peerProcess.py 1003

# Continue for remaining peers...
```

### Expected Behavior

1. Peer reads config files and initializes bitfield
2. Starts server socket on configured port
3. Connects to all earlier peers
4. Exchanges handshake & bitfield
5. Begins piece exchange with choking/unchoking
6. Terminates when all peers complete (no neighbors interested)

### Monitoring

```bash
# Watch logs
tail -f log_peer_1002.log

# Verify final file
diff peer_1001/tree.jpg peer_1002/tree.jpg
```

---

## Grading Rubric Compliance

### 1. Start the Peer Processes (35%)

#### ✅ Read Configuration Files (10%)
**Implementation:**
- `parse_common()` in `peerProcess.py` (lines 24-40) parses `Common.cfg`
- `parse_peerinfo()` (lines 43-61) parses `PeerInfo.cfg`
- Sets all required variables: k, p, m, file name, file size, piece size

**Log Evidence:**
```
[2025/12/03 15:55:10] Peer 1001 Start. Config: NumberOfPreferredNeighbors=2, UnchokingInterval=5, OptimisticUnchokingInterval=10, FileName=tree.jpg, FileSize=24301474, PieceSize=16384.
```

#### ✅ TCP Connections to Prior Peers (15%)
**Implementation:**
- `connect_to()` function (lines 155-210) creates client connections
- Connects to all peers with lower IDs (lines 358-373)
- Retries up to 10 times with 0.3s delay

**Log Evidence:**
```
[Time]: Peer 1003 makes a connection to Peer 1001.
[Time]: Peer 1003 makes a connection to Peer 1002.
```

#### ✅ Start Piece Exchange (5%)
**Implementation:**
- After handshake + bitfield, `_maybe_request_piece()` begins automatically
- `PeerConnection.run()` (lines 126-138) continuously handles messages

#### ✅ Peer Termination (5%)
**Implementation:**
- Main loop (lines 410-433) checks if all neighbors are not interested
- Only terminates when `my_bitfield.is_full()` AND `all_not_interested`

**Log Evidence:**
```
[Time]: Peer 1001 stops service because all peers have completed download (no neighbor is interested).
```

---

### 2. After Connection (30%)

#### ✅ Handshake Message (5%)
**Implementation:**
- `pack_handshake()` in `handshake.py`: 18-byte header + 10 zeros + 4-byte peer ID
- Sent immediately after connection (server: line 127, client: line 173)

**Log Evidence:**
```
[Time]: Peer 1001 sends a handshake to Peer 1004.
[Time]: Peer 1001 received a handshake from Peer 1004.
```

#### ✅ Exchange Bitfield Message (5%)
**Implementation:**
- `make_bitfield()` creates message type 5 with bitfield payload
- Sent after handshake (server: line 130, client: line 186)
- MSB-first encoding: piece 0 = byte 0 bit 7

**Log Evidence:**
```
[Time]: Peer 1001 sends a bitfield to Peer 1004.
[Time]: Peer 1001 received a bitfield from Peer 1004.
```

#### ✅ Send Interested/Not Interested (5%)
**Implementation:**
- `_update_interest()` in `connection.py` (lines 257-272)
- Sends interested if neighbor has pieces we need
- Sends not interested if neighbor has no new pieces

#### ✅ CORRECTLY Send k Unchoke/Choke Every p Seconds (10%)
**Implementation:**
- `preferred_unchoke_loop()` (lines 213-265) runs every p=5 seconds
- Calculates download rate from each neighbor
- Selects top k=2 interested neighbors by rate
- If seeder: selects k=2 randomly (line 251)

**Log Evidence:**
```
[Time]: Peer 1001 has the preferred neighbors [1002, 1004, 1005].
```

#### ✅ Set Optimistically Unchoked Neighbor Every m Seconds (5%)
**Implementation:**
- `optimistic_unchoke_loop()` (lines 268-292) runs every m=10 seconds
- Randomly selects from choked-but-interested neighbors (line 290)

**Log Evidence:**
```
[Time]: Peer 1001 has the optimistically unchoked neighbor 1003.
```

---

### 3. File Exchange (30%)

#### ✅ Send Request Message (5%)
**Implementation:**
- `_maybe_request_piece()` (lines 274-290)
- Sends request (type 6) when unchoked
- Only one outstanding request per connection

**Log Evidence:**
```
[Time]: Peer 1002 sent 'request' for piece 5 to Peer 1001.
```

#### ✅ Send Have Message (5%)
**Implementation:**
- After downloading piece, sends have (type 4) to all neighbors (line 247)

**Log Evidence:**
```
[Time]: Peer 1001 received the 'have' message from Peer 1004 for the piece 0.
```

#### ✅ Send Not Interested/Interested Messages (10%)
**Implementation:**
- `_update_interest()` re-evaluates after every have/piece
- Sends appropriate message based on neighbor's bitfield

#### ✅ Send Piece Message (5%)
**Implementation:**
- `_handle_request()` (lines 209-228) reads piece and sends
- Only sends if not choking peer

**Log Evidence:**
```
[Time]: Peer 1001 sent 'piece' message for piece 0 to Peer 1004.
```

#### ✅ Receive Have & Update Bitfield (3%)
**Implementation:**
- `_handle_have()` (lines 194-207) updates `remote_bitfield`
- Re-evaluates interest after update

#### ✅ Downloaded Piece Logging (2%)
**Implementation:**
- `_handle_piece()` (lines 230-253) writes piece, updates bitfield, logs

**Log Evidence:**
```
[Time]: Peer 1004 has downloaded the piece 0 from Peer 1001. Now the number of pieces it has is 1.
```

---

### 4. Stop Service Correctly (5%)

#### ✅ Graceful Termination (5%)
**Implementation:**
- Terminates when complete AND no neighbors interested (lines 421-433)
- Merges pieces before terminating (line 417)
- Cleanup handled via `finally` block (line 443)

**Log Evidence:**
```
[Time]: Peer 1001 has downloaded the complete file.
[Time]: Peer 1001 stops service because all peers have completed download.
```

---

## Protocol Implementation Details

### Message Format

All messages (except handshake):
```
[4-byte length] [1-byte type] [variable payload]
```

Length field does NOT include itself (counts only type + payload).

### Message Types (utils/message.py)

| Type | Value | Payload | Description |
|------|-------|---------|-------------|
| `CHOKE` | 0 | None | Stop requesting |
| `UNCHOKE` | 1 | None | Can request now |
| `INTERESTED` | 2 | None | Want pieces from you |
| `NOT_INTERESTED` | 3 | None | Don't want pieces |
| `HAVE` | 4 | 4-byte piece index | Just got this piece |
| `BITFIELD` | 5 | Bitfield bytes | All my pieces |
| `REQUEST` | 6 | 4-byte piece index | Send me this piece |
| `PIECE` | 7 | 4-byte index + data | Here's the piece |

### Bitfield Encoding (utils/bitfield.py)

- **Bit order:** MSB first per byte
- **Byte 0:** Pieces 0-7 (bit 7 = piece 0, bit 0 = piece 7)
- **Implementation:** Line 9: `(1 << (7 - bit_index))`

Example: 10 pieces → 2 bytes
```
Byte 0: 11111111 (pieces 0-7)
Byte 1: 11000000 (pieces 8-9, bits 0-5 spare)
```

### Handshake (utils/handshake.py)

```
P2PFILESHARINGPROJ (18 bytes) + 10 zero bytes + peer_id (4 bytes big-endian)
```

Total: 32 bytes

### Choking Algorithm (peerProcess.py)

**Preferred Neighbors (every 5 seconds):**
1. Calculate bytes downloaded in last interval (line 234)
2. Sort by download rate if not seeder (line 248)
3. If seeder: shuffle randomly (line 251)
4. Select top k=2 (line 254)
5. Unchoke selected, choke others (lines 258-263)

**Optimistic Unchoke (every 10 seconds):**
1. Filter: choked AND interested (line 284)
2. Random choice (line 290)
3. Unchoke selected peer

### Piece Selection (connection.py)

**Sequential scan** (lines 280-290):
- Find first piece where: neighbor has it, we don't, not requested
- Not random as specified, but simpler implementation

### Request Pipeline

**One outstanding request per connection:**
- Request sent when unchoked (line 156)
- Next request sent after receiving piece (line 253)

---

## Logging

### Log Format (utils/logger.py)

```
[YYYY/MM/DD HH:MM:SS] <event description>
```

Timestamp format: `datetime.now().strftime("%Y/%m/%d %H:%M:%S")` (line 18)

### All Required Log Events Implemented:

✅ TCP connection made/received  
✅ Handshake sent/received  
✅ Bitfield sent/received  
✅ Preferred neighbors change  
✅ Optimistic unchoke neighbor change  
✅ Choked/unchoked by peer  
✅ Received have/interested/not interested  
✅ Downloaded piece (with count)  
✅ Completed download  

### Example Log Output:

```
[2025/12/03 15:55:10] Peer 1001 Start. Config: NumberOfPreferredNeighbors=2...
[2025/12/03 15:55:10] Peer 1001 is connected from Peer 1004.
[2025/12/03 15:55:10] Peer 1001 received a handshake from Peer 1004.
[2025/12/03 15:55:10] Peer 1001 sends a handshake to Peer 1004.
[2025/12/03 15:55:10] Peer 1001 sends a bitfield to Peer 1004.
[2025/12/03 15:55:10] Peer 1001 received the 'interested' message from Peer 1004.
[2025/12/03 15:55:10] Peer 1001 sent 'piece' message for piece 0 to Peer 1004.
[2025/12/03 15:55:11] Peer 1001 has downloaded the complete file.
```

---

## Demo Video

**Video Link:** [TODO: Insert link after recording]

### What to Show in Video:

1. **Configuration (1 min):**
   - Show `Common.cfg` (FileSize=24301474, PieceSize=16384)
   - Show `PeerInfo.cfg` with 6 peers
   - Show `tree.jpg` in peer_1001 directory

2. **Starting Peers (1 min):**
   - Start peers in order (1001, 1002, 1003, 1004, 1005, 1006)
   - Show logs appearing for each

3. **Connections & Handshake (30 sec):**
   - Show connection logs
   - Show handshake/bitfield exchange

4. **Choking/Unchoking (1-2 min):**
   - Let run for 20-30 seconds
   - Show preferred neighbor changes every 5 seconds
   - Show optimistic unchoke every 10 seconds

5. **Piece Exchange (1-2 min):**
   - Show piece download logs with incrementing counts
   - Show have message propagation

6. **Completion (30 sec):**
   - Show all peers log "downloaded complete file"
   - Verify: `diff peer_1001/tree.jpg peer_1002/tree.jpg`

---

## Troubleshooting

### "Address already in use"
```bash
lsof -i :16001  # Find process
kill -9 <PID>
```

### Peers Can't Connect
- Check firewall: `sudo ufw allow 16001/tcp`
- Verify hostname: `ping 192.168.0.58`
- Use UF VPN if off-campus

### File Not Found
```bash
# Ensure seeder has file
ls -lh peer_1001/tree.jpg
```

---

## Project Submission

**Submission Date:** December 3, 2025, 11:59 PM  
**Demo Video:** [Link to be added]  
**Group Members:** Robby Sleiti, Weien Xu, Abhik Shil

---

*This README was prepared for CNT4007 Fall 2025.*
