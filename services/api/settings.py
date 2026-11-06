"""Explicit, fail-closed API configuration; never read a test identity by default."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from services.api.db.settings import database_url


@dataclass(frozen=True)
class ApiSettings:
    synthetic_data: bool = False
    database_url: str | None = field(default=None, repr=False)
    issuer: str = ""
    audience: str = ""
    jwks_url: str = ""
    public_key: str = field(default="", repr=False)
    tenant_claim: str = "tenant_id"
    max_upload_bytes: int = 50 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.max_upload_bytes < 1 or self.max_upload_bytes > 50 * 1024 * 1024:
            raise ValueError("Upload limit must be between 1 byte and 50 MiB")
        if self.issuer:
            issuer = urlsplit(self.issuer)
            if (
                issuer.scheme != "https"
                or not issuer.hostname
                or issuer.username
                or issuer.password
                or issuer.query
                or issuer.fragment
                or len(self.issuer) > 512
            ):
                raise ValueError("OIDC issuer must be a bounded HTTPS issuer URL")
        if len(self.audience) > 255 or not 1 <= len(self.tenant_claim) <= 64:
            raise ValueError("OIDC audience and tenant claim must be bounded")
        if self.jwks_url:
            url = urlsplit(self.jwks_url)
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                raise ValueError("JWKS URL must be an administrator-controlled HTTPS URL")
        if self.public_key and self.jwks_url:
            raise ValueError("Configure either a pinned public key or JWKS, not both")

    @property
    def auth_configured(self) -> bool:
        return bool(self.issuer and self.audience and (self.jwks_url or self.public_key))

    @classmethod
    def from_env(cls) -> "ApiSettings":
        path = os.getenv("OIDC_PUBLIC_KEY_FILE", "")
        return cls(
            database_url=database_url(),
            issuer=os.getenv("OIDC_ISSUER", ""),
            audience=os.getenv("OIDC_AUDIENCE", ""),
            jwks_url=os.getenv("OIDC_JWKS_URL", ""),
            public_key=Path(path).read_text(encoding="utf-8") if path else "",
            tenant_claim=os.getenv("OIDC_TENANT_CLAIM", "tenant_id"),
        )
