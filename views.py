import tornado.web, motor
from tornado import template, gen
from tornado.httpclient import AsyncHTTPClient
from bson.objectid import ObjectId
from datetime import datetime
import json, pickle, security

ASCENDING, DESCENDING = 1, -1

def keyfind(key, domain):
    if key in domain:
        return domain[key]
    else:
        for v in domain.values():
            if type(v).__name__ == 'dict':
                return keyfind(key, v)
            else:
                return None

def queryfind(key, domain):
    def query_find(key, domain):
        if key in domain:
            return {'$elemMatch': {key: domain[key]}}
        else:
            for k,v in domain.items():
                if type(v).__name__ == 'dict':
                    return {'$elemMatch':{k: query_find(key, v)}}
                else:
                    return None
    result = query_find(key,domain)
    if result:
        if '$elemMatch' in result:
            return result['$elemMatch']
        else:
            return result
    else:
        return result              

class BaseHandler(tornado.web.RequestHandler):
    
    @property
    def db(self):
        return self.application.settings['db']
    @property
    def session(self):
        return self.application.settings['sessions']

    inputDict=dict(
                site_title="Blue Ridge Mountain Sports Car Club",
                nav=['intro', 'next_rally', 'schedule', 'tutorial', 'club_info']
            )
            
    def render_page(self, template_name, suppItems):
        for name,value in suppItems.items():
            self.inputDict[name]=value
        self.render(template_name, **self.inputDict)

    def write_error(self, status_code, **kwargs):
        message = """
            <div style="text-align:center">
                We must have made a wrong turn, the OOPS mileage was {oops} and we are at {mile}!
            </div>
        """.format(oops=str(status_code - (status_code%100)), mile=status_code)
        self.render_page(
            'simplepages.html',
            dict(title=str(status_code), content=message)
            )
        

    def get_current_user(self):
        #auth = pickle.loads(self.get_secure_cookie("auth"))
        auth = self.get_secure_cookie("auth")
        if not auth:
            return None


class NextRallyHandler(BaseHandler):
    """Displays the next rally based on the current date and time"""
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        cursor = self.db.rallies.find({'start_datetime': {'$gt': datetime.now()}}).sort('start_datetime', ASCENDING).limit(1)
        yield cursor.fetch_next
        next_rally = cursor.next_object()
        if next_rally:
            next_rally['start_date'] = next_rally['start_datetime'].strftime('%A, %B %e, %Y')
            next_rally['reg_time'] = next_rally['registration_datetime'].strftime('%l%P')
            next_rally['start_time'] = next_rally['start_datetime'].strftime('%l:%M%P')
            next_rally['visible_lat'] = next_rally['latitude']
            next_rally['visible_long'] = next_rally['longitude']
            
            self.render_page('rallies.html', dict(rally=next_rally))
        else:
            self.render_page("base.html", dict(msg='No upcoming rallies, check back soon.'))

class RallyHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self, rally_id):
        rally = yield motor.Op(self.db.rallies.find_one, {'_id': ObjectId(rally_id)}) 
        rally['start_date'] = rally['start_datetime'].strftime('%A, %B %e, %Y')
        rally['reg_time'] = rally['registration_datetime'].strftime('%l%P')
        rally['start_time'] = rally['start_datetime'].strftime('%l:%M%P')
        rally['visible_lat'] = rally['latitude']
        rally['visible_long'] = rally['longitude']
            
        self.render_page('rallies.html', dict(rally=rally))

class ScheduleHandler(BaseHandler):
    """Displays the current year's events plus January if the current month is December"""
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        today = datetime.today()
        fromDate = datetime(today.year, 1, 1)
        if today.month == 12:
            toDate = datetime(today.year + 1, 1, 31)
        else:
            toDate = datetime(today.year, 12, 31)
        events = {'page_title': 'Rally Schedule', 'year': today.year}
        rallies = self.db.rallies.find(
			{'start_datetime': {"$gte": fromDate, "$lte": toDate}},
			{'start_datetime': 1, 'title': 1, 'rallymaster': 1}
			).sort('start_datetime', ASCENDING).limit(13)
        rallies.to_list(callback=(yield gen.Callback('rallies')))
        events['rallies'] = []
        meetings = self.db.meetings.find(
			{'start_datetime': {"$gte": fromDate, "$lte": toDate}},
			{'start_datetime': 1, 'description': 1}).sort('start_datetime', ASCENDING).limit(7)
        meetings.to_list(callback=(yield gen.Callback('meetings')))
        events['meetings'] = []
        events['rallies'], events['meetings'] = yield motor.WaitAllOps(['rallies', 'meetings'])
        for rally in events['rallies']:
            rally['start_datetime'] = rally['start_datetime'].strftime('%B %e')
        for meeting in events['meetings']:
            meeting['start_datetime'] = meeting['start_datetime'].strftime('%A, %B %e')
        self.render_page("schedule.html", events)

