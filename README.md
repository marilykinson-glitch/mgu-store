# MGU Store Installer (Windows)

A small Windows GUI wrapper for the **official MGU Store installer**. It does not patch the head unit, bootstrap root access, or create SSH keys.

## Requirements
- Windows 10/11
- BMW MGU reachable from this PC over ENET or the MGU hotspot/network
- Existing working root SSH access and the matching private SSH key
- Vehicle parked with stable power

## Run from source
1. Install Python 3.10+.
2. Run `python app.py`.
3. Choose the existing root private key.
4. Optionally enter the MGU IP address. Leave it blank to let the official installer discover the head unit.
5. Click **Install MGU Store** and follow the output.

The app checks for the Windows OpenSSH Client and offers to install the Windows optional feature if it is missing. That step may request administrator approval.

## Build a Windows executable
Run `build_windows.bat`. The output is `dist\\MGU-Store-Installer.exe`.

## Radmin VPN / remote customer installs
Radmin VPN connects PCs to each other; it does **not** automatically expose the MGU's ENET/hotspot network to your PC. Supported practical workflow:
- Copy/run this app on the customer's Windows PC that is physically/network-connected to the MGU, then control that PC through Radmin; or
- Configure and verify a deliberate network route/SSH jump path from your PC through the customer's PC before attempting a remote install. This GUI currently targets the MGU from the Windows PC on which it is running; it is not an SSH-jump client.

Do not assume the customer's Radmin IP is the MGU IP.

## Safety
- This app uses the upstream project's published `deploy/install.ps1`, which downloads the release installer and verifies it against the release `SHA256SUMS`.
- It requires an existing private key. It will never generate, upload, or print a private key.
- It only runs `first-install`; it does not run `--arm-debug` or other root/debug bootstrap actions.
- Keep the vehicle parked and power stable. Do not disconnect power during installation.
- Review the upstream project and its instructions: https://github.com/robertnisipeanu/mgu-store

## License
MIT for this wrapper. The MGU Store installer and related upstream components remain subject to their respective licenses.
