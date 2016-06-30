# -*- coding: utf-8 -*-
"""
Created on Tue Jun 07 15:13:12 2016

@author: calorim
"""

from __future__ import print_function
import httplib2
import os

#import numpy as np

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import smtplib
from email.mime.text import MIMEText

sender = 'BigLabLeakDetectors@gmail.com'
receivers = ['daniel.timbie@gmail.com', '6089572745@messaging.sprintpcs.com','6085560289@txt.att.net']

#with open('Leak.docx') as fp:
#    msg = MIMEText(fp.read())

#msg = {}
#msg['Subject'] = 'The contents of\n' #%s' % 'Leak.docx'
#msg['From'] = sender
#msg['To'] = receivers

msg = 'Epic flood upon you'


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
      print('Labels:')
      for label in labels:
        print(label['name'])

def sendGmail(receivers, msg):
    '''Uses secure SMTP to send email to receiver list'''
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    username = 'BigLabLeakDetectors@gmail.com'
    password = 'leakyfaucet'
    server.login(username, password)
    server.sendmail(sender, receivers, msg)
    server.close()

    

if __name__ == '__main__':
    pass
#    main()
#try:
    #print 'successfully sent the mail'
    #except Exception, e:
    #        print "failed to send mail:", e
