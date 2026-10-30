# WorkBOXig 1.5 — development checklist

Goal: improve reliability and day-to-day usability before adding major features.

## P0 — data safety (first review)
- [x] Bound the size of backup metadata before JSON decoding.
- [x] Reject archive metadata whose root is not a JSON object.
- [x] Add regression tests for malformed and oversized metadata.
- [x] Add regression tests for interrupted saves and attachment-name collisions (Windows CI passed on 1d201021).
- [ ] Test real v1.3–v1.4 backup files and notebook images on Windows (synthetic v1.4 JSON fixture covered).
- [x] Fill missing default settings on legacy import without discarding custom settings; add regression test.
- [x] Document recovery steps for a corrupted local storage file (see `docs/DATA_RECOVERY.md`).

## P1 — UI and workflows
- [ ] Audit the Today dashboard at 100%, 125% and 150% DPI.
- [ ] Check keyboard navigation, focus order, and screen-reader labels.
- [x] Show recurring lessons in the month inspector using the selected date's actual ISO week parity (Windows CI passed on 3f69b216).
- [x] Highlight recurring lessons in the visible month, respecting week parity and page navigation; add regression test.
- [x] Default weekly timetable follows actual ISO week parity; explicit odd/even previews have a regression test.
- [x] Follow midnight/week rollover in an open calendar without overriding user-browsed weeks; add regression tests.
- [ ] Audit daylight saving/time zones on a real Windows machine.
- [x] Show tasks in the monthly inspector, navigate to Tasks, refresh after edits and clear stale date highlights (Windows CI passed on 3f69b216).
- [ ] Verify task creation/completion updates dashboard immediately.
- [x] Fix direct task completion timestamp handling and add regression test.
- [ ] Check RU/EN strings and small-window layouts.

## P1 — release quality
- [x] Windows unit tests passed for calendar commit `99e09512`; updater hardening awaits CI.
- [x] Portable EXE and installer built successfully for `99e09512`; updater hardening awaits CI.
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

## Progress notes — 2026-10-30 early morning
- Weekly timetable now uses the displayed ISO week's actual parity by default; odd/even buttons remain explicit previews.
- Monthly grid highlights recurring lessons on matching dates, updates when changing month, and removes stale highlights when lessons are deleted.
- Calendar detects date changes even after sleep at the same clock hour, advances the current week only when following it, and preserves manually browsed dates.
- Older JSON backups now receive missing settings defaults without overwriting existing or custom settings; synthetic legacy fixture added.
- Added UI regression tests for recurring highlights, weekly parity and midnight rollover, plus a legacy import test.
- **Pending:** verify Windows CI on the latest branch head, confirm new review artifact, and manually smoke-test EXE/installer and historical backup files.

## Progress notes — 2026-10-30 updater hardening
- Found a rate-limit fallback that omitted `is_newer` and fabricated direct EXE URLs/sizes. Redirects now require a real version tag and return the GitHub release page without guessing assets.
- Installer launch now stops if a pre-update backup fails; the dialog reports the failure and re-enables controls.
- Portable-only releases open the release page rather than launching a portable EXE as if it were an installer.
- Downloads now use unique temporary directories, validate filenames and reject empty or incomplete responses before exposing an EXE.
- Added mocked-network regression tests for redirects, download validation, backup failures and dialog recovery.
- **Pending:** Windows CI and artifact upload for latest updater changes; manually test updating from 1.4.2 with a copy of real user data.
