from celery import shared_task
from celery.utils.log import get_task_logger

## grab the celery task logger
logger = get_task_logger(__name__)

@shared_task
def dispense(*args, **kwargs):
    logger.info("simulation.dispense")
    return True

@shared_task
def seal(*args, **kwargs):
    logger.info("simulation.seal")
    return True

@shared_task
def spin(*args, **kwargs):
    logger.info("simulation.seal")
    return True


