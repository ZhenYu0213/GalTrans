

import os

import psutil


def get_dll():
    host_dll = "LunaHook/LunaHost32.dll"
    hook_dll = "LunaHook/LunaHook32.dll"
    return host_dll,hook_dll

def get_pids(exclude_system_processes=True):
    system_dirs = [
        os.environ.get("SystemRoot", r"C:\Windows") + r"\System32",
        os.environ.get("SystemRoot", r"C:\Windows") + r"\SysWOW64"
    ]
    
    exclude_names = {"svchost.exe", "System", "winlogon.exe", "lsass.exe", "services.exe"}
    
    pids = {}
    for p in psutil.process_iter(attrs=["pid", "name", "exe", "username"]):
        try:
            info = p.info
            if exclude_system_processes:
                if info["name"] in exclude_names:
                    continue
                if info["exe"] and any(info["exe"].startswith(path) for path in system_dirs):
                    continue

                if info["username"] and info["username"].lower() == "nt authority\\system":
                    continue

            pids[info["pid"]] = info["name"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass 

    return pids