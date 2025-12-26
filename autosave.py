import os
import time
import subprocess

# --- CONFIGURATION ---
REMOTE_NAME = "megaremote"
CLOUD_FOLDER = "RDP_Backup/Work"
LOCAL_FOLDER = r"C:\Users\RDP\Desktop\Work"
CONFIG_PATH = r"C:\rclone.conf"  # Points to our forced config file

# Wait 2 seconds to ensure file is fully saved
DEBOUNCE_SECONDS = 2

def get_folder_state(folder):
    state = {}
    if not os.path.exists(folder):
        return state 
    for root, dirs, files in os.walk(folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                state[filepath] = os.path.getmtime(filepath)
            except OSError:
                continue
    return state

def backup():
    print(f"⚡ [Sync] Change detected! Mirroring to Mega...")
    
    # Sync using the specific config file
    command = f'rclone sync "{LOCAL_FOLDER}" {REMOTE_NAME}:{CLOUD_FOLDER} --transfers=8 --config "{CONFIG_PATH}"'
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("✅ [Sync] Success! Mega updated.")
    except Exception as e:
        print(f"❌ [Sync] Error: {e}")

def main():
    print("--- 👁️ SMART SYNC MONITOR (MANUAL MODE) ---")
    print(f"Watching: {LOCAL_FOLDER}")
    print("Keep this window OPEN to sync files.")
    
    if not os.path.exists(CONFIG_PATH):
        print(f"⚠️ ERROR: Config file not found at {CONFIG_PATH}")
        time.sleep(10)
        return

    last_state = get_folder_state(LOCAL_FOLDER)
    
    while True:
        current_state = get_folder_state(LOCAL_FOLDER)
        
        if current_state != last_state:
            time.sleep(DEBOUNCE_SECONDS)
            backup()
            last_state = get_folder_state(LOCAL_FOLDER)
            
        time.sleep(1)

if __name__ == "__main__":
    main()
