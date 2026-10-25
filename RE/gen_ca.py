import os
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

BASE = r'C:\Users\Manoel\AppData\Local\Temp\opencode\mitm'
os.makedirs(BASE, exist_ok=True)

now = datetime.utcnow()

# 1) CA
ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ca_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, 'CapCut Local CA'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'capcut-local'),
])
ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_name)
    .issuer_name(ca_name)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - timedelta(days=1))
    .not_valid_after(now + timedelta(days=3650))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .add_extension(x509.KeyUsage(
        digital_signature=True, key_cert_sign=True, crl_sign=True,
        content_commitment=False, key_encipherment=False, data_encipherment=False,
        key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
    .sign(ca_key, hashes.SHA256())
)

# 2) Serv cert multi-SAN
HOSTS = [
    'commerce-api-sg.capcutapi.com',
    'commerce-api.capcutapi.com',
    'commerce-api-va.capcut.com',
    'commercepro.capcut.com',
]
sv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
sv_cert = (
    x509.CertificateBuilder()
    .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HOSTS[0])]))
    .issuer_name(ca_name)
    .public_key(sv_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - timedelta(days=1))
    .not_valid_after(now + timedelta(days=3650))
    .add_extension(x509.SubjectAlternativeName([x509.DNSName(h) for h in HOSTS]), critical=False)
    .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    .sign(ca_key, hashes.SHA256())
)

def w(path, data):
    with open(os.path.join(BASE, path), 'wb') as f:
        f.write(data)

w('ca.key', ca_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
w('ca.crt', ca_cert.public_bytes(serialization.Encoding.PEM))
w('ca.der', ca_cert.public_bytes(serialization.Encoding.DER))
w('server.key', sv_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
w('server.crt', sv_cert.public_bytes(serialization.Encoding.PEM))
print('OK: CA + servidor criados em', BASE)
print('hosts cobertos:', ', '.join(HOSTS))
