# Releaseclock

`releaseclock` is an offline tool for turning a **declared** music-release date
and an **owner-authored** list of campaign milestones into a clear timeline,
spreadsheet, and importable calendar file.

It fills a narrow gap between canonical release metadata and a real campaign:
it makes your intended dates visible before you manually schedule, send, upload,
or publish anything.

## What it does

- Reads one local TOML plan with a release date, a written planning basis, and
  milestones you explicitly authored.
- Calculates each milestone date from its signed day offset, including dates
  across month/year boundaries.
- Sorts the timeline chronologically and rejects duplicate milestone IDs after
  whitespace/case normalization.
- Builds a portable Markdown timeline, CSV, deterministic all-day `.ics`
  calendar, and checksum-backed JSON manifest.
- Keeps `check` completely read-only and requires `build` to use a new output
  directory, so an existing reviewed bundle is never overwritten.

## What it does **not** do

- It does not decide which campaign actions you should take, impose a universal
  lead time, or add generic milestones to your plan.
- It does not connect to or import into Google Calendar, Apple Calendar,
  Notion, email, social media, a distributor, Bandcamp, SoundCloud, or any
  other service.
- It does not send outreach, upload content, schedule posts, publish a
  release, inspect a platform, or measure campaign results.

Every output starts with:

```text
DECLARED CAMPAIGN PLAN - EXTERNAL SCHEDULING, CONTENT, OUTREACH, AND PUBLICATION STATUS UNVERIFIED
```

That is intentional. A local plan or an `.ics` file is not proof that anything
was imported, scheduled, made, sent, saved, uploaded, published, or received.

## Install

Requires Python 3.11+ with no runtime dependencies.

```sh
python3 -m pip install .
```

For development:

```sh
python3 -m pip install -e . pytest ruff
pytest
ruff check .
ruff format --check .
```

## Create a plan

Copy [examples/campaign-example.toml](examples/campaign-example.toml) and
replace every field. The example is generic and fictional; it does not describe
or schedule a real release, artist, label, or platform action.

```toml
[release]
artist = "Example Artist"
title = "Example Release"
release_date = "2026-10-23"
timezone = "Europe/Berlin" # optional label included in the .ics calendar
requirements_basis = "Provisional internal campaign plan; manually confirm every external action."

[[milestones]]
id = "metadata-review"
offset_days = -42
title = "Review the declared metadata sheet"
owner = "Artist / label"
status = "planned"
critical = true
evidence_next_step = "Read the current local metadata sheet and note any unresolved fields."
notes = "This does not upload or change metadata anywhere."
```

Each `offset_days` value is relative to `release_date`:

- Negative values are before the declared release date: `-42` is 42 days
  earlier.
- `0` is the declared release date.
- Positive values are after it: `+14` is 14 days later.

Releaseclock does not prescribe those offsets. They are your project-specific
assumptions, so explain the source in `requirements_basis`.

Allowed declared milestone statuses are `planned`, `in_progress`, `blocked`,
and `declared_done`. A status is wording from the plan author, not independent
evidence that the work happened or was accepted.

## Check a plan without writing

```sh
releaseclock check ./campaign.toml
releaseclock check ./campaign.toml --json
```

`--json` contains release data, declared milestones, derived dates, and the
unverified boundary, but never the local plan path.

## Build a local review bundle

`--output` must name a **new** directory whose parent already exists.

```sh
releaseclock build ./campaign.toml --output ./review/example-release-campaign
releaseclock build ./campaign.toml --output ./review/example-release-campaign --json
```

The bundle contains:

- `CAMPAIGN_TIMELINE.md` — readable dates, declared ownership/status, and
  evidence gates.
- `campaign_milestones.csv` — an ordered spreadsheet-friendly register.
- `CAMPAIGN.ics` — a manual-import, all-day calendar representation of the
  declared plan. Releaseclock never imports it for you.
- `manifest.json` — portable plan facts, derived dates, artifact names, and
  a SHA-256 fingerprint of the exact input TOML plus checksums for the other
  three files. It contains no local input/output paths.

The calendar uses deterministic IDs and a deterministic timestamp derived from
the declared release date so the same plan produces the same local calendar
content. That metadata does not represent an import time or a scheduled event.

## Interpretation

Use the generated timeline as a planning and review surface. Before treating a
milestone as real, verify the specific external state it requires: a saved
calendar entry, completed asset, sent outreach, an upload/processing result,
or the intended public page. Record that evidence separately; Releaseclock
does not retrieve or fabricate it.

## License

[MIT](LICENSE)

---

---

<!-- funnel-footer -->
Part of the Gabriel Tools + Code catalog — [browse all tools, products, repositories, and services](https://tools.gabs-utilities.com/).

Free and open source: [theme-contrast](https://github.com/notgabriels-sys/theme-contrast) (WCAG contrast checking for colour themes) · [htmlshot](https://github.com/notgabriels-sys/htmlshot) (HTML → exact-size PNG/PDF) · [50 dark themes for Claude Code](https://github.com/notgabriels-sys/claude-code-50-dark-themes).

Hologram People soundware and Gabriel audio/product work are linked from the master catalog above.

Mixing and mastering enquiries — [public preview](https://gabriel-mixing-and-mastering-d1dmyt.v2.appdeploy.ai/).
