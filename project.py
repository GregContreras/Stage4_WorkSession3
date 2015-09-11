import os
import urllib
import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'], 
    autoescape=True)


DEFAULT_SECTION_NAME = 'General_Submission'

# We set a parent key on the 'Comment' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def section_key(section_name=DEFAULT_SECTION_NAME):
    return ndb.Key('Section', section_name)
  #Constructs a Datastore key for a Section entity.We use section_name as the key.


# [START comment]
# These are the objects that will represent our Author and our Post. We're using
# Object Oriented Programming to create objects in order to put them in Google's
# Database. These objects inherit Googles ndb.Model class.
class Author(ndb.Model):
  """Sub model for representing an author."""
  identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  email = ndb.StringProperty(indexed=False)

class Comment(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

# [END comment]

class Handler(webapp2.RequestHandler): 
    """
    Basic Handler; will be inherited by more specific path Handlers
    """
    def write(self, *a, **kw):
        "Write small strings to the website"
        self.response.out.write(*a, **kw)  

    def render_str(self, template, **params):  
        "Render jija2 templates"
        t = JINJA_ENVIRONMENT.get_template(template)
        return t.render(params)   

    def render(self, template, **kw):
        "Write the jinja template to the website"
        self.write(self.render_str(template, **kw))


# [START main_page]
class MainPage(webapp2.RequestHandler):
    def get(self):
        section_name = self.request.get('section_name', DEFAULT_SECTION_NAME)
        if section_name == DEFAULT_SECTION_NAME.lower(): section_name = DEFAULT_SECTION_NAME
        comments_query = Comment.query(ancestor=section_key(section_name)).order(-Comment.date)
        num_comments = 10
        comments_list = comments_query.fetch(num_comments)

        # If a person is logged in to Google's Services
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            user = 'Anonymous Poster'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'user': user,
            'comment': comments_list,
            'section_name': urllib.quote_plus(section_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('intro_programming.html')
        self.response.write(template.render(template_values))

# [END main_page]

# [START Comment Submission]
class Section(webapp2.RequestHandler):
    def post(self):
        # We set a parent key on the 'Comment' to ensure that they are all
        # in the same entity group. Queries across the single entity group
        # will be consistent.  However, the write rate should be limited to
        # ~1/second. 
        section_name = self.request.get('section_name', DEFAULT_SECTION_NAME)
        
        comment = Comment(parent=section_key(section_name))

        if users.get_current_user():
            comment.author = Author(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email())

        # Get the content from our request parameters, in this case, the message
        # is in the parameter 'content'
        comment.content = self.request.get('content')

        # Write to the Google Database
        comment.put()

        query_params = {'section_name': section_name}
        self.redirect('/?' + urllib.urlencode(query_params))

#[END Comment Submission]


app = webapp2.WSGIApplication([
    ('/', MainPage), 
    ('/section', Section),
], debug=True)
