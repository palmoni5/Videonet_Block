import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import random
import hashlib
import json
import shutil
import time

# --- מפתח סודי ---
SECRET_SALT = "GhostSystemKey2025"

# ==========================================
# 1. תצורת הרשת: סוכני משתמש (User Agents)
# תפקיד: חסימת וידאו, יוטיוב וקבצים
# ==========================================
USER_AGENTS_NETWORK = [
    {
        "id": 0,
        "path": "/Users/Shared/.Config/sys_net_daemon", 
        "plist_path": "/Library/LaunchAgents/com.apple.sys.net.daemon.plist",
        "label": "com.apple.sys.net.daemon"
    },
    {
        "id": 1,
        "path": "/Users/Shared/.Config/sys_update_service",
        "plist_path": "/Library/LaunchAgents/com.apple.sys.update.helper.plist",
        "label": "com.apple.sys.update.helper"
    },
    {
        "id": 2,
        "path": "/Users/Shared/.Config/kernel_audit_d",
        "plist_path": "/Library/LaunchAgents/com.apple.kernel.audit.plist",
        "label": "com.apple.kernel.audit"
    },
    {
        "id": 3,
        "path": "/Users/Shared/.Config/mdworker_sys_ext",
        "plist_path": "/Library/LaunchAgents/com.apple.mdworker.sys.ext.plist",
        "label": "com.apple.mdworker.sys.ext"
    },
    {
        "id": 4,
        "path": "/Users/Shared/.Config/core_audio_d",
        "plist_path": "/Library/LaunchAgents/com.apple.core.audio.daemon.plist",
        "label": "com.apple.core.audio.daemon"
    }
]

# ==========================================
# 2. תצורת הרשת: שוטרי רוט (Root Daemons)
# תפקיד: חסימת אינטרנט, חסימת הגדרות, אבטחת המעגל
# ==========================================
ROOT_DAEMON_NETWORK = [
    {
        "id": 0,
        "path": "/Library/PrivilegedHelperTools/com.apple.net.shield.daemon",
        "plist_path": "/Library/LaunchDaemons/com.apple.net.shield.daemon.plist",
        "label": "com.apple.net.shield.daemon"
    },
    {
        "id": 1,
        "path": "/Library/PrivilegedHelperTools/com.apple.sys.firewall.guard",
        "plist_path": "/Library/LaunchDaemons/com.apple.sys.firewall.guard.plist",
        "label": "com.apple.sys.firewall.guard"
    },
    {
        "id": 2,
        "path": "/Library/PrivilegedHelperTools/com.apple.network.integrity",
        "plist_path": "/Library/LaunchDaemons/com.apple.network.integrity.plist",
        "label": "com.apple.network.integrity"
    },
    {
        "id": 3,
        "path": "/Library/PrivilegedHelperTools/com.apple.wifi.secure.helper",
        "plist_path": "/Library/LaunchDaemons/com.apple.wifi.secure.helper.plist",
        "label": "com.apple.wifi.secure.helper"
    },
    {
        "id": 4,
        "path": "/Library/PrivilegedHelperTools/com.apple.packet.filter.d",
        "plist_path": "/Library/LaunchDaemons/com.apple.packet.filter.d.plist",
        "label": "com.apple.packet.filter.d"
    }
]

USER_NET_JSON = json.dumps(USER_AGENTS_NETWORK)
ROOT_NET_JSON = json.dumps(ROOT_DAEMON_NETWORK)

