from pathlib import Path
from configparser import ConfigParser

def get_common_config():
    """Returns the common configuration as a dictionary."""
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
    return common_dict

def get_peer_info():
    """Returns the peer information as a dictionary."""
    # Resolve project root
    project_root = Path(__file__).resolve().parent.parent
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
    print(f"Loaded from: {peerinfo_path}")
    return peer_info

def get_peer_by_id(peer_id):
    """Returns the peer information for a specific peer ID."""
    peer_info = get_peer_info()
    return peer_info.get(peer_id, None)

def get_neighbors(peer_id):
    """Returns a list of all peer IDs except the given peer_id."""
    peer_info = get_peer_info()
    return [pid for pid in peer_info.keys() if pid != peer_id]

def main():
    # Example usage
    common_config = get_common_config()
    print("Common Config:", common_config)

    peer_info = get_peer_info()
    print("Peer Info:", peer_info)

    specific_peer = get_peer_by_id(1001)
    print("Peer 1001 Info:", specific_peer)

    neighbors = get_neighbors(1001)
    print("Neighbors of Peer 1001:", neighbors)

if __name__ == "__main__":
    main()