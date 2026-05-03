import yaml
import subprocess
import sys
import os

with open("/build/config.yaml") as f:
    config = yaml.safe_load(f)

apps = config.get("apps", [])

for app in apps:
    playbook = f"/apps/{app}/playbook.yaml"
    if not os.path.exists(playbook):
        print(f"ERROR: No playbook found for '{app}'")
        sys.exit(1)
    print(f"==> Startup tasks for {app}...")
    subprocess.run([
        "ansible-playbook", playbook,
        "-i", "localhost,",
        "--tags", "startup"
    ])

print("==> Startup complete.")