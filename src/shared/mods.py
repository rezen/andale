
# @todo way to generated namedspaced object that items tasks can call
class Plugin(object):
    #
    def action(self, name, *args, **kwargs):
        print(name)

    def filter(self, name, data, *args):
        return data



hooks = Plugin()