import os
import time

def cleanup_old_files(folder, hours=2):
    print(f"[CLEANUP] Checking for files older than {hours} hours in {folder}...")
    
    if not os.path.exists(folder):
        print(f"[CLEANUP] Folder {folder} does not exist.")
        return

    current_time = time.time()
    age_in_seconds = hours * 3600

    deleted_count = 0
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        
        # Only process files
        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)
            
            # If older than target age
            if current_time - file_mod_time > age_in_seconds:
                try:
                    os.remove(file_path)
                    print(f"  - Deleted {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  - Failed to delete {file_path}: {e}")

    print(f"[CLEANUP] Deleted {deleted_count} files in {folder}.")

if __name__ == "__main__":
    # Clean up both uploads and processed folders
    cleanup_old_files('uploads', hours=2)
    cleanup_old_files('processed', hours=2)
