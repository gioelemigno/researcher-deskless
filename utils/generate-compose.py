import yaml
import sys
import os

with open("config.yaml") as f:
    config = yaml.safe_load(f)

apps = config.get("apps", [])

includes = ["compose.main.yaml"]

for app in apps:
    compose_fragment = f"apps/{app}/compose.yaml"
    if not os.path.exists(compose_fragment):
        print(f"ERROR: No compose fragment found for '{app}' at {compose_fragment}")
        sys.exit(1)
    includes.append(compose_fragment)
    
output = {"include": includes}

with open("compose.yaml", "w") as f:
    yaml.dump(output, f, default_flow_style=False)

print(f"==> compose.yaml generated with: {includes}")