# ==========================================
# 3. קוד ה-ROOT (השוטר הגדול)
# כולל: PFCTL (אינטרנט), KILL SETTINGS, RESURRECT
# ==========================================
ROOT_ENFORCER_LOGIC = r"""
import subprocess
import time
import os
import json
import sys

MY_ID = __MY_ID_PLACEHOLDER__
USER_CONFIG = __USER_NET_JSON_PLACEHOLDER__
ROOT_CONFIG = __ROOT_NET_JSON_PLACEHOLDER__
MY_CODE_TEMPLATE = __ROOT_REPR_PLACEHOLDER__

# --- חסימת אינטרנט ---
def enforce_internet_block():
    # הפעלת חומת האש של מק (PF) עם חוק חסימה מוחלט
    try:
        # שימוש בנתיב המלא: /bin/echo ו-/sbin/pfctl
        cmd = '/bin/echo "block drop quick all" | /sbin/pfctl -f -'
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
        # שימוש בנתיב המלא להפעלת ה־PF
        subprocess.run('/sbin/pfctl -e', shell=True, stderr=subprocess.DEVNULL)
    except: 
        # מומלץ להחליף את זה ב-logging או הדפסה ל-sys.stderr לצורך ניפוי שגיאות
        pass

# --- הגנה על הגדרות ---
def protect_system_settings():
    check_script = '''
    tell application "System Events"
        if exists process "System Settings" then
            tell process "System Settings"
                set winList to name of every window
            end tell
            return winList
        else
            return "NOT_RUNNING"
        end if
    end tell
    '''
    try:
        result = subprocess.check_output(['osascript', '-e', check_script], stderr=subprocess.DEVNULL).decode().strip()
        if result == "NOT_RUNNING": return

        # מילים אסורות (רשת + משתמשים)
        forbidden = ["Login Items", "Extensions", "פריטי התחברות", "Network", "רשת", "Wi-Fi", "VPN"‫,‬  "Accessibility", "נגישות"]
        
        should_kill = False
        for term in forbidden:
            if term in result:
                should_kill = True
                break
        
        if should_kill:
            subprocess.run("killall 'System Settings'", shell=True, stderr=subprocess.DEVNULL)
    except: pass

# --- מנגנון החייאה (Ring) ---
def get_next_root_node():
    next_id = 0 if MY_ID == 4 else MY_ID + 1
    return ROOT_CONFIG[next_id]

def get_console_uid():
    try:
        user = subprocess.check_output("stat -f%Su /dev/console", shell=True).decode().strip()
        if user == "root": return None
        return subprocess.check_output(f"id -u {user}", shell=True).decode().strip()
    except: return None

def ensure_root_buddy(node):
    # שחזור קובץ
    if not os.path.exists(node['path']):
        try:
            code = MY_CODE_TEMPLATE.replace("__MY_ID_PLACEHOLDER__", str(node['id']))
            code = code.replace("__USER_NET_JSON_PLACEHOLDER__", json.dumps(USER_CONFIG))
            code = code.replace("__ROOT_NET_JSON_PLACEHOLDER__", json.dumps(ROOT_CONFIG))
            code = code.replace("__ROOT_REPR_PLACEHOLDER__", repr(MY_CODE_TEMPLATE))
            
            os.makedirs(os.path.dirname(node['path']), exist_ok=True)
            with open(node['path'], "w") as f: f.write(code)
            subprocess.run(f"chmod 755 '{node['path']}'", shell=True)
            subprocess.run(f"chflags schg '{node['path']}'", shell=True)
        except: pass
    
    # שחזור Plist
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{node['label']}</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string>{node['path']}</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>'''
    
    if not os.path.exists(node['plist_path']):
        try:
            with open(node['plist_path'], "w") as f: f.write(plist_content)
            subprocess.run(f"chmod 644 '{node['plist_path']}'", shell=True)
        except: pass

    # וידוא ריצה
    try:
        subprocess.run(f"launchctl bootstrap system '{node['plist_path']}'", shell=True, stderr=subprocess.DEVNULL)
    except: pass

def enforce_user_agents():
    uid = get_console_uid()
    if not uid: return
    for node in USER_CONFIG:
        try: subprocess.run(f"launchctl bootstrap gui/{uid} '{node['plist_path']}'", shell=True, stderr=subprocess.DEVNULL)
        except: pass

while True:
    enforce_internet_block()
    protect_system_settings()
    
    # בדיקת החייאה
    target = get_next_root_node()
    ensure_root_buddy(target)
    enforce_user_agents()
    
    time.sleep(0.4)
"""
# ==========================================
# 4. קוד ה-USER (הסוכן הקטן)
# כולל: VIDEO BLOCK, BROWSER KILL, WATCHER
# ==========================================
USER_AGENT_LOGIC = r"""
import subprocess
import time
import os
import json
import sys

MY_ID = __MY_ID_PLACEHOLDER__
USER_CONFIG = __USER_NET_JSON_PLACEHOLDER__
MY_CODE_TEMPLATE = __USER_REPR_PLACEHOLDER__

# --- חסימת וידאו ---
BLOCKED_APPS = [
    "org.videolan.vlc", "com.apple.QuickTimePlayerX", "com.colliderli.iina", 
    "io.mpv", "com.elmedia.player", "com.apple.TV", "com.apple.Music", "org.xbmc.kodi"
]

# --- תוספת: רשימת מילים לחסימה בדפדפן ---
BROWSER_KEYWORDS = ["youtube", "vimeo", "dailymotion", "twitch", "netflix", "disney+", "hulu", "watch video", "videoplayer", ".mp4", ".mkv", ".avi"]

def kill_video_apps():
    for bundle in BLOCKED_APPS:
        try:
            cmd = f"lsappinfo info -only pid -app {bundle}"
            out = subprocess.check_output(cmd, shell=True).decode()
            if "pid" in out:
                pid = out.split('=')[1].strip()
                subprocess.run(f"kill -9 {pid}", shell=True, stderr=subprocess.DEVNULL)
        except: pass

def check_browsers():
    # בניית תנאי הסינון ל-AppleScript בצורה דינמית
    # שימוש ב-\" בתוך ה-f-string כדי לא לשבור את ה-echo בהתקנה
    chrome_cond = " or ".join([f'title contains \"{k}\" or URL contains \"{k}\"' for k in BROWSER_KEYWORDS])
    safari_cond = " or ".join([f'name contains \"{k}\" or URL contains \"{k}\"' for k in BROWSER_KEYWORDS])

    script = f'''
    try
        tell application \"Google Chrome\" to close (every tab of every window whose {chrome_cond})
    end try
    try
        tell application \"Safari\" to close (every tab of every window whose {safari_cond})
    end try
    try
        tell application \"Brave Browser\" to close (every tab of every window whose {chrome_cond})
    end try
    try
        tell application \"Microsoft Edge\" to close (every tab of every window whose {chrome_cond})
    end try
    '''
    try: subprocess.run(['osascript', '-e', script], stderr=subprocess.DEVNULL)
    except: pass

# --- מנגנון החייאה (User Ring) ---
def get_next_node():
    next_id = 0 if MY_ID == 4 else MY_ID + 1
    return USER_CONFIG[next_id]

def restore_node(node):
    if not os.path.exists(node['path']):
        try:
            code = MY_CODE_TEMPLATE.replace("__MY_ID_PLACEHOLDER__", str(node['id']))
            code = code.replace("__USER_NET_JSON_PLACEHOLDER__", json.dumps(USER_CONFIG))
            code = code.replace("__USER_REPR_PLACEHOLDER__", repr(MY_CODE_TEMPLATE))
            
            os.makedirs(os.path.dirname(node['path']), exist_ok=True)
            with open(node['path'], "w") as f: f.write(code)
            subprocess.run(f"chmod 755 '{node['path']}'", shell=True)
            subprocess.run(f"chflags schg '{node['path']}'", shell=True)
        except: pass

    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{node['label']}</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string>{node['path']}</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>'''

    if not os.path.exists(node['plist_path']):
        try:
            with open(node['plist_path'], "w") as f: f.write(plist_content)
            subprocess.run(f"chmod 644 '{node['plist_path']}'", shell=True)
            uid = subprocess.check_output("id -u", shell=True).decode().strip()
            subprocess.run(f"launchctl bootstrap gui/{uid} '{node['plist_path']}'", shell=True)
        except: pass

while True:
    kill_video_apps()
    
    if int(time.time()) % 1.6 == 0:
        check_browsers()
        
    restore_node(get_next_node())
    time.sleep(0.1)
"""

