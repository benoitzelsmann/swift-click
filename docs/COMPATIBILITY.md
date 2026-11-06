# Swift Click 3.5.0 compatibility

3.5.0 is a Windows desktop release with an unsigned installer. The following separates implemented
features, completed checks and hardware qualification still in progress.

| Component | Scope |
| --- | --- |
| Operating system | Windows 10 22H2 or Windows 11, x64, Intel or AMD |
| Controller | Zwift Click V2 right, Y/A/B/Z/+, tested firmware 1.2.0 |
| Other controllers | Left Click V2, Click V1, Play and Ride are not supported |
| MyWhoosh gears | OpenBikeControl network connection; independent of foreground focus |
| Media | Windows volume, mute/unmute, play/pause and previous/next track |
| Video | Complete left/right key presses to the selected Media window; player needs keyboard focus |
| Applications and media | Named applications and websites (YouTube, Netflix, Spotify or custom); MyWhoosh is never minimized or moved |
| Websites | Existing Edge and Chrome tabs identified by their address, not the video title; several matches ask for a choice |
| Routines | Simple actions plus ordered open, activate, minimize, normal close, switch, click, seek and wait steps; routines cannot close or minimize MyWhoosh |
| MyWhoosh moves | OpenBikeControl Steer Left/Right when MyWhoosh announces them, otherwise A / D keys with MyWhoosh in front |
| MyWhoosh junctions | Reads the on-screen direction tiles at press time and clicks the matching arrow inside MyWhoosh; tested with MyWhoosh 5.7.0 at 1920 × 1080 |
| MyWhoosh ERG intensity | Finds the Intensity bar at press time and clicks − or + inside MyWhoosh, 1 to 10 clicks per press; recognised from a MyWhoosh 5.7.0 capture, not yet qualified in a live workout |
| Mouse | Named physical coordinates, local previews and associated windows; targeted routine clicks verify the window |
| macOS / Windows ARM | Not available or qualified |
| Browser extension | Not used |

Five editable timing controls were added in 1.4.0. Existing configurations receive the previous defaults without resetting assignments; active presses retain their snapshots.

## Completed checks

- 198 automated tests cover gesture boundaries/exclusivity, mute assignment,
  multimedia key pairs, migration, saved references, routine editing/reordering,
  cancellation, activation denial, covered clicks and held-key release. Version 3.0
  also covers backup/recovery, catalogue filtering, routine duplication, system
  appearance, translated update notices, local HTTP origins and service cleanup.
- English/French layouts checked at minimum and default sizes, including 100%,
  125%, 150% and 200% simulated scaling across all ten pages and the action, window,
  position and routine editors in Light and Dark. Supplementary checks cover
  scrolled backup/update controls, offline status, recovery and confirmation dialogs.
- The right controller transmitted all five buttons in a read-only physical check.
  Earlier real media commands and MyWhoosh shifting worked on the development PC.
- A named click reached a local test button exactly once on each of two displays
  at 120/96 DPI, with pointer restoration. Simulated tests cover negative origins,
  changed displays and physical movement taking priority over cursor restoration.
- The Routine Test button completed six alternating selections in Edge tabs and
  six between Edge and MyWhoosh. The same twelve checks passed with Chrome using
  local test pages. Swift Click was brought forward again before each click.
  These checks exercised switching, not media playback or physical controller input.
- Installer checks include x64 payload, resources, Per-Monitor V2/asInvoker
  manifest, isolated startup/migration/running-app upgrade/uninstall, and user-data
  preservation. The 2.0.0 → 3.0.0 upgrade was checked on the development PC;
  configuration and interface-preference hashes remained unchanged.

## Remaining qualification

An independent clean-PC installation, two 90-minute rides including 30 minutes
without input, controller-driven foreground routines during a ride, real
YouTube/Netflix mouse targets, MyWhoosh lane/junction semantics, and physical
negative-coordinate/disconnected-monitor scenarios remain to be qualified.
Simulated checks do not establish compatibility with every Windows PC.

The optional keep-awake method is experimental. It is restricted to the tested
right controller firmware 1.2.0 and explicit consent. It uses the firmware-update
mechanism and can erase the secondary firmware slot. Long-term effects are not
qualified. Normal shutdown attempts to exit that mode before closing.

Report the app/Windows versions and steps to reproduce. Remove personal details,
Bluetooth addresses and private paths from public screenshots and logs.
