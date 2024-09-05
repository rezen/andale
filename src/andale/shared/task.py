class Task(object):
    attrs = [
        "vars",
        "type",
        "id",
        "name",
        "params",
        "export",
        "loop",
        "key",
        "raw",
    ]

    def __init__(self, parent):
        self.parent = parent
        self.subtasks = []

    def __or__(self, other):
        print(other)

    def progress(self):
        pass

    def status(self):
        pass

    def data(self):
        pass

    def is_running(self):
        pass
