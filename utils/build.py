import yaml
import subprocess
import sys
import os

with open("/build/config.yaml") as f:
    config = yaml.safe_load(f)

apps = config.get("apps", [])

if not apps:
    print("No apps configured in config.yaml. Nothing to install.")
    sys.exit(0)

for app in apps:
    playbook = f"/apps/{app}/playbook.yaml"
    if not os.path.exists(playbook):
        print(f"ERROR: No playbook found for '{app}' at {playbook}")
        sys.exit(1)
    print(f"==> Installing {app}...")
    result = subprocess.run([
        "ansible-playbook", playbook,
        "-i", "localhost,",
        "--tags", "build"
    ])
    if result.returncode != 0:
        print(f"ERROR: Playbook for '{app}' failed.")
        sys.exit(1)

print("==> All apps installed successfully.")