def __init__():
    pass

import redis, pickle

class MyRedis(redis.StrictRedis):
    def set(self, key, value):
        return super().set(key, pickle.dumps(value))
    def setex(self, key, time, value):
        return super().setex(key, time, pickle.dumps(value))
    def get(self, key):
        value = super().get(key)
        if value:
            return pickle.loads(value)
        else:
            return None
