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

class RedmineError(StandardError):
	pass


class Redmine_Item(object):
	'''Base class used for all items returned from Redmine.'''
	# List out the attributes that aren't user-settable
	_protected_attr = ['id']
	_type = ''
	_changes = None
	
	def __init__(self, redmine, update_fn, json_data=None, data={}):
		self._redmine = redmine
		self._update_fn = update_fn
		
		if json_data:
			# Parse the data
			try:
				data = json.loads(json_data)
			except ValueError:
				# If parsing failed, then raise the string which likely contains an error message instead of data
				raise RedmineError(json_data)
		if self._type:
			try:
				data = data[self._type]
			except:
				pass
		# Map all dictionary data to object attributes
		self.__dict__.update(data)

		# Set the changes dict to track all changes from here on out
		self._changes = {}
		
	def __setattr__(self, name, value):
		'''Set the attribute for any non-protected attribute.'''
		if name in self._protected_attr:
			raise AttributeError("Can't set attribute %s." % name)
		# Track any new changes for later saving
		try:
			self._changes[name] = value
		except TypeError:
			pass
		
		# Set the instance value
		self.__dict__[name] = value

	def save(self, notes=None):
		'''Save all changes (if any) back to Redmine.'''
		if not self._changes:
			return None
		try:
			self._update_fn(self.id, **self._changes)
		except:
			raise
		else:
			# Successful save, woot! Now clear the changes dict
			self._changes.clear()


class Redmine_Item_Control(object):
	_object = Redmine_Item
	
	_query_path = ''
	_query_container = ''
	_item_path = ''
	_item_new_path = ''
	
	def __init__(self, redmine):
		self._redmine = redmine
	
	def __getitem__(self, key):
		# returned when self[key] is called
		return self.get(key)
	
	def _objectify(self, json_data):
		'''Return an object derived from the given json data.'''
		return self._object(self._redmine, self.update, json_data=json_data)
	
	def new(self, **dict):
		'''Create a new item with the provided dict information.  Returns the new item.'''
		if not self._item_new_path:
			raise AttributeError('new is not available for %s' % self._type)
		target = self._item_new_path
		payload = json.dumps({self._object._type:dict})	
		json_data = self._redmine.post(target, payload)
		return self._objectify(json_data)
	
	def get(self, id):
		'''Get a single item with the given ID'''
		if not self._item_path:
			raise AttributeError('get is not available for %s' % self._type)
		target = self._item_path % id
		json_data = self._redmine.get(target)
		return self._objectify(json_data)
	
	def update(self, id, **dict):
		'''Update a given item with the passed data.'''
		if not self._item_path:
			raise AttributeError('update is not available for %s' % self._type)
		target = self._item_path % id
		payload = json.dumps({self._object._type:dict})	
		self._redmine.put(target, payload)
		return None	
		
	def delete(self, id):
		'''Delete a single item with the given ID'''
		if not self._item_path:
			raise AttributeError('delete is not available for %s' % self._type)
		target = self._item_path % id
		self._redmine.delete(target)
		return None
	
		


class Project(Redmine_Item):
	'''Object representing a Redmine project.
	Returned by Redmine getProject calls.
	'''
	# data hints:
	id = None
	name = None
	identifier = None
	homepage = None
	
	_type = 'project'
	_protected_attr = ['id',
					   'created_on',
					   'updated_on',
					   'identifier',
					   ]
	
	def __init__(self, redmine, *args, **kw_args):
		# Override init to also set up sub-queries
		# Call the base-class init
		super(Project, self).__init__(redmine, *args, **kw_args)
		
		# Create our own issues controller,
		# using __dict__ to bypass the changes__dict__
		self.__dict__['issues'] = Issue_Control(redmine)
		# Bake this project ID into queries and new issue commands
		self.issues._query_path = '/projects/%s/issues.json' % self.id
		self.issues._item_new_path = self.issues._query_path
			
	def __repr__(self):
		return '<Redmine project #%s "%s">' % (self.id, self.identifier)
	
class Project_Control(Redmine_Item_Control):
	_object = Project
	_query_container = 'projects'
	_query_path = '/projects.json'
	_item_path = '/projects/%s.json'
	_item_new_path = '/projects.json'
	


class Issue(Redmine_Item):
	'''Object representing a Redmine issue.'''
	# data hints:
	id = None
	subject = None
	description = None
	tracker = None
	status = None
	project = None
	estimated_hours = None
	done_ratio = None
	assigned_to = None
	
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

	def save(self, notes=None):
		'''Save all changes back to Redmine with optional notes.'''
		# Capture the notes if given
		if notes:
			self._changes['notes'] = notes
		
		# Check the changes dict for fields that need remapping
		# Several fields need to go from field['id'] to field_id
		for tag in ['assigned_to', 'project', 'category', 'status', 'parent_issue']:
			try:
				value = self._changes[tag]
			except:
				continue
			
			tag_id = tag + '_id'
			try:
				# Remap the ID change to the required field
				self._changes[tag_id] = value['id']
			except KeyError:
				try:
					# Try and grab the id of the object
					self._changes[tag_id] = value.id
				except AttributeError:
					# If the changes field is not a dict or object, just use whatever value was given
					self._changes[tag_id] = value
			
			# Remove the tag from the changed data
			del self._changes[tag]
			
		
		# Call the base-class save function
		super(Issue, self).save()

	def set_status(self, new_status, notes=None):
		'''Save all changes and set to the given new_status'''
		self.status_id = new_status
		try:
			self.status['id'] = self.status_id
			# We don't have the id to name mapping, so blank the name
			self.status['name'] = None
		except:
			pass
		self.save(notes)		

	def resolve(self, notes=None):
		'''Save all changes and resolve this issue'''
		self.set_status( self._redmine.ISSUE_STATUS_ID_RESOLVED, notes=notes )
		
	def close(self, notes=None):
		'''Save all changes and close this issue'''
		self.set_status( self._redmine.ISSUE_STATUS_ID_CLOSED, notes=notes )

