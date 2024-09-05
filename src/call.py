import re
import os
import json 
import asyncio
from andale.shared.template import render_recursive, eval_conditional
import timeflake
import pathlib
from time import time
import os.path
import importlib
import inspect
import hashlib
import types
import services.metrics as metrics

from shared.mods import hooks
from shared.schema import validate_params, validate_schema
from andale.models import TaskModel
from services.cache import cache

class Task(object):
    def update_progress(self, percent):
        pass

    def update_status(self, status):
        pass

class LoadingZone(object):
    pass

class Stager(object):
    pass


class Director(object):
    pass

class ActionDiscovery(object):
    pass

class ActionRegistry(object):
    pass


class ActionLoader(object):

    def __init__(self):
        pass

    def get_by_name(self, action):
        action = re.sub(r'[^a-z0-9_\.]+', '', action)
        try:
            module = importlib.import_module(f"tasks.{action}")
        except Exception as err:
            raise Exception("Invalid action")
    
        return Action(module)


class Action(object):
    def __init__(self, module):
        self.module = module

    @property
    def version(self):
        return "1.0"

    @property
    def should_cache_results(self):
        return hasattr(self.module, 'CACHE')

    @property
    def cache_duration(self):
        return getattr(self.module, 'CACHE', 0)

    @property
    def is_missing_handler(self):
        return not self.get_handler()

    def get_handler(self):
        if hasattr(self.module, 'task'):
            return self.module.task
        elif hasattr(module, 'task_async'):
            return self.module.task_async
        return None

    def validate_params(self, params):
        validate_params(self.module, params)


class ExecuteableAction(object):
    pass

class Artifacts(object):

    def __init__(self, workspace):
        self.workspace = workspace

    def add_reference(ref):
        pass
    
    def discover(self):
        artifacts = []
        for cwd, _, files in os.walk(self.workspace.path):
            for file in files:
                artifacts.append(os.path.join(cwd, file).replace(self.workspace.path, "").lstrip("/"))
        return artifacts


# @todo project based workspace
class Workspace(object):
    def __init__(self, id, directory):
        self._id = id
        self._directory = directory
        self.artifacts = Artifacts(self)

    def setup(self):
        pathlib.Path(self.path).mkdir(parents=True, exist_ok=True)

    def open(self, *args):
        args = list(args)
        args[0] = os.path.join(self.path, args[0])
        return open(*args)

    @property
    def path(self):
        return os.path.abspath(os.path.join(self._directory, '_task', self._id))
    
    def get_artifacts(self):
        return self.artifacts.discover()



class Context(object):    
    def __init__(self, id, workspace):
        self._id = id
        self.workspace = workspace


    def setup(self):
        self.workspace.setup()

    @property 
    def id(self):
        return self._id

    @property
    def workspace_path(self):
        return self.workspace.path

    @classmethod
    def create(klass):
        id = str(timeflake.random().uuid)
        workspace = Workspace(id, "./.data")
        return klass(id, workspace)


def build_ctx():
    # In lambda workspace will need to be tmp
    # @todo make immutable
    # @todo what if you want to re-use a workspace?
    # So for example, you may want all wpscan results to live in the same directory
    # workspace/{{ id }}/
    ctx =  Context.create()
    ctx.setup()
    return ctx



# environ is lambda,ec2,container,project
# namespaced acts
# whois.domain vs. whois.ip
# browser.request vs browser.screenshot 

def execute_task(task):
    pass

 
