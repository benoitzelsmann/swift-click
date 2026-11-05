# Installing Swift Click

The SwiftClick-<version>-Setup.exe file includes the app, Python and its libraries.
It installs offline on Windows 11 x64 with an Intel or AMD processor. Bluetooth is
required for the controller. This package does not qualify macOS or Windows ARM.

## Installation

Open Setup.exe and follow the English-language installer. The desktop shortcut is
optional. Swift Click appears in the Start menu and in Windows Settings → Apps →
Installed apps. Only the right-hand Zwift Click V2 (Y/A/B/Z/+) is supported.

The installation is per user and does not require administrator rights. Its default
folder is %LOCALAPPDATA%\Programs\Swift Click. Preferences are stored separately in
%LOCALAPPDATA%\SwiftClick. Each Windows account has its own settings.

## Language, credits and contact

Choose English or French under Settings → General. The choice applies immediately,
is saved locally and does not restart Bluetooth or MyWhoosh. Custom mouse-position
names remain unchanged. Credits and Contact are also available under Settings.
GitHub feedback links work independently of the future support email address.

Actions contains Mouse positions, Windows and Routines. Select Edge or Chrome
in the window picker to see its open tabs. Double-click a saved item to edit it.
New mouse captures include a small local preview. Selecting a captured position
in a routine fills the window when it can be identified. Edit an older position
and capture it again to add this information.
The Dashboard's Open MyWhoosh button launches the registered game or activates
its running window. Start session establishes Swift Click's connections separately.

## Updates and removal

1.4 adds editable timing controls under Settings → General. Missing values use
the previous defaults. Save applies changes to new presses; active presses retain
their existing timings. Assignments, named targets, language and connections are
preserved. Versions before 1.4 ignore the custom durations and use their defaults.

In 1.3, media controls are grouped together and include Mute / unmute. Gesture
timing details are under Settings → General. Window switching is configured as
a routine step; the old direct Switch windows choice is no longer offered.
Your existing named routines and targets are retained; no default routines are
created. Example screenshots show illustrative assignments only.

Before updating, keep your previous installer and back up the full
`%LOCALAPPDATA%\SwiftClick` folder with Swift Click closed. Older versions cannot
read an assignment using the new mute action. To downgrade, close Swift Click,
back up the current data, reinstall the earlier installer and restore your
configuration backup from that version before opening it.

Version 1.2 adds a window catalogue and visual routine sequences. The upgrade from
1.1 saves `controller.pre-v4.json` and converts existing routines without changing
their button assignments. Windows and mouse positions have stable references;
renaming them keeps routines intact. Deleting one leaves affected routines marked
as needing configuration, rather than silently retargeting an action.

To return to 1.1, close Swift Click normally and back up the full
`%LOCALAPPDATA%\SwiftClick` folder. Install the previous installer and copy
`controller.pre-v4.json` to `controller.json` before starting it. Do not open the
1.2 configuration with the older application.

Run the newer installer. It reuses the existing folder and requests a normal app
shutdown so Bluetooth cleanup can finish. If shutdown does not complete, the
installation stops rather than forcing the app to close.

Updates preserve preferences. The first upgrade from a pre-0.15 configuration
backs up the old settings and resets the fifteen button assignments once.
Bluetooth settings and the keep-awake choice are retained. Upgrading from 0.15 to
the English 0.16 release does not reset assignments or rename saved mouse targets.

The 1.0 → 1.1 upgrade retains all mappings, positions, language and connection
settings. It saves controller.pre-v3.json before migration. Simple stays enabled;
previous Long/Hold gestures are enabled when assigned. Double starts disabled.
Manage these switches in Settings → Buttons → Manage presses. Window targets and
routines are configured under Actions. No temporary window handles are saved.

## Return to 1.0

Keep the previous installer before upgrading. Close Swift Click normally, copy the
entire %LOCALAPPDATA%\SwiftClick folder to a safe backup, then install the previous
1.0 installer. Before opening it, replace controller.json with a copy of
controller.pre-v3.json in the same folder. The 1.0 reader cannot read the 1.1 schema.
Keep the newer configuration backup if you intend to return to 1.1. New Double,
window and routine settings are unavailable in 1.0. The language preferences remain
separate and are retained. No automatic downgrade is performed.

Uninstalling removes the installed files and shortcuts. Saved positions, mappings
and logs remain in the user account for a later reinstallation. If an old unpacked
Swift Click browser extension is still present, remove it once from the browser's
Extensions page. This version does not use a browser extension.

## Silent deployment

Run as the intended Windows user, without elevation.

```powershell
.\SwiftClick-<version>-Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="installation.log"
```

Add `/TASKS="desktopicon"` for a desktop shortcut, or `/TASKS=""` to omit it. Silent
installation does not launch the app. Exit code 0 indicates success. Treat a
nonzero code as a failure and inspect the log. No automatic restart is requested.

## Installer signature

The current installer is unsigned. Windows may warn about or block it depending on the
PC's security settings. A public signing identity requires certificate validation.
A self-signed local certificate does not provide public publisher trust.

Installer checks on the development PC do not replace testing on a clean PC or
qualifying a full ride on the intended Bluetooth hardware.
