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
from xml.dom import minidom, getDOMImplementation
import xml.etree.ElementTree as ET
		

class _Project:
	'''Object returned by Redmine getProject calls
	   redmine is the redmine object.
	   objXML is the xml object containing the object data'''
	
	def __init__(self, redmine, eTree=None ):
		self.__redmine = redmine
		self.root = None
		self.number = None
		self.id = None
		self.name = None
		self.custom = {}
		self.tracker = {}
		
		if eTree:
			try:
				self.parseETree( eTree )
			except:
				if self.__redmine.readonlytest:
					self.THIS_IS_FAKE_DATA = True
					self.number = '6789'
					self.name = 'Fake Project'
					self.id = 'fakeproject'
					return
				else:
					raise
		
	def parseETree(self, eTree ):
		self.root = eTree.getroot()
		
		if self.root.tag == 'projects':
			raise TypeError ('XML does not describe a single project, but a collection of projects.')
		elif not self.root.tag == 'project':
			raise TypeError ('XML does not describe a project as I know it.')
		
		self.number = self.root.find('id').text
		self.id = self.root.find('identifier').text
		self.name = self.root.find('name').text
		
		for field in self.root.find('custom_fields'):
			self.custom[ field.attrib['name'] ] = field.text
			
		for tracker in self.root.find('trackers'):
			self.tracker[ tracker.attrib['name'] ] = tracker.attrib['id']
		
	
	def newIssue(self, **data ):
		'''Create a new issue for this project from the given pairs.
		
		newIssue( subject="The Arguments Department is closed", description="Good morning." )
		
		Possible keys are:
		 subject
		 description
		 status_id
		 priority_id
		 tracker_id - can be looked up from name in Project.trackers[name]
		 assigned_to_id
		
		Unfortunately, there is no easy way to discover the valid values for most of the _id fields'''
			
		if not 'subject' in data:
			TypeError('Subject cannot be blank.  Use subject=str')
		
		data[ 'project_id' ] = self.number
		return self.__redmine.newIssueFromDict( data )
		
	def getIssues(self ):
		pass
		#todo: finish



class _Issue:
	'''Object returned by Redmine getIssue and newIssue calls'''
	def __init__(self, redmine, eTree=None ):
		self.__redmine = redmine
		
		self.id = None
		self.subject = None
		self.custom = {}
		self.relations = {}
		self.assigned_to = None
		self.tracker = None
		self.status = None
		
		if eTree:
			try:
				self.parseETree( eTree )
			except:
				if self.__redmine.readonlytest:
					self.THIS_IS_FAKE_DATA = True
					self.id = '12345'
					self.subject = 'Fake Issue'
					self.project = '6789'
					self.status = '1'
					return
				else:
					raise

	
	def parseETree(self, eTree):
		'''Parse fields from given eTree into this object'''
		self.root = eTree.getroot()
		
		if self.root.tag == 'issues':
			raise TypeError ('XML does not describe a single issue, but a collection of issues.')
		elif not self.root.tag == 'issue':
			raise TypeError ('XML does not describe an issue as I know it.')
		
		self.id 		= self.root.find('id').text
		self.subject 	= self.root.find('subject').text
		self.project 	= self.root.find('project').attrib
		self.tracker 	= self.root.find('tracker').attrib
		self.status 	= self.root.find('status').attrib
		
		try:
			self.assigned_to = self.root.find('assigned_to').attrib
		except:
			pass
		
		
		for field in self.root.find('custom_fields'):
			self.custom[ field.attrib['name'] ] = field.text

		for field in self.root.find('relations'):
			self.relations[ field.attrib['issue_id'] ] = field.attrib
			
	def resolve(self):
		'''Resolve this issue'''
		self.__redmine.resolveIssue( self.id )
		
	def close(self):
		'''Close this issue'''
		self.__redmine.closeIssue( self.id )
		
	def save(self):
		'''Saves this issue - updates or creates new issue as necessary.  Failed updates DO NOT return any errors.'''
		pass


