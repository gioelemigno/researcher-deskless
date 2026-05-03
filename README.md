# researcher-deskless

> A portable Docker environment for researchers. Carry your full note-taking and reference management setup on a USB drive and run it on any Ubuntu machine.

A minimal GUI launcher lets you start any tool independently. The launcher stays open so you can run multiple apps at the same time.

---

## What's inside

| Tool | Purpose | Status |
|------|---------|--------|
| [Zotero](https://www.zotero.org/) | Reference manager — collect, organize, cite | ✅ Available |
| [Obsidian](https://obsidian.md/) | Knowledge base — notes, links, ideas | *Coming soon*|

All data lives on the drive. All tools run in Docker. No installation required on the host beyond Docker itself.

---

## Requirements

Every host machine needs:

- Ubuntu 22.04 or later
- Docker installed
- An X11 display (standard on Ubuntu with Xorg)
- Python3

---

## Project structure

```
researcher-deskless/
├── apps/
│   └── zotero/
│       ├── compose.yaml       ← Zotero compose fragment (volumes)
│       └── playbook.yaml      ← Zotero Ansible playbook (install + startup)
├── data/
│   └── zotero/                ← Zotero library and profile (auto-created)
├── utils/
│   ├── build.py               ← Runs playbooks at build time
│   ├── entrypoint.sh          ← Container entrypoint
│   ├── generate-compose.py    ← Generates compose.yaml from config.yaml
│   ├── launcher.py            ← GUI launcher
│   └── startup.py             ← Runs playbooks at startup
├── compose.main.yaml          ← Base compose file (generic, never edited)
├── compose.yaml               ← Generated from config.yaml, do not edit
├── config.yaml                ← Edit this to choose your apps
├── Dockerfile
├── LICENSE
├── Makefile
└── README.md
```

---

## Getting started

### 1. Clone the repository onto your USB drive

```bash
git clone https://github.com/yourusername/researcher-deskless.git /media/$USER/your-drive/
cd /media/$USER/your-drive/
```

### 2. Choose your apps

Edit `config.yaml` to select which apps to install:

```yaml
apps:
  - zotero
  # - obsidian
```

### 3. Build the Docker image

Do this once on any machine with internet access:

```bash
make build
```

This generates `compose.yaml`, builds the image, and saves it as `researcher-deskless.tar.gz` on the drive.

### 4. Run

On any Ubuntu machine:

```bash
make run
```

If the app list in `config.yaml` has changed since the last build, the image will be rebuilt automatically. If the image is not loaded on the current machine, it will be loaded from `researcher-deskless.tar.gz`. The launcher window will then open.

---

## The launcher

When you run `make run`, a small GUI launcher opens. From there you can start any installed tool with a single click. Each app runs as an independent process — the launcher stays open so you can run multiple tools at the same time or restart one if it crashes.

```
┌─────────────────────────────────────────┐
│          researcher-deskless            │
│       Launch your research tools        │
│                                         │
│  ┌───────────────┐  ┌────────────────┐  │
│  │    Zotero     │  │    Obsidian    │  │
│  │    running    │  │  not running   │  │
│  │  [ Launch ]   │  │  [ Launch ]    │  │
│  └───────────────┘  └────────────────┘  │
│                                         │
│  Close this window to exit all apps     │
└─────────────────────────────────────────┘
```

Closing the launcher terminates all running apps.

---

## Makefile targets

| Target | Description |
|--------|-------------|
| `make run` | Rebuild if config changed, load image if needed, start the launcher |
| `make build` | Generate compose, build image and save to tar |
| `make generate` | Generate compose.yaml from config.yaml |
| `make help` | Show available targets |

---

## How it works

The container starts as root, creates a user matching your host UID/GID, fixes ownership of the data directories, then drops privileges before launching the GUI launcher. This ensures your files on the drive are always owned by the correct user regardless of which machine you plug into.

Each app is fully self-contained in its `apps/<name>/` folder:

- `playbook.yaml` — declares apt packages, downloads and installs the app, registers it with the launcher, and handles startup setup
- `compose.yaml` — declares the app's volume mounts

```
USB drive
├── researcher-deskless.tar.gz  ──►  docker load
├── data/zotero/   ── -v mount ──►  /data/zotero   (inside container)
└── utils/launcher.py                    │
                                    Tkinter GUI
                                    ┌────┴─────┐
                                 Zotero    Obsidian
                                    └────┬─────┘
                                    X11 display  ──►  your screen
```

---

## Data and privacy

All your data stays on the drive under `data/`:

| App | Host path | Container path |
|-----|-----------|----------------|
| Zotero | `data/zotero/` | `/data/zotero` |
| Obsidian | `data/obsidian/` | `/data/obsidian` |

Nothing is written to the host machine except Docker's image cache, which is safe to clear with:

```bash
docker image rm researcher-deskless
```

---

## Adding a new app

1. Create `apps/<name>/playbook.yaml` with `build` and `startup` tagged plays
2. Create `apps/<name>/compose.yaml` with the app's volume mounts
3. Add the app name to `config.yaml`
4. Run `make build`

The `playbook.yaml` structure:

```yaml
- name: Install MyApp
  hosts: localhost
  connection: local
  tags: build
  tasks:
    - name: Install apt dependencies
      apt:
        name: [...]
        state: present

    - name: Register with launcher
      copy:
        dest: /opt/launcher/apps/myapp.json
        content: |
          {
            "name": "MyApp",
            "cmd": ["/opt/myapp/myapp", "--no-sandbox"],
            "color": "#hexcolor",
            "env": {}
          }

- name: Setup MyApp at startup
  hosts: localhost
  connection: local
  tags: startup
  tasks:
    - name: Create data directories
      file:
        path: /data/myapp
        state: directory
        owner: "{{ lookup('env', 'PUID') }}"
        group: "{{ lookup('env', 'PGID') }}"
        mode: '0755'
```

---

## Roadmap

- [x] Zotero 9
- [ ] Obsidian
- [x] GUI launcher
- [x] Ansible-based app management
- [x] Config-driven builds

---

## Contributing

Pull requests are welcome. If something does not work on your machine, open an issue with your Ubuntu version and the output of `make run`.

---

## License

MIT