def caller(act, params, environ=None):
    act = re.sub(r'[^a-z0-9_\.]+', '', act)
    module = importlib.import_module(f"tasks.{act}")
    executor = None
    
    cache_duration = module.CACHE if hasattr(module, 'CACHE') else None

    if hasattr(module, 'task'):
        executor = getattr(module, 'task')
    elif hasattr(module, 'task_async'):
        executor = getattr(module, 'task_async')

    if executor is None:
        metrics.counter("executor.missing")
    
    # For indexing purposes
    hash = 'md5:' + hashlib.md5(json.dumps(params, default=str).encode("utf8")).hexdigest()
    
    # @todo Modules should be able to specify cache key they use?
    cache_key = "task.result_" + hash
    validate_params(module, params)

    # If task is async wrap in 'sync' executor
    if inspect.iscoroutinefunction(executor):
        loop = asyncio.get_event_loop()
        original = executor
        def _new_executor(*args, **kwargs):
            return loop.run_until_complete(original(*args, **kwargs))

        executor = _new_executor
    else:
        pass
    
    ctx = build_ctx()
    start = time()

    # @todo middleware for task execution
    # @todo before job
    
    # @todo setup loading-zone for files etc
    #  that will be used by job but get thrown away
    #  use template interpolation
    if hasattr(executor, '__self__'):
        # pass ctx to class
        pass
    else:
        # Some methods want ctx as `self`
        args = inspect.getfullargspec(executor)
        if args.varkw or 'self' in args.args:
            params['self'] = ctx
    
    # @todo perfect place for middleware 
    # so caching or db lookups can be middleware
    data = None
    should_execute = True
    if cache_duration:
        exists, data = cache.get(cache_key)
        if exists:
            should_execute = False

    if should_execute: 
        # Update params
        params = hooks.filter('act.before', params, act)
        metrics.counter(f"executor.started.{act}")
        try:
            data = executor(**params)
            metrics.counter(f"executor.complete.{act}")
        except Exception as err:
            data = None
            print(err)
            metrics.counter(f"executor.error.{act}")

        # Modify data
        data = hooks.filter('act.data', data, act, ctx)

        if cache_duration:
            cache.put("task.result" + hash, data, cache_duration)

    # @todo log durations 
    end = time()
    duration = round(end - start, 4)
    
    result = {
        'id': ctx.id,
        'task': act,
        'data': data,
        'duration': duration,
        'hash': hash,
    }

    # Afterwards ... job can be handled by "digesters"
    # which parse out artifacts and do something useful
    # @todo after job
    print(json.dumps(result, indent=2, default=str))

    with ctx.workspace.open("__result.json", 'w+') as fh:
        json.dump(result, fh, default=str)

    # @todo create index of tasks types results
    # @todo for data the returns hashes index to view similar runs
    # job can provide hash ... otherwise the precalculated hash iis used
    # eg
    #  whois
    #   - id-244-3423434-xxx   
    #   - id-344-3423435-xxx
    # whois.$hash
    #   - id-244-3423434-xxx   
    #   - id-344-3423435-xxx


    # task.artifacts['stderr.log']
    # Migrate to appropriate storage
    # eg move to s3 etc
    # @todo uploader should de-dupe with hashes?
    # all task files are hashed and stored in same place
    # task artifacts have references to their hashes
    artifacts = ctx.workspace.get_artifacts()
    print(artifacts)
    return TaskResult(result)


    

INPUT_VARS = set([
    'name',
    'action', 
    'params', 
    'loop', 
    'loop_control', 
    'when', 
    'register',
    'ignore_errors' # If an error is hit ... continue
])

# Template
class Workflow(object):
    def __init__(self, name, params={}, tasks=[]):
        self._name = name
        self._params = params
        self._tasks = tasks


class WorkflowExecution(object):
    def __init__(self, id, workflow=None):
        self.id = id
        self.workflow = workflow


class PreparedTask(object):
    def __init__(self, id, workflow, data={}, parent=None):
        self.id = id
        self.workflow = workflow
        self.data = data
        self._parent = parent
    
    @property
    def action(self):
        return self.data.get('action')
    
    @property
    def params(self):
        return self.data.get('params', {})
    
    @property
    def register(self):
        return self.data.get('register', None)

    
    def progress(self):
        pass

# @todo flag for tasks that run in parallel
class TaskGroup(object):
    def __init__(self, id, workflow, tasks=[]):
        self.id = id
        self.workflow = workflow
        self.tasks = tasks
    
    def append(self, task):
        self.tasks.append(task)

    def progress(self):
        pass

# Need to go through each step and generate id
# So we'll have staged steps

# So we'll start workflow
# - Stage environment/workspace
#   - Expand params
#   - Setup executor
#   - Setup files
# - Stage all tasks
#   - Ensure tasks are real 
#   - Ensure tasks actually have params needed to execute
#      - We don't want to execute if a required param is missing
#   - Create task_id
#   - Ensure task has reference to parent
#   - Give tasks positional index to help executor know what is next
#   - Set status to `prerun`
# - Start on tasks
#   - Create lock for building task
#   - Get tasks where workflow_id = x
#   - Make sure none are in progress
#   - If a task had an error confg workflow config to see if you stop or continue  
#   - Get first task that is positionally lowest
# - Execute task
#   - Prepare workspace
#       - Setup directory 
#       - Ensure files from templated are expanded 
#   - Validate params
#      - If a param is invalid ... mark task as errored
# 

def prepare_env(env, workflow):
    # Setup any files
    # expand vars
    pass

def validate_workflow(workflow, vars):
    True, []

def stage_workflow(workflow, vars={}, env=None):
    valid, errors = validate_workflow(workflow, vars)
    if not valid:
        return
    
    id = str(timeflake.random().uuid)
    execution = WorkflowExecution(id, workflow)
    # expand vars
    # setup files
    for task_config in workflow.tasks:
        task = todo_task(task_config, execution, vars, env)



def is_when():
    pass


def execute_task(task, workflow, env):
    if not is_when(task):
        pass
    
    data = caller(task.action, task.params)



