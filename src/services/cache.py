import os.path
import json

class Cache(object):
    def __init__(self, dir):
        self.dir = dir
    
    def put(self, key, data, expires_in_secs=300):
        key = key.replace(":", "_")
        with open(f'{self.dir}/{key}.json', 'w+') as fh:
            json.dump(data, fh, default=str)

    def get(self, key):
        key = key.replace(":", "_")
        file = f'{self.dir}/{key}.json'
        if not os.path.exists(file):
            return False, None
        
        with open(file, 'r+') as fh:
            data = json.load(fh)
            return True, data
        return False, None

cache = Cache(".data/_cache")