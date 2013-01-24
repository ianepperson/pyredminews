# PyRedmineWS - Python Redmine Web Services
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import urllib2
import xml.etree.ElementTree as ET
import json
from types import MethodType


# In order to handle the proper wrappers for unknown types, we need to correctly
# work out the plural container info from the singular type
#   project -> projects
#   news -> news
#   issue_category -> issue_categories
#   etc.
# Subset from http://code.activestate.com/recipes/577781-pluralize-word-convert-singular-word-to-its-plural/

# Adding a plural to the map will correct unusual English plurals
# and will also speed up the lookup.
KNOWN_PLURAL_MAP = {
	'':'',
    'appendix': 'appendices',
    'child': 'children',
    'criterion': 'criteria',
    'echo': 'echoes',
    'index': 'indices',
    'news': 'news',
    'issue_status': 'issue_statuses',
    'project': 'projects',
    'issue': 'issues',
    }

VOWELS = set('aeiou')

def pluralize(singular, lookup=KNOWN_PLURAL_MAP):
	'''Return a plural word given the singular word'''
	try:
		return lookup[singular]
	except:
		pass
	root = singular
	try:
		if singular[-1] == 'y' and singular[-2] not in VOWELS:
			root = singular[:-1]
			suffix = 'ies'
		elif singular[-1] == 's':
			if singular[-2] in VOWELS:
				if singular[-3:] == 'ius':
					root = singular[:-2]
					suffix = 'i'
				else:
					root = singular[:-1]
					suffix = 'ses'
			else:
				suffix = 'es'
		elif singular[-2:] in ('ch', 'sh'):
			suffix = 'es'
		else:
			suffix = 's'
	except IndexError:
		suffix = 's'
	return root + suffix


class _Redmine_Item(object):
	'''Base class used for all items returned from Redmine.'''
	# List out the attributes that aren't user-settable
	_protected_attr = ['id']
	_type = ''
	_path = None
	
	def __init__(self, redmine, json_data=None, data={}):
		self._redmine = redmine
		if json_data:
			# Parse the data
			data = json.loads(json_data)
		if self._type:
			try:
				data = data[self._type]
			except:
				pass
		# Map all dictionary data to object attributes
		self.__dict__.update(data)
		
	def __setattr__(self, name, value):
		'''Set the attribute for any non-protected attribute.'''
		if name in self._protected_attr:
			raise AttributeError("Can't set attribute %s." % name)
		self.__dict__[name] = value

	def save(self):
		pass

class _Project(_Redmine_Item):
	'''Object representing a Redmine project.
	Returned by Redmine getProject calls.
	'''
	id = None
	identifier = None
	_type = 'project'
	_protected_attr = ['id',
					   'created_on',
					   'updated_on',
					   'identifier',
					   ]
	
	def __repr__(self):
		return '<Redmine project #%s "%s">' % (self.id, self.identifier)
	
	def save(self):
		'''Save changes for this project back to the server.'''
		raise NotImplementedError('sorry')
	
	def new_issue(self, **data):
		'''Create a new issue for this project from the given pairs.
		
		newIssue( subject="The Arguments Department is closed", description="Good morning." )
		
		Possible keys are:
		 subject
		 description
		 status_id
		 priority_id
		 tracker_id - can be looked up from name in Project.trackers[name]
		 assigned_to_id
		'''
		if not 'subject' in data:
			TypeError('Subject cannot be blank.  Use subject="This parrot is dead."')
		if 'id' in data:
			TypeError('Cannot set an ID.  You\'ll get that from the database.')
		data[ 'project_id' ] = self.number
		return self._redmine.newIssueFromDict( data )

	def get_issues(self ):
		'''Get the issue for this project.'''
		raise NotImplementedError('sorry')
		#todo: finish


class _Issue(_Redmine_Item):
	'''Object representing a Redmine issue.'''
	id = None
	subject = None
	_type = 'issue'
	_protected_attr = ['id',
					   'created_on',
					   'updated_on',
					   'identifier',
					   ]

	def __repr__(self):
		return '<Redmine issue #%s>' % self.id
	
	def __str__(self):
		return '<Redmine issue #%s, "%s">' % (self.id, self.subject)

	def resolve(self):
		'''Resolve this issue'''
		self._redmine.resolve_issue( self.id )
		
	def close(self):
		'''Close this issue'''
		self._redmine.close_issue( self.id )
		
	def save(self):
		'''Saves this issue - updates or creates new issue as necessary.  Failed updates DO NOT return any errors.'''
		raise NotImplementedError('sorry')
		#todo: finish

