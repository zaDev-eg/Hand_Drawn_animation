import logging
from typing import List

from celery import Celery
from asgiref.sync import async_to_sync

from ..utils.mail_service import create_mail_message
from .mail_service import mail
from .config import redis_settings


logger = logging.getLogger(__name__)


# Create Celery instance and connect it to Redis
c_app = Celery(
    "Hand_Drawn_animation",
    broker=redis_settings.REDIS_URL,
)


# Background task for sending emails
@c_app.task(bind=True)
def send_message(self, recipients: List[str], subject: str, body: str):

    try:
        message = create_mail_message(
            recipients=recipients,
            subject=subject,
            body=body,
        )

        async_to_sync(mail.send_message)(message)

        logger.info(
            "Email sent successfully to %s | Task ID: %s",
            recipients,
            self.request.id,
        )

        return "Email sent successfully"

    except Exception:

        logger.exception(
            "Failed to send email to %s | Task ID: %s",
            recipients,
            self.request.id,
        )

        raise