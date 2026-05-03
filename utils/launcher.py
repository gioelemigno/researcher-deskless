import tkinter as tk
import subprocess
import threading
import json
import os

APPS_DIR = "/opt/launcher/apps"

def load_apps():
    apps = []
    if not os.path.exists(APPS_DIR):
        return apps
    for f in sorted(os.listdir(APPS_DIR)):
        if f.endswith(".json"):
            with open(os.path.join(APPS_DIR, f)) as fh:
                apps.append(json.load(fh))
    return apps

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("researcher-deskless")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.processes = {}
        self.apps = load_apps()
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text="researcher-deskless",
            bg="#1e1e2e",
            fg="#cdd6f4",
            font=("sans-serif", 14, "bold"),
            pady=16,
        ).pack()

        tk.Label(
            self,
            text="Launch your research tools",
            bg="#1e1e2e",
            fg="#6c7086",
            font=("sans-serif", 9),
        ).pack()

        btn_frame = tk.Frame(self, bg="#1e1e2e", pady=20, padx=30)
        btn_frame.pack()

        self.buttons = {}
        self.status_labels = {}

        for app in self.apps:
            frame = tk.Frame(btn_frame, bg="#313244", padx=16, pady=16)
            frame.pack(side=tk.LEFT, padx=10)

            tk.Label(
                frame,
                text=app["name"],
                bg="#313244",
                fg="#cdd6f4",
                font=("sans-serif", 11, "bold"),
            ).pack()

            status = tk.Label(
                frame,
                text="not running",
                bg="#313244",
                fg="#6c7086",
                font=("sans-serif", 8),
            )
            status.pack(pady=(4, 8))
            self.status_labels[app["name"]] = status

            btn = tk.Button(
                frame,
                text="Launch",
                bg=app["color"],
                fg="white",
                font=("sans-serif", 9, "bold"),
                relief=tk.FLAT,
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda a=app: self._launch(a),
            )
            btn.pack()
            self.buttons[app["name"]] = btn

        tk.Label(
            self,
            text="Close this window to exit all apps",
            bg="#1e1e2e",
            fg="#45475a",
            font=("sans-serif", 8),
            pady=12,
        ).pack()

    def _launch(self, app):
        name = app["name"]
        if name in self.processes and self.processes[name].poll() is None:
            self._set_status(name, "already running", "#f9e2af")
            return

        self._set_status(name, "starting...", "#89b4fa")
        self.buttons[name].config(state=tk.DISABLED)

        def run():
            try:
                env = os.environ.copy()
                env.update(app.get("env", {}))

                proc = subprocess.Popen(
                    app["cmd"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.processes[name] = proc
                self.after(0, lambda: self._set_status(name, "running", "#a6e3a1"))
                proc.wait()
                self.after(0, lambda: self._on_exit(name))
            except FileNotFoundError:
                self.after(0, lambda: self._set_status(name, "not installed", "#f38ba8"))
                self.after(0, lambda: self.buttons[name].config(state=tk.NORMAL))

        threading.Thread(target=run, daemon=True).start()

    def _on_exit(self, name):
        self._set_status(name, "not running", "#6c7086")
        self.buttons[name].config(state=tk.NORMAL)

    def _set_status(self, name, text, color):
        self.status_labels[name].config(text=text, fg=color)

    def on_close(self):
        for proc in self.processes.values():
            if proc.poll() is None:
                proc.terminate()
        self.destroy()

if __name__ == "__main__":
    app = Launcher()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()