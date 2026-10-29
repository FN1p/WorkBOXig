# WorkBOXig 1.5 — development checklist

Goal: improve reliability and day-to-day usability before adding major features.

## P0 — data safety (first review)
- [x] Bound the size of backup metadata before JSON decoding.
- [x] Reject archive metadata whose root is not a JSON object.
- [x] Add regression tests for malformed and oversized metadata.
- [x] Add regression tests for interrupted saves and attachment-name collisions (Windows CI passed on 1d201021).
- [ ] Test backward compatibility with v1.3–v1.4 backups and notebook images.
- [x] Document recovery steps for a corrupted local storage file (see `docs/DATA_RECOVERY.md`).

## P1 — UI and workflows
- [ ] Audit the Today dashboard at 100%, 125% and 150% DPI.
- [ ] Check keyboard navigation, focus order, and screen-reader labels.
- [x] Show recurring lessons in the month inspector using the selected date's actual ISO week parity (CI pending).
- [ ] Audit weekly parity filters, time zones and midnight rollover.
- [x] Show tasks in the monthly inspector, navigate to Tasks, refresh after edits and clear stale date highlights (CI pending).
- [ ] Verify task creation/completion updates dashboard immediately.
- [x] Fix direct task completion timestamp handling and add regression test.
- [ ] Check RU/EN strings and small-window layouts.

## P1 — release quality
- [x] Windows unit tests passed for previous commit `1d201021`; verify again for the latest calendar changes.
- [x] Previous portable EXE and installer built successfully for `1d201021`; build again for latest calendar changes.
- [ ] Manually launch both builds and test first-run onboarding, update checks and data migration.
- [ ] Confirm that updating preserves existing user data.
- [ ] Publish a prerelease only after checks pass.

## Release rule
Do not merge or publish a stable release until Windows CI succeeds and manual backup/import smoke checks pass.

## Progress notes — 2026-10-29 night
- Prior Windows PR checks passed on commit `325dadde`.
- Fixed a recovery path that could overwrite unreadable `storage.json` when moving it to safety failed.
- Fixed a restore collision that could delete an existing attachment during cleanup.
- Fixed missing `completed_at` updates for direct task completion changes.
- Added regression tests for these cases and recovery/rollback documentation.
- Enabled short-lived Windows EXE/installer artifacts for this PR. Verify artifact upload and CI success before inviting manual testing.

## Progress notes — 2026-10-29 late-night calendar iteration
- Monthly date inspector now displays recurring lessons only on matching odd/even ISO weeks.
- Pending tasks now appear in the monthly inspector and open the Tasks page.
- Inspector refreshes when tasks/events/recurring lessons change.
- Removed obsolete date highlights after tasks are completed or events are deleted.
- Added isolated UI regression tests for recurrence, task navigation and highlight removal.
- **Pending:** check GitHub Actions on latest commit before recommending the new build.
