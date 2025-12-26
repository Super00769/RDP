import os
import time
import subprocess

# --- CONFIGURATION ---
REMOTE_NAME = "megaremote"
CLOUD_FOLDER = "RDP_Backup/Work"

# This points specifically to the NEW user's desktop
LOCAL_FOLDER = r"C:\Users\RDP\Desktop\Work"

# Backup every 300 seconds (5 Minutes)
INTERVAL = 300

def backup():
    # Only run if the folder actually exists
    if not os.path.exists(LOCAL_FOLDER):
        print(f"⚠️ Waiting for folder creation: {LOCAL_FOLDER}")
        return

    print(f"⏳ [AutoSave] Backing up '{LOCAL_FOLDER}' to Mega...")
    
    # We use 'copy' to upload new changes safely
    command = f'rclone copy "{LOCAL_FOLDER}" {REMOTE_NAME}:{CLOUD_FOLDER} --transfers=4'
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("✅ [AutoSave] Backup successful!")
    except Exception as e:
        print(f"❌ [AutoSave] Backup failed: {e}")

def main():
    print("--- 🔄 AUTO-SAVE SCRIPT STARTED ---")
    print(f"Target: {LOCAL_FOLDER}")
    while True:
        time.sleep(INTERVAL)
        backup()

if __name__ == "__main__":
    main()
