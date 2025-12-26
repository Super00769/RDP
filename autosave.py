import os
import time
import subprocess

# --- CONFIGURATION ---
# 1. The Rclone remote name (Must match the YAML file)
REMOTE_NAME = "megaremote"

# 2. The path inside Mega where files will be stored
# It will create a folder "RDP_Backup" and inside it "Work"
CLOUD_FOLDER = "RDP_Backup/Work"

# 3. The local folder on the RDP Desktop to backup
# This matches the folder we create in the YAML file
LOCAL_FOLDER = "Work"

# 4. How often to save (in seconds)
# 300 seconds = 5 minutes
INTERVAL = 300

def backup():
    print(f"⏳ [AutoSave] Backing up '{LOCAL_FOLDER}' to Mega...")
    
    # We use 'copy' to be safe. It uploads new/changed files.
    # --transfers=4 makes it upload 4 files at a time (faster)
    command = f"rclone copy {LOCAL_FOLDER} {REMOTE_NAME}:{CLOUD_FOLDER} --transfers=4"
    
    try:
        # Run the command and wait for it to finish
        subprocess.run(command, shell=True, check=True)
        print("✅ [AutoSave] Backup successful!")
    except Exception as e:
        print(f"❌ [AutoSave] Backup failed: {e}")

def main():
    print("--- 🔄 AUTO-SAVE SCRIPT STARTED ---")
    print(f"Saving '{LOCAL_FOLDER}' every {INTERVAL} seconds.")
    
    # Infinite loop that runs until the RDP stops
    while True:
        time.sleep(INTERVAL)
        backup()

if __name__ == "__main__":
    main()
