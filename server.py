import os.path
import tornado.ioloop
from tornado.web import Application
import motor
from myredis import MyRedis
import uuid
from views import *

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("mongo_host", default="localhost", help="host for MongoDB", type=str)
define("mongo_port", default=27017, help="port MongoDB is running on", type=int)

handlers=[
    ("/next_rally", NextRallyHandler),
    (r"/rallies/([0-9a-zA-Z]+)", RallyHandler),
    ("/schedule", ScheduleHandler),
    (r"/archive/([1-2][90][0-9]{2})", ArchiveHandler),
    ("/login", LoginHandler),
    ("/logout", LogoutHandler),
    ("/admin", AdminHandler),
    (r"/email/(subscribe|unsubscribe)", EmailSignupHandler),
    (r"/email/verify/([0-9a-zA-z]+)", EmailVerifyHandler),
    (r"/admin/(email)", EmailBlastHandler),
    (r"/([A-Za-z_]+).html", RedirectHandler),

    # ResourceHandler_v1
    # arg1: MongoDB collection
    # arg2: resource id (MongoDB _id/ObjectId)
    (r"/api/v1/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]*)", ResourceHandler_v1),
    (r"/([A-Za-z0-9_-]*)", SimpleHandler)
    ]

settings=dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=False,
        cookie_secret="jdf;lajdlj_BlueRidge_jagfykjgfyukje",
        db_secret="jdf;lajdlj_BlueRidgeMountainSportsCarClub_ja;phjio;phje",
        janrain_api_key='30d453b2c91274510da7a4ef403cd23916f9f702',
        login_url="/login",
        autoescape=None,
        db=motor.MotorClient(options.mongo_host, options.mongo_port).open_sync().BlueRidge,
        sessions=MyRedis(unix_socket_path='/tmp/redis.sock', db=0),
        cache=MyRedis(unix_socket_path='/tmp/redis.sock', db=1),
        genRandom=uuid.uuid4,
        debug=True
    )

app = Application(handlers, **settings)

def main():
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
