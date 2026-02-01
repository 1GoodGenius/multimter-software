// Placeholder test certificate and private key (PEM encoded)
// For production, generate a real certificate and private key and replace these strings.
// Example (on host):
//  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=multimeter'

#ifndef BRIDGE_CERTS_H
#define BRIDGE_CERTS_H

// For testing, set these constants to PEM strings. Leave empty to use insecure/non-TLS mode.
// To enable mTLS, set TEST_CA_PEM to the CA cert that signs client certs.
static const char* TEST_CERT_PEM = "";
static const char* TEST_PRIVKEY_PEM = "";
static const char* TEST_CA_PEM = ""; // CA cert used to verify client certs for mTLS (optional)

#endif // BRIDGE_CERTS_H
