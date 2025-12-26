from __future__ import annotations
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

@dataclass
class CmdResult:
    cmd: str
    returncode: int
    stdout: str
    stderr: str

def _env_for_subprocess(extra_env: Optional[dict] = None) -> dict:
    env = os.environ.copy()
    
    # Add common Homebrew paths to PATH if they exist (macOS)
    # Jupyter notebooks often don't inherit full PATH from launching shell
    homebrew_paths = [
        "/opt/homebrew/bin",  # Apple Silicon Macs
        "/usr/local/bin",    # Intel Macs / Linux
        "/opt/homebrew/sbin",
        "/usr/local/sbin",
    ]
    
    current_path = env.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    
    # Add Homebrew paths if they exist and aren't already in PATH
    for brew_path in homebrew_paths:
        if Path(brew_path).exists() and brew_path not in path_parts:
            path_parts.insert(0, brew_path)
    
    if path_parts != current_path.split(os.pathsep) if current_path else []:
        env["PATH"] = os.pathsep.join(path_parts)
    
    # Respect AWS_PROFILE if set (AWS CLI + boto3 will use it)
    if env.get("AWS_PROFILE", "").strip() == "":
        env.pop("AWS_PROFILE", None)
    if extra_env:
        env.update(extra_env)
    return env

def run(
    cmd: Union[str, Sequence[str]],
    cwd: Optional[str] = None,
    check: bool = True,
    stream: bool = True,
    extra_env: Optional[dict] = None,
) -> CmdResult:
    """
    Run a shell command with optional streaming output.
    - cmd can be a string or list of args.
    - stream=True prints output live and still captures it.
    """
    if isinstance(cmd, (list, tuple)):
        cmd_str = " ".join(shlex.quote(str(c)) for c in cmd)
        popen_args = list(cmd)
        shell = False
    else:
        cmd_str = cmd
        popen_args = cmd
        shell = True

    env = _env_for_subprocess(extra_env)

    proc = subprocess.Popen(
        popen_args,
        cwd=cwd,
        shell=shell,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    out_lines, err_lines = [], []
    assert proc.stdout and proc.stderr

    if stream:
        for line in proc.stdout:
            print(line, end="")
            out_lines.append(line)
        for line in proc.stderr:
            print(line, end="")
            err_lines.append(line)
    else:
        stdout, stderr = proc.communicate()
        out_lines.append(stdout or "")
        err_lines.append(stderr or "")

    rc = proc.wait()
    result = CmdResult(cmd=cmd_str, returncode=rc, stdout="".join(out_lines), stderr="".join(err_lines))

    if check and rc != 0:
        raise RuntimeError(f"Command failed (rc={rc}): {cmd_str}\n\nSTDERR:\n{result.stderr}")

    return result
