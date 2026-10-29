# WorkBOXig 1.5 — development checklist

Goal: improve reliability and day-to-day usability before adding major features.

## P0 — data safety (first review)
- [x] Bound the size of backup metadata before JSON decoding.
- [x] Reject archive metadata whose root is not a JSON object.
- [x] Add regression tests for malformed and oversized metadata.
- [ ] Test interrupted saves and interrupted restore scenarios on Windows.
- [ ] Test backward compatibility with v1.3–v1.4 backups and notebook images.
- [ ] Document recovery steps for a corrupted local storage file.

## P1 — UI and workflows
- [ ] Audit the Today dashboard at 100%, 125% and 150% DPI.
- [ ] Check keyboard navigation, focus order, and screen-reader labels.
- [ ] Validate recurring events, time zones and day rollover.
- [ ] Verify task creation/completion updates dashboard immediately.
- [ ] Check RU/EN strings and small-window layouts.

## P1 — release quality
- [ ] Run `python -m unittest discover -s tests -v` on Windows.
- [ ] Build portable EXE and installer via GitHub Actions.
- [ ] Manually launch both builds and test first-run onboarding, update checks and data migration.
- [ ] Confirm that updating preserves existing user data.
- [ ] Publish a prerelease only after checks pass.

## Release rule
Do not merge or publish a stable release until Windows CI succeeds and manual backup/import smoke checks pass.
