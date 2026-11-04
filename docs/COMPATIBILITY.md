# Compatibility and beta status

| Component | Initial beta |
| --- | --- |
| Operating system | Windows 11 x64, Intel or AMD |
| Controller | Zwift Click V2 right, tested firmware 1.2.0 |
| Other controllers | Left Click V2, Click V1, Play and Ride controls are not supported |
| MyWhoosh | Network connection through OpenBikeControl |
| Media | Windows media and volume commands |
| Video navigation | Complete left/right key presses to the focused player |
| Mouse | Current pointer or named physical screen coordinates |
| macOS / Windows ARM | Not qualified |
| Browser extension | Not used |

Controller connection, media commands and MyWhoosh shifting have been tested on the development PC. Installer launch, upgrade with the app running, settings preservation and uninstall have been tested in an isolated installation on that PC. These tests do not establish compatibility with every Windows PC.

Clean-PC installation, physical multi-display configurations with different scaling, real YouTube/Netflix mouse targets and two 90-minute controller sessions remain part of beta qualification. Video seeking depends on the player, its focus and shortcuts. A named mouse target must be repositioned when the target window moves or the display configuration changes.

The optional keep-awake method uses the controller's firmware-update mechanism. It is restricted to the tested hardware/firmware and explicit consent. Long-term effects have not been qualified. Normal app closure attempts to exit this mode before shutdown.

Please include the Swift Click version and Windows version in reports. Do not publish Bluetooth addresses, private screen captures or unedited logs containing personal paths.
