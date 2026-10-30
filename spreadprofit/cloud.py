"""
Google Cloud Storage and Local Backup Manager for spreadProfit.

Provides automated snapshot creation, local archiving, and synchronization
with Google Cloud Storage (GCS) to protect user portfolio data.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
import zipfile
from typing import Any, Dict, List, Optional, Tuple


def get_default_data_dir() -> str:
    """Return the data directory path relative to project or execution root."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.dirname(pkg_dir)
        if os.path.exists(os.path.join(parent, "data")):
            base_dir = parent
        elif os.path.exists(os.path.join(pkg_dir, "data")):
            base_dir = pkg_dir
        else:
            base_dir = parent
    data_dir = os.path.join(base_dir, "data")
    if os.path.exists(data_dir):
        return data_dir
    return base_dir


DATA_DIR = get_default_data_dir()
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
TRACKED_FILES = ("gold_transactions.json", "market_prices.json", "custom_assets.json")


def ensure_backup_dir(target_dir: Optional[str] = None) -> str:
    """Ensure the target backup directory exists and return its path."""
    dest = target_dir or BACKUP_DIR
    os.makedirs(dest, exist_ok=True)
    return dest


def create_local_snapshot(target_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a timestamped archive and unified JSON snapshot of all database files.

    Returns:
        Dict containing metadata: timestamp, file count, archive path, and file hashes.
    """
    dest_dir = ensure_backup_dir(target_dir)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_filename = f"spreadprofit_snapshot_{timestamp}.json"
    archive_filename = f"spreadprofit_backup_{timestamp}.zip"

    snapshot_path = os.path.join(dest_dir, snapshot_filename)
    archive_path = os.path.join(dest_dir, archive_filename)

    snapshot_data: Dict[str, Any] = {
        "app": "spreadProfit",
        "created_at": datetime.datetime.now().isoformat(),
        "timestamp": timestamp,
        "files": {},
    }

    # 1. Build unified JSON snapshot
    found_files = 0
    for name in TRACKED_FILES:
        src = os.path.join(DATA_DIR, name)
        if os.path.exists(src):
            try:
                with open(src, "r", encoding="utf-8") as f:
                    content = json.load(f)
                snapshot_data["files"][name] = content
                found_files += 1
            except Exception as e:
                snapshot_data["files"][name] = {"_error": str(e)}

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

    # 2. Build ZIP archive containing exact physical files
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(snapshot_path, arcname=snapshot_filename)
        for name in TRACKED_FILES:
            src = os.path.join(DATA_DIR, name)
            if os.path.exists(src):
                zf.write(src, arcname=f"data/{name}")

    # 3. Maintain 'latest' copies for rapid retrieval
    latest_snapshot = os.path.join(dest_dir, "spreadprofit_latest_snapshot.json")
    shutil.copyfile(snapshot_path, latest_snapshot)

    # 4. Also mirror to OneDrive if available on Windows
    user_profile = os.environ.get("USERPROFILE", "")
    onedrive_base = os.path.join(user_profile, "OneDrive") if user_profile else ""
    if onedrive_base and os.path.isdir(onedrive_base):
        onedrive_dest = os.path.join(onedrive_base, "SpreadProfit_Backups")
        try:
            os.makedirs(onedrive_dest, exist_ok=True)
            shutil.copyfile(snapshot_path, os.path.join(onedrive_dest, snapshot_filename))
            shutil.copyfile(snapshot_path, os.path.join(onedrive_dest, "spreadprofit_latest_snapshot.json"))
            shutil.copyfile(archive_path, os.path.join(onedrive_dest, archive_filename))
        except Exception:
            pass

    return {
        "status": "success",
        "timestamp": timestamp,
        "snapshot_path": snapshot_path,
        "archive_path": archive_path,
        "files_backed_up": found_files,
    }


def upload_to_google_cloud(
    bucket_name: Optional[str] = None,
    custom_archive_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Upload the latest backup archive to Google Cloud Storage (GCS).

    Uses `gcloud storage` or `gsutil` CLI if available, or python google-cloud-storage.

    Args:
        bucket_name: Target GCS bucket name (e.g. 'gs://my-bucket' or 'my-bucket').
        custom_archive_path: Specific archive file to upload. If None, creates a fresh one.

    Returns:
        Tuple of (success: bool, message: str)
    """
    # 1. Ensure local snapshot exists
    archive_path = custom_archive_path
    if not archive_path or not os.path.exists(archive_path):
        meta = create_local_snapshot()
        archive_path = meta["archive_path"]

    target_bucket = bucket_name or os.environ.get("GCS_BACKUP_BUCKET", "")
    if not target_bucket:
        # Check config file if present
        cfg_file = os.path.join(DATA_DIR, "cloud_config.json")
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    target_bucket = cfg.get("gcs_bucket", "")
            except Exception:
                pass

    if not target_bucket:
        return (
            False,
            "No Google Cloud Storage bucket configured. Set GCS_BACKUP_BUCKET or configure cloud_config.json.",
        )

    # Normalize bucket URI
    if not target_bucket.startswith("gs://"):
        target_bucket = f"gs://{target_bucket}"

    dest_uri = f"{target_bucket.rstrip('/')}/spreadprofit/backups/{os.path.basename(archive_path)}"

    # 2. Try gcloud storage CLI
    try:
        proc = subprocess.run(
            ["gcloud", "storage", "cp", archive_path, dest_uri],
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        if proc.returncode == 0:
            return True, f"Successfully uploaded backup to Google Cloud Storage: {dest_uri}"
        stderr = proc.stderr.strip()
    except Exception as e:
        stderr = str(e)

    # 3. Fallback to gsutil CLI
    try:
        proc_gs = subprocess.run(
            ["gsutil", "cp", archive_path, dest_uri],
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
        if proc_gs.returncode == 0:
            return True, f"Successfully uploaded backup via gsutil to: {dest_uri}"
        stderr_gs = proc_gs.stderr.strip()
    except Exception as e:
        stderr_gs = str(e)

    return (
        False,
        f"GCS upload failed.\nCLI output: {stderr or stderr_gs}\n"
        "Ensure active GCP credentials and billing on the owning project.",
    )


# Alias for unified sync API
sync_portfolio_to_cloud = upload_to_google_cloud


def list_local_backups() -> List[Dict[str, Any]]:
    """List all available local backup snapshots ordered by recency."""
    dest_dir = ensure_backup_dir()
    results = []
    if not os.path.isdir(dest_dir):
        return results

    for fname in sorted(os.listdir(dest_dir), reverse=True):
        if fname.startswith("spreadprofit_snapshot_") and fname.endswith(".json"):
            fpath = os.path.join(dest_dir, fname)
            size = os.path.getsize(fpath)
            results.append({
                "filename": fname,
                "path": fpath,
                "size_bytes": size,
                "modified": datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
            })
    return results


def restore_snapshot(snapshot_path: str) -> Tuple[bool, str]:
    """
    Restore transactions, prices, and assets from a snapshot file.
    Creates an automatic safety backup before modifying current data.
    """
    if not os.path.exists(snapshot_path):
        return False, f"Snapshot file not found: {snapshot_path}"

    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Failed to parse snapshot JSON: {e}"

    files_dict = data.get("files", {})
    if not files_dict:
        return False, "Snapshot contains no file payload."

    # Pre-restore safety backup
    create_local_snapshot()

    restored_count = 0
    for name, content in files_dict.items():
        if isinstance(content, dict) and "_error" in content:
            continue
        target_path = os.path.join(DATA_DIR, name)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            restored_count += 1
        except Exception as e:
            return False, f"Error writing file {name}: {e}"

    return True, f"Successfully restored {restored_count} database files from snapshot."


if __name__ == "__main__":
    print("--- spreadProfit Cloud & Local Backup Service ---")
    meta = create_local_snapshot()
    print(f"[OK] Local snapshot created: {meta['snapshot_path']}")
    print(f"[OK] Archive package created: {meta['archive_path']}")
    print(f"[OK] Files included: {meta['files_backed_up']}")

    # Check for GCS environment
    gcs_bucket = os.environ.get("GCS_BACKUP_BUCKET")
    if gcs_bucket:
        print(f"Syncing to Google Cloud Storage bucket: {gcs_bucket}...")
        ok, msg = upload_to_google_cloud(gcs_bucket)
        print(f"Result: {msg}")
    else:
        print("Note: Set GCS_BACKUP_BUCKET to enable direct Google Cloud Storage upload.")
