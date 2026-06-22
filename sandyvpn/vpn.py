"""OpenVPN 3 session helpers."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from datetime import datetime


def _run_openvpn3(
    args: list[str],
    stdin: str | None = None,
    on_output: Callable[[str], None] | None = None,
) -> tuple[int, str]:
    proc = subprocess.Popen(
        ["openvpn3", *args],
        stdin=subprocess.PIPE if stdin is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if stdin is not None:
        assert proc.stdin is not None
        proc.stdin.write(stdin)
        proc.stdin.close()

    assert proc.stdout is not None
    lines: list[str] = []
    for line in proc.stdout:
        lines.append(line)
        if on_output is not None:
            on_output(line)

    return proc.wait(), "".join(lines)


def start_session(
    config_name: str,
    username: str,
    password: str,
    on_output: Callable[[str], None] | None = None,
) -> tuple[int, str]:
    """Start an OpenVPN 3 session in the background, piping credentials on stdin."""
    return _run_openvpn3(
        ["session-start", "--config", config_name, "--background"],
        stdin=f"{username}\n{password}\n",
        on_output=on_output,
    )


def disconnect_session(config_name: str) -> tuple[int, str]:
    """Disconnect a running VPN session."""
    return _run_openvpn3(["session-manage", "--config", config_name, "--disconnect"])


def restart_session(config_name: str) -> tuple[int, str]:
    """Disconnect and reconnect a running VPN session."""
    return _run_openvpn3(["session-manage", "--config", config_name, "--restart"])


def get_session_stats(config_name: str) -> tuple[int, str]:
    """Fetch live statistics for a running VPN session."""
    return _run_openvpn3(["session-stats", "--config", config_name])


def session_is_active(config_name: str) -> bool:
    code, _ = get_session_stats(config_name)
    return code == 0


_CREATED_RE = re.compile(r"Created:\s*(.+?)(?:\s+PID:|\s*$)", re.MULTILINE)
_CONFIG_NAME_RE = re.compile(r"Config name:\s*(.+)", re.MULTILINE)
_CREATED_FMT = "%a %b %d %H:%M:%S %Y"


def _parse_session_blocks(output: str) -> list[str]:
    return [block for block in re.split(r"-{20,}", output) if block.strip()]


def _config_name_matches(listed_name: str, config_name: str) -> bool:
    listed_name = listed_name.strip()
    if listed_name == config_name:
        return True
    # Renamed profiles: "newname (was: oldname)"
    return f"(was: {config_name})" in listed_name


def get_session_started_at(config_name: str) -> datetime | None:
    """Return when the running session was created, from ``openvpn3 sessions-list``."""
    code, output = _run_openvpn3(["sessions-list"])
    if code != 0:
        return None

    for block in _parse_session_blocks(output):
        config_match = _CONFIG_NAME_RE.search(block)
        if config_match is None or not _config_name_matches(config_match.group(1), config_name):
            continue
        created_match = _CREATED_RE.search(block)
        if created_match is None:
            continue
        try:
            return datetime.strptime(created_match.group(1).strip(), _CREATED_FMT)
        except ValueError:
            continue
    return None
