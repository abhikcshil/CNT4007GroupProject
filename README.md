CNT4007GroupProject
===================

P2P File Sharing Application
----------------------------

This project implements a peer-to-peer (P2P) file sharing system where multiple peers exchange pieces of a file over TCP connections. Each peer connects to others based on configuration files and follows the project specification for connection setup, message passing, and logging.

---

## Quick Start

### 1. Setup Environment
Create and activate a virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate
```

(Optional) install any required dependencies:
```
pip install -r requirements.txt
```

---

### 2. Configuration Files
Make sure the following configuration files exist in the project root directory:

**Common.cfg**
```
NumberOfPreferredNeighbors = 2
UnchokingInterval = 5
OptimisticUnchokingInterval = 15
FileName = TheFile.dat
FileSize = 10000232
PieceSize = 32768
```

**PeerInfo.cfg**
```
1001 localhost 6008 1
1002 localhost 6009 0
1003 localhost 6010 0
```

- The last column (1 or 0) indicates whether the peer starts with the complete file.
- Each peer will automatically create its own folder named peer_<id> on startup.

---

### 3. Running the Peers
Run each peer in its own terminal window:

```
python3 peerProcess.py 1001
python3 peerProcess.py 1002
python3 peerProcess.py 1003
```

Each peer will:
- Parse both configuration files.
- Create its corresponding folder (peer_<id>).
- Start a listener socket on the assigned port.
- Connect to all earlier peers in PeerInfo.cfg.
- Log connection events to log_peer_<id>.log.

---

### 4. Log Files
All connection and message events are written to:
```
log_peer_<id>.log
```
Example output:
```
[2025/10/22 11:45:10] Peer 1001 makes a connection to Peer 1002.
[2025/10/22 11:45:10] Peer 1001 is connected from Peer 1003.
```

---

### 5. Project Structure
```
CNT4007GroupProject/
│
├── peerProcess.py          # Peer main process logic
├── utils/                  # Helper modules (config_parser, logger, message, etc.)
├── Common.cfg              # Global configuration
├── PeerInfo.cfg            # Peer connection info
├── log_peer_<id>.log       # Output logs for each peer
└── requirements.txt        # Python dependencies (if any)
```

---

### 6. Notes
- The current version supports peer initialization, connection setup, and logging.
- Future updates will include message handling, bitfield exchange, choking/unchoking logic, and piece download management.