def todo_task(config, workflow, vars={}, env=None):
    # @todo tasks container
    data = {var: config.get(var) for var in INPUT_VARS}
   
    # @todo middleware for handling config
    # Adding variables to workflow level state
    # @todo need locking for setting variable in context of loops
    register = config.pop('register', None)

    # Should this task even run?
    when = config.pop('when', None)
    when = eval_conditional(when, vars) if when else True
    
    # 
    if not when:
        # @todo model for tasks that won't happen
        print("Now is not when")
        print(config)
        task_id = str(timeflake.random().uuid)
        return PreparedTask(task_id, workflow, vars)

    # Is this a collection of tasks?
    loop = config.pop('loop', None)
    loop = render_recursive(loop, vars) if loop else False
    loop_size = 0
    default_loop_control = {
        'parallel': False, # Or set number to parallel
        'loop_var': 'item',
        'index_var': 'item_index',
    }
    loop_control = config.pop('loop_control', default_loop_control)
    loop_control = {a: config.get(a, default_loop_control[a]) for a in default_loop_control}

    if not loop:
        task_data = render_recursive(config, {
            'params': vars,
            'steps'
        })
        print(task_data)

        task_id = str(timeflake.random().uuid)
        return caller(task_data['action'], task_data['params'])

        return PreparedTask(task_id, workflow, vars)

    if isinstance(loop, types.GeneratorType):
        print("Generator?")
    
    try:
        loop_size = len(loop)
    except Exception as err:
        print(err)

    if loop_size:
        print("size", loop_size)

    index = 0
    parent_id = str(timeflake.random().uuid)
    parent = TaskGroup(parent_id, workflow, None)
    
    # @todo loop needs to be lazy for handling cursors
    for val in loop:
        task_id =  str(timeflake.random().uuid)
        tmpl = dict(config)
        scoped = dict(vars)
        scoped.update({
            'workflow': workflow,
            'task_id': task_id,
            loop_control['loop_var']: val,
            loop_control['index_var']: index,
        })

        task_data = render_recursive(tmpl, scoped)
        task = PreparedTask(task_id, workflow, task_data, parent=tasks)
        print(task_data)
        # @todo Send task to queue ...
        # ... for large data sets you cant loop before queuing lest you OOOM
        # parent.append(task)
        index += 1

    return parent

class TaskReference(object):
    def __init__(self, flow, task_id):
        self._flow = flow
        self.id = task_id


class TaskResult(object):
    def __init__(self, result):
        pass

class TasksReference(object):
    # For looking up tasks.nmap.export.http_services

    def __init__(self, flow):
        self._flow = flow
    
tasks = todo_task({
    # 'id':'{{ item | hash("md5") }}',
    'action': "http",
    'params': {
       #  "url": "https://ahermosilla.com/{{ item.action }}-{{ item_index }}-{{ item.__dict__ }}"
        "url": "https://ahermosilla.com/"
    },
    # 'loop': "{{ lazy }}", 
    'when': "test",
    'register': "varname",
}, {
    'tasks': "",
    'test': True,
    'lazy': [TaskModel(action='x')]
    # 'lazy': TaskModel.select().where(TaskModel.action.in_(["http"]))
})

print(tasks)

def work():
    # caller("whois", pararms={'domain':"ahermosilla.com"})
    """
    caller("command", {
        'exec': [
            'nmap', 
            '-sV', 
            '--top-ports', '50', 
            'ready2hire.org', 
            '--script', 'http-title', 
            '-oX', '-'
        ]
    })
    """

    """
    caller(
        'docker',
        params={
            'image':"projectdiscovery/nuclei", 
            'command': [
                '-target', 'https://fortifiedleather.com', 
                '-t', '/root/nuclei-templates/technologies/tech-detect.yaml',
                '-json',
                '-o',
                'run.json',
                '-stats',
                '-project-path',
                '/data/workspace/.tmp',
                "-v",
                # '-update-templates', 
            ]
        }
    )
    """
    """
    caller(
        'browser',
        {'url': 'https://ahermosilla.com/', 'actions': [
        {
            'method': 'evaluate',
            'record': 'test',
            'args': [
                '() => Object.keys(window).filter(k => k.indexOf("on") !== 0)'
            ],
        }
    ]})
    """

# caller("whois", params={'domain':"ahermosilla.com"})

def flow(vars, params, steps):
    try:
        validate_schema(params, vars)
    except Exception as err:
        print(err)

    workflow = Workflow("stub", params={}, tasks=[])
    id = str(timeflake.random().uuid)
    execution = WorkflowExecution(id, workflow)
    # expand vars
    # setup files

    for step in steps:
        task = todo_task(step, execution, vars, env={})

print("------------------")
flow(
    {
        "domain": "ahermosilla.com",
    },
    {
        "domain": {
            "type": "string",
            "required": "true",
            "format": "hostname"
        }
    },
    [
        {
            'action': 'whois',
            'params': {
                'domain':"{{ params.domain }}"
            }
        }, 
        {
            'action': 'browser',
            'params': {

                'url': 'https://{{ params.domain }}', 
                'actions': [
                    {
                        'method': 'evaluate',
                        'record': 'test',
                        'args': [
                            '() => Object.keys(window).filter(k => k.indexOf("on") !== 0)'
                        ],
                    }
                ]
            }
        }
    ]
)