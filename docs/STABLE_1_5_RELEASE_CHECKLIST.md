# WorkBOXig 1.5.0 — release gate

**Release status:** not yet approved. The GitHub release tag `v1.5.0-beta.2` was marked a *regular/latest release* even though its executable identifies itself as a beta. This is not the final `v1.5.0` release.

## Automated gates
- [ ] Windows CI success for the **exact** final commit being released (all tests, portable EXE and installer).
- [ ] Mismarked `-beta` GitHub releases are never offered on the stable update channel.
- [ ] Beta channel lists published beta and stable releases using semantic version ordering.
- [ ] Synthetic 1.4.7 migration: notes, tasks, notebook images, calendar, custom settings and legacy backups survive.
- [ ] No update installer is launched unless a pre-update backup completes successfully.
- [ ] Download checks size and SHA-256 (when published by GitHub); cancellation never destroys a running Qt thread.
- [ ] Only create the final stable `v1.5.0` tag from the tested source, with matching executable version.

## Manual Windows 11 gates
Use a **copy** of a real user profile. Do not use live-only data for destructive tests.

- [ ] Launch `WorkBOXig.exe` fresh, create a lesson and task, close/reopen, confirm persistence.
- [ ] Open and close add/edit/delete popups; no blank flashing windows.
- [ ] Repeat modal form tests at 100%, 125%, 150% scaling; verify Save and Cancel remain visible.
- [ ] Upgrade existing v1.4.7 installation with `WorkBOXig_Setup.exe`, retaining notes, notebook images, calendar events, settings, and tasks.
- [ ] Export a backup from a **real** v1.3–v1.4 installation and restore it into a **throwaway** v1.5 profile. Confirm all attachments and content.
- [ ] Test Beta toggle in both RU and EN; quit and relaunch and ensure it persists.
- [ ] Verify the stable channel does not advertise any `-beta` build; beta channel displays warnings.
- [ ] Check manual download cancellation and recovery after offline/network failure.
- [ ] Confirm uninstall with “delete user data” **unchecked** retains the profile.
- [ ] Check first run, Ctrl+S and warning behaviour on an unwritable temporary profile.

## Publication
Do **not** merge the stabilization PR, update `main`, or publish a final stable release until Windows CI and relevant manual gates pass. Publish the tested `v1.5.0` with portable EXE, installer, checksums and release notes; keep the published Beta 2 tag as history.

## Rollback
If any gate fails, preserve the current v1.4.7 and Beta 2 downloads, keep the PR open, and fix the issue in the stabilization branch. Never delete or overwrite user data in the name of rollback.