class Redmine:
	'''Class to interoperate with a Redmine installation using the REST web services.
	instance = Redmine(url, [key=strKey], [username=strName, password=strPass] )
	
	url is the base url of the Redmine install ( http://my.server/redmine )
	
	key is the user API key found on the My Account page for the logged in user
		All interactions will take place as if that user were performing them, and only
		data that that user can see will be seen

	If a key is not defined then a username and password can be used
	If neither are defined, then only publicly visible items will be retreived	
	'''
	
	def __init__(self, url, key=None, username=None, password=None, debug=False, readonlytest=False ):
		self.__url = url
		self.__key = key
		self.debug = debug
		self.readonlytest = readonlytest
		self.projects = {}
		self.projectsID = {}
		self.projectsXML = {}
		
		self.issuesID = {}
		self.issuesXML = {}
		
		# Status ID from a default install
		self.ISSUE_STATUS_ID_NEW = 1
		self.ISSUE_STATUS_ID_RESOLVED = 3
		self.ISSUE_STATUS_ID_CLOSED = 5
		
		if readonlytest:
			print 'Redmine instance running in read only test mode.  No data will be written to the server.'
		
		self.__opener = None
		
		if not username:
			username = key
			self.__key = None
			
		if not password:
			password = '12345'  #the same combination on my luggage!  (dummy value)
		
		if( username and password ):
			#realm = 'Redmine API'
			# create a password manager
			password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

			password_mgr.add_password(None, url, username, password )
			handler = urllib2.HTTPBasicAuthHandler( password_mgr )

			# create "opener" (OpenerDirector instance)
			self.__opener = urllib2.build_opener( handler )

			# set the opener when we fetch the URL
			self.__opener.open( url )

			# Install the opener.
			urllib2.install_opener( self.__opener )
			
		else:
			if not key:
				pass
				#raise TypeError('Must pass a key or username and password')
		

	def Issue(self, eTree=None ):
		'''Issue object factory'''
		return _Issue( self, eTree )
		
	def Project(self, eTree=None ):
		'''Issue project factory'''
		return _Project( self, eTree )
	
	# extend the request to handle PUT command
	class PUT_Request(urllib2.Request):
		def get_method(self):
			return 'PUT'

	# extend the request to handle DELETE command
	class DELETE_Request(urllib2.Request):
		def get_method(self):
			return 'DELETE'
	
	
	
	def openRaw(self, page, parms=None, XMLstr=None, HTTPrequest=None ):
		'''Opens a page from the server with optional XML.  Returns a response file-like object'''
		if not parms:
			parms={}
			
		# if we're using a key, add it to the parms array
		if self.__key:
			parms['key'] = self.__key
		
		# encode any data
		urldata = ''
		if parms:
			urldata = '?' + urllib.urlencode( parms )
		
		
		fullUrl = self.__url + '/' + page
		
		# register this url to be used with the opener
		if self.__opener:
			self.__opener.open( fullUrl )
			
		#debug
		if self.debug:
			print fullUrl + urldata
		
		# Set up the request
		if HTTPrequest:
			request = HTTPrequest( fullUrl + urldata )
		else:
			request = urllib2.Request( fullUrl + urldata )
		# get the data and return XML object
		if XMLstr:
			request.add_header('Content-Type', 'text/xml')
			response = urllib2.urlopen( request, XMLstr )			
		else:
			response = urllib2.urlopen( request )
		
		return response
	
	def open(self, page, parms=None, objXML=None, HTTPrequest=None ):
		'''Opens a page from the server with optional XML.  Returns an XML ETree object or string if return value isn't XML'''
		response = self.openRaw( page, parms, objXML, HTTPrequest )
		try:
			etree = ET.ElementTree()
			etree.parse( response )
			return etree
		except:
			return response.read()
		
	
	def get(self, page, parms=None ):
		'''Gets an XML object from the server - used to read Redmine items.'''
		return self.open( page, parms )
	
	def post(self, page, objXML, parms=None ):
		'''Posts an XML object to the server - used to make new Redmine items.  Returns an XML object.'''
		if self.readonlytest:
			print 'Redmine read only test: Pretending to create: ' + page
			return objXML
		else:
			return self.open( page, parms, objXML )
	
	def put(self, page, objXML, parms=None ):
		'''Puts an XML object on the server - used to update Redmine items.  Returns nothing useful.'''
		if self.readonlytest:
			print 'Redmine read only test: Pretending to update: ' + page
		else:
			return self.open( page, parms, objXML, HTTPrequest=self.PUT_Request )
	
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
		
		
	def getProject(self, projectIdent ):
		'''returns a project object for the given project name'''
		return self.Project( self.get('projects/'+projectIdent+'.xml') )
		
	def getIssue(self, issueID ):
		'''returns an issue object for the given issue number'''
		return self.Issue( self.get('issues/'+str(issueID)+'.xml') )
		
	def newIssueFromDict(self, dict ):
		'''creates a new issue using fields from the passed dictionary.  Returns the issue number or None if it failed. '''
		xmlStr = self.dict2XML( 'issue', dict )
		newIssue = self.Issue( self.post( 'issues.xml', xmlStr ) )
		return newIssue
	
	def updateIssueFromDict(self, ID, dict ):
		'''updates an issue with the given ID using fields from the passed dictionary'''
		xmlStr = self.dict2XML( 'issue', dict )
		self.put( 'issues/'+str(ID)+'.xml', xmlStr )

	def deleteIssue(self, ID ):
		'''delete an issue with the given ID.  This can't be undone - use carefully!
		Note that the proper method of finishing an issue is to update it to a closed state.'''
		self.delete( 'issues/'+str(ID)+'.xml' )
		
	def closeIssue(self, ID ):
		'''close an issue by setting the status to self.ISSUE_STATUS_ID_CLOSED'''
		self.updateIssueFromDict( ID, {'status_id':self.ISSUE_STATUS_ID_CLOSED} )
		
	def resolveIssue(self, ID ):
		'''close an issue by setting the status to self.ISSUE_STATUS_ID_RESOLVED'''
		self.updateIssueFromDict( ID, {'status_id':self.ISSUE_STATUS_ID_RESOLVED} )
		
	