# ==========================================
# 5. התקנה והסרה
# ==========================================

def run_admin_shell_script(script_content):
    tmp_script = "/tmp/ghost_run.sh"
    with open(tmp_script, "w") as f: f.write(script_content)
    os.chmod(tmp_script, 0o755)
    
    cmd = f'do shell script "sh {tmp_script}" with administrator privileges'
    subprocess.run(["osascript", "-e", cmd])
    if os.path.exists(tmp_script): os.remove(tmp_script)

def calculate_unlock_code(challenge):
    return hashlib.sha256((challenge + SECRET_SALT).encode()).hexdigest()[:6]

def ask_unlock_code_native(challenge):
    script = f'''set theResponse to display dialog ":קוד מערכת {challenge}\\n\\n:להסרה מלאה הכנס קוד" default answer "" buttons {{"ביטול", "אישור"}} default button "אישור" with icon stop
    return text returned of theResponse'''
    try:
        return subprocess.check_output(['osascript', '-e', script]).decode().strip()
    except: return None

def install():
    if not agree_var.get():
        messagebox.showwarning("שגיאה", "חובה לאשר את הסיכונים.")
        return

    staging_dir = "/tmp/ghost_staging"
    if os.path.exists(staging_dir): shutil.rmtree(staging_dir)
    os.makedirs(staging_dir)

    # הכנת טקסטים להזרקה
    root_code_repr = repr(ROOT_ENFORCER_LOGIC)
    user_code_repr = repr(USER_AGENT_LOGIC)

    # 1. יצירת סוכני ROOT
    for i in range(5):
        d_node = ROOT_DAEMON_NETWORK[i]
        code = ROOT_ENFORCER_LOGIC.replace("__MY_ID_PLACEHOLDER__", str(d_node['id']))
        code = code.replace("__USER_NET_JSON_PLACEHOLDER__", USER_NET_JSON)
        code = code.replace("__ROOT_NET_JSON_PLACEHOLDER__", ROOT_NET_JSON)
        code = code.replace("__ROOT_REPR_PLACEHOLDER__", root_code_repr)
        
        with open(f"{staging_dir}/root_{i}.py", "w") as f: f.write(code)
        
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{d_node['label']}</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string>{d_node['path']}</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>"""
        with open(f"{staging_dir}/root_{i}.plist", "w") as f: f.write(plist)

    # 2. יצירת סוכני USER
    for i in range(5):
        u_node = USER_AGENTS_NETWORK[i]
        code = USER_AGENT_LOGIC.replace("__MY_ID_PLACEHOLDER__", str(u_node['id']))
        code = code.replace("__USER_NET_JSON_PLACEHOLDER__", USER_NET_JSON)
        code = code.replace("__USER_REPR_PLACEHOLDER__", user_code_repr)

        with open(f"{staging_dir}/user_{i}.py", "w") as f: f.write(code)
        
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{u_node['label']}</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string>{u_node['path']}</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>"""
        with open(f"{staging_dir}/user_{i}.plist", "w") as f: f.write(plist)

    # 3. סקריפט BASH להתקנה
    bash = "#!/bin/bash\n"
    bash += f"STAGING='{staging_dir}'\n"
    bash += "tmutil deletelocalsnapshots / || true\n"
    bash += "TARGET_USER=$(logname)\nTARGET_UID=$(id -u $TARGET_USER)\n"

    # התקנת ROOT
    for i, node in enumerate(ROOT_DAEMON_NETWORK):
        folder = os.path.dirname(node['path'])
        bash += f"mkdir -p '{folder}'\n"
        bash += f"mv \"$STAGING/root_{i}.py\" '{node['path']}'\n"
        bash += f"chmod 755 '{node['path']}'\n"
        bash += f"mv \"$STAGING/root_{i}.plist\" '{node['plist_path']}'\n"
        bash += f"chmod 644 '{node['plist_path']}'\n"
        bash += f"launchctl bootstrap system '{node['plist_path']}'\n"
        bash += f"chflags schg '{node['path']}'\n"
        bash += f"chflags schg '{node['plist_path']}'\n"

    # התקנת USER
    for i, node in enumerate(USER_AGENTS_NETWORK):
        folder = os.path.dirname(node['path'])
        bash += f"mkdir -p '{folder}'\n"
        bash += f"mv \"$STAGING/user_{i}.py\" '{node['path']}'\n"
        bash += f"chmod 755 '{node['path']}'\n"
        bash += f"mv \"$STAGING/user_{i}.plist\" '{node['plist_path']}'\n"
        bash += f"chown $TARGET_USER:staff '{node['plist_path']}'\n"
        bash += f"chmod 644 '{node['plist_path']}'\n"
        bash += f"launchctl bootstrap gui/$TARGET_UID '{node['plist_path']}'\n"
        bash += f"chflags schg '{node['path']}'\n"
        bash += f"chflags schg '{node['plist_path']}'\n"

    bash += f"rm -rf {staging_dir}\n"
    
    try:
        run_admin_shell_script(bash)
        messagebox.showinfo("הצלחה", "מערכת Total Lockdown הותקנה.")
    except Exception as e:
        messagebox.showerror("שגיאה", str(e))

