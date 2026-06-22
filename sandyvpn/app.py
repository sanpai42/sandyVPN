"""SandyVPN — simple GUI for OpenVPN 3 session-start."""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from sandyvpn.glow import TopBanner
from sandyvpn.mascot import GingerCatMascot
from sandyvpn.storage import (
    Credentials,
    clear_credentials,
    credentials_exist,
    has_stored_password,
    load_profile,
    save_credentials,
    unlock_password,
)
from sandyvpn.theme import BG, ScrolledText, apply_theme, style_text_widget
from sandyvpn.vpn import (
    disconnect_session,
    get_session_started_at,
    get_session_stats,
    restart_session,
    session_is_active,
    start_session,
)

STATUS_POLL_MS = 10_000
UPTIME_TICK_MS = 1_000
PASSWORD_PLACEHOLDER = "•" * 20


def _format_duration(seconds: int) -> str:
    hours, rem = divmod(max(0, seconds), 3600)
    minutes, secs = divmod(rem, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class SandyVPNApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SandyVPN")
        self.root.minsize(520, 480)
        self._busy = False
        self._connected = False
        self._active_config = ""
        self._status_timer_id: str | None = None
        self._uptime_timer_id: str | None = None
        self._connected_since: datetime | None = None

        apply_theme(root)
        self._build_ui()
        self._set_busy(False)
        self._load_saved_credentials()
        self._check_existing_session()

    def _build_ui(self) -> None:
        self.frame = ttk.Frame(self.root, padding=12)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.top_banner = TopBanner(self.frame)
        self.top_banner.grid(row=0, column=0, sticky=tk.EW, pady=(0, 12))

        self.mascot = GingerCatMascot()
        self.mascot.set_mood(False)
        self.top_banner.set_mascot(self.mascot)

        self.setup_frame = ttk.Frame(self.frame)
        self.setup_frame.grid(row=1, column=0, sticky=tk.NSEW)

        field_pad = (0, 8)
        ttk.Label(self.setup_frame, text="Config name").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=(0, 4))
        ttk.Label(self.setup_frame, text="Auth username").grid(row=0, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 4))
        ttk.Label(self.setup_frame, text="Auth password").grid(row=0, column=2, sticky=tk.W, pady=(0, 4))

        self.config_var = tk.StringVar()
        self.config_entry = ttk.Entry(self.setup_frame, textvariable=self.config_var, width=18)
        self.config_entry.grid(row=1, column=0, sticky=tk.EW, padx=(0, 8), pady=field_pad)

        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.setup_frame, textvariable=self.username_var, width=18)
        self.username_entry.grid(row=1, column=1, sticky=tk.EW, padx=(0, 8), pady=field_pad)

        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.setup_frame, textvariable=self.password_var, show="•", width=18)
        self.password_entry.grid(row=1, column=2, sticky=tk.EW, pady=field_pad)
        self.password_entry.bind("<FocusIn>", self._on_password_focus_in)
        self.password_entry.bind("<Key>", self._on_password_key, add="+")

        setup_btn_row = ttk.Frame(self.setup_frame)
        setup_btn_row.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 12))

        self.connect_btn = ttk.Button(
            setup_btn_row, text="Connect", style="Accent.TButton", command=self._on_connect
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.save_btn = ttk.Button(setup_btn_row, text="Save credentials", command=self._on_save)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.clear_btn = ttk.Button(setup_btn_row, text="Clear saved", command=self._on_clear)
        self.clear_btn.pack(side=tk.LEFT)

        self.status_frame = ttk.LabelFrame(self.frame, text="VPN status", padding=8)
        self.status_frame.grid(row=2, column=0, sticky=tk.NSEW, pady=(0, 12))
        self.status_frame.grid_remove()

        self.status_summary_var = tk.StringVar(value="Not connected")
        ttk.Label(self.status_frame, textvariable=self.status_summary_var).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8)
        )

        self.status_text = ScrolledText(self.status_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.status_text.grid(row=1, column=0, sticky=tk.NSEW, pady=(0, 8))
        style_text_widget(self.status_text)

        status_btn_row = ttk.Frame(self.status_frame)
        status_btn_row.grid(row=2, column=0, sticky=tk.W)

        self.disconnect_btn = ttk.Button(status_btn_row, text="Disconnect", command=self._on_disconnect)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.reconnect_btn = ttk.Button(
            status_btn_row, text="Reconnect", style="Accent.TButton", command=self._on_reconnect
        )
        self.reconnect_btn.pack(side=tk.LEFT)

        ttk.Label(self.frame, text="Log").grid(row=3, column=0, sticky=tk.W, pady=(0, 4))
        self.output = ScrolledText(self.frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.output.grid(row=4, column=0, sticky=tk.NSEW)
        style_text_widget(self.output)

        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(4, weight=1)
        for col in range(3):
            self.setup_frame.columnconfigure(col, weight=1)
        self.status_frame.columnconfigure(0, weight=1)
        self.status_frame.rowconfigure(1, weight=1)
        self._update_credential_buttons()

    def _password_is_placeholder(self) -> bool:
        return self.password_var.get() == PASSWORD_PLACEHOLDER

    def _show_password_placeholder(self) -> None:
        self.password_var.set(PASSWORD_PLACEHOLDER)

    def _clear_password_field(self) -> None:
        self.password_var.set("")

    def _purge_password_from_ui(self) -> None:
        if credentials_exist() and has_stored_password():
            self._show_password_placeholder()
        else:
            self._clear_password_field()

    def _get_typed_password(self) -> str | None:
        value = self.password_var.get()
        if not value or value == PASSWORD_PLACEHOLDER:
            return None
        return value

    def _on_password_focus_in(self, _event: tk.Event) -> None:
        if self._password_is_placeholder():
            self._clear_password_field()

    def _on_password_key(self, _event: tk.Event) -> None:
        if self._password_is_placeholder():
            self._clear_password_field()

    def _update_credential_buttons(self) -> None:
        if credentials_exist():
            self.save_btn.pack_forget()
            self.clear_btn.pack(side=tk.LEFT)
        else:
            self.clear_btn.pack_forget()
            self.save_btn.pack(side=tk.LEFT, padx=(0, 8))

    def _load_saved_credentials(self) -> None:
        profile = load_profile()
        if profile is None:
            return
        self.config_var.set(profile.config_name)
        self.username_var.set(profile.username)
        self._purge_password_from_ui()
        self._update_credential_buttons()
        if has_stored_password():
            self._append_output("Loaded saved profile. Password stays encrypted until connect.\n")
        else:
            self._append_output("Loaded saved profile.\n")

    def _resolve_connect_auth(self) -> tuple[str, str, str] | None:
        config_name = self.config_var.get().strip()
        username = self.username_var.get().strip()
        typed_password = self._get_typed_password()

        if not config_name:
            messagebox.showwarning("Missing config", "Enter a configuration profile name.")
            return None
        if not username:
            messagebox.showwarning("Missing username", "Enter an auth username.")
            return None

        if typed_password:
            password = typed_password
            self._purge_password_from_ui()
            if not credentials_exist():
                save_credentials(Credentials(config_name, username, password))
                self._update_credential_buttons()
            return config_name, username, password

        password = unlock_password()
        if password is None:
            messagebox.showwarning(
                "Missing password",
                "Enter a password, or save credentials first.",
            )
            return None
        return config_name, username, password

    def _resolve_save_auth(self) -> Credentials | None:
        if credentials_exist():
            return None
        config_name = self.config_var.get().strip()
        username = self.username_var.get().strip()
        password = self._get_typed_password()

        if not config_name:
            messagebox.showwarning("Missing config", "Enter a configuration profile name.")
            return None
        if not username:
            messagebox.showwarning("Missing username", "Enter an auth username.")
            return None
        if not password:
            messagebox.showwarning("Missing password", "Enter an auth password to save.")
            return None
        return Credentials(config_name=config_name, username=username, password=password)

    def _check_existing_session(self) -> None:
        config_name = self.config_var.get().strip()
        if not config_name:
            return

        def run() -> None:
            if not session_is_active(config_name):
                return
            started_at = get_session_started_at(config_name)
            self.root.after(
                0,
                lambda c=config_name, s=started_at: self._enter_connected_state(c, started_at=s),
            )

        threading.Thread(target=run, daemon=True).start()

    def _on_save(self) -> None:
        creds = self._resolve_save_auth()
        if creds is None:
            return
        save_credentials(creds)
        self._purge_password_from_ui()
        self._update_credential_buttons()
        self._append_output("Credentials saved (password encrypted on disk).\n")

    def _on_clear(self) -> None:
        if not messagebox.askyesno("Clear credentials", "Remove saved credentials and clear the form?"):
            return
        clear_credentials()
        self.config_var.set("")
        self.username_var.set("")
        self._purge_password_from_ui()
        self._update_credential_buttons()
        self._append_output("Saved credentials cleared.\n")

    def _on_connect(self) -> None:
        if self._busy:
            return
        auth = self._resolve_connect_auth()
        if auth is None:
            return

        config_name, username, password = auth
        self._set_busy(True)
        self._append_output(f"\nStarting session for config '{config_name}'...\n")

        def run() -> None:
            def append_line(line: str) -> None:
                self.root.after(0, lambda: self._append_output(line))

            session_password = password
            try:
                code, _ = start_session(
                    config_name,
                    username,
                    session_password,
                    on_output=append_line,
                )
                if code == 0:
                    self.root.after(
                        0,
                        lambda: self._enter_connected_state(config_name, "Session started.\n"),
                    )
                else:
                    self.root.after(
                        0,
                        lambda: self._append_output(f"\nSession start failed with code {code}.\n"),
                    )
            except FileNotFoundError:
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "openvpn3 not found",
                        "Could not find the openvpn3 command. Is OpenVPN 3 installed?",
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("Connection error", str(exc)))
            finally:
                session_password = ""
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=run, daemon=True).start()

    def _on_disconnect(self) -> None:
        if self._busy or not self._connected:
            return
        if not messagebox.askyesno("Disconnect", f"Disconnect VPN session '{self._active_config}'?"):
            return

        self._set_busy(True)
        self._append_output(f"\nDisconnecting '{self._active_config}'...\n")

        def run() -> None:
            try:
                code, output = disconnect_session(self._active_config)
                self.root.after(0, lambda: self._append_output(output))
                if code == 0:
                    self.root.after(0, self._enter_disconnected_state)
                    self.root.after(0, lambda: self._append_output("Disconnected.\n"))
                else:
                    self.root.after(
                        0,
                        lambda: messagebox.showerror("Disconnect failed", output or f"Exit code {code}"),
                    )
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("Disconnect error", str(exc)))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=run, daemon=True).start()

    def _on_reconnect(self) -> None:
        if self._busy or not self._connected:
            return

        self._set_busy(True)
        self._append_output(f"\nReconnecting '{self._active_config}'...\n")

        def run() -> None:
            try:
                code, output = restart_session(self._active_config)
                self.root.after(0, lambda: self._append_output(output))
                if code == 0:
                    self.root.after(
                        0,
                        lambda: self._append_output("Reconnect triggered successfully.\n"),
                    )
                    started_at = get_session_started_at(self._active_config)
                    self.root.after(0, lambda s=started_at: self._reset_uptime(s))
                    self.root.after(0, self._refresh_status)
                else:
                    self.root.after(
                        0,
                        lambda: messagebox.showerror("Reconnect failed", output or f"Exit code {code}"),
                    )
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("Reconnect error", str(exc)))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=run, daemon=True).start()

    def _set_connected_look(self, active: bool) -> None:
        self.top_banner.set_connected(active)

    def _enter_connected_state(
        self,
        config_name: str,
        message: str = "",
        started_at: datetime | None = None,
    ) -> None:
        self._connected = True
        self._active_config = config_name
        self._purge_password_from_ui()
        self.status_frame.grid()
        self._set_credentials_enabled(False)
        self.status_summary_var.set(f"Connected — {config_name}")
        self.mascot.set_mood(True)
        self._set_connected_look(True)
        self._reset_uptime(started_at)
        if message:
            self._append_output(message)
        self._refresh_status()
        self._schedule_status_poll()
        self._set_busy(False)

    def _enter_disconnected_state(self) -> None:
        self._connected = False
        self._active_config = ""
        self._cancel_status_poll()
        self._stop_uptime_counter()
        self.status_frame.grid_remove()
        self._set_credentials_enabled(True)
        self.status_summary_var.set("Not connected")
        self.top_banner.set_uptime_text("")
        self.mascot.set_mood(False)
        self._set_connected_look(False)
        self._set_status_text("")
        self._purge_password_from_ui()
        self._update_credential_buttons()
        self._set_busy(False)

    def _reset_uptime(self, started_at: datetime | None = None) -> None:
        self._cancel_uptime_timer()
        self._connected_since = started_at or datetime.now()
        self._update_uptime_display()
        self._uptime_timer_id = self.root.after(UPTIME_TICK_MS, self._tick_uptime)

    def _cancel_uptime_timer(self) -> None:
        if self._uptime_timer_id is not None:
            self.root.after_cancel(self._uptime_timer_id)
            self._uptime_timer_id = None

    def _stop_uptime_counter(self) -> None:
        self._cancel_uptime_timer()
        self._connected_since = None

    def _tick_uptime(self) -> None:
        if not self._connected or self._connected_since is None:
            return
        self._update_uptime_display()
        self._uptime_timer_id = self.root.after(UPTIME_TICK_MS, self._tick_uptime)

    def _update_uptime_display(self) -> None:
        if self._connected_since is None:
            self.top_banner.set_uptime_text("")
            return
        elapsed = int((datetime.now() - self._connected_since).total_seconds())
        self.top_banner.set_uptime_text(f"Connected for: {_format_duration(elapsed)}")

    def _set_credentials_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.config_entry.config(state=state)
        self.username_entry.config(state=state)
        self.password_entry.config(state=state)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.reconnect_btn.config(state=tk.DISABLED)
            return

        if self._connected:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.reconnect_btn.config(state=tk.NORMAL)
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.reconnect_btn.config(state=tk.DISABLED)

    def _schedule_status_poll(self) -> None:
        self._cancel_status_poll()
        self._status_timer_id = self.root.after(STATUS_POLL_MS, self._poll_status)

    def _cancel_status_poll(self) -> None:
        if self._status_timer_id is not None:
            self.root.after_cancel(self._status_timer_id)
            self._status_timer_id = None

    def _poll_status(self) -> None:
        if not self._connected:
            return
        self._refresh_status()
        self._schedule_status_poll()

    def _refresh_status(self) -> None:
        if not self._connected:
            return

        config_name = self._active_config

        def run() -> None:
            try:
                code, output = get_session_stats(config_name)
                timestamp = datetime.now().strftime("%H:%M:%S")
                if code == 0:
                    text = f"Updated {timestamp}\n\n{output.strip()}\n"
                    self.root.after(0, lambda: self._set_status_text(text))
                    self.root.after(
                        0,
                        lambda: self.status_summary_var.set(f"Connected — {config_name} (updated {timestamp})"),
                    )
                else:
                    text = f"Updated {timestamp}\n\nSession no longer active.\n{output.strip()}\n"
                    self.root.after(0, lambda: self._set_status_text(text))
                    self.root.after(0, self._enter_disconnected_state)
                    self.root.after(0, lambda: self._append_output("VPN session ended.\n"))
            except Exception as exc:  # noqa: BLE001
                self.root.after(
                    0,
                    lambda: self._set_status_text(f"Failed to fetch status: {exc}\n"),
                )

        threading.Thread(target=run, daemon=True).start()

    def _set_status_text(self, text: str) -> None:
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, text)
        self.status_text.config(state=tk.DISABLED)

    def _append_output(self, text: str) -> None:
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)


def main() -> None:
    root = tk.Tk()
    SandyVPNApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
