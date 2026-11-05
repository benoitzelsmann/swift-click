# Compatibility and 1.2.0 draft status

| Component | Windows release candidate |
| --- | --- |
| Operating system | Windows 11 x64, Intel or AMD |
| Controller | Zwift Click V2 right, tested firmware 1.2.0 |
| Other controllers | Left Click V2, Click V1, Play and Ride controls are not supported |
| MyWhoosh | Network connection through OpenBikeControl |
| Media | Windows media and volume commands |
| Video navigation | Complete left/right key presses to the selected Video window; player needs keyboard focus |
| Window control | Named targets, MyWhoosh/media detection, verified foreground and visual sequences |
| MyWhoosh arrows | Separate from gears; held key released on focus loss; junction behaviour unverified |
| Mouse | Current pointer or named physical screen coordinates |
| macOS / Windows ARM | Not qualified |
| Browser extension | Not used |

The development PC has been used to test media commands and MyWhoosh shifting. For 1.0.0, a real right controller with firmware 1.2.0 transmitted all five buttons and disconnected cleanly in a read-only test. A native named mouse click reached a local test button once on each of two real displays at 125% and 100% scaling, with the pointer restored after each click. These tests do not establish compatibility with every Windows PC.

The UI was rendered and checked at simulated 100%, 125%, 150% and 200% scaling in both languages, at minimum and default window sizes. The installer checks include executable manifest validation and live Per-Monitor V2 window awareness.

Clean-PC installation, physical negative-coordinate/disconnected-monitor scenarios, real YouTube/Netflix mouse targets and two 90-minute controller sessions remain part of qualification. Video seeking depends on the player, its focus and shortcuts. A named mouse target must be repositioned when the target window moves or the display configuration changes.

The new foreground service is covered by cancellation, activation-denial, ambiguous-window and key-release tests. Physical MyWhoosh/Edge switching and MyWhoosh lateral/junction behaviour remain unqualified: MyWhoosh reported a server error during preparation. Simulated tests are not ride qualification.

The 1.2 candidate passed 138 automated tests. Native mouse clicks passed on both attached displays (125% and 100%), with one click and cursor restoration. Native minimize/normal close passed on disposable windows. A live MyWhoosh/media focus check completed one switch, then Windows refused activation; no keys or clicks were sent. Reliable repeated switching remains to be qualified. The isolated 1.2 installer passed migration from the 1.0 configuration format, normal launch, running-app upgrade and uninstall. The development installation retained its configuration and assignments.

The optional keep-awake method uses the controller's firmware-update mechanism. It is restricted to the tested hardware/firmware and explicit consent. Long-term effects have not been qualified. Normal app closure attempts to exit this mode before shutdown.

Please include the Swift Click version and Windows version in reports. Do not publish Bluetooth addresses, private screen captures or unedited logs containing personal paths.
