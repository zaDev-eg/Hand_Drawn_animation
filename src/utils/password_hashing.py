from passlib.context import CryptContext

## take instances
context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


## hashing function -> returns the hashed password
def hashing_password(password: str) -> str:
    return context.hash(password)


## verifying function -> returns True if password matches hash, else False
def varifying_password(password: str, hashed_password: str | None) -> bool:
    if not password or not hashed_password:
        return False
    return context.verify(password, hashed_password)