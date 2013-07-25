This is the source for [www.brmscc.org](http://www.brmscc.org).  I am the first to admit that it needs refactored badly.  Also, I'm a github noob so please forgive any odd files in here or anything missing like a requirements.txt which I will get to eventually.  

Speaking of dependencies this website is built with Python 3, MongoDB, Redis, and I'm using [Janrain](http://janrain.com/) for authentication. 
Python library dependencies are as follows and can all be obtained with pip:

* [Tornado v3.1](http://www.tornadoweb.org/en/stable/)
* [Motor v0.1.1](http://motor.readthedocs.org/en/stable/)
* [redis-py v2.7.4](https://github.com/andymccurdy/redis-py)

Currently all page rendering is server side and the admin pages are a bit of a mess.  I am in the process of converting the Python to a simplified, rest API and at the same time beef up the client side a bit with [Angular](http://angularjs.org/) or [Ractive](http://www.ractivejs.org/).  I also need to make the site responsive which will probably happen before the switch to the rest API.
