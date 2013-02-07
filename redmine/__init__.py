'''Python Redmine Web Services Library

This Python library facilitates creating, reading, updating and deleting content from a Redmine_ installation through the REST API.

Communications are performed via HTTP/S, freeing up the need for the Python script to run on the same machine as the Redmine installation.

LICENSE
+++++++

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
  
Locate a Redmine installation
+++++++++++++++++++++++++++++

If you don't have Redmine installed somewhere that you can play with you can use the public demo server.  
With your web browser, go take a look at http://demo.redmine.org.  Find or make a project and note its identifier 
(not its pretty name, but the path it ends up in such as "testproject" in ``http://demo.redmine.org/projects/testproject``).  
Make a bug and note its number.  The remaining examples will assume you've done this.

Currently the Redmine instalation running at demo.redmine.org *does not* have the REST interface enabled.  

Set up the Connection
+++++++++++++++++++++

Make an instance that represents the server you want to connect to.

::

   >>> demo_anon = Redmine('http://demo.redmine.org')
   >>>


Authentication
++++++++++++++

You can perform most of the view actions with this anonymous access, but for the cool stuff, 
you should register an account and set up that access:

::

   >>> demo = Redmine('http://demo.redmine.org', username='pyredmine', password='password')
   >>>


Since leaving around your password in a script really sucks, Redmine allows you to use a user API key instead.  
Once logged into Redmine, on the My Account page, click on the Show button under the API Access Key on the right.  
That will reveal a key that can be used instead of a username/password.  If you do not see any reference to the
API key in the right-hand panel, the REST interface probably hasn't been enabled - see `Set up Redmine`_ above.

::

   >>> demo = Redmine('http://demo.redmine.org', key='701c0aec4330fb2f1db944f1808e1e987050c7f5')
   >>>


Define the Redmine Version
++++++++++++++++++++++++++

Different versions of Redmine can use improved security, and have different items available through the REST interface.
In order for the module to correctly represent the data and use available security features, you should tell
the object what version your Redmine server is using.

::

   >>> demo = Redmine('http://demo.redmine.org', username='pyredmine', password='password', version=2.1)
   >>>



View Project Data
+++++++++++++++++

Although you can use this library to look up a large list of projects, the easiest helper functions are designed 
to work with a single project of a given identifier (testproject, in our example above).  The projects parameter on
the Redmine object can be used to return a single Project object. 

::

   >>> project = demo.projects['demoproject']
   >>> 

Now with that shiny new project object, you can take a look at the data available:

::

   >>> project.id
   393
   >>> project.identifier
   u'demoproject'
   >>> 

The fields available on the project will differ depending on the version of Redmine.
To see the full list of items available for the project, try:

::

   >>> dir(project)
   (politely ignore anything staring with a _)
    u'created_on',
    u'description',
    u'homepage',
    u'id',
    u'identifier',
    'issues',
    u'name',
    'parent',
    'refresh',
    'save',
    'time_entries',
    u'updated_on']

   

If you happen to know the numeric ID of your project, that can also be used to look it up.  If demoproject is in fact
id 393, then the following will return the same project:

::

    >>> project = demo.projects[393]
    
Change the Project
++++++++++++++++++

Changing the fields of the project are as easy as changing the objects parameters and invoking the save method.

::

   >>> project.homepage = 'http://www.dead-parrot.com'
   >>> project.name = 'Dead Parrot Society'
   >>> project.save()
   
If you try and set a parameter for a read-only field, you'll get an attribute error.

::

   >>> project.updated_on = 'today'
   AttributeError: Can't set attribute updated_on.
   
If your Redmine instance has custom fields set for projects, those fields and their values will be returned and can be changed
in the same manner:

::

   >>> project.custom_fields['Customer'] = 'John Cleese'
   >>> project.save()
   

Examine All Projects
++++++++++++++++++++

The projects member can be iterated over to retrieve information about all projects.  Be default, Redmine will return 25 items
at a time, so the following query might take some time to complete.

::

   >>> for proj in demo.projects:
   ...   print "%s : %s" % (proj.name, proj.homepage)
   
   (truncated)
   Test Project LS II : None
   Test Project Only : None
   Test Project Rizal : None
   Create home page : None
   Test Project SES : None
   Test project SGO : None
   Test Project Trial : None
   Test Project Tutorial ABCDE : None
   

Get All Issues for a Project
++++++++++++++++++++++++++++

The issues associated for a project can be retreived by iterating over the 'issues' method in a project.

::

   >>> for issue in project.issues:
   ...    print issue
   <Redmine issue #3903, "mary was here too">
   <Redmine issue #3902, "Johny was there">
   <Redmine issue #3870, "Demo Feature">
   (truncated)
   
(You may get an Unicode error if any of the issues has unicode in the subject.  If you do, instead use: print "%s" % issue )

If you want to exclude issues from any subprojects, you can add query parameters to the iterator:

::

    >>> for issue in project.issues(subproject_id='!*'):
    ...    print issue
    
Other parameters are:

* tracker_id: get issues from the tracker with the given id
* status_id: get issues with the given status id only. Possible values: open, closed, * to get open and closed issues, status id
* assigned_to_id: get issues which are assigned to the given user id
* cf_x: get issues with the given value for custom field with an ID of x. (Custom field must have 'used as a filter' checked.)


Create a New Issue
++++++++++++++++++

You can use the project object to create a new issue for that project:

::

   >>> issue = project.issues.new(subject="Test from Python", description="That rabbit is dynamite!")
   >>> issue.id
   35178
   >>> issue.created_on
   datetime.datetime(2013, 2, 7, 1, 0, 28, tzinfo=tzutc())
   >>>

Note that the new command returned an Issue object containing all (or, on older Redmine versions, most) of the new issue's data.  
You can now go to http://demo.redmin.org/projects/demoproject/issues to see your new issue.  Any date/time information is returned
as a `Python datetime object <http://docs.python.org/2/library/datetime.html#datetime-objects>`_.
(Note the issue ID, you'll need that for the next steps)

View an Issue
+++++++++++++

You can view any issue by its ID:

::

   >>> issue = demo.issues[35178]
   >>> issue.status
   <Redmine status #1 - New>
   >>> issue.subject
   u'That rabbit is dynamite!'

Like the issues.new command above, it's returning an object with all of the issue data.  
Note that this command is not running from the Project object but from the Redmine object.

If you examine your issue object, you'll see that it contains an author parameter, which is itself another object:

::

   >>> issue.author
   <Redmine user #5 - Ian Epperson>

However, this user object is incomplete:

::

   >>> issue.author.last_login
   
   >>>

pyRedmine created the object with the data it had on hand, and since it doesn't have the last_login data (it wasn't
in the issue information) it isn't shown here.  There are two ways to flesh out that data, one is to use the refresh
method for the author (works on Redmine 1.1 and later where this data is available).

::

   >>> issue.author.refresh()
   >>> issue.author.last_login
   datetime.datetime(2013, 2, 7, 1, 0, 28, tzinfo=tzutc())
   
The other is to simply request that user id from the server

::

   >>> demo.users[5]
   <Redmine user #5 - Ian Epperson>
   >>> issue.author.last_login
   datetime.datetime(2013, 2, 7, 1, 0, 28, tzinfo=tzutc())

pyRedmine caches all objects it sees and sets up all cross references.  Updating a Redmine object attached to one object 
will update them all.  Also, this allows you to directly compare objects if needed:

::

   >>> issue.author == issue.assigned_to
   True      

Change an Issue's Status
++++++++++++++++++++++++

You can move an issue through the workflow as well.  You must set an issue status based on the status ID,
which is can only be discovered in Redmine version 2.2 and later (but not yet available via this library).
By default, the library uses the status ID for Resolved and Closed from a default Redmine installation, 
but if you've changed them in the Administration page, you'll have to change these each time as well.

::

   >>> demo.ISSUE_STATUS_ID_RESOLVED
   3
   >>> demo.ISSUE_STATUS_ID_CLOSED
   5
    

The closed and resolved methods are available on the issue itself, with an optional comment:

::

   >>> issue.close('Closed the issue from Python!')
   >>> issue.resolve('Resolved the issue from Python!')
   
Some versions of Redmine will not return an error if this operation fails, so be careful of false hopes.

If you need to set another status, you'll need to find the requisite status ID, then use the set_status method
(again, with optional comment):

::

   >>> issue.set_status(8, 'Setting the status from Python!')

If you need to close an issue and don't need to get an issue object, you can set the issue status directly
using the Redmine server object with a single operation:

::

   >>> demo.issues.update(35178, status_id=5)
   

Change an Issue
+++++++++++++++

Just like with projects, to change a field on an issue simply change the parameter on the issue object
then invoke the save method.

::

   >>> issue.description = "The parrot doesn't seem to be alive."
   >>> issue.save()
   
If your installation of Redmine has custom fields on issues, those fields can be inspected and set.

::

   >>> issue.custom_fields['Inform the client']
   u'0'
   >>> issue.custom_fields['Inform the client'] = 1
   >>> issue.save()
   

If you want to change the project this issue is assigned to, you can set it directly to either a project object
or a numeric project ID, then save it.

::

   >>> issue.project = 12
   >>> issue.save()
   
   >>> issue.project = demo.projects['test']
   >>> issue.save()


Delete an Issue
+++++++++++++++

There is also an issue delete command that you should use with care.  In a real production environment, 
you normally would never delete an issue - just leave it closed.  Deleting it will remove history, time worked, 
and almost every trace of it.  So, be careful!  On the demo server, you don't have permission to delete, so go ahead and try:

::

   >>> demo.issues.delete(35178)
   (whole lot of response, including)
   urllib2.HTTPError: HTTP Error 403: Forbidden
   >>>

Different versions of Redmine are inconsistent about when they returns 403 and when they just doesn't work.  You can't rely on the lack of an 
HTTPError to guarantee success.

Note that there is no good method to assign an issue to a user.  You can assign to the numeric user ID, 
but there's no interface yet for looking up the ID based on a user name.   You can use the catch-all 
command updateIssueFromDict to assign the issue to user number 25:

::

   >>> demo.updateIssueFromDict(35178, {'assigned_to_id':'25'} )
   http://demo.redmine.org/issues/35178.xml
   ''

Other Objects
+++++++++++++

Depending on what Redmine version you have, you can use these same commands to get/update/delete different Redmine items:

* users
* news
* time_entries

Not every item supports every method.  For instance, no current version of Redmine allows creating a news item, thus:

::

   >>> demo.news.new(title='does this work?', description='Nope', author_id=4)
   AttributeError: new is not available for News



'''

__all__ = []

from redmine import Redmine
