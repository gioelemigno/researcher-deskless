import tkinter as tk
from tkinter import ttk
import subprocess
import threading

APPS = [
    {
        "name": "Zotero",
        "cmd": ["/opt/zotero/zotero", "-profile", "/zotero-data/profile", "-no-remote", "--no-sandbox"],
        "color": "#CC2936",
    },
    {
        "name": "Obsidian",
        "cmd": ["/opt/obsidian/obsidian", "--no-sandbox"],
        "color": "#7B68EE",
    },
]

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("researcher-deskless")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.processes = {}
        self._build_ui()

    def _build_ui(self):
        # Header
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

        # App buttons
        btn_frame = tk.Frame(self, bg="#1e1e2e", pady=20, padx=30)
        btn_frame.pack()

        self.buttons = {}
        self.status_labels = {}

        for app in APPS:
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

        # Footer
        tk.Label(
            self,
            text="Apps run independently — close this window to exit all",
            bg="#1e1e2e",
            fg="#45475a",
            font=("sans-serif", 8),
            pady=12,
        ).pack()

    def _launch(self, app):
        name = app["name"]

        # If already running, do nothing
        if name in self.processes and self.processes[name].poll() is None:
            self._set_status(name, "already running", "#f9e2af")
            return

        self._set_status(name, "starting...", "#89b4fa")
        self.buttons[name].config(state=tk.DISABLED)

        def run():
            try:
                proc = subprocess.Popen(
                    app["cmd"],
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
        for name, proc in self.processes.items():
            if proc.poll() is None:
                proc.terminate()
        self.destroy()


if __name__ == "__main__":
    app = Launcher()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()