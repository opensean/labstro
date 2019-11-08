# -*- coding: utf-8 -*-

"""Main module."""

from celery import chain, shared_task
from celery.utils.log import get_task_logger
from copy import copy
import importlib
import json
from autoprotocol.protocol import Ref, Protocol
## grab the celery task logger
logger = get_task_logger(__name__)


class AutoprotocolToCelery():

   
    @staticmethod
    def import_task(operation, plugin_dict):
        """
        Import a task.
    
        Args:
            operation (str): name of the task to import.
    
            plugin_dict (dict):  reference for import paths e.g.::
    
                {"seal": ["apto.plugins.simulation.seal"],
                 "spin": ["apto.plugins.simulation.spin"]
    
        Returns:
            (function):  imported function.
    
        """
        path = plugin_dict.get(operation, None)
        ## if more than one pluging maps not sure how to deal with this yet
        path = path[0]
        m = importlib.import_module(path.rsplit(".", 1)[0])
        return getattr(m, path.rsplit(".", 1)[1])


    @staticmethod
    def from_json(path):
        """
        Load an Autoprotocol formatted JSON.

        Args:
            path (str):  file path.

        Returns:
            [autoprotocol.container.Container], autoprotocol.protocol.Protocol
        """
        containers = []
        with open(path, "r") as f:
            p_dict = json.load(f)
            p = Protocol()
            for k,v in p_dict["refs"].items():

                ## get storage info

                storage = v.get("store", None)
                if storage:
                    storage = v["store"]["where"]

                
                ## cont_type is not available in spec unless it is a "new" 
                ## container e.g,
                ##
                ## "sample_plate_1": {
                ##   "new": "96-pcr",
                ##   "discard": true
                ## }

                cont_type = v.get("new", None)

                ## create container, this will break without cont_type
                c =  Container(v.get("id", None), cont_type, name = k,
                               storage = storage,
                               cover = v.get("cover", None))

                containers.append(c)
                
                ## create Ref and add to protocol
                r = Ref(k, v, c)

                p.refs[k] = r


            ## create instructions
            #for i in p_dict["instructions"]:
                
                ## insert code here

                ## p._append_and_return(Instruction)

        return containers, p

    @staticmethod
    def route_plugins(operations, plugins):
        """
        Establish the routes to the corresponding plugins as requested by the
        operations.
    
        Args:
            operations (list): a list of operations e.g., ["seal", "spin"]
    
            plugins (list): a list of plugins to import e.g. ["apto.plugins.simulation"]
    
    
        Returns:
            (dict):  a map of each operation to a list of potential routes e.g.::
    
                {"seal": ["apto.plugins.simulation.seal"],
                 "spin": ["apto.plugins.simulation.spin"]
    
        """
        plugins = [importlib.import_module(p) for p in plugins]
        rmap = {}
    
        for o in operations:
            for p in plugins:
                if hasattr(p, o):
                    r = ".".join([p.__name__,o])
                    if rmap.get(o):
                        rmap[0].append(r)
                    else:
                        rmap[o] = [r]
                    logger.info("routing " + o + " to " + r)
    
        return rmap
 
    
    
    def to_celery(self, protocol, plugins):
        """
        Translate Autoprotocol instructions into schedulable workflows
        using celery canvas.  Currently, a protocol is simple transformed to
        a celery chain.
    
        See [celery canvas](http://docs.celeryproject.org/en/latest/userguide/canvas.html)
    
        Args:
            protocol (dict):  Autoprotocol formatted dictionary, which can be created with::
    
                # instantiate a protocol object
                p = Protocol()
    
                # generate a ref
                # specify where it comes from and how it should be handled when the Protocol is done
                plate = p.ref("test pcr plate", id=None, cont_type="96-pcr", discard=True)
    
                # generate seal and spin instructions that act on the ref
                # some parameters are explicitly specified and others are left to vendor defaults
                p.seal(
                    ref=plate,
                    type="foil",
                    mode="thermal",
                    temperature="165:celsius",
                    duration="1.5:seconds"
                )
                p.spin(
                    ref=plate,
                    acceleration="1000:g",
                    duration="1:minute"
                )
    
                # serialize the protocol as Autoprotocol JSON
                pjson = json.dumps(p.as_dict(), indent=2)
                # serialize the protocol as Autoprotocol dict
                pd = p.as_dict()
    
    
                protocol_celery = autoprotocol_to_celery(pd, ["apto.plugins.simulation"]


            plugins (list): plugins to use for routing operations e.g. ["apto.plugins.simulation"]
    
        """
        operations = [i["op"] for i in protocol["instructions"]]
        plugin_dict = self.route_plugins(operations, plugins)
    
        return chain([self.import_task(i["op"], plugin_dict).s(protocol["refs"], i) for i in protocol["instructions"]])