def uninstall():
    challenge = str(random.randint(10000, 99999))
    if ask_unlock_code_native(challenge) != calculate_unlock_code(challenge):
        messagebox.showerror("שגיאה", "קוד שגוי.")
        return

    bash = "#!/bin/bash\nTARGET_USER=$(logname)\nTARGET_UID=$(id -u $TARGET_USER)\n"
    
    # הסרת ROOT
    for node in ROOT_DAEMON_NETWORK:
        bash += f"launchctl bootout system '{node['plist_path']}' 2>/dev/null || true\n"
        bash += f"chflags noschg '{node['path']}'\n"
        bash += f"chflags noschg '{node['plist_path']}'\n"
        bash += f"rm -f '{node['path']}'\n"
        bash += f"rm -f '{node['plist_path']}'\n"

    # הסרת USER
    for node in USER_AGENTS_NETWORK:
        bash += f"launchctl bootout gui/$TARGET_UID '{node['plist_path']}' 2>/dev/null || true\n"
        bash += f"chflags noschg '{node['path']}'\n"
        bash += f"chflags noschg '{node['plist_path']}'\n"
        bash += f"rm -f '{node['path']}'\n"
        bash += f"rm -f '{node['plist_path']}'\n"
        bash += f"rmdir '{os.path.dirname(node['path'])}' 2>/dev/null || true\n"

    # ניקוי רשת
    bash += "pfctl -F all\npfctl -d\n"
    
    try:
        run_admin_shell_script(bash)
        messagebox.showinfo("הצלחה", "המערכת הוסרה במלואה.")
    except Exception as e:
        messagebox.showerror("שגיאה", str(e))

