## Sean Landry

import os
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from flask import request
from flask_restful import Resource, Api
import importlib
from celery.result import AsyncResult
from itertools import chain
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def task_signature(TaskFunction, data):
    """
    Unpack args/kwargs from request and create a celery task signature.

    Args:
        TaskFunction (celery.Task):  The celery task function.

        request (rest_framework.Request):  The original request.

    Returns:

        celery.Task.signature

    """
    if data.get("args", False) and data.get("kwargs", False):
        return TaskFunction.s(*data["args"], **data["kwargs"])

    if data.get("args", False) and not data.get("kwargs", False):
        return TaskFunction.s(*data["args"])

    if not data.get("args", False) and data.get("kwargs", False):
        return TaskFunction.s(**data["kwargs"])

    if not data.get("args", False) and not data.get("kwargs", False):
        return TaskFunction.s()

def validate_apply_schema(data, schema_root = None, schema_path = None):
    """
    Validate the json schema of a request.

    Args:
        data (dict):  parsed json body of a request.

    Kwargs:
        schema_root (str):  file path to root directory of schema definition.

        schema_path (str):  file apth to schema definition.

    Returns:
        (dict): {"result":"schema valid"}, 200  or  {"result": "invalid schema", "exc":str(e)}, 400
        

    """
    logger.info("validating schema")

    try:
        schema_path = data["kwargs"]["schema"]
        schema_path = os.path.join(schema_root, schema_path)
        with open(schema_path, "r") as f:
            schema = json.load(f)
    except Exception as e:
        logger.warning("problem with schema: \n" + str(e))
        schema_path = os.path.join(schema_root, schema_path)
        logger.warning("applying default schema: " + schema_path)
        with open(schema_path, "r") as f:
            schema = json.load(f)
    try:    
        validate(data, schema = schema)
        return {"result":"schema valid"}, 200
    except (AttributeError, ValueError, ValidationError) as e:
        return {"result": "invalid schema", "exc":str(e)}, 400


class TaskList(Resource):
    """
    API endpoint to view a list all registered celery tasks.


    list:  Return a list of all registered Tasks.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskList, self).__init__()



    def get(self):
        """
        Return a list of all regiestered celery tasks.
        """
        return [t for t in self.celery.tasks]

class TaskRoutes(Resource):
    """
    API endpoint to view celery task routes.


    list:  Return a list of all registered Tasks.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskRoutes, self).__init__()



    def get(self):
        """
        Return a list of all regiestered celery tasks.
        """
        return self.celery.conf["task_routes"]

class TaskApplyAsync(Resource):
    """
    API endpoint to view and/or execute Tasks.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskApplyAsync, self).__init__()



    def post(self, task_name):
        """
        Equivalent to celery.Task.apply_async().

        """
        try:
            logger.info("POST TaskApplyAsync " + task_name)
            response, code  = validate_apply_schema(request.json,
                                 schema_root = self.celery.conf["APTO_API_JSONSCHEMA_ROOT"],
                                 schema_path = self.celery.conf["APTO_API_JSONSCHEMA_DEFAULT"])
            if code == 200:
                r = self.celery.send_task(task_name,
                     args = request.json.get("args", None),
                     kwargs = request.json.get("kwargs", None))
                
                logger.info("sent task " + task_name)
                return {"task-id":r.id, "state":r.state}, 200
            else:
                return response

        except (AttributeError, ValueError) as e:
            return {"result": "failed to apply async " + task_name, "exc":str(e)}, 404

class TaskApply(Resource):
    """
    API endpoint to view and/or execute Tasks.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskApply, self).__init__()

    def post(self, task_name):
        """
        Equivalent to celery.Task.apply().

        """
        try:
            response, code  = validate_apply_schema(request.json,
                                 schema_root = self.celery.conf["APTO_API_JSONSCHEMA_ROOT"],
                                 schema_path = self.celery.conf["APTO_API_JSONSCHEMA_DEFAULT"])
            if code == 200:
                TaskFunction = self.celery.tasks[task_name]
                TaskSig = task_signature(TaskFunction, request.json) 
                r = TaskSig.apply()
                return {"task-id":r.id, "state":r.state, "result":r.get()}, code
            else:
                return response
        except (AttributeError, ValueError) as e:
            return {"result": "failed to apply " + task_name, "exc":str(e)}, 404

class TaskResult(Resource):
    """
    API endpoint that allows celery task results to be viewed or edited.

    retrieve:  Return a given TaskResult.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskResult, self).__init__()


    def get(self, task_id):
        r = self.celery.AsyncResult(task_id)
        data = {"task_id": r.id,
            "state": r.state,
            "result": r.result,
            "traceback": str(r.traceback)}
        return data, 200

class TaskSuccess(Resource):
    """
    API endpoint that to mark a task as a success.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskSuccess, self).__init__()


    def post(self, task_id):
        self.celery.backend.mark_as_done(task_id, request.json)
        r = self.celery.AsyncResult(task_id)
        data = {"task_id": r.id,
            "state": r.state,
            "result": r.result,
            "traceback": str(r.traceback)}
        return data, 200

class TaskStarted(Resource):
    """
    API endpoint that to mark a task as started.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskStarted, self).__init__()


    def put(self, task_id):
        self.celery.backend.mark_as_started(task_id)
        r = self.celery.AsyncResult(task_id)
        data = {"task_id": r.id,
            "state": r.state,
            "result": r.result,
            "traceback": str(r.traceback)}
        return data, 200
    
    def post(self, task_id):
        self.celery.backend.mark_as_started(task_id)
        r = self.celery.AsyncResult(task_id)
        data = {"task_id": r.id,
            "state": r.state,
            "result": r.result,
            "traceback": str(r.traceback)}
        return data, 200

class TaskFailed(Resource):
    """
    API endpoint that to mark a task as started.

    """
    def __init__(self, celery = None):
        self.celery = celery
        super(TaskFailed, self).__init__()


    def put(self, task_id):
        self.celery.backend.store_result(task_id, request.json, "FAILED", traceback = None)
        r = self.celery.AsyncResult(task_id)
        data = {"task_id": r.id,
            "state": r.state,
            "result": r.result,
            "traceback": str(r.traceback)}
        return data, 200
    
    def post(self, task_id):

        self.celery.backend.store_result(task_id, request.json, "FAILED", traceback = None)
        r = self.celery.AsyncResult(task_id)
        data = {"task_id": r.id,
            "state": r.state,
            "result": r.result,
            "traceback": str(r.traceback)}
        return data, 200



def setup_api(api, celery):
    ## setup API resource routing
    api.add_resource(TaskList, '/apiv1/tasks', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskRoutes, '/apiv1/task/routes', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskResult, '/apiv1/task/result/<task_id>', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskSuccess, '/apiv1/task/success/<task_id>', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskStarted, '/apiv1/task/started/<task_id>', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskFailed, '/apiv1/task/failed/<task_id>', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskApply, '/apiv1/task/apply/<task_name>', resource_class_kwargs = {"celery":celery})
    api.add_resource(TaskApplyAsync, '/apiv1/task/apply_async/<task_name>', resource_class_kwargs = {"celery":celery})


