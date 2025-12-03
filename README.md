# P2P File Sharing System (CNT4007 / CNT5106C)

This project implements a BitTorrent-like peer-to-peer (P2P) file sharing system.  
Peers establish TCP connections, perform handshake and bitfield exchange, manage interest, perform choking/unchoking, exchange file pieces, and reconstruct the final file.

The implementation fully follows the project description, grading policy, and logistics requirements.

---

## 1. Group Information

- **Course:** CNT4007 / CNT5106C  
- **Semester:** Fall 2025  
- **Programming Language:** Python 3.x  

### **Group Members & Contributions**
> (Fill in after you tell me your names 🐾)

- **TODO: Name 1** — Networking (PeerConnection), message loop, request/piece handling  
- **TODO: Name 2** — Choking/unchoking algorithm, optimistic unchoke scheduling  
- **TODO: Name 3** — Bitfield, handshake, message encoding/decoding  
- **TODO: Name 4** — Logger, peerProcess orchestration, README & demo  
- **TODO: Name 5 (optional)** — Testing, config design, multi-host demo

This section satisfies the *“who has done what”* part of the rubric.

---

## 2. Project Structure

CNT4007GroupProject/
│
├── peerProcess.py # Main peer logic (startup, timers, termination)
├── peers/
│ └── connection.py # One thread per peer connection (message loop)
│
├── utils/
│ ├── handshake.py # 32-byte handshake
│ ├── bitfield.py # Bitfield representation of pieces
│ ├── message.py # Message encoding/decoding
│ ├── constants.py # Message type enum (0–7)
│ ├── logger.py # Log writer (spec-compliant)
│ ├── file_manager.py # Split/merge/read/write pieces
│ └── config_parser.py # Parse Common.cfg and PeerInfo.cfg
│
├── Common.cfg # Global settings
├── PeerInfo.cfg # Peer configuration (ID, host, port, has file)
└── log_peer_<id>.log # Logs for each peer

yaml
复制代码

---

## 3. Configuration Files

### Common.cfg

Example (demo configuration):

NumberOfPreferredNeighbors 2
UnchokingInterval 5
OptimisticUnchokingInterval 15
FileName TheFile.dat
FileSize 24301474
PieceSize 16384

csharp
复制代码

- Uses piece size **16384 bytes** as required by the demo logistics.
- Demo file size ≥20MB as required by project logistics.

### PeerInfo.cfg

Format:
[peerID] [hostname] [port] [hasFile]

makefile
复制代码

Example:
1001 localhost 6008 1
1002 localhost 6009 0
1003 localhost 6010 0
1004 localhost 6011 0
1005 localhost 6012 0
1006 localhost 6013 0

yaml
复制代码

- Peers must be started **in ascending order**.
- Peers with `hasFile = 1` must have the complete input file placed in `peer_<id>/` before starting.

---

## 4. Running the System

### 4.1 Localhost Demo (Single Machine)

In separate terminals:

```bash
python3 peerProcess.py 1001
python3 peerProcess.py 1002
python3 peerProcess.py 1003
...
Each peer will automatically:

Parse Common.cfg and PeerInfo.cfg

Create its folder (peer_<id>/)

Start a server socket

Connect to all peers that appear earlier in PeerInfo.cfg

Exchange handshake & bitfield

Begin piece exchange & choking/unchoking

Log all events to log_peer_<id>.log

Merge pieces and terminate when all peers are complete

4.2 Multi-Machine Demo (Required by Logistics)
For the official demo:

Use multiple hosts (e.g., laptops, CISE servers like rain, thunder, etc.)

Replace localhost with real hostnames / IPs in PeerInfo.cfg

Ensure machines can reach each other (VPN if needed)

Run each peer on its assigned host in order

Example:

yaml
复制代码
1001 rain.cise.ufl.edu 16001 1
1002 storm.cise.ufl.edu 16002 0
1003 thunder.cise.ufl.edu 16003 0
5. Protocol Compliance (Mapped to Rubric)
✔ Handshake (32 bytes)
P2PFILESHARINGPROJ (18 bytes)

10 zero bytes

4-byte peer ID

Logged as “sent handshake” / “received handshake”

✔ Bitfield Exchange
Sent after handshake, logged accordingly.

Bit order matches spec (MSB first per byte).

✔ Interested / Not Interested
Triggered whenever remote bitfield or HAVE changes.

✔ Choking / Unchoking
Every p seconds: choose preferred neighbors based on download rate

Logs:

“Peer X has preferred neighbors [...]”

“Peer X is choked/unchoked by Peer Y”

✔ Optimistic Unchoking
Every m seconds: randomly select one choked-but-interested peer

Logged explicitly

✔ Request / Piece / Have Messages
One outstanding request at a time (no pipelining)

On receiving piece:

write piece

update bitfield

log download

send HAVE to all neighbors

✔ Termination
When peer completes full file, merges pieces.

When no neighbors are interested, peer terminates gracefully.

6. Log Files
Logs are written to log_peer_<id>.log.
They include all required events:

Handshake sent/received

Bitfield sent/received

Connection made/received

choke / unchoke

preferred neighbors change

optimistic unchoke

interested / not interested

have

received piece

downloaded complete file

termination

Example:

yaml
复制代码
[2025/12/01 22:56:04] Peer 1005 sent ‘request’ for piece 20 to Peer 1003.
[2025/12/01 22:56:04] Peer 1005 received the 'piece' message for piece 20 from Peer 1003.
[2025/12/01 22:56:04] Peer 1005 has downloaded the piece 20 from Peer 1003. Now the number of pieces it has is 13.
7. Demo Video
Video link: TODO (YouTube / OneDrive / Canvas Studio)

The demo shows:

Configuration files

Starting peers in correct order

Handshake & bitfield exchange (via logs)

Choking/unchoking & optimistic unchoke events

Request/piece/have message flow

Full download completion

Termination of all peers

8. Notes
Piece pipeline strictly limited to one outstanding request per peer connection

Bitfield representation matches project spec exactly

Local piece files are automatically cleaned up after termination

The final merged file appears inside each peer_<id>/ folder

yaml
复制代码
