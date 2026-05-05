import yaml
import sys
import os
from pathlib import Path

with open("config.yaml") as f:
    config = yaml.safe_load(f)

apps = config.get("apps", [])

includes = ["compose.main.yaml"]

dir_script = Path(__file__).resolve().parent

for app in apps:
    compose_fragment = f"apps/{app}/compose.yaml"
    if not os.path.exists(compose_fragment):
        print(f"ERROR: No compose fragment found for '{app}' at {compose_fragment}")
        sys.exit(1)
    includes.append(compose_fragment)
    dir_data_app = Path(dir_script / Path(f"../data/{app}")).resolve()
    os.makedirs(dir_data_app, exist_ok=True)

output = {"include": includes}

with open("compose.yaml", "w") as f:
    yaml.dump(output, f, default_flow_style=False)

print(f"==> compose.yaml generated with: {includes}")