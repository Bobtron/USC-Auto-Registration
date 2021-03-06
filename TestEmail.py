import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from base64 import urlsafe_b64decode, urlsafe_b64encode

import time
import re

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = []
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages


# utility functions
def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


def parse_parts(service, parts, message):
    """
    Utility function that parses the content of an email partition
    """
    return_this = ""

    if parts:
        for part in parts:
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            # file_size = body.get("size")
            # part_headers = part.get("headers")
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                return_this += parse_parts(service, part.get("parts"), message)
            if mimeType == "text/plain":
                # if the email part is text plain
                if data:
                    # print(data)
                    text = urlsafe_b64decode(data).decode()
                    return_this += text
    return return_this
            # elif mimeType == "text/html":
            #     # if the email part is an HTML content
            #     # save the HTML file and optionally open it in the browser
            #     if not filename:
            #         filename = "index.html"
            #     # filepath = os.path.join(folder_name, filename)
            #     # print("Saving HTML to", filepath)
            #     # with open(filepath, "wb") as f:
            #     #     f.write(urlsafe_b64decode(data))
            #     text = urlsafe_b64decode(data)
            #     print(data)
            # else:
            #     # attachment other than a plain text or HTML
            #     for part_header in part_headers:
            #         part_header_name = part_header.get("name")
            #         part_header_value = part_header.get("value")
            #         if part_header_name == "Content-Disposition":
            #             if "attachment" in part_header_value:
            #                 # we get the attachment ID
            #                 # and make another request to get the attachment itself
            #                 print("Saving the file:", filename, "size:", get_size_format(file_size))
            #                 attachment_id = body.get("attachmentId")
            #                 attachment = service.users().messages() \
            #                             .attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
            #                 data = attachment.get("data")
            #                 filepath = os.path.join(folder_name, filename)
            #                 if data:
            #                     with open(filepath, "wb") as f:
            #                         f.write(urlsafe_b64decode(data))


def read_message(service, message):
    """
    This function takes Gmail API `service` and the given `message_id` and does the following:
        - Downloads the content of the email
        - Prints email basic information (To, From, Subject & Date) and plain/text parts
        - Creates a folder for each email based on the subject
        - Downloads text/html content (if available) and saves it under the folder created as index.html
        - Downloads any file that is attached to the email and saves it in the folder created
    """
    msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
    # parts can be the message body, or attachments
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    if headers:
        # this section prints email basic info & creates a folder for the email
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            # print(name)
            if name.lower() == 'from':
                # we print the From address
                print("From:", value)
            if name.lower() == "to":
                # we print the To address
                print("To:", value)
            if name.lower() == "subject":
                print("Subject:", value)
            if name.lower() == "date":
                # we print the date when the message was sent
                print("Date:", value)
    # if not has_subject:
    #     # if the email does not have a subject, then make a folder with "email" name
    #     # since folders are created based on subjects
    #     if not os.path.isdir(folder_name):
    #         os.mkdir(folder_name)
    return parse_parts(service, parts, message)


def parse_passcodes(message):
    regex = r"SMS passcodes: (\d{7})"
    if re.search(regex, message):
        match = re.search(regex, message)
        return match.group(1)
    return None


def retrieve_passcode(timestamp):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        # results = service.users().labels().list(userId='me').execute()
        # labels = results.get('labels', [])
        #
        # if not labels:
        #     print('No labels found.')
        #     return
        # print('Labels:')
        # for label in labels:
        #     print(label['name'])

        max_tries = 10
        tries = 0
        while tries < max_tries:
            tries += 1
            print(f'Current Try: {tries}')
            messages = search_messages(service, 'subject:"New text message from" after:' + str(int(timestamp)))
            if len(messages) > 0:
                return parse_passcodes(read_message(service, messages[0]))
            time.sleep(2)
        return None

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


