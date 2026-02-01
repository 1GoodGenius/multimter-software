# Authentication & Access Hardening

This project currently implements a simple token-based AUTH frame (FT_AUTH). For lab use this is convenient, but for network-facing deployments you should harden the access path.

Recommendations

- Use SSH local port forwarding when connecting to devices on an untrusted network:

  On the remote/bridge host (e.g., Raspberry Pi or gateway):

  ssh -N -L 5000:localhost:5000 youruser@bridge-host

  Then point the host tooling to localhost:5000. The SSH tunnel provides encryption and authentication using SSH keys.

- Use TLS or mutually-authenticated TLS (mTLS) for transports that support it (TCP/ESP32+TLS).

- Rotate tokens and prefer short-lived credentials. Put token validation behind an ACL if possible.

- Consider adding a pairing step (HMAC exchange or one-time tokens) and store persistent keys in secure storage on the host.

Example: using SSH tunnel + the current host tool

1. On the remote gateway (where the serial device is connected): run the `tools/serial_bridge.py --serial /dev/ttyACM0 --tcp-port 5000`.
2. From your local machine run: `ssh -N -L 5000:localhost:5000 youruser@gateway`.
3. Run the host tool as: `python tools/comm_helper.py --tcp localhost:5000 hello` and `python tools/comm_helper.py --tcp localhost:5000 auth --token <token>`.

These changes add an immediate encryption and authentication layer with minimal changes to your current stack.
