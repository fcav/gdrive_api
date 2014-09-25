from apiclient.discovery import build
from apiclient import errors
from apiclient.http import MediaFileUpload
import httplib2
import auth
import datetime
import pprint
import ConfigParser


CONFIG = 'gdrive.ini'

def build_service(credentials):
    """Build a Drive service object.

    Args:
        credentials: OAuth 2.0 credentials.

    Returns:
        Drive service object.
    """
    http = httplib2.Http()
    http = credentials.authorize(http)
    return build('drive', 'v2', http=http)

def print_file_metadata(service, file_id):
    """Print a file's metadata.

    Args:
        service: Drive API service instance.
        file_id: ID of the file to print metadata for.
    """
    try:
        file = service.files().get(fileId=file_id).execute()

        print 'Title: %s' % file['title']
        print 'Description: %s' % file['description']
        print 'MIME type: %s' % file['mimeType']
    except errors.HttpError, error:
        if error.resp.status == 401:
         #Credentials have been revoked.
         # TODO: Redirect the user to the authorization URL.
             raise NotImplementedError()

def upload_file(service, filepath, title, description, mimeType):
    media_body = MediaFileUpload(filepath, mimetype='text/plain', resumable=True)
    body = {
      'title': title,
      'description': description,
      'mimeType': mimeType
    }
    file = service.files().insert(body=body, media_body=media_body).execute()
    return file


def get_folder(service, folder_name = None):
    query = "mimeType = 'application/vnd.google-apps.folder'"
    if folder_name:
         query += "and title = '{}'".format(folder_name)
    folder = service.files().list(q=query).execute()
    return folder


def get_folder_files(service, folder, modified_since=None):
    if len(folder['items']) < 1:
        yield
    folder_id = folder['items'][0]['id']
    child_list_response = service.files().list(q="'{}' in parents".format(folder_id)).execute()
    children = child_list_response['items']
    for child in children:
        modified = datetime.datetime.strptime(child['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if (modified_since is None) or modified > modified_since:
            yield child        
            
def get_file(service, file_name):
    query = "mimeType != 'application/vnd.google-apps.folder' and title = '{}'".format(file_name)
    file = service.files().list(q=query).execute()
    return file['items']

def download_xlsx(files, path):
    for file in files:
        pprint.pprint(file)
        title = file['title']
        download_url = file['exportLinks']['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        with open(path + '/' + title + ".xlsx", 'w')  as fout:
            response, content = service._http.request(download_url)
            fout.write(content)
    
def read_config(fpath):
    config = ConfigParser.SafeConfigParser()
    config.read(fpath)
    sprdsht = []
    for sp_name in config.sections():
        sp_details = {}
        sp_details['job_name'] = sp_name
        sp_details['type'] = config.get(sp_name, 'type')
        sp_details['title'] = config.get(sp_name, 'title')
        sp_details['folder'] = config.get(sp_name, 'folder')
        try:
            sp_details['modified_since'] = config.get(sp_name,'modified_since')
        except ConfigParser.NoOptionError:
            pass #optional
        sprdsht.append(sp_details)
    return sprdsht

if __name__ == '__main__':
    creds = auth.get_stored_credentials('data@essencedigital.com')
    service = build_service(creds)
    
    config = read_config(CONFIG)
    
    files = []
    for job in config:
        if job['type'] == 'file':
            file_name = job['title']
            files = get_file(service,file_name)
        elif job['type'] == 'folder':
            folder_name = job['title']
            folder = get_folder(service, folder_name)
            date = job.get('modified_since',None)
            modified_since = datetime.datetime.strptime(date, '%Y-%m-%d') if date else None
            files = get_folder_contents(service, folder, modified_since)
        download_xlsx(files, job['folder']) 



