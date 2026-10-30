# WorkBOXig data recovery (Windows)

WorkBOXig stores user data locally. **Close WorkBOXig before moving or editing files.**

## Locate the data directory

By default, the directory is `%USERPROFILE%\.workboxig`. If a `data` folder exists in the application's *current working directory*, WorkBOXig uses that instead. In a running application, Settings → Data & Backups → Open data folder shows the actual directory.

Important files:
- `storage.json` — current tasks, calendar, settings, notes and notebook metadata.
- `attachments/` — notebook images.
- `storage.json.bak-*` — unreadable original storage preserved during automatic recovery.
- `storage.pre_import_*.workboxig` — snapshot made before importing another backup.
- `storage.pre_update_*.workboxig` — snapshot made before an update.

## If notes or tasks disappear after startup

1. **Exit WorkBOXig**, including its tray process, and make a copy of the **entire** data directory somewhere safe.
2. Check for `storage.json.bak-*`. A file with this name means WorkBOXig detected invalid data and moved the original aside before creating defaults. Do not delete it.
3. To recover a previously exported `.workboxig` archive, open WorkBOXig → Settings → Data & Backups → Import, select the archive and confirm. The app creates a pre-import snapshot first.
4. To inspect an unreadable `storage.json.bak-*`, use a text editor on a **copy**. It may be partially damaged. Do not overwrite `storage.json` with unverified contents.
5. If a restore fails, keep both the original data directory and the backup archive. Report the error message and attach only non-sensitive diagnostic details.

## If WorkBOXig refuses to start because data cannot be saved

A new profile or a profile recovering from damaged JSON must be writable before WorkBOXig opens. If the initial atomic save fails (for example, because the disk is full or the data folder is read-only), startup now stops instead of showing an empty workspace whose changes would be lost on exit.

1. Close WorkBOXig and copy the entire data folder before troubleshooting.
2. Check available disk space and write permissions for the folder shown above; do not delete the `attachments/` directory or any `storage.json.bak-*` recovery files.
3. If a `storage.json.bak-*` file exists, the original JSON was preserved even if creation of a replacement `storage.json` failed. Keep it for manual recovery.
4. After correcting the storage problem, restart WorkBOXig. If the original data was corrupt, restore a verified backup rather than treating the newly created default dataset as recovered data.

## Safe rollback after testing a new build

1. Exit WorkBOXig completely.
2. Back up the full data directory before changing versions.
3. Reinstall or run the previous known-good WorkBOXig executable.
4. If data is missing or incompatible, import your saved `.workboxig` backup via Settings. The backup includes notebook images; legacy `.json` exports do not include them.

## Limitations

Automatic recovery preserves the unreadable file, but **does not repair malformed JSON**. If WorkBOXig cannot move the damaged file to a recovery copy (for example, due to permissions), it stops initialization rather than overwriting the original. A backup is still essential.

Review builds from pull requests are experimental. Do not test them on your only copy of important data.
