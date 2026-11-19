
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
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
    )
    
    POATGRES_HOST : str = "localhost"
    POSTGRES_PORT : int = "5432"
    POSTGRES_USER : str = "postgres"
    POSTGRES_PASSWORD : int = "1123"
    POSTGRES_DB : str = "Hand_Drawn_animationDB"
    
    
## initiate object from DataBase Class 
db = DataBase()

## Create the DataBase URL 
def data_base_url(db: DataBase): 
    return f"postgresql+asyncpg://{db.POSTGRES_USER}:{db.POSTGRES_PASSWORD}@{db.POATGRES_HOST}:{db.POSTGRES_PORT}/{db.POSTGRES_DB}"


## Fixed Settings 
app_settings = AppSettings()
db_url = data_base_url(db)