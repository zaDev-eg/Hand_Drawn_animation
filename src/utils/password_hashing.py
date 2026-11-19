
from passlib.context import CryptContext

## take instances
context = CryptContext(
    schemes=['argon2']
)

## hashing function -> just returning the hashed version from pass
def hashing_password(password: str):
    return context.hash(password)

## varifying function -> the return value is (True / False)
def varifying_password(password: str, hashed_password: str):
    return context.verify(password, hashed_password)