from pathlib import Path
from configparser import ConfigParser

# Resolve project root (the folder this script is in)
project_root = Path(__file__).resolve().parent.parent
cfg_path = project_root / "Common.cfg"

if not cfg_path.exists():
    raise FileNotFoundError(f"Config file not found at: {cfg_path}")

config = ConfigParser()
config.read(cfg_path)

if not config.has_section("GLOBALINFO"):
    raise KeyError(f"Section 'GLOBALINFO' not found. Available sections: {config.sections()}")

NumberOfPreferredNeighbors = config.get("GLOBALINFO", "NumberOfPreferredNeighbors")
common_dict = dict(config.items("GLOBALINFO"))
print(common_dict)
print(f"Loaded from: {cfg_path}")