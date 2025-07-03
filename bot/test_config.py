import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
cfg_path = os.path.join(script_dir, "config.json")

with open(cfg_path) as f:
    config = json.load(f)

print("✅ Loaded config:", config)
