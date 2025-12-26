from __future__ import annotations
from typing import Optional
from ._shell import run
from ._validation import ok, warn, fail

def kubectl(*args: str, namespace: Optional[str] = None, check: bool = True, stream: bool = True):
    cmd = ["kubectl"]
    if namespace:
        cmd += ["-n", namespace]
    cmd += list(args)
    return run(cmd, check=check, stream=stream)

def namespace_exists(ns: str) -> bool:
    r = kubectl("get", "namespace", ns, check=False, stream=False)
    return r.returncode == 0

def require_namespace(ns: str) -> None:
    if not namespace_exists(ns):
        fail(f"Kubernetes namespace '{ns}' does not exist (did you deploy yet?)")
    ok(f"Namespace exists: {ns}")

def get_pods(ns: str) -> str:
    return kubectl("get", "pods", "-o", "wide", namespace=ns, stream=False).stdout

def wait_for_deployments_ready(ns: str, timeout: str = "10m") -> None:
    r = kubectl("wait", "--for=condition=available", "deployment", "--all", f"--timeout={timeout}",
                namespace=ns, check=False, stream=True)
    if r.returncode != 0:
        warn("Not all deployments became ready within timeout. Check pods/events.")
    else:
        ok("All deployments available.")
