# Swift Click privacy

Swift Click reads the controller over Bluetooth and sends gear changes to MyWhoosh
on the local network. PC commands are sent directly to Windows.

Named mouse positions, display characteristics, button assignments, the controller's
Bluetooth reference and activity logs are stored locally in the Windows user
account. A local mouse-motion detector preserves physical pointer movements when
restoring the pointer after a click. Mouse actions do not require screen recording.

Selecting a window reads the titles and application paths of open windows. Only
the saved application identities and titles are stored locally, along with
named routine settings. Temporary window handles stay in memory for the session.
They are not uploaded. No browser page contents are read.
Automatic detection reads media sessions exposed by Windows, including application
identifiers and current media titles, to match an open player window. Media titles
are used in memory only and are not logged or uploaded. Detection does not inspect
browser history or page contents. Ambiguous matches require a manual selection.
The Open MyWhoosh button looks up MyWhoosh's local Start-menu registration. It
does not send an installation inventory to a server.

The interface language and expanded-guide choices are also saved locally. Contact
links open the user's browser or email application only when selected.

The app requires no Swift Click account and includes no telemetry or remote
analytics. The status page is available only through the local loopback interface.

The uninstaller removes the program and keeps preferences and configuration
backups for reinstallation. To remove them, close Swift Click and delete its
SwiftClick folder in the Windows account's local application data.

If you submit an issue on GitHub, it is public. Remove Bluetooth addresses, personal
screen content and account names or private paths from any logs you attach.
