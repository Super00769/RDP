import os
import time
import subprocess

# --- CONFIGURATION ---
REMOTE_NAME = "megaremote"
CLOUD_FOLDER = "RDP_Backup/Work"
LOCAL_FOLDER = r"C:\Users\Public\Desktop\Work"

# Wait 2 seconds after a change to let the file finish saving
DEBOUNCE_SECONDS = 2

def get_folder_state(folder):
    """
    Scans the folder to create a list of files and their modification times.
    """
    state = {}
    if not os.path.exists(folder):
        return state
        
    for root, dirs, files in os.walk(folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                # Store the full path and the time it was last modified
                state[filepath] = os.path.getmtime(filepath)
            except OSError:
                continue
    return state

def backup():
    print(f"⚡ [Sync] Change detected! Mirroring Desktop to Mega...")
    
    # SYNC COMMAND: Makes Mega match the Desktop exactly.
    # Deleted local files = Deleted cloud files.
    command = f'rclone sync "{LOCAL_FOLDER}" {REMOTE_NAME}:{CLOUD_FOLDER} --transfers=8'
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("✅ [Sync] Success! Mega is now identical to Desktop.")
    except Exception as e:
        print(f"❌ [Sync] Failed: {e}")

def main():
    print("--- 👁️ SMART SYNC MONITOR STARTED ---")
    print(f"Watching: {LOCAL_FOLDER}")
    print("⚠️ WARNING: Sync Mode is ON. Deleting files here deletes them on Mega!")
    
    # 1. Take a snapshot of the folder right now
    last_state = get_folder_state(LOCAL_FOLDER)
    
    while True:
        # 2. Check the folder again
        current_state = get_folder_state(LOCAL_FOLDER)
        
        # 3. Compare the old snapshot vs new snapshot
        # This detects additions, edits, AND deletions
        if current_state != last_state:
            # Wait for the user to finish what they are doing
            time.sleep(DEBOUNCE_SECONDS)
            
            # Run the backup
            backup()
            
            # Update the snapshot
            last_state = get_folder_state(LOCAL_FOLDER)
            
        # 4. Check again in 1 second
        time.sleep(1)

if __name__ == "__main__":
    main()
