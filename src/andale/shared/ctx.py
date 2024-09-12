import hashlib
from andale.shared.mods import Plugin


class Context(object):
    def __init__(self, hooks, storage):
        self.hooks = hooks
        self.storage = storage

    @property
    def id(self):
        pass

    @property
    def workspace_path(self):
        pass

    def get_artifacts(self):
        return []

    def put_artifact(self, name, body):
        # Put in job namespaced storage
        # hash_of_body = "md5:" + hashlib.md5(body).hexdigest()
        ref_key = self.id + "/" + name
        self.storage.put(ref_key, body)

    def put_storage(self, name, body):
        # Put in global storage
        pass

    @staticmethod
    def create(klass):
        hooks = Plugin()
        return klass(hooks)