class _Redmine_CRUD(object):
	def __init__(self, redmine, type_str, obj=_Redmine_Item):
		self._redmine = redmine
		self._type_str = type_str
		self._obj = obj
	
	def new(self, **kw_args):
		data = self._redmine.new_item(self._type_str, **kw_args)
		return self._obj(data)
	def get(self, id=None):
		if id:
			data = self._redmine.get_item(self._type_str, id)
		else:
			raise NotImplementedError('sorry')
		return self._obj(self._redmine, json_data=data)
	def update(self, **kw_args):
		pass
	def delete(self, id):
		pass

class Redmine(object):
	'''Class to interoperate with a Redmine installation using the REST web services.
	instance = Redmine(url, [key=strKey], [username=strName, password=strPass] )
	
	url is the base url of the Redmine install ( http://my.server/redmine )
	
	key is the user API key found on the My Account page for the logged in user
		All interactions will take place as if that user were performing them, and only
		data that that user can see will be seen

	If a key is not defined then a username and password can be used
	If neither are defined, then only publicly visible items will be retreived	
	'''
	# Status ID from a default install
	ISSUE_STATUS_ID_NEW = 1
	ISSUE_STATUS_ID_RESOLVED = 3
	ISSUE_STATUS_ID_CLOSED = 5		
	
	# Grab a global reference to the plural word map
	KNOWN_PLURAL_MAP = KNOWN_PLURAL_MAP
	
	TYPE_OBJECT = {
		'issue': _Issue,
		'project': _Project,
		}
	
	def __init__(self, url, key=None, username=None, password=None, debug=False, readonlytest=False ):
		self._url = url
		self._key = key
		self.debug = debug
		self.readonlytest = readonlytest
		self.projects = {}
		
		if readonlytest:
			print 'Redmine instance running in read only test mode.  No data will be written to the server.'
		
		self._opener = None
		
		if not username:
			username = key
			self._key = None
			
		if not password:
			password = '12345'  #the same combination on my luggage!  (required dummy value)
		
		if( username and password ):
			#realm = 'Redmine API'
			# create a password manager
			password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

			password_mgr.add_password(None, url, username, password )
			handler = urllib2.HTTPBasicAuthHandler( password_mgr )

			# create "opener" (OpenerDirector instance)
			self._opener = urllib2.build_opener( handler )

			# set the opener when we fetch the URL
			self._opener.open( url )

			# Install the opener.
			urllib2.install_opener( self._opener )
			
		else:
			if not key:
				pass
				
		

	# extend the request to handle PUT command
	class PUT_Request(urllib2.Request):
		def get_method(self):
			return 'PUT'

	# extend the request to handle DELETE command
	class DELETE_Request(urllib2.Request):
		def get_method(self):
			return 'DELETE'
	
	
	
	def open_raw(self, page, parms=None, payload=None, HTTPrequest=None, payload_type='application/json' ):
		'''Opens a page from the server with optional XML.  Returns a response file-like object'''
		if not parms:
			parms={}
			
		# if we're using a key, add it to the parms array
		if self._key:
			parms['key'] = self.__key
		
		# encode any data
		urldata = ''
		if parms:
			urldata = '?' + urllib.urlencode( parms )
		
		
		fullUrl = self._url + '/' + page
		
		# register this url to be used with the opener
		if self._opener:
			self._opener.open( fullUrl )
			
		#debug
		if self.debug:
			print fullUrl + urldata
		
		# Set up the request
		if HTTPrequest:
			request = HTTPrequest( fullUrl + urldata )
		else:
			request = urllib2.Request( fullUrl + urldata )
		# get the data and return XML object
		if payload:
			request.add_header('Content-Type', payload_type)
			response = urllib2.urlopen( request, payload )			
		else:
			response = urllib2.urlopen( request )
		
		return response
	
	def open(self, page, parms=None, payload=None, HTTPrequest=None ):
		'''Opens a page from the server with optional content.  Returns the string response.'''
		response = self.open_raw( page, parms, payload, HTTPrequest )
		return response.read()
		
	
	def get(self, page, parms=None ):
		'''Gets an XML object from the server - used to read Redmine items.'''
		return self.open( page, parms )
	
	def post(self, page, payload, parms=None ):
		'''Posts a string payload to the server - used to make new Redmine items.  Returns an JSON string or error.'''
		if self.readonlytest:
			print 'Redmine read only test: Pretending to create: ' + page
			return payload
		else:
			return self.open( page, parms, payload )
	
	def put(self, page, payload, parms=None ):
		'''Puts an XML object on the server - used to update Redmine items.  Returns nothing useful.'''
		if self.readonlytest:
			print 'Redmine read only test: Pretending to update: ' + page
		else:
			return self.open( page, parms, payload, HTTPrequest=self.PUT_Request )
	
	def delete(self, page ):
		'''Deletes a given object on the server - used to remove items from Redmine.  Use carefully!'''
		if self.readonlytest:
			print 'Redmine read only test: Pretending to delete: ' + page
		else:
			return self.open( page, HTTPrequest=self.DELETE_Request )


			
	def dict2XML(self, tag, dict ):
		'''Return an XML string encoding the given dict'''
		root = ET.Element( tag )
		for key in dict:
			ET.SubElement( root, str(key) ).text = str(dict[key])
		
		return ET.tostring( root, encoding='UTF-8' )
		
	
	def new_item(self, type, **dict):
		'''Create a new item'''
		target = '%s.json' % type
		payload = json.dumps(dict)
		return self.post( target, payload)
	
	def get_item(self, type, id):
		'''Get a given item by id'''
		target = '%s/%s.json' % (type, id)
		return self.get(target)
	
	def get_items(self, type):
		'''Get a group of items'''
		target = '%s.json' % type
		return self.get(target)
	
	def update_item(self, type, id, **dict):
		'''Update an item at the path with a given id'''
		target = '%s/%s.json' % (type, id)
		payload = json.dumps(dict)
		return self.put(target, payload)
	
	def delete_item(self, type, id):
		target = '%s/%s.json' % (type, id)
		self.delete(target)

	
	@classmethod
	def handle_type(cls, new_type):
		'''Instruct this class to handle a new type of data.'''
		if new_type == 'type':
			raise RuntimeError('You can\'t set a type of type!')
		for action, fn in cls.generic_action.items():
			method_name = action + '_' + new_type
			def fn_wrap(self, *kargs, **kw_args):
				fn(self, new_type, *kargs, **kw_args)
			cls.__dict__[action+'_'+new_type] = MethodType(fn_wrap, None, cls)
			
	def get_project(self, id ):
		'''returns a project object for the given project name'''
		#return self.Project( self.get('projects/'+projectIdent+'.xml') )
		url = 'projects/%s.json' % id
		return _Project( self, json_data=self.open(url), wrapper='project' )
		
	def get_issue(self, id ):
		'''returns an issue object for the given issue number'''
		#return self.Issue( self.get('issues/'+str(issueID)+'.xml') )
		url = 'issues/%s.json' % id
		return _Issue(self, json_data=self.open(url), wrapper='issue' )
		
	def newIssueFromDict(self, dict ):
		'''creates a new issue using fields from the passed dictionary.  Returns the issue number or None if it failed. '''
		xmlStr = self.dict2XML( 'issue', dict )
		newIssue = self.Issue( self.post( 'issues.xml', xmlStr ) )
		return newIssue
	
	def updateIssueFromDict(self, ID, dict ):
		'''updates an issue with the given ID using fields from the passed dictionary'''
		xmlStr = self.dict2XML( 'issue', dict )
		self.put( 'issues/'+str(ID)+'.xml', xmlStr )

	def delete_issue(self, ID ):
		'''delete an issue with the given ID.  This can't be undone - use carefully!
		Note that the proper method of finishing an issue is to update it to a closed state.'''
		self.delete( 'issues/'+str(ID)+'.json' )
		
	def close_issue(self, ID ):
		'''close an issue by setting the status to self.ISSUE_STATUS_ID_CLOSED'''
		self.updateIssueFromDict( ID, {'status_id':self.ISSUE_STATUS_ID_CLOSED} )
		
	def resolve_issue(self, ID ):
		'''close an issue by setting the status to self.ISSUE_STATUS_ID_RESOLVED'''
		self.updateIssueFromDict( ID, {'status_id':self.ISSUE_STATUS_ID_RESOLVED} )
		
	