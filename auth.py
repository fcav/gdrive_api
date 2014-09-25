import logging

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import Credentials
from oauth2client.client import FlowExchangeError


import httplib2


# Copy your credentials from the console
CLIENT_ID = '966628529222-04dnc40etlli3e0r4bf2lbn2fofm0iqr.apps.googleusercontent.com'
CLIENT_SECRET = '0dnz2sCapeVIQ8lfDfi0ALad'

# Check https://developers.google.com/drive/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

# Redirect URI for installed apps
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

class GetCredentialsException(Exception):
  """Error raised when an error occurred while retrieving credentials.

  Attributes:
    authorization_url: Authorization URL to redirect the user to in order to
                       request offline access.
  """

  def __init__(self, authorization_url):
    """Construct a GetCredentialsException."""
    self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
  """Error raised when a code exchange has failed."""


class NoUserIdException(Exception):
  """Error raised when no user ID could be retrieved."""


def get_stored_credentials(user_id):
    """Retrieved stored credentials for the provided user ID.

    Args:
    user_id: User's ID.
    Returns:
    Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
    Raises:
    NotImplemented: This function has not been implemented.
    """
    #       To instantiate an OAuth2Credentials instance from a Json
    #       representation, use the oauth2client.client.Credentials.new_from_json
    #       class method.
    with open('./{}-creds.txt'.format(user_id)) as fin:
        return Credentials.new_from_json(fin.read())


def store_credentials(user_id, credentials):
    """Store OAuth 2.0 credentials in the application's database.

    This function stores the provided OAuth 2.0 credentials using the user ID as
    key.

    Args:
    user_id: User's ID.
    credentials: OAuth 2.0 credentials to store.
    Raises:
    NotImplemented: This function has not been implemented.
    """
    #       To retrieve a Json representation of the credentials instance, call the
    #       credentials.to_json() method.
    with open('/home/alex/work/drive/{}-creds.txt'.format(user_id), 'w') as fout:
        fout.write(credentials.to_json()) 

def exchange_code(authorization_code):
    """Exchange an authorization code for OAuth 2.0 credentials.

    Args:
    authorization_code: Authorization code to exchange for OAuth 2.0
                        credentials.
    Returns:
    oauth2client.client.OAuth2Credentials instance.
    Raises:
    CodeExchangeException: an error occurred.
    """
    flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)

    try:
        credentials = flow.step2_exchange(authorization_code)
        return credentials
    except FlowExchangeError, error:
        logging.error('An error occurred: %s', error)
        raise CodeExchangeException(None)


def get_user_info(credentials):
  """Send a request to the UserInfo API to retrieve the user's information.

  Args:
    credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                 request.
  Returns:
    User information as a dict.
  """
  user_info_service = build(
      serviceName='oauth2', version='v2',
      http=credentials.authorize(httplib2.Http()))
  user_info = None
  try:
    user_info = user_info_service.userinfo().get().execute()
  except errors.HttpError, e:
    logging.error('An error occurred: %s', e)
  if user_info and user_info.get('id'):
    return user_info
  else:
    raise NoUserIdException()


def get_authorization_url(email_address):
    """Retrieve the authorization URL.

    Args:
    email_address: User's e-mail address.
    Returns:
    Authorization URL to redirect the user to.
    """
    flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)

    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    flow.params['user_id'] = email_address

    return flow.step1_get_authorize_url()


if __name__ == '__main__':
    auth_url = get_authorization_url('data@essencedigital.com')
    print 'Go to the following link in your browser: ' + auth_url
    code = raw_input('Enter verification code: ').strip()
    creds = exchange_code(code)
    store_credentials('data@essencedigital.com', creds)
