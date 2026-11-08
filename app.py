import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

UPSTREAM_INSTALL_PS1 = "https://raw.githubusercontent.com/robertnisipeanu/mgu-store/main/deploy/install.ps1"


def powershell_exe():
    return shutil.which("powershell.exe") or shutil.which("powershell") or "powershell.exe"


def run_powershell(script, elevated=False):
    encoded = __import__("base64").b64encode(script.encode("utf-16le")).decode("ascii")
    args = [powershell_exe(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]
    if elevated:
        # Elevate only the Windows optional-feature installation operation.
        args = [powershell_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                "Start-Process PowerShell.exe -Verb RunAs -Wait -ArgumentList " +
                "'-NoProfile -ExecutionPolicy Bypass -EncodedCommand " + encoded + "'"]
    return subprocess.run(args, text=True, capture_output=True, encoding="utf-8", errors="replace")


class InstallerApp:
    def __init__(self, root):
        self.root = root
        root.title("MGU Store Installer")
        root.geometry("720x570")
        root.minsize(620, 500)

        outer = ttk.Frame(root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="MGU Store Installer", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Windows 10/11 · Official upstream installer · Existing root SSH key required",
                  foreground="#555").pack(anchor="w", pady=(2, 14))

        keyrow = ttk.Frame(outer)
        keyrow.pack(fill="x", pady=5)
        ttk.Label(keyrow, text="Root SSH private key", width=20).pack(side="left")
        self.key_var = tk.StringVar(value=str(Path.home() / ".ssh" / "id_rsa"))
        ttk.Entry(keyrow, textvariable=self.key_var).pack(side="left", fill="x", expand=True)
        ttk.Button(keyrow, text="Browse…", command=self.pick_key).pack(side="left", padx=(8, 0))

        hostrow = ttk.Frame(outer)
        hostrow.pack(fill="x", pady=5)
        ttk.Label(hostrow, text="MGU IP (optional)", width=20).pack(side="left")
        self.host_var = tk.StringVar()
        ttk.Entry(hostrow, textvariable=self.host_var).pack(side="left", fill="x", expand=True)
        ttk.Label(outer, text="Leave IP blank for upstream head-unit discovery (ENET / MGU hotspot).",
                  foreground="#555").pack(anchor="w", pady=(0, 8))

        self.install_btn = ttk.Button(outer, text="Install MGU Store", command=self.start_install)
        self.install_btn.pack(anchor="w", pady=(8, 10))

        ttk.Label(outer, text="Output").pack(anchor="w")
        self.output = scrolledtext.ScrolledText(outer, height=16, wrap="word", state="disabled",
                                                font=("Consolas", 9))
        self.output.pack(fill="both", expand=True, pady=(4, 8))
        self.status = tk.StringVar(value="Ready")
        ttk.Label(outer, textvariable=self.status, foreground="#555").pack(anchor="w")

        self.log("Ready. Connect this PC to the MGU, select the existing root private key, then install.")
        self.log("Important: vehicle must be parked and have stable power.")

    def pick_key(self):
        chosen = filedialog.askopenfilename(title="Select existing root SSH private key",
            initialdir=str(Path.home() / ".ssh"),
            filetypes=[("SSH private keys", "*"), ("All files", "*")])
        if chosen:
            self.key_var.set(chosen)

    def log(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def set_busy(self, busy):
        self.install_btn.configure(state="disabled" if busy else "normal")
        self.status.set("Working…" if busy else "Ready")

    def start_install(self):
        key = Path(self.key_var.get()).expanduser()
        host = self.host_var.get().strip()
        if not key.is_file():
            messagebox.showerror("SSH key required", "Select an existing root SSH private key file.")
            return
        if not messagebox.askyesno("Confirm installation",
            "Confirm all of the following:\n\n"
            "• The vehicle is parked and has stable power.\n"
            "• This PC can reach the MGU over ENET / hotspot / configured network.\n"
            "• The selected key is the existing authorized root SSH private key.\n\n"
            "Continue with the official first-install operation?"):
            return
        self.set_busy(True)
        threading.Thread(target=self.install_worker, args=(str(key), host), daemon=True).start()

    def install_worker(self, key, host):
        try:
            ssh = shutil.which("ssh.exe") or shutil.which("ssh")
            if not ssh:
                self.log("OpenSSH Client not found. Requesting Windows optional-feature installation…")
                ps = ("$ErrorActionPreference='Stop'; "
                      "Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0 | Out-String")
                result = run_powershell(ps, elevated=True)
                if result.stdout:
                    self.log(result.stdout)
                if result.stderr:
                    self.log(result.stderr)
                if result.returncode != 0:
                    raise RuntimeError("Could not install OpenSSH Client. Re-run as administrator or install it in Windows Settings.")
                ssh = shutil.which("ssh.exe") or shutil.which("ssh")
                if not ssh:
                    raise RuntimeError("OpenSSH installation completed but ssh.exe is not on PATH. Restart the app and try again.")
                self.log("OpenSSH Client is available.")

            self.log("Downloading and running the upstream install.ps1…")
            # Use the upstream script as documented. Arguments are passed as an array,
            # avoiding shell interpolation of user-supplied paths or hostnames.
            args = ["first-install", "--identity", key]
            if host:
                args += ["--host", host]
            ps_args = ", ".join("'" + value.replace("'", "''") + "'" for value in args)
            ps = (
                "$ErrorActionPreference='Stop'; "
                f"$u='{UPSTREAM_INSTALL_PS1}'; "
                "$s=Invoke-RestMethod -Uri $u; "
                "$sb=[scriptblock]::Create($s); "
                f"$a=@({ps_args}); "
                "$global:LASTEXITCODE=1; "
                "& $sb @a; "
                "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
            )
            result = run_powershell(ps)
            if result.stdout:
                self.log(result.stdout)
            if result.stderr:
                self.log(result.stderr)
            if result.returncode != 0:
                raise RuntimeError(f"Installer exited with code {result.returncode}. See output above.")
            self.log("Installer finished successfully.")
            self.root.after(0, lambda: messagebox.showinfo("Finished",
                "The upstream installer completed successfully. Follow any restart prompt shown in the output."))
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            self.root.after(0, lambda e=str(exc): messagebox.showerror("Installation failed", e))
        finally:
            self.root.after(0, lambda: self.set_busy(False))


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
