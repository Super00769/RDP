import os
import time
import subprocess

# --- CONFIGURATION ---
REMOTE_NAME = "megaremote"
CLOUD_FOLDER = "RDP_Backup/Work"
LOCAL_FOLDER = "Work"
INTERVAL = 300  # 5 Minutes

def backup():
    print(f"⏳ [AutoSave] Backing up '{LOCAL_FOLDER}' to Mega...")
    command = f"rclone copy {LOCAL_FOLDER} {REMOTE_NAME}:{CLOUD_FOLDER} --transfers=4"
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("✅ [AutoSave] Backup successful!")
    except Exception as e:
        print(f"❌ [AutoSave] Backup failed (Internet issue?): {e}")

def main():
    print("--- 🔄 AUTO-SAVE SCRIPT STARTED ---")
    while True:
        time.sleep(INTERVAL)
        backup()

if __name__ == "__main__":
    main()
