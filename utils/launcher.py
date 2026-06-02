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


class LogWindow(tk.Toplevel):
    """A terminal-style output window for a single app.

    It is created on demand (when the user clicks "Logs") and populated
    from the in-memory buffer held by the Launcher.  If the user closes
    it and reopens it, the same buffer is replayed from scratch so no
    output is ever lost.
    """

    def __init__(self, parent, app_name, app_color):
        super().__init__(parent)
        self.title(f"{app_name} — output")
        self.configure(bg="#1e1e2e")
        self.geometry("720x420")
        self.resizable(True, True)
        self._build_ui(app_name, app_color)

    def _build_ui(self, app_name, app_color):
        # Header bar
        header = tk.Frame(self, bg="#181825", pady=8, padx=14)
        header.pack(fill=tk.X)

        tk.Label(header, text="●", bg="#181825", fg=app_color,
                 font=("monospace", 10)).pack(side=tk.LEFT)

        tk.Label(header, text=f"  {app_name}", bg="#181825", fg="#cdd6f4",
                 font=("monospace", 10, "bold")).pack(side=tk.LEFT)

        tk.Button(
            header, text="Clear", bg="#313244", fg="#6c7086",
            font=("monospace", 8), relief=tk.FLAT, padx=8, pady=2,
            cursor="hand2", command=self.clear,
        ).pack(side=tk.RIGHT)

        # Terminal text area
        text_frame = tk.Frame(self, bg="#1e1e2e")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(
            text_frame,
            bg="#11111b",
            fg="#cdd6f4",
            font=("monospace", 10),
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
            insertbackground="#cdd6f4",
            selectbackground="#45475a",
            padx=8,
            pady=6,
            spacing1=1,
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text.yview)

        # Color tags
        self.text.tag_config("stderr", foreground="#f38ba8")
        self.text.tag_config("stdout", foreground="#cdd6f4")
        self.text.tag_config("meta",   foreground="#6c7086", font=("monospace", 9))

    def append(self, line, stream="stdout"):
        """Append one line; must be called from the main thread."""
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, line, stream)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def load_buffer(self, buffer):
        """Bulk-insert all buffered (line, stream) entries at once."""
        self.text.config(state=tk.NORMAL)
        for line, stream in buffer:
            self.text.insert(tk.END, line, stream)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("researcher-deskless")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.processes   = {}   # name -> Popen
        self.log_buffers = {}   # name -> list[(line, stream)]  ← source of truth
        self.log_windows = {}   # name -> LogWindow | None (display only)
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

        self.buttons      = {}
        self.status_labels = {}

        for app in self.apps:
            name = app["name"]

            # Each app starts with an empty buffer
            self.log_buffers[name] = []

            frame = tk.Frame(btn_frame, bg="#313244", padx=16, pady=16)
            frame.pack(side=tk.LEFT, padx=10)

            tk.Label(
                frame,
                text=name,
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
            self.status_labels[name] = status

            tk.Button(
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
            ).pack()
            self.buttons[name] = frame.winfo_children()[-1]

            tk.Button(
                frame,
                text="Logs",
                bg="#45475a",
                fg="#cdd6f4",
                font=("sans-serif", 8),
                relief=tk.FLAT,
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda a=app: self._open_logs(a),
            ).pack(pady=(6, 0))

        tk.Label(
            self,
            text="Close this window to exit all apps",
            bg="#1e1e2e",
            fg="#45475a",
            font=("sans-serif", 8),
            pady=12,
        ).pack()

    # ------------------------------------------------------------------
    # Log window management
    # ------------------------------------------------------------------

    def _open_logs(self, app):
        """Open (or focus) the log window for this app.

        The window is created fresh each time the user requests it.
        All past output is replayed from the in-memory buffer, so
        nothing is ever lost even if the window was closed before.
        """
        name = app["name"]
        win  = self.log_windows.get(name)

        # If the window is already open, just bring it forward
        if win is not None:
            try:
                win.lift()
                win.focus_force()
                return
            except tk.TclError:
                pass  # window was destroyed by the user — recreate it below

        # Create a fresh window and populate it from the buffer
        win = LogWindow(self, name, app["color"])
        win.load_buffer(self.log_buffers[name])
        self.log_windows[name] = win

    def _live_append(self, app, line, stream):
        """Push one new line into the buffer and, if the window is open, into it too."""
        name = app["name"]

        # The buffer is the persistent record — always append here
        self.log_buffers[name].append((line, stream))

        # Forward to the window only if it currently exists
        win = self.log_windows.get(name)
        if win is not None:
            try:
                win.append(line, stream)
            except tk.TclError:
                # Window was closed between the check and the write — that's fine
                self.log_windows[name] = None

    # ------------------------------------------------------------------
    # Launch / process management
    # ------------------------------------------------------------------

    def _launch(self, app):
        name = app["name"]
        if name in self.processes and self.processes[name].poll() is None:
            self._set_status(name, "already running", "#f9e2af")
            return

        self._set_status(name, "starting...", "#89b4fa")
        self.buttons[name].config(state=tk.DISABLED)

        # Note: we deliberately do NOT open the log window here.
        # Output is collected silently in the buffer; the user can
        # open the log window whenever they want.

        def run():
            try:
                env = os.environ.copy()
                env.update(app.get("env", {}))

                proc = subprocess.Popen(
                    app["cmd"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # line-buffered so output arrives promptly
                )
                self.processes[name] = proc
                self.after(0, lambda: self._set_status(name, "running", "#a6e3a1"))

                # Two threads drain stdout and stderr concurrently so
                # neither pipe blocks the other
                stdout_t = threading.Thread(
                    target=self._stream_pipe,
                    args=(proc.stdout, app, "stdout"),
                    daemon=True,
                )
                stderr_t = threading.Thread(
                    target=self._stream_pipe,
                    args=(proc.stderr, app, "stderr"),
                    daemon=True,
                )
                stdout_t.start()
                stderr_t.start()

                proc.wait()
                stdout_t.join()
                stderr_t.join()

                self.after(0, lambda: self._on_exit(app))

            except FileNotFoundError:
                self.after(0, lambda: self._set_status(name, "not installed", "#f38ba8"))
                self.after(0, lambda: self.buttons[name].config(state=tk.NORMAL))

        threading.Thread(target=run, daemon=True).start()

    def _stream_pipe(self, pipe, app, stream):
        """Read lines from a pipe and schedule a buffer append on the main thread."""
        try:
            for line in pipe:
                # Use after() so all UI and buffer writes happen on the main thread
                self.after(0, lambda l=line, s=stream: self._live_append(app, l, s))
        except ValueError:
            pass  # pipe already closed

    def _on_exit(self, app):
        name = app["name"]
        self._set_status(name, "not running", "#6c7086")
        self.buttons[name].config(state=tk.NORMAL)
        # Record the exit marker in the buffer so it shows up whenever
        # the user opens the log window, even after the process is gone
        self._live_append(app, "\n[process exited]\n", "meta")

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