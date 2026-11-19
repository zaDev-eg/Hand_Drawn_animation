
import redis.asyncio as aioredis
from ..utils.config import redis_settings



## Create the connection
token_blocklist = aioredis.from_url(redis_settings.REDIS_URL)


## Method that will add tokens in the blocklist
async def add_tokens_to_blocklist(
    token_data: dict,
    exp: int = 3600,
) -> None:
    
    ## add the token to the database
    await token_blocklist.set(
        name=token_data["jti"],
        value="revoked",
        ex=exp,
    )


## Method that will check if the token is already exist in blocklist 
async def check_blocklist(token_data: dict) -> bool: 
    
    ## got the token by jti
    check = await token_blocklist.get(token_data['jti'])
    
    ## check the token exist 
    if check is None: 
        return False ## -> means the token was not found 
    return True ## means the token was found 