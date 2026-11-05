# Swift Click privacy

Swift Click reads the controller over Bluetooth and sends gear changes to MyWhoosh
on the local network. PC commands are sent directly to Windows.

Named mouse positions, display characteristics, button assignments, the controller's
Bluetooth reference and activity logs are stored locally in the Windows user
account. A local mouse-motion detector preserves physical pointer movements when
restoring the pointer after a click. When you capture a mouse position, Swift Click
saves a small still image around that point and the window's identity with the
position. The image stays in your local settings and is replaced on recapture.
Remove personal screen content before sharing settings or backups.

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

The interface language, appearance and expanded-guide choices are also saved locally.
Export settings writes a local backup containing assignments, targets, previews and
controller information. Restore settings preserves a recovery copy before replacing
configuration. Treat these backup files as private.

Check for updates contacts GitHub only when selected. GitHub receives the normal
network request, including the connection's IP address. No settings or logs are
included. View release opens GitHub in your browser. Copy technical details places
app/system versions, language/appearance, connection states and saved-item counts
on the clipboard. This report excludes saved names, paths, Bluetooth references
and activity logs. Contact
links open the user's browser or email application only when selected.

The app requires no Swift Click account and includes no telemetry or remote
analytics. The status page is available only through the local loopback interface.

The uninstaller removes the program and keeps preferences and configuration
backups for reinstallation. To remove them, close Swift Click and delete its
SwiftClick folder in the Windows account's local application data.

If you submit an issue on GitHub, it is public. Remove Bluetooth addresses, personal
screen content and account names or private paths from any logs you attach.
