from pathlib import Path
from typing import List
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from .config import mail_settings

## get back the current working dir
Current_WD = Path(__file__).resolve().parent  ## -> got the parent dir


## set the connection Config for the main service
mail_config = ConnectionConfig(
    MAIL_USERNAME=mail_settings.MAIL_USERNAME,
    MAIL_PASSWORD=mail_settings.MAIL_PASSWORD,
    MAIL_PORT=mail_settings.MAIL_PORT,
    MAIL_SERVER=mail_settings.MAIL_SERVER,
    MAIL_STARTTLS=mail_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=mail_settings.MAIL_SSL_TLS,
    MAIL_FROM=mail_settings.MAIL_FROM,
    MAIL_FROM_NAME=mail_settings.MAIL_FROM_NAME,
    TEMPLATE_FOLDER=Path(Current_WD, "templates"),
)


## take an instance from the module
mail = FastMail(config=mail_config)


## create the meassage
def create_mail_message(
    recipients: List[str],
    body: str,
    subject: str,
):

    ## build the message
    message = MessageSchema(
        recipients=recipients,
        body=body,
        subject=subject,
        subtype=MessageType.html,  ## that means the message will be in html formate
    )

    ## return the message to be sent to the client by the endpoint
    return message
