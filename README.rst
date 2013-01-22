pyredminews
===========

Python Redmine Web Services Library

This python library facilitates creating, reading, updating and deleting content from a Redmine_ installation through the REST API.

Communications are performed via HTTP/S, freeing up the need for the Python script to run on the same machine as the Redmine installation.

This library was originally published at http://code.google.com/p/pyredminews/

.. _Redmine: http://www.redmine.org/

How to use it
-------------

The library, like most good Python libraries, is self documenting.  In the console, import the library then type ''help(redmine)'' 
for all the details.

Step by Step
++++++++++++

Open a Python terminal window.  (If PyRedmineWS is not installed in the library path, you'll need to be in the 
folder where the redmine.py resides.)

::

   $ python
   Python 2.6.1 (r261:67515, Feb 11 2010, 00:51:29) 
   [GCC 4.2.1 (Apple Inc. build 5646)] on darwin
   Type "help", "copyright", "credits" or "license" for more information.
   >>> 

Now, import redmine

::

   >>> import redmine
   >>>

View the documentation
++++++++++++++++++++++

::

   >>> help(redmine)
   Help on module redmine:  
   NAME
       redmine
   FILE
       /redmine.py
   CLASSES
       Redmine    
    class Redmine
     |  Class to interoperate with a Redmine installation using the REST web services.
     |  instance = Redmine(url, [key=strKey], [username=strName, password=strPass] )
     |  
   ...
   (type q to quit)

etc.

Locate a Redmine installation
+++++++++++++++++++++++++++++

If you don't have Redmine installed somewhere that you can play with you can use the public demo server.  
With your web browser, go take a look at http://demo.redmine.org.  Find or make a project and note its ID 
(not its pretty name, but the path it ends up in such as "testproject" in ``http://demo.redmine.org/projects/testproject``).  
Make a bug and note its number.  The remaining examples will assume you've done this.

Set up the Connection
+++++++++++++++++++++

Make an instance that represents the server you want to connect to.

::

   >>> demo_anon = redmine.Redmine('http://demo.redmine.org')
   >>>


Authentication
++++++++++++++

You can perform most of the view actions with this anonymous access, but for the really cool stuff, 
you should register an account and set up that access:

::

   >>> demo = redmine.Redmine('http://demo.redmine.org', username='pyredmine', password='password')
   >>>


Since leaving around your password in a script really sucks, Redmine allows you to use a user API key instead.  
Once logged into Redmine, on the My Account page, click on the Show button under the API Access Key on the right.  
That will reveal a key that can be used instead of a username/password.

::

   >>> demo = redmine.Redmine('http://demo.redmine.org', key='701c0aec4330fb2f1db944f1808e1e987050c7f5')
   >>>


View Project Data
+++++++++++++++++

Although you can use this library to look up a large list of projects, the easiest helper functions are designed 
to work with a single project of a given identifier (testproject, in our example above).  The getProject method 
returns a Project object.

::

   >>>project = demo.getProject('demoproject')
   http://demo.redmine.org/projects/demoproject.xml
   >>> 

(that url cruft is debugging info.  Please excuse my mess - it's only at version 0.1!)

Now with that shiny new project object, you can take a look at the data available:

::

  >>> project.id
  u'demoproject'
  >>> project.number
  u'9042'
  >>> project.data
  {u'name': u'New Demo Project', u'trackers': u'\n    ', u'created_on': u'Wed Jan 20 20:58:38 -0800 2010', u'updated_on': u'Wed Jan 20 20:58:38 -0800 2010', u'identifier': u'demoproject', u'id': u'9042', u'custom_fields': u'\n    '}
  >>> 


Create a New Issue
++++++++++++++++++

You can use the project object to create a new issue for that project:

::

   >>> issue = project.newIssue("Test from Python", "That rabbit is dynamite!")
   http://demo.redmine.org/issues.xml
   >>> issue['id']
   u'35178'
   >>> issue['created_on']
   u'Wed Oct 20 22:50:36 -0700 2010'
   >>>

Note that the newIssue command returned a dictionary containing most (hopefully, one day all) of the new issue's data.  
You can now go to http://demo.redmin.org/projects/demoproject/issues to see your new issue.
(Note the issue ID, you'll need that for the next steps)

View an Issue
+++++++++++++

You can view any issue by its ID:

::

   >>> demo.getIssue(35178)
   http://demo.redmine.org/issues/35178.xml
   {u'description': u'That rabbit is dynamite!', u'relations': u'\n  ', u'start_date': u'2010-10-20', u'created_on': u'Wed Oct 20 22:50:36 -0700 2010', u'custom_fields': u'\n    ', u'spent_hours': u'0.0', u'updated_on': u'Wed Oct 20 23:29:56 -0700 2010', u'id': u'35178', u'done_ratio': u'0', u'subject': u'Test from Python'}
   >>> 

Like the newIssue command above, it's returning a dictionary of (almost) all of the issue data.  
Note that this command is not running from the Project object but from the Redmine object.

Change an Issue's Status
++++++++++++++++++++++++

You can move an issue through the workflow as well.  Unfortunately, the Redmine REST API will 
only allow setting a status by the status ID and provides no mechanism to discover what status ID's are available.  
By default, the library uses the status ID for Resolved and Closed from a default Redmine installation, 
but if you've changed them in the Administration page, you'll have to change these each time as well.

::

   >>> demo.ISSUE_STATUS_ID_RESOLVED
   3
   >>> demo.ISSUE_STATUS_ID_CLOSED
   5
    

The following commands won't work for you with just copying and pasting - you'll need to grab that ''issue['id']'' from the example above.  
Here it was noted as u'35178' - so we'll use that for our example

::

   >>> demo.resolveIssue(35178)
   http://demo.redmine.org/issues/35178.xml
   ''
   >>> 

Success and failure both mean an empty string.  In this case, the sample user isn't allowed to modify or delete this issue, so it failed.
However, this command does function if you have the proper permissions.  There are a couple of other helpful issue commands as well:

::

   >>> demo.closeIssue(35178)
   http://demo.redmine.org/issues/35178.xml
   ''

Delete an Issue
+++++++++++++++

There is also a delete Issue command that you should use with care.  In a real production environment, 
you normally would never delete an issue - just leave it closed.  Deleting it will remove history, time worked, 
and almost every trace of it.  So, be careful!  On the demo server, you don't have permission to delete, so go ahead and try:

::

   >>> demo.deleteIssue(35178)
   (whole lot of response, including)
   urllib2.HTTPError: HTTP Error 403: Forbidden
   >>>

Redmine is inconsistent about when it returns 403 and when it just doesn't work.  You can't rely on the lack of an 
HTTPError to guarantee success.

Note that there is no good method to assign an issue to a user.  You can assign to the numeric user ID, 
but there's no interface yet for looking up the ID based on a user name.   You can use the catch-all 
command updateIssueFromDict to assign the issue to user number 25:

::

   >>> demo.updateIssueFromDict(35178, {'assigned_to_id':'25'} )
   http://demo.redmine.org/issues/35178.xml
   ''

Lower Level Functions
---------------------
There's a set of functions that can be used to perform more detailed (and complicated) queries and updates.  
Many of the methods implement these - read through the library documentation and even the library code for more information.


