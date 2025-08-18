#!/usr/bin/env python3
"""
Synchronization Manager for G-code Debugger

Handles bi-directional synchronization between a local directory and the controller's file system.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from .communication import Communication

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages the bi-directional synchronization of macros."""

    def __init__(self, comm: Communication, local_sync_dir: str):
        """Initialize the SyncManager.

        Args:
            comm: The communication object for controller interaction.
            local_sync_dir: The local directory to synchronize with the controller.
        """
        self.comm = comm
        self.local_sync_dir = Path(local_sync_dir)
        os.makedirs(self.local_sync_dir, exist_ok=True)

    def synchronize_files(self) -> None:
        """Perform a bi-directional synchronization between local and remote files."""
        logger.info("Starting file synchronization...")
        if not self.comm or not self.comm.connected:
            logger.warning("Synchronization skipped: Not connected to controller.")
            return

        try:
            local_files = self._get_local_files()
            remote_files = self._get_remote_files("Home")

            if remote_files is None:
                logger.error("Synchronization failed: Could not retrieve remote file list.")
                return

            # Plan the necessary actions
            actions = self._compare_files(local_files, remote_files)

            # Execute the plan
            self._execute_sync_actions(actions)

            logger.info("File synchronization complete.")
        except Exception as e:
            logger.error(f"An error occurred during synchronization: {e}", exc_info=True)

    def _get_local_files(self) -> Dict[str, float]:
        """Get a dictionary of local files and their modification times."""
        local_files = {}
        for item in self.local_sync_dir.glob('**/*'):
            if item.is_file():
                # Use relative path as the key
                relative_path = item.relative_to(self.local_sync_dir).as_posix()
                local_files[relative_path] = item.stat().st_mtime
        logger.debug(f"Found {len(local_files)} local files.")
        return local_files

    def _get_remote_files(self, path: str) -> Dict[str, float]:
        """Recursively get a dictionary of remote files and their modification times."""
        remote_files = {}
        listing = self.comm.list_directory(path)

        if listing is None:
            return None

        for item in listing:
            name = item.get('name')
            item_type = item.get('type')
            full_path = f"{path}/{name}" if path != "Home" else name

            if item_type == 'directory':
                # Recursively list subdirectories
                sub_files = self._get_remote_files(full_path)
                if sub_files is not None:
                    remote_files.update(sub_files)
            else:
                remote_files[full_path] = item.get('modified', 0)
        return remote_files

    def _compare_files(self, local: Dict[str, float], remote: Dict[str, float]) -> Dict[str, List[str]]:
        """Compare local and remote file lists and determine actions."""
        actions = {
            'upload': [],
            'download': [],
            'delete_local': [],
            'delete_remote': []
        }

        local_set = set(local.keys())
        remote_set = set(remote.keys())

        common_files = local_set.intersection(remote_set)
        local_only_files = local_set.difference(remote_set)
        remote_only_files = remote_set.difference(local_set)

        for f in common_files:
            # Compare modification times, with a small tolerance
            if local[f] > remote[f] + 2:
                actions['upload'].append(f)
            elif remote[f] > local[f] + 2:
                actions['download'].append(f)

        # New local files should be uploaded
        actions['upload'].extend(list(local_only_files))

        # New remote files should be downloaded
        actions['download'].extend(list(remote_only_files))

        logger.info(f"Sync plan: {len(actions['upload'])} to upload, {len(actions['download'])} to download.")
        return actions

    def _execute_sync_actions(self, actions: Dict[str, List[str]]) -> None:
        """Execute the planned synchronization actions."""
        # Download files from controller
        for path in actions['download']:
            logger.info(f"Downloading: {path}")
            content = self.comm.read_file(path)
            if content is not None:
                local_path = self.local_sync_dir / path
                os.makedirs(local_path.parent, exist_ok=True)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                logger.error(f"Failed to download {path}.")

        # Upload files to controller
        for path in actions['upload']:
            logger.info(f"Uploading: {path}")
            local_path = self.local_sync_dir / path
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                success, msg = self.comm.write_file(path, content)
                if not success:
                    logger.error(f"Failed to upload {path}: {msg}")
            except FileNotFoundError:
                logger.error(f"Could not upload {path}: local file not found.")
