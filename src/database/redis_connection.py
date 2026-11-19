from datetime import datetime, timezone
import redis.asyncio as aioredis
from ..utils.config import redis_settings

## Create the connection
token_blocklist = aioredis.from_url(redis_settings.REDIS_URL)


## Method that will add tokens in the blocklist
async def add_tokens_to_blocklist(
    token_data: dict,
    exp: int | None = None,
) -> None:
    jti = token_data.get("jti")
    if not jti:
        return

    if exp is None:
        exp_timestamp = token_data.get("exp")
        if exp_timestamp:
            remaining = int(exp_timestamp - datetime.now(timezone.utc).timestamp())
            exp = max(remaining, 1)
        else:
            exp = 3600

    await token_blocklist.set(
        name=jti,
        value="revoked",
        ex=exp,
    )


## Method that will check if the token is already exist in blocklist
async def check_blocklist(token_data: dict) -> bool:
    jti = token_data.get("jti")
    if not jti:
        return False

    check = await token_blocklist.get(jti)
    return check is not None