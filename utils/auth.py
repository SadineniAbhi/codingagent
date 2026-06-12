import jwt
import json
import httpx
from functools import lru_cache
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.env import settings

security = HTTPBearer()


@lru_cache
def get_jwks():
    url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


def validate_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)

        jwks = get_jwks()

        rsa_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = key
                break

        if not rsa_key:
            raise HTTPException(
                status_code=401,
                detail="Unable to find matching key",
            )

        public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))

        payload = jwt.decode(
            token,
            public_key, # type: ignore
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
            issuer= f"https://{settings.AUTH0_DOMAIN}/",
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "bro Token expired")

    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, f"bro Invalid token: {exc}")
