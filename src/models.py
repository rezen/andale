import json
import peewee

# logger = logging.getLogger('peewee')
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)

class JSONField(peewee.TextField):
    """
    Class to "fake" a JSON field with a text field. Not efficient but works nicely
    """
    def db_value(self, value):
        """Convert the python value for storage in the database."""
        return value if value is None else json.dumps(value)

    def python_value(self, value):
        """Convert the database value to a pythonic value."""
        return value if value is None else json.loads(value)


db = peewee.SqliteDatabase('andale.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db

class Whois(BaseModel):
    pass

class Certificate(BaseModel):
    pass

class Package(BaseModel):
    # pip, npm, docker, maven ... etc
    pass

class Code(BaseModel):
    pass

class Ip(BaseModel):
    pass

class Domain(BaseModel):
    pass

class DnsRecord(BaseModel):
    pass

class Cloud(BaseModel):
    pass

class Asset(BaseModel):
    root_id = peewee.TextField(null=True) # root domain or subnet
    parent_id = peewee.TextField(null=True) # subdomain is child of x
    label = peewee.TextField()
    type = peewee.TextField()
    src = peewee.TextField()
    src_account_label = peewee.TextField(null=True)
    src_account_id = peewee.TextField(null=True)
    last_seen = peewee.DateTimeField()

    
class TaskModel(BaseModel):
    # Identification information about signature
    hash = peewee.TextField(null=True)

    next_id = peewee.TextField(null=True)
    parent_id = peewee.TextField(null=True)
    task_index = peewee.TextField(null=True) # What position is it?
    # workflow_run_id
    # job_runner

    # If an asset is discovered in args
    # @todo what if there are multiple assets?
    # @todo target?
    asset = peewee.ForeignKeyField(Asset, backref='tasks', null=True)

    # User controlled
    name = peewee.TextField(null=True)
    action = peewee.TextField()
    params = JSONField(default={})
    loop = JSONField(null=True)
    loop_control = JSONField(null=True)
    when = peewee.TextField(null=True)
    register = peewee.TextField(null=True)

    # For monitoring status
    status = peewee.IntegerField(default=0, choices=[0, 1, 2, 3, 4, 5, 6, 7])
    progress = peewee.IntegerField(null=True)
    eta = peewee.DateTimeField(null=True)

    # For end result
    error = peewee.TextField(null=True)
    data = JSONField(null=True)
    artifacts = JSONField(null=True)
    duration = peewee.IntegerField(null=True)
    started_at = peewee.DateTimeField(null=True)
    stopped_at = peewee.DateTimeField(null=True)

db.connect()
db.create_tables([Asset, TaskModel])

