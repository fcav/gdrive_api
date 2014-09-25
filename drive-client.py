from apiclient.discovery import build
from apiclient import errors
from apiclient.http import MediaFileUpload
import httplib2

import auth

import datetime
import pprint

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

def get_folder(service, folder_name):
    query = "mimeType = 'application/vnd.google-apps.folder' and title = '{}'".format(folder_name)
    folder = service.files().list(q=query).execute()
    return folder

def get_folder_contents(service, folder, modified_since=None):
    folder_id = folder['items'][0]['id']
    child_list_response = service.files().list(q="'{}' in parents".format(folder_id)).execute()
    children = child_list_response['items']
    for child in children:
        modified = datetime.datetime.strptime(child['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if (modified_since is None) or modified > modified_since:
            yield child


if __name__ == '__main__':
    creds = auth.get_stored_credentials('data@essencedigital.com')
    service = build_service(creds)
    folder = get_folder(service, 'data@')
    modified_since = datetime.datetime.strptime('2014-08-24', '%Y-%m-%d')
    for child in get_folder_contents(service, folder, modified_since):
        pprint.pprint(child)
        title = child['title']
        download_url = child['exportLinks']['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        with open(title + ".xlsx", 'w')  as fout:
            response, content = service._http.request(download_url)
            fout.write(content)
        #pprint.pprint(child['originalFilename'])


