import sys
from OpenSSL import SSL
from cryptography import x509
from cryptography.x509.oid import NameOID
import idna
from socket import socket

CACHE = 1200  # How many seconds to cache result


def cert_to_dict(cert):
    crypto_cert = cert.to_cryptography()
    return {
        "serial": crypto_cert.serial_number,
        "fingerprint": crypto_cert.fingerprint(
            crypto_cert.signature_hash_algorithm
        ).hex(),
        "algo": crypto_cert.signature_hash_algorithm,
        "version": crypto_cert.version,
        "cn": get_common_name(crypto_cert),
        "alt": get_alt_names(crypto_cert),
        "issuer": get_issuer(crypto_cert),
        "not_before": crypto_cert.not_valid_before,
        "not_after": crypto_cert.not_valid_after,
        "is_expired": cert.has_expired(),
    }


def get_alt_names(cert):
    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        return ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return None


def get_common_name(cert):
    try:
        names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        return names[0].value
    except x509.ExtensionNotFound:
        return None


def get_issuer(cert):
    try:
        names = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        return names[0].value
    except x509.ExtensionNotFound:
        return None


TAGS = ["ssl", "tls", "certificate", "network"]


SCHEMA = r"""
hostname:
    type: string
    anyOf:
        - format: ipv4
        - format: ipv6
        - format: hostname
port:
    type: integer
    default: 443
"""


def task(hostname, port=443):
    parts = hostname.split(":")
    hostname = parts[0]
    port = parts[1] if len(parts) > 1 else port

    hostname_idna = idna.encode(hostname)
    sock = socket()
    sock.connect((hostname, port))
    peername = sock.getpeername()
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.check_hostname = False
    ctx.verify_mode = SSL.VERIFY_NONE

    ssl_cxn = SSL.Connection(ctx, sock)
    ssl_cxn.set_connect_state()
    ssl_cxn.set_tlsext_host_name(hostname_idna)
    ssl_cxn.do_handshake()
    cert = ssl_cxn.get_peer_certificate()

    """
    for index in range(0, cert.get_extension_count()):
        print(cert.get_extension(index))
        print("-------")
    """
    chain = [cert_to_dict(c) for c in ssl_cxn.get_peer_cert_chain()]
    crypto_cert = cert.to_cryptography()
    ssl_cxn.close()
    sock.close()

    return {
        "peername": peername,
        "hostname": hostname,
        "serial": crypto_cert.serial_number,
        "fingerprint": crypto_cert.fingerprint(
            crypto_cert.signature_hash_algorithm
        ).hex(),
        "algorithm": crypto_cert.signature_hash_algorithm.name,
        "version": crypto_cert.version.name,
        "cn": get_common_name(crypto_cert),
        "alt": get_alt_names(crypto_cert),
        "issuer": get_issuer(crypto_cert),
        "not_before": crypto_cert.not_valid_before,
        "not_after": crypto_cert.not_valid_after,
        "is_expired": cert.has_expired(),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print({})
        exit(1)

    target = sys.argv[1]
    parts = target.split(":")
    host = parts[0]
    port = parts[1] if len(parts) > 1 else 443

    cert = task(host, port)
    print(cert)
