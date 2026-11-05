# Swift Click 3.0 deployment

## Supported target

Windows 11 x64 (build 22000 or later), Intel or AMD, and the right-hand Zwift Click
V2 controller. The installer bundles its runtime. Installation is per Windows user
and requires no administrator privileges. Bluetooth and the MyWhoosh local network
connection must be available to that user.

## Verify and install

Download the Setup.exe, SHA256SUMS.txt and release.json from the same release.
Compare the installer's SHA-256 with both accompanying files. A managed deployment
can pin this digest in its software catalogue. The release manifest also records
version, architecture, minimum OS, size and whether the package is signed.

Run in the target user's interactive or user deployment context:

```powershell
$installer = 'C:\Packages\SwiftClick-3.0.0-Setup.exe'
$setup = Start-Process -FilePath $installer -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/LOG="C:\Packages\SwiftClick-install.log"' -WindowStyle Hidden -Wait -PassThru
if ($setup.ExitCode -ne 0) { throw "Swift Click installation failed ($($setup.ExitCode)). See the installer log." }
```

The default location is `%LOCALAPPDATA%\Programs\Swift Click`. The installer
reuses an existing installation path and asks the running app to disconnect and
close normally. If shutdown fails, installation stops. The application's version
is registered under `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\SwiftClick.Desktop_is1`
in DisplayVersion. Validate that it equals the intended release before declaring
the deployment successful. Running the installer in a SYSTEM context installs for
that context, so use a deployment tool's user installation mode.

The package can be distributed from an internal software catalogue or installed
manually from GitHub. A direct public download supports individual users without
an application account or central runtime service.

## Data and recovery

Settings and local backups are in `%LOCALAPPDATA%\SwiftClick`. Export settings
before a managed rollout. A configuration backup contains controller references,
window paths and small captured images, so protect it as user data. The installer
preserves it during upgrades. Uninstalling removes program files and preserves
user settings. To remove user data, close the app and remove that user's SwiftClick
data directory according to your retention policy.

Roll out to a small group first, verify Bluetooth/network access and the user's
saved assignments, then expand deployment. Keep the previous installer and exported
configuration available for rollback. A previous application may not understand
future configuration formats, so restore its matching backup when reverting.

## Publisher trust

The current build is unsigned unless release.json says signed=true. Windows or an
organization's application-control policy may block unsigned executables. For such
environments, request a package signed with an approved identity from the maintainer
before rollout. Checksums provide integrity, not publisher identity.
No signing certificate is distributed with this repository.
