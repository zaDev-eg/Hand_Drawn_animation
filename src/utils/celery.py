import src.utils.config as celery_config
from typing import List
from celery import Celery
from asgiref.sync import async_to_sync
from ..utils.mail_service import create_mail_message
from .mail_service import mail

## get the instance from Celery module
c_app = Celery()

## set the configurations
c_app.config_from_object(celery_config)


## create the operation that will work as a backgroundTask
@c_app.task()
def send_message(recipients: List[str], subject: str, body: str):

    ## create the message that will be send via email
    message = create_mail_message(
        recipients=recipients,
        subject=subject,
        body=body,
    )

    ## -> this process will be added to BackGroundTasks
    ## send the message
    async_to_sync(mail.send_message)(message)
