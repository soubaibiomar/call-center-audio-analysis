"""Verify signed identity, then resolve enabled users and roles from PostgreSQL."""

from dataclasses import dataclass
from uuid import UUID

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from fastapi import HTTPException
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWTError
from sqlalchemy import select
from sqlalchemy.engine import Engine

from services.api.db.models import ExternalIdentity, User
from services.api.settings import ApiSettings
from src.database.connection import session_scope


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    user_id: str
    role: str

    @property
    def owner_filter(self) -> str | None:
        return self.user_id if self.role == "agent" else None


class Authenticator:
    def __init__(self, settings: ApiSettings, engine: Engine | None) -> None:
        self.settings = settings
        self.engine = engine
        self.jwks = (
            PyJWKClient(settings.jwks_url, timeout=3, lifespan=300) if settings.jwks_url else None
        )
        self.key = (
            serialization.load_pem_public_key(settings.public_key.encode())
            if settings.public_key
            else None
        )
        if self.key is not None and (
            not isinstance(self.key, RSAPublicKey) or self.key.key_size < 2048
        ):
            raise ValueError("OIDC requires an RSA public key of at least 2048 bits")

    def authenticate(self, authorization: str) -> Principal:
        if not self.settings.auth_configured or self.engine is None:
            raise HTTPException(503, "Authentication is not configured")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or len(token) > 16384:
            raise HTTPException(401, "A valid bearer token is required")
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256":
                raise ValueError("Unexpected algorithm")
            key = self.key
            if self.jwks is not None:
                if not isinstance(header.get("kid"), str) or len(header["kid"]) > 255:
                    raise ValueError("Missing key identifier")
                candidate = self.jwks.get_signing_key_from_jwt(token).key
                if not isinstance(candidate, RSAPublicKey) or candidate.key_size < 2048:
                    raise ValueError("Invalid signing key")
                key = candidate
            if not isinstance(key, RSAPublicKey):
                raise ValueError("No signing key")
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.settings.audience,
                issuer=self.settings.issuer,
                options={
                    "require": ["iss", "aud", "sub", "exp", "iat", self.settings.tenant_claim]
                },
            )
            tenant_claim = claims[self.settings.tenant_claim]
            if not isinstance(tenant_claim, str):
                raise ValueError("Tenant claim must be a UUID string")
            tenant = str(UUID(tenant_claim))
            subject = claims["sub"]
            if not isinstance(subject, str) or not 1 <= len(subject) <= 255:
                raise ValueError("Invalid subject")
            if (
                isinstance(claims["exp"], bool)
                or isinstance(claims["iat"], bool)
                or not isinstance(claims["exp"], int | float)
                or not isinstance(claims["iat"], int | float)
                or not 0 < claims["exp"] - claims["iat"] <= 3600
            ):
                raise ValueError("Invalid lifetime")
        except PyJWKClientConnectionError as exc:
            raise HTTPException(503, "Identity verification is temporarily unavailable") from exc
        except (PyJWTError, ValueError, TypeError, KeyError, OverflowError) as exc:
            raise HTTPException(401, "A valid bearer token is required") from exc
        with session_scope(self.engine, tenant_id=tenant) as session:
            user = session.scalar(
                select(User)
                .join(
                    ExternalIdentity,
                    (ExternalIdentity.user_id == User.id)
                    & (ExternalIdentity.tenant_id == User.tenant_id),
                )
                .where(
                    ExternalIdentity.tenant_id == tenant,
                    ExternalIdentity.issuer == self.settings.issuer,
                    ExternalIdentity.subject == subject,
                    User.tenant_id == tenant,
                )
            )
            if (
                user is None
                or not user.enabled
                or user.role not in {"agent", "supervisor", "admin"}
            ):
                raise HTTPException(403, "User access has not been enabled")
            return Principal(tenant, user.id, user.role)
