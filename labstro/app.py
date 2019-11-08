# -*- coding: utf-8 -*-

## Sean Landry
from flask import Flask, escape, request
from celery import Celery
import logging
from flask_restful import Api
from .api import apiv1
from flask.logging import default_handler

root = logging.getLogger()
root.addHandler(default_handler)
root.setLevel(logging.INFO)

def make_celery(app):
    """
    Instantiate and configure a Celery application using a Flask configuration.

    Args:
        app (flask.Flask): instance of a Flask application.

    Returns:
        celery (celery.Celery): instance of a Celery application.

    """
    celery = Celery(
        app.import_name
    )
    celery.config_from_object(app.config, namespace='LABSTRO')

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def make_flask(config_obj="labstro.config.settings.default",
               user_config_obj="labstro.config.settings.user.default",
               app_name = "labstro"):
    """
    Instantiate and configure a Flask application.

    Kwargs:
        config_obj (str):  python module containing flask settings.

        user_config_obj (str):  python module containing user defined flask settings.

        app_name (str):  name given to flask application.

    """

    ## setup flask app
    app = Flask(app_name)
    app.config.from_object(config_obj)
    app.config.from_object(user_config_obj)

    return app


## setup flask app
app = make_flask()

app.logger.setLevel(logging.INFO)

## setup api
api = Api(app)


## setup celery
celery = make_celery(app)
celery.loader.import_default_modules()
app.logger.info("registered routes: " + str(celery.conf["LABSTRO_TASK_ROUTES"]))
app.logger.info("including: " + str(celery.conf["LABSTRO_INCLUDE"]))

apiv1.setup_api(api, celery)

@app.route('/')
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!'

@celery.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))




if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0')

