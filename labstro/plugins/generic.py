## opensean
from celery import shared_task
from celery import Task

class PlugInTask(Task):
    """
    Using the following strategy outlined in the celery documention, the 
    PlugInTask class can be used to cache a client.  Caching a client reduces
    the number of times a connection may need to established with a device 
    or service.

    http://docs.celeryproject.org/en/latest/userguide/tasks.html#instantiation

    A task is not instantiated for every request, but is registered in the 
    task registry as a global instance.  This means that the __init__ 
    constructor will only be called once per process, and that the 
    task class is semantically closer to an Actor.

    If you have a task::

        from celery import Task
        
        class NaiveAuthenticateServer(Task):
        
            def __init__(self):
                self.users = {'george': 'password'}
        
            def run(self, username, password):
                try:
                    return self.users[username] == password
                except KeyError:
                    return False

    And you route every request to the same process, then it will keep state between requests.
    
    This can also be useful to cache resources, For example, a base Task class that caches a database connection::
    
        from celery import Task
        
        class DatabaseTask(Task):
            _db = None
        
            @property
            def db(self):
                if self._db is None:
                    self._db = Database.connect()
                return self._db
        that can be added to tasks like this:
        
        @app.task(base=DatabaseTask)
        def process_rows():
            for row in process_rows.db.table.all():
                process_row(row)


    The db attribute of the process_rows task will then always stay the same in each process.

    """
    def __init__(self):
        self._client = None

    @property
    def client(self):
        """
        Return a client used for communication.

        """
        return self._client


   

