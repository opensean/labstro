## Sean Landry
from decouple import config

## FLASK
## python3 -c 'import os; print(os.urandom(16).hex())'
SECRET_KEY=config("SECRET_KEY", default = "dev")

## python module to use for loading plugins
LABSTRO_PLUGINS=[]
LABSTRO_SIMULATION_PLUGINS=["labstro.plugins.simulation"]

## API
LABSTRO_API_JSONSCHEMA_ROOT="config"
LABSTRO_API_JSONSCHEMA_DEFAULT="schema/default.schema.json"


LABSTRO_CELERY_RESULT_BACKEND="redis://:labstro_dev@labstro-redis:6379/0"
LABSTRO_INCLUDE=["labstro.labstro"] + LABSTRO_PLUGINS + LABSTRO_SIMULATION_PLUGINS
LABSTRO_BROKER_URL="amqp://guest:guest@labstro-rabbitmq:5672//"
LABSTRO_CELERY_TASK_ACKS_LATE=True
LABSTRO_BROKER_POOL_LIMIT=0
#LABSTRO_BEAT_SCHEDULE = {}

LABSTRO_TASK_ROUTES={
    'labstro.plugins.simulation.*': {'queue': 'labstro-simulation'},
    }

