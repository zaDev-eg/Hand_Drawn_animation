
## Imports 
from pydantic_settings import BaseSettings, SettingsConfigDict

## The main Settings for all classes 
class BaseConfigurations(BaseSettings):
    model_config = SettingsConfigDict(
            env_file=".env",
            extra="ignore"
        )

class AppSettings(BaseConfigurations):
    APP_NAME : str = "Hand_Drawn_animation"
    APP_VERSION : str = "1.0.0"


class DataBase(BaseConfigurations): 
    
    POATGRES_HOST : str = "localhost"
    POSTGRES_PORT : int = "5432"
    POSTGRES_USER : str = "postgres"
    POSTGRES_PASSWORD : int = "1123"
    POSTGRES_DB : str = "Hand_Drawn_animationDB"
    
    
class JwtSetting(BaseConfigurations): 
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    
    
class MailConfig(BaseConfigurations): 
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM: str
    MAIL_FROM_NAME: str

    ## mail verification 
    DOMAIN_NAME: str
    
    
## open a connection with Redis database 
class RedisConfig(BaseConfigurations): 
    # REDIS_HOST: str = "localhost"
    # REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    
    
    
## initiate object from DataBase Class 
db = DataBase()
jwt_settings = JwtSetting()
mail_settings = MailConfig()
redis_settings = RedisConfig()



## Create the DataBase URL 
def data_base_url(db: DataBase): 
    return f"postgresql+asyncpg://{db.POSTGRES_USER}:{db.POSTGRES_PASSWORD}@{db.POATGRES_HOST}:{db.POSTGRES_PORT}/{db.POSTGRES_DB}"


## Fixed Settings 
app_settings = AppSettings()
db_url = data_base_url(db)