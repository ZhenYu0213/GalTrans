

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
            # 過濾條件
            if exclude_system_processes:
                # 根據進程名稱排除
                if info["name"] in exclude_names:
                    continue
                
                # 根據路徑排除
                if info["exe"] and any(info["exe"].startswith(path) for path in system_dirs):
                    continue
                
                # 根據用戶排除 (例如 SYSTEM)
                if info["username"] and info["username"].lower() == "nt authority\\system":
                    continue
            
            # 如果通過過濾，加入結果
            pids[info["pid"]] = info["name"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # 忽略無法訪問的進程

    return pids