class ArchiveHandler(BaseHandler):
    """Displays a year's worth of events"""
    @tornado.web.asynchronous
    @gen.engine
    def get(self, year):
        fromDate = datetime(int(year), 1, 1)
        toDate = datetime(int(year), 12, 31)
        events = {'page_title': 'Rally Schedule', 'year': year}
        rallies = self.db.rallies.find(
			{'start_datetime': {"$gte": fromDate, "$lte": toDate}},
			{'start_datetime': 1, 'title': 1, 'rallymaster': 1}
			).sort('start_datetime', ASCENDING)
        rallies.to_list(callback=(yield gen.Callback('rallies')))
        events['rallies'] = []
        meetings = self.db.meetings.find(
			{'start_datetime': {"$gte": fromDate, "$lte": toDate}},
			{'start_datetime': 1, 'description': ASCENDING})
        meetings.to_list(callback=(yield gen.Callback('meetings')))
        events['meetings'] = []
        events['rallies'], events['meetings'] = yield motor.WaitAllOps(['rallies', 'meetings'])
        for rally in (yield motor.Op(rallies.to_list)):
            rally['start_datetime'] = rally['start_datetime'].strftime('%B %e')
        for meeting in (yield motor.Op(rallies.to_list)):
            meeting['start_datetime'] = meeting['start_datetime'].strftime('%A, %B %e')
        self.render_page("schedule.html", events)

class SimpleHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self, simplePage):
        if not simplePage or simplePage == '' or simplePage == 'intro':
            alt_id = 'index'
        else:
            alt_id = simplePage
			
        page = yield motor.Op(self.db.simplepages.find_one, {'alt_id': alt_id})

        if page:
            self.render_page("simplepages.html", page)
        else:
            raise tornado.web.HTTPError(404)

class ResourceHandler_v1(BaseHandler):

    #@security.check_authorization
    @tornado.web.asynchronous
    @gen.engine
    def get(self, collection, resource_id):
        if resource_id == 'create':
            self.render_page('admin/%s.html' % collection, dict(page_title=collection))
        else:
            resource = yield motor.Op(self.db[collection].find_one, {'_id': ObjectId(str(resource_id))})
            resource['_id'] = resource_id
            for key in resource.keys():
                if 'datetime' in key.lower():
                    resource[key] = resource[key].strftime('%m/%d/%Y at %I:%M%p')
            self.render_page('admin/update-%s.html' % collection, dict(page_title=collection, resource=resource))

    #@security.check_authorization
    @tornado.web.asynchronous
    @gen.engine  
    def post(self, collection, resource_id="doesn't matter here"):
        newResource = json.loads(self.request.body.decode('utf-8'))
        for key,value in newResource.items():
            if 'datetime' in key.lower():
                newResource[key] = datetime.strptime(value, '%m/%d/%Y at %I:%M%p') 
        result = yield motor.Op(self.db[collection].insert, newResource)
        self.write('%s %s created' % (collection, str(result)))
        self.finish()
        #self.render_page('base.html', dict(msg=self.request.body.decode('utf-8')))
        #self.redirect('/api/v1/{collection}/create' % collection)

    #@security.check_authorization
    @tornado.web.asynchronous
    @gen.engine    
    def put(self, collection, resource_id):
        resource = json.loads(self.request.body.decode('utf-8'))
        for key,value in resource.items():
            if 'datetime' in key.lower():
                resource[key] = datetime.strptime(value, '%m/%d/%Y at %I:%M%p')
        #{'_id': ObjectId(resource_id)}
        resource['_id'] = ObjectId(resource_id)
        mongo_response = yield motor.Op(self.db[collection].update, {'_id': ObjectId(resource_id)}, resource)
        self.write(mongo_response)
        self.finish()

    #@security.check_authorization   
    @tornado.web.asynchronous
    @gen.engine  
    def delete(self, collection, resource_id):
        yield motor.Op(self.db[collection].remove, {'_id': ObjectId(resource_id)})
        self.write({'msg': collection + ' ' + resource_id + ' removed'})
        self.finish()

class AdminHandler(BaseHandler):
    #@security.check_authorization
    @tornado.web.asynchronous
    @gen.engine  
    def get(self):
        resources = {'simplepages':[],'rallies':[],'meetings':[]}
        simplepages = self.db.simplepages.find()
        rallies = self.db.rallies.find().sort('start_datetime', DESCENDING)
        meetings = self.db.meetings.find().sort('start_datetime', DESCENDING)
        for simplepage in (yield motor.Op(simplepages.to_list)):
            resources['simplepages'].append(simplepage)
        for rally in (yield motor.Op(rallies.to_list)):
            resources['rallies'].append(rally)
        for meeting in (yield motor.Op(meetings.to_list)):
            resources['meetings'].append(meeting)
