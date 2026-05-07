"""
自签名 SSL 证书生成脚本
用于 WSS（WebSocket Secure）测试

使用方法:
    python generate_cert.py

生成文件:
    cert.pem  - 证书文件
    key.pem   - 私钥文件
"""

import datetime
import ipaddress
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_self_signed_cert(cert_file: str = "cert.pem", key_file: str = "key.pem") -> None:
    # 生成 RSA 私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 证书主题信息
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Test"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WebRTC Signaling Test"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    # 构建证书
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    # 写入证书文件
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # 写入私钥文件
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    print(f"[OK] 证书已生成: {cert_file}")
    print(f"[OK] 私钥已生成: {key_file}")
    print("[提示] 浏览器访问 WSS 时需要手动信任此自签名证书")
    print("       Chrome: 访问 https://localhost:8766 并点击「高级」->「继续访问」")


if __name__ == "__main__":
    generate_self_signed_cert()
