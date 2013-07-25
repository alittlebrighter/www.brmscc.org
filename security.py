def __init__():
    pass

from functools import wraps
import pickle, ast
from tornado.web import HTTPError

def check_authorization(view):
    def _decorator(request, *args, **kwargs):

        token = request.get_secure_cookie('auth')
        auth = request.session.get(token)

        if request.request.remote_ip != auth['session_ip']:
            request.session.delete(token)
            request.clear_cookie('auth')
            raise HTTPError(403)
            
            # check second argument (request is first) for authorizations
            # in user's auth_groups
        if len(args) > 0:
            auth_funcs = auth['auth_groups'][args[0]]
            # check for 'collection' or 'action' in keywords for authorizations
            # in user's auth_groups
        elif len(kwargs) > 0:
            if 'collection' in kwargs:
                auth_funcs = auth['auth_groups'][kwargs['collection']]
            elif 'action' in kwargs:
                    auth_funcs = auth['auth_groups'][kwargs['action']]
        elif len(auth[auth_groups]) > 0:
            auth_funcs = ['get']

        if view.__name__ in auth_funcs:
            response = view(request, *args, **kwargs)
        else:
            raise HTTPError(403)

        return response
    return wraps(view)(_decorator)
