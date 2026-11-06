# Swift Click

Ride **MyWhoosh on Windows with a Zwift Click V2 right controller**: change gears, move across the road, pick your road at junctions, and control music, videos and windows without leaving the saddle.

[Download 3.1.0 for Windows](https://github.com/benoitzelsmann/swift-click/releases/download/v3.1.0/SwiftClick-3.1.0-Setup.exe) · [Release notes](https://github.com/benoitzelsmann/swift-click/releases/tag/v3.1.0) · [Report an issue](https://github.com/benoitzelsmann/swift-click/issues) · [Installation](docs/INSTALLATION.md) · [Compatibility](docs/COMPATIBILITY.md) · [Privacy](docs/PRIVACY.md)

![Visual routine editor: open YouTube, click Skip, return to MyWhoosh](docs/images/routine-editor.png)

## Why Swift Click

Many smart trainers ship with Zwift Cog and Click hardware. [MyWhoosh is free to ride](https://www.mywhoosh.com/docs/is-there-a-membership-fee-to-use-mywhoosh/), but the Click V2 does not pair with it for shifting. Swift Click bridges the two: it reads the controller over Bluetooth and talks to MyWhoosh through the OpenBikeControl protocol. No account, subscription, daily limit or telemetry.

**Supported controller:** the right-hand Zwift Click V2 (buttons **Y, A, B, Z, +**). The left-hand controller, Click V1, Zwift Play and Zwift Ride are not supported.

## What's new in 3.1

- **Junctions.** Pick *left*, *straight* or *right* when MyWhoosh shows its direction buttons. Swift Click reads the arrows on screen at the moment you press, so it works with two or three buttons, wherever they appear.
- **Move left / right.** Lateral moves on the road use OpenBikeControl *Steer* commands, so MyWhoosh doesn't need to be in front. A / D keys remain as a fallback.
- **One Connections page.** Controller and MyWhoosh side by side, guides underneath.
- **Faster button setup.** *Manage presses* shows a check box next to each gesture, right on the diagram.
- **A calmer interface.** New blue theme in light and dark, clear icons on every button, one-tap choices instead of drop-down menus, shorter texts.
- **A link that holds.** Keep-alive on both sides, automatic recovery after sleep or a network change, and stale commands discarded instead of shifting late.

## Features

| | |
|---|---|
| **MyWhoosh** | Gear up / down, move left / right, junction left / straight / right |
| **Media** | Volume, mute, play / pause, previous / next track, video seek |
| **Windows** | Show, switch, minimize or close saved apps and browser tabs |
| **Clicks** | Click at the pointer or at a saved screen position, then restore the pointer |
| **Routines** | Chain actions visually: show a video, click *Skip*, return to MyWhoosh |
| **Gestures** | Simple, Double, Long and Continuous hold on each of the five buttons |
| **Comfort** | Light, dark or system theme · English and French · settings backup |

## Junctions

Assign **Junction left**, **Junction straight** or **Junction right** under **Settings → Buttons → MyWhoosh**. When MyWhoosh shows its direction tiles, press the gesture: Swift Click finds the tile with the matching arrow and clicks it inside MyWhoosh, then puts the pointer back. If that direction isn't offered, nothing is clicked and the app tells you.

MyWhoosh offers no keyboard shortcut or network command for junctions, so Swift Click looks at a small band of the MyWhoosh window, only when you press, entirely on your PC. Nothing is saved or sent.

## Routines

Prepare **Mouse positions** and **Applications and media** under **Actions**, then build a routine: drag steps into the sequence, pick their targets, confirm. Assign it to a gesture under **Settings → Buttons → Routines** — the routine list opens directly.

Example, *Skip ad and return*: show YouTube, click the saved *Skip* position, return to MyWhoosh.

![Routine catalogue](docs/images/routines.png)

## Applications and media

Save MyWhoosh, an application or a website (YouTube, Netflix, Deezer or your own address) under **Actions → Applications and media**. Websites are found by address, so a new video title doesn't break them. Swift Click never minimizes or moves MyWhoosh.

![Applications and media](docs/images/windows.png)

[Read the windows, clicks and routines guide](docs/ACTIONS.md).

## Install

1. Download the file ending in **Setup.exe** from [Releases](https://github.com/benoitzelsmann/swift-click/releases) and run it. Python is included.
2. In **Connections**, wake the controller and choose **Connect**.
3. Choose **Connect** for MyWhoosh, then in MyWhoosh click the **OpenBikeControl** handlebar icon and accept with **YES**.
4. Assign your buttons under **Settings → Buttons**.

Requires Windows 10 22H2 or Windows 11 (x64) with Bluetooth. The installer is unsigned: Windows may warn before running it. Check the SHA-256 checksum in the release notes.

## Good to know

- **Gesture timings** (defaults): Simple on release, Double within 300 ms, Long from 650 ms, Continuous hold from 1.5 s. Editable under **Settings → General**.
- **Keep awake** is an optional, experimental mode for controller firmware 1.2.0. It uses the firmware-update mechanism and asks for your consent first.
- **Targeted input is verified.** Keys and clicks are sent only when the expected window is in front and the point isn't covered.

## Compared with BikeControl

[BikeControl](https://bikecontrol.app/) supports many controllers and apps and is a useful OpenBikeControl reference. Swift Click focuses on one setup — right Click V2, MyWhoosh, Windows — and is free with no daily action limit. See [BikeControl's pricing](https://bikecontrol.app/pricing/) for its current plans.

## This repository

Public distribution and issue tracking. `ui/` holds the PySide6 interface sources; the Bluetooth engine and system controls are private, so these files don't run on their own — use the installer. Publishing the UI sources doesn't grant an open-source license.

Swift Click is an independent project by [benoitzelsmann](https://github.com/benoitzelsmann), not affiliated with Zwift or MyWhoosh. Product names and logos belong to their owners. Feedback: [GitHub Issues](https://github.com/benoitzelsmann/swift-click/issues) or **Settings → Contact** in the app.