#        pages = self.db.simplepages.find()
#        rallies = self.db.rallies.find().sort('start_datetime', DESCENDING)
#        meetings = self.db.meetings.find().sort('start_datetime', DESCENDING)
        
        #resources['simplepages'],resources['rallies'],resources['meetings'] = yield motor.WaitAllOps([simplepages,rallies,meetings])

        for resource in resources.keys():
            temp = []
            for item in resources[resource]:
                item['_id'] = str(item['_id'])
                temp.append(item)
            resources[resource] = temp
        self.render_page("admin/admin.html", dict(resources=resources))    

class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect('/admin')
        else:
            self.render_page('login.html', dict(usr=None, error=0))

    def get_or_insert_user(self, profileDict):
        dbUser = self.db.site_users.find_one(dict(identifier=profileDict['identifier']), dict(identifier=1, auth_groups=1, _id=0))
        if not dbUser:
            profileDict['auth_groups'] = {}
            self.db.site_users.insert(profileDict)
            return dict(identifier=profileDict['identifier'], auth_groups=profileDict['auth_groups'])

        else:
            return dict(identifier=dbUser['identifier'], auth_groups=dbUser['auth_groups'])

    @tornado.web.asynchronous
    def post(self):
        """Makes the call to Janrain and inserts or gets a site_user"""
        api_params = {
            'token': str(self.get_arguments('token')[0]),
            'apiKey': self.application.settings['janrain_api_key'],
            'format': 'json',
            }

        self.ip = self.request.remote_ip
        
        http_client = AsyncHTTPClient()
        http_client.fetch("https://rpxnow.com/api/v2/auth_info?token={token}&apiKey={apiKey}&format={format}".format(**api_params),
            callback=self.on_fetch)
    
    def on_fetch(self, response):
        returnedUser = json.loads(response.body.decode('utf-8'))
        if returnedUser['stat']=='ok':
            auth = self.get_or_insert_user(returnedUser['profile'])
            auth['session_ip'] = self.ip
            token = str(self.application.settings['genRandom']())
            self.session.setex(token, 60*30, auth)
            self.set_secure_cookie('auth', token)
        self.redirect('/admin')

class LogoutHandler(BaseHandler):
    def get(self):
        self.session.delete(self.get_secure_cookie('auth'))
        self.clear_cookie('auth')
        self.redirect('/')

import sendEmail
        
class EmailSignupHandler(BaseHandler):
    def get(self, action):
        if action == 'subscribe':
            message = 'to receive information regarding upcoming events'
        else:
            message = 'remove yourself from the mailing list'
        self.render_page('email_signup.html', dict(msg='Enter your email address in the box below and click "Submit" to ' + message, action=action))
    
    def post(self, action):
        email = json.loads(self.request.body.decode('utf-8'))['email']
        
        if action == 'unsubscribe':
            self.db.email_list.remove({'email': email})
        elif not self.db.email_list.find_one({'email': email}):
            verificationCode = str(self.db.email_list.insert({'email': email, 'verified': False, 'submitted': datetime.now()}))
            sendEmail.emailBlast(to=email, bcc=email, subject='Email Verification', text='Please visit http://www.brmscc.org:8888/email/verify/%s' % verificationCode, html='Click <a href="http://www.brmscc.org:8888/email/verify/%s">here</a> to verify your email address for the BRMSCC mailing list.' % verificationCode)
    
class EmailBlastHandler(BaseHandler):
    @security.check_authorization
    def get(self, action):
        self.render_page('email_blast.html', dict())
        
    @security.check_authorization
    def post(self, action):
        mail = json.loads(self.request.body.decode('utf-8'))
        recipients = []
        for recipient in self.db.email_list.find({'verified': True}):
            recipients.append(recipient['email'])
        self.write(sendEmail.emailBlast(bcc=recipients, **mail))
        
class EmailVerifyHandler(BaseHandler):
    def get(self, verificationCode):
        response = self.db.email_list.update({'_id': ObjectId(verificationCode)}, {'$set': {'verified': True}, '$unset': {'submitted': 1}})
        if response:
            self.render_page('base.html', dict(page_title='Email Verified', msg='Your email has been verified and you are now on the BRMSCC mailing list.'))
        else:
            self.redirect('/email/subscribe')

class RedirectHandler(BaseHandler):
    def get(self, page):
        self.redirect('/%s' % page.lower())
