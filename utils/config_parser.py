from pathlib import Path
from configparser import ConfigParser

# Resolve project root
project_root = Path(__file__).resolve().parent.parent
common_path = project_root / "Common.cfg"

# Handles error if config file is missing
if not common_path.exists():
    raise FileNotFoundError(f"Config file not found at: {common_path}")

# Parse Common.cfg
config = ConfigParser()
config.read(common_path)

# Handles error if section is missing (if Common.cfg is malformed/incomplete/etc)
if not config.has_section("GLOBALINFO"):
    raise KeyError(f"Section 'GLOBALINFO' not found. Available sections: {config.sections()}")

# Example of accessing a specific config value
NumberOfPreferredNeighbors = config.get("GLOBALINFO", "NumberOfPreferredNeighbors")

# Convert section to dictionary
common_dict = dict(config.items("GLOBALINFO"))
print(common_dict)

# Example output
print(f"Loaded from: {common_path}")

# sets path to PeerInfo.cfg
peerinfo_path = project_root / "PeerInfo.cfg"

# Handles error if PeerInfo.cfg is missing
if not peerinfo_path.exists():
    raise FileNotFoundError(f"PeerInfo.cfg not found at: {peerinfo_path}")

# Parse PeerInfo.cfg
peer_info = {}

# Read PeerInfo.cfg line by line and store in dictionary in format {peer_id: {host, port, has_file}}
with open(peerinfo_path, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Invalid line format: {line}")
        
        peer_id, host, port, has_file = parts
        peer_info[int(peer_id)] = {
            "host": host,
            "port": int(port),
            "has_file": has_file == "1"
        }

# Example output
print(peer_info)