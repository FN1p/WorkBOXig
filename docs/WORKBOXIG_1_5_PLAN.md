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

## Progress notes — 2026-10-30 download integrity
- GitHub release asset downloads now verify the expected byte count supplied by the Releases API, even if the HTTP response omits Content-Length.
- Reject mismatched Content-Length, truncated/oversized transfers, and assets above a 1 GiB safety cap before launching an installer; retain private temporary download cleanup on failure.
- Update dialog forwards the release asset size to the downloader.
- Added five regression tests covering size mismatch, missing headers, truncated downloads, oversized headers and size forwarding.
- Prior updater-hardening commit `3ee0490e` passed Windows CI (run 40983422164, review artifact available). New download-integrity commits await CI.
- Next: verify the latest Windows CI and review artifact, then smoke-test actual 1.4.2 → 1.5 update and rollback with a copied user profile.

## Progress notes — 2026-10-30 accessibility follow-up
- Navigation uses custom QLabel children inside QPushButton; their button text was empty for assistive technology. NavItem now exposes its visible label as accessibleName, including collapsed mode and language changes.
- Both icon-only sidebar collapse buttons now expose translated accessible names; added an isolated regression test.
- Broader keyboard focus-order, DPI and screen-reader audits remain manual review items.
- Latest CI is pending for these commits; do not treat the new EXE as verified until the workflow succeeds.

## Progress notes — 2026-10-30 reminder rollover
- Found a long-running-window bug: event/task reminder ID sets were never reset, so an item moved to the next day could silently miss its notification.
- Reset per-day notification keys at local date rollover; event deduplication also includes scheduled time so a moved lesson can notify at its new time.
- Added UI-level regression tests for same-day polling, next-day rescheduling and same-day time changes.
- **Pending:** Windows CI on reminder commits; confirm review artifact before manual testing. No real Windows notification delivery test yet.

## Progress notes — 2026-10-30 storage initialization safety
- Verified reminder CI run 40989483124 succeeded on `5f2e0b2a` (Windows tests, portable EXE, installer and review artifact).
- Found a data-loss risk: if a new or recovered profile could not write its initial `storage.json`, the app opened with unsaved default data and silently discarded subsequent edits on restart.
- Startup now aborts with a clear storage error when the first atomic save fails. Corrupt originals already moved to `storage.json.bak-*` remain preserved.
- Added regression tests for fresh-profile write failure and corrupt-file recovery followed by write failure; updated `docs/DATA_RECOVERY.md`.
- **Pending:** Windows CI and new review artifact for this iteration, plus manual Windows disk-full/permissions and installer smoke tests. Do not claim these changes verified until CI passes.

## Progress notes — 2026-10-30 failed-save visibility
- Verified storage initialization safety on Windows CI [run 40994978935](https://github.com/FN1p/WorkBOXig/actions/runs/40994978935): unit tests, portable EXE, installer and review artifact all succeeded for `92ceaff0`. Artifact `WorkBOXig-Windows-review` (119,657,854 bytes; expires 2026-10-31 03:03 UTC).
- Found that failed atomic autosaves after startup only printed to console; user edits could remain unsaved with no visible warning. Ctrl+S incorrectly displayed “All data saved” even when the save returned False.
- StorageManager now emits `save_failed` on failed atomic writes. MainWindow shows a localized error toast **and persistent status-bar warning**, cleared only after a successful save. Ctrl+S displays success only on success.
- Added regression tests for disk-full autosave, retry persistence and Ctrl+S error/success feedback.
- **Pending:** Windows CI on the new commits; manual Windows disk-full, permissions and first-run checks. Do not treat the new EXE as verified until CI passes.

## Progress notes — 2026-10-30 legacy task deadlines and live Today updates
- Task filters previously compared raw deadline strings: missing/empty deadlines were treated as overdue, and `None` mixed with strings could crash date sorting.
- Parse deadlines defensively in the Tasks view; exclude undated/invalid legacy tasks from Today/Upcoming/Overdue while retaining them in All. Sorting places undated tasks after dated ones.
- Added UI regression tests for empty, null and invalid dates, plus immediate Today badge updates on task creation, completion and rescheduling.
- **Pending:** confirm Windows CI on latest branch head and a new `WorkBOXig-Windows-review` artifact; manually test legacy profiles and real Windows UI. No merge or stable release.

## Progress notes — 2026-10-30 backup export/import consistency
- Found that the archive writer accepted oversized metadata, oversized attachments, aggregate uncompressed data over 500 MiB, and filenames the importer rejects. Such exports could succeed but fail on restore.
- Preflight archive metadata bytes and attachment sizes/names against the existing importer limits; recheck actual ZIP entry sizes after writing to guard against file growth during export.
- Added regression tests for oversized metadata, a single oversized attachment, excessive aggregate size, and unsafe attachment names.
- The storage export flow already uses a temporary file and atomic replacement, so validation failures leave an existing destination backup untouched. Large or unusual user attachments are **not deleted**; export now fails explicitly rather than creating a non-restorable backup.
- **Pending:** Windows CI for this change and manual export/restore tests using real legacy images. Keep PR draft, do not merge or release.

## Progress notes — 2026-10-30 calendar flicker report
- User reproduced transient blank Windows windows when adding or deleting calendar lessons; windows disappear after the calendar redraw.
- Root cause identified in shared `clear_layout`: `setParent(None)` made visible Qt children temporary top-level windows before deferred deletion.
- Fix hides removed widgets *before* `setParent(None)` and `deleteLater`, preventing visible transient popups while keeping stale widgets out of Qt `findChildren()` queries.
- Added `tests/test_layout_cleanup.py` covering visible calendar-like widgets and empty cleanup.
- **Pending:** confirm latest Windows CI and manually reproduce add/delete/edit of lessons using the new Windows review build. Do not claim the flicker fixed on real Windows until manual verification.
- First Windows CI attempt exposed three tests depending on immediate detachment; revised the fix to hide **before** detaching (instead of keeping old widgets parented) and updated regression test. Verify CI on the latest commit.

## Progress notes — 2026-10-30 dialog and popup UX
- User requested improvements to the popup windows when adding lessons and other records.
- Lesson editor: remove the unmovable frameless fixed 540x680 window, use parent-owned window-modal dialog, bound initial size to screen, place the form in a scroll area, keep Save/Cancel outside the scroll area.
- Task editor: adopt the same high-DPI-friendly scrollable form and fixed footer so lengthy subtask lists do not clip the buttons.
- Fix lesson preset / edited-event color selection: rely on explicit color properties rather than matching tooltip text or CSS substrings.
- Shared layout cleanup now recursively removes controls in nested subtask rows instead of leaving orphaned children that can flash or persist.
- Add tests for visible modal forms, scrollable content, color selection, and nested layout cleanup.
- **Verification required:** review latest Windows CI before recommending any EXE; manually test on Windows at 100%, 125%, 150% DPI, add/edit/delete lessons and tasks, keyboard Escape / close controls and long subtask lists.

## Progress notes — 2026-10-30 beta update channel and updater safety
- Opt-in "Receive beta updates" checkbox in Settings > About > Updates, persisted in `update_channel` (defaults to stable). RU/EN strings and helper text included.
- Stable channel uses GitHub Releases /latest; beta channel checks published releases, selects highest SemVer (including a newer final/stable release) and ignores drafts/invalid tags. Rate-limit fallback does not silently switch beta users to stable.
- Correct semantic version precedence: same-number stable > beta; numeric prerelease identifiers order numerically. Prevent unintended downgrades.
- Verify official GitHub release asset SHA-256 digest when provided, as well as expected download size; reject tampered files and arbitrary EXE-as-installer fallback.
- Label prereleases explicitly in the update dialog. Safely cancel a running download on Escape/window close without destroying a live QThread.
- Use saved update channel for background startup checks and manual settings checks.
- Added mocked API, settings persistence, release ranking, checksum and cancellation tests.
- **Still required:** Windows CI on latest branch head; manual Windows beta opt-in, update from v1.4.7 / v1.5.0-beta.1, and installer smoke test with copied user data. Leave PR draft and stable release unchanged.
