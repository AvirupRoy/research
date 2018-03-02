# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 15:23:22 2018

@author: wisp10
"""

import smtplib
from email.mime.text import MIMEText

def sendMessage(receipients, subject, text):
    '''Uses secure SMTP to send email to receiver list'''
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    userName = 'BigLabLeakDetectors@gmail.com'
    password = 'leakyfaucet'
    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = userName
    msg['To'] = ','.join(receipients)
    server.login(userName, password)
    server.sendmail(userName, receipients, msg.as_string())
    server.close()

if __name__ == '__main__':
    text = 'Test message from WISP10.'
    subject = 'Problem'
    receipients = ['felix.jaeckel@wisc.edu', '6089572745@messaging.sprintpcs.com']
    sendMessage(receipients, subject, text)
