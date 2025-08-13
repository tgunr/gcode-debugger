import os
import logging
from typing import List
# Assuming libraries for remote access (e.g., requests for HTTP API, or paramiko for SSH)
import requests  # Replace with actual remote access method

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def sync_macros_on_startup(controller_url: str, local_macros_path: str) -> None:
    """
    Sync remote files from controller to local macros folder on startup.
    Ensures local folder matches remote content.
    """
    try:
        # Step 1: Fetch remote files list/metadata (adjust for your remote protocol)
        response = requests.get(f"{controller_url}/files")  # Example: HTTP API endpoint
        response.raise_for_status()
        remote_files: List[dict] = response.json()  # Assume JSON response with file list
        
        # Step 2: Ensure local path exists
        os.makedirs(local_macros_path, exist_ok=True)
        
        # Step 3: Sync each file (download if missing or changed)
        for file_info in remote_files:
            remote_path = file_info['path']
            local_path = os.path.join(local_macros_path, os.path.basename(remote_path))
            
            # Check if local file needs update (e.g., by size or hash)
            if not os.path.exists(local_path) or os.path.getsize(local_path) != file_info['size']:
                logging.debug(f"Syncing {remote_path} to {local_path}")
                file_response = requests.get(f"{controller_url}/download/{remote_path}")
                file_response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(file_response.content)
        
        # Step 4: Optional: Clean up local files not present remotely
        local_files = set(os.listdir(local_macros_path))
        remote_filenames = set(os.path.basename(f['path']) for f in remote_files)
        for extra_file in local_files - remote_filenames:
            os.remove(os.path.join(local_macros_path, extra_file))
            logging.debug(f"Removed extra local file: {extra_file}")
        
        logging.info("Macros sync completed successfully.")
    
    except requests.RequestException as e:
        logging.error(f"Failed to sync macros: Network error - {e}")
    except OSError as e:
        logging.error(f"Failed to sync macros: File I/O error - {e}")
    except Exception as e:
        logging.error(f"Unexpected error during sync: {e}")

# Example usage on app startup
# preferences = load_preferences()  # Your function to load config
# sync_macros_on_startup(preferences['controller_url'], preferences['macros_path'])