class Issue_Control(Redmine_Item_Control):
	_object = Issue
	_query_container = 'issues'
	_query_path = '/issues.json'
	_item_path = '/issues/%s.json'
	_item_new_path = '/issues.json'
	


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
		
	def __init__(self, url, key=None, username=None, password=None, debug=False, readonlytest=False ):
		self._url = url
		self._key = key
		self.debug = debug
		self.readonlytest = readonlytest
		self.projects = {}
		
		if readonlytest:
			print 'Redmine instance running in read only test mode.  No data will be written to the server.'
		
		self._opener = None
		
		#if not username:
		#	username = key
		#	self._key = None
			
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
			
		# Create objects to manipulate different types
		self.issues = Issue_Control(self)
		self.projects = Project_Control(self)	
		

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
			parms['key'] = self._key
		
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


#			
#	def dict2XML(self, tag, dict ):
#		'''Return an XML string encoding the given dict'''
#		root = ET.Element( tag )
#		for key in dict:
#			ET.SubElement( root, str(key) ).text = str(dict[key])
#		
#		return ET.tostring( root, encoding='UTF-8' )
#		
#	
#	def new_item(self, type, **dict):
#		'''Create a new item'''
#		target = '%s.json' % type
#		payload = json.dumps(dict)
#		return self.post( target, payload)
#	
#	def get_item(self, type, id):
#		'''Get a given item by id'''
#		target = '%s/%s.json' % (type, id)
#		return self.get(target)
#	
#	def get_items(self, type):
#		'''Get a group of items'''
#		target = '%s.json' % type
#		return self.get(target)
#	
#	def update_item(self, type, id, **dict):
#		'''Update an item at the path with a given id'''
#		target = '%s/%s.json' % (type, id)
#		payload = json.dumps(dict)
#		self.put(target, payload)
#	
#	def delete_item(self, type, id):
#		target = '%s/%s.json' % (type, id)
#		self.delete(target)
#
#	
#	@classmethod
#	def handle_type(cls, new_type):
#		'''Instruct this class to handle a new type of data.'''
#		if new_type == 'type':
#			raise RuntimeError('You can\'t set a type of type!')
#		for action, fn in cls.generic_action.items():
#			method_name = action + '_' + new_type
#			def fn_wrap(self, *kargs, **kw_args):
#				fn(self, new_type, *kargs, **kw_args)
#			cls.__dict__[action+'_'+new_type] = MethodType(fn_wrap, None, cls)
#			
#	def get_project(self, id ):
#		'''returns a project object for the given project name'''
#		#return self.Project( self.get('projects/'+projectIdent+'.xml') )
#		url = 'projects/%s.json' % id
#		return _Project( self, json_data=self.open(url), wrapper='project' )
#		
#	def get_issue(self, id ):
#		'''returns an issue object for the given issue number'''
#		#return self.Issue( self.get('issues/'+str(issueID)+'.xml') )
#		url = 'issues/%s.json' % id
#		return _Issue(self, json_data=self.open(url), wrapper='issue' )
#		
#	def newIssueFromDict(self, dict ):
#		'''creates a new issue using fields from the passed dictionary.  Returns the issue number or None if it failed. '''
#		xmlStr = self.dict2XML( 'issue', dict )
#		newIssue = self.Issue( self.post( 'issues.xml', xmlStr ) )
#		return newIssue
#	
#	def updateIssueFromDict(self, ID, dict ):
#		'''updates an issue with the given ID using fields from the passed dictionary'''
#		xmlStr = self.dict2XML( 'issue', dict )
#		self.put( 'issues/'+str(ID)+'.xml', xmlStr )
#
#	def delete_issue(self, ID ):
#		'''delete an issue with the given ID.  This can't be undone - use carefully!
#		Note that the proper method of finishing an issue is to update it to a closed state.'''
#		self.delete( 'issues/'+str(ID)+'.json' )
#		
#	def close_issue(self, ID ):
#		'''close an issue by setting the status to self.ISSUE_STATUS_ID_CLOSED'''
#		self.updateIssueFromDict( ID, {'status_id':self.ISSUE_STATUS_ID_CLOSED} )
#		
#	def resolve_issue(self, ID ):
#		'''close an issue by setting the status to self.ISSUE_STATUS_ID_RESOLVED'''
#		self.updateIssueFromDict( ID, {'status_id':self.ISSUE_STATUS_ID_RESOLVED} )
#		
#	