import weakref
import functools
def memoize(func):
    cache = weakref.WeakKeyDictionary()
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key not in cache.setdefault(self, {}):
            cache[self][key] = func(self, *args, **kwargs)
        return cache[self][key]
    return wrapper