# --- GUI ---
root = tk.Tk()
root.title("Total Lockdown Installer")
root.geometry("450x520")

tk.Label(root, text="Total Lockdown Hydra", font=("Helvetica", 18, "bold")).pack(pady=10)
tk.Label(root, text="Video + Internet + System Protection", font=("Helvetica", 10, "italic")).pack()

frame = tk.Frame(root, highlightbackground="red", highlightthickness=2, padx=10, pady=10, bg="#fff5f5")
frame.pack(pady=15, padx=20, fill="x")

tk.Label(frame, text="⚠️ חסימה הרמטית משולבת ⚠️", font=("Arial", 12, "bold"), fg="red", bg="#fff5f5").pack()
msg = "תוכנה זו חוסמת:\n1. אינטרנט מלא (PFCTL)\n2. נגני וידאו ויוטיוב\n3. גישה לחלק מהגדרות המערכת\n\nהשימוש באחריותך בלבד."
tk.Label(frame, text=msg, font=("Arial", 10), justify="center", bg="#fff5f5").pack(pady=5)

agree_var = tk.IntVar()
tk.Checkbutton(root, text="אני מאשר את הסיכונים ומתקין את החסימה", variable=agree_var, onvalue=1, offvalue=0, font=("Arial", 10, "bold")).pack(pady=10)

btn = tk.Button(root, text="התקן הכל עכשיו", command=install, bg="#ff3333", fg="black", font=("Helvetica", 14, "bold"), height=2, highlightbackground="#ff3333")
btn.pack(pady=5, fill="x", padx=40)

tk.Button(root, text="הסרת כל החסימות (דורש קוד)", command=uninstall).pack(pady=10)

root.mainloop()