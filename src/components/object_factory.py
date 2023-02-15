

# Inspiration: https://realpython.com/factory-method-python/

class ObjectFactory:
    def __init__(self):
        self.builders = {}

    def register_builder(self, key, builder):
        self.builders[key] = builder

    def create(self, key, **kwargs):
        builder = self.builders.get(key)
        if not builder:
            raise ValueError(key)
        #return builder.create(**kwargs)
        return builder(**kwargs)