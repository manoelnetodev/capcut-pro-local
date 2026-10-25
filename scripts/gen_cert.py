import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

BASE = r'C:\Users\Manoel\AppData\Local\Temp\opencode\mitm'

ca_cert = x509.load_pem_x509_certificate(open(BASE + r'\ca.crt', 'rb').read())
ca_key = serialization.load_pem_private_key(open(BASE + r'\ca.key', 'rb').read(), password=None)

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
now = datetime.datetime.now(datetime.timezone.utc)
subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'www.capcut.com')])
builder = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(ca_cert.subject)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - datetime.timedelta(days=1))
    .not_valid_after(now + datetime.timedelta(days=800))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName('www.capcut.com'),
            x509.DNSName('feed-api-sg.capcut.com'),
            x509.DNSName('*.capcut.com'),
            x509.DNSName('*.capcutapi.com'),
            x509.DNSName('commerce-api-sg.capcutapi.com'),
            x509.DNSName('commerce-api.capcutapi.com'),
            x509.DNSName('commerce-api-va.capcut.com'),
            x509.DNSName('commercepro.capcut.com'),
            x509.DNSName('commerce-api-sg.capcut.com'),
            x509.DNSName('passport-api-sg.capcut.com'),
            x509.DNSName('passport-api-sg.capcutapi.com'),
        ]),
        critical=False,
    )
    .add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True,
    )
    .add_extension(
        x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=True,
                      data_encipherment=False, key_agreement=False, key_cert_sign=False,
                      crl_sign=False, encipher_only=False, decipher_only=False), critical=True,
    )
    .add_extension(
        x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False,
    )
)
cert = builder.sign(ca_key, hashes.SHA256())

open(BASE + r'\server.crt', 'wb').write(cert.public_bytes(serialization.Encoding.PEM)
                                          + ca_cert.public_bytes(serialization.Encoding.PEM))
open(BASE + r'\server.key', 'wb').write(key.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption()))
print('novo server.crt com SANs:', [n.value for n in cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value])
print('valido ate:', cert.not_valid_after_utc)
