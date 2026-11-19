
## Imports 
from typing import List
from datetime import datetime
from pydantic import BaseModel 
from enum import Enum

## Enum Class 
class UserRole(str, Enum): 
    ADMIN = "admin"
    USER = "user"

## Base Schema
class Base(BaseModel): 
    username: str 
    email: str 

## Request Schema for a user 
class GetUser(Base): 
    created_at: datetime
    updated_at: datetime
    
class CreateUser(Base): 
    password: str
    role: UserRole
    
class UpdateUser(Base): 
    username: str = None ## -> to be obtional 
    email: str = None ## -> to be obtional
    password: str = None ## -> to be obtional 
    
class Login_User(BaseModel):
    email: str
    password: str 
    
    
class MailSchema(BaseModel): 
    emails: List[str]