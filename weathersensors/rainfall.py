#!/usr/bin/python
#   networking daemon running on Raspberry PI for wind-measuring
#   Copyright (C) 2014-2015 Patrick Rudolph

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys
import datetime
from datetime import timedelta
import json
import subprocess
import MySQLdb
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import RPi.GPIO as GPIO
import math
import time


impulses = 0
events = []



def interrupt(val):
    global impulses
    impulses += 1

# function that sends emails, either warning or weekly averages in order to see that pi is alive
def emailWarning(msg, msgType):
    
    configurations = getConfigurations()
    
    fromaddr = configurations["mailinfo"][0]["senderaddress"]
    toaddrs = configurations["mailinfo"][0]["receiveraddress"]
    username = configurations["mailinfo"][0]["username"]
    password = configurations["mailinfo"][0]["password"]
    subj = configurations["mailinfo"][0]["subjectwarning"]
        
    if msgType == 'Info':
        subj = configurations["mailinfo"][0]["subjectmessage"]
    
    # Message to be sended with subject field
    message = 'Subject: %s\n\n%s' % (subj,msg)

    # The actual mail sending
    server = smtplib.SMTP('mail.thecoltharps.org',25)
    #server.starttls()
    #server.login(username,password)
    server.sendmail(fromaddr, toaddrs, message)
    server.quit()

    return

# helper function for database actions. Handles select, insert and sqldumpings. Update te be added later. Added preening function - GSC
def databaseHelper(sqlCommand,sqloperation):

    configurations = getConfigurations()

    host = configurations["mysql"][0]["host"]
    user = configurations["mysql"][0]["user"]
    password = configurations["mysql"][0]["password"]
    database = configurations["mysql"][0]["database"]
    backuppath = configurations["sqlbackuppath"]
    
    data = ""
    
    db = MySQLdb.connect(host,user,password,database)
    cursor=db.cursor()

    if sqloperation == "Select":
        try:
            cursor.execute(sqlCommand)
            data = cursor.fetchone()
        except:
            db.rollback()
    elif sqloperation == "Insert":
            try:
                cursor.execute(sqlCommand)
                db.commit()
                #print sqlCommand
            except:
                db.rollback()
                warnmsg = 'Logger\nDatabase insert failed.\nCommand:%s\n' % (sqlCommand)
                emailWarning(warnmsg, "")
    elif sqloperation == "Cleanup":
        # SQL to purge all records older than configuration limit
                try:
                    cursor.execute(sqlCommand)
                    db.commit()
                except:
                    db.rollback()
                    emailWarning("Database cleanup failed", "")
    
    elif sqloperation == "Backup":  
        # Getting current datetime to create seprate backup folder like "12012013-071334".
        date = datetime.date.today().strftime("%Y-%m-%d")
        backupbathoftheday = backuppath + date

        # Checking if backup folder already exists or not. If not exists will create it.
        if not os.path.exists(backupbathoftheday):
            os.makedirs(backupbathoftheday)

        # Dump database
        db = database
        dumpcmd = "mysqldump -u " + user + " -p" + password + " " + db + " > " + backupbathoftheday + "/" + db + ".sql"
        os.system(dumpcmd)

    return data

def getConfigurations():

    path = os.path.dirname(os.path.realpath(sys.argv[0]))

    #get configs
    configurationFile = path + '/config.json'
    configurations = json.loads(open(configurationFile).read())

    return configurations

def main():
    currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    configurations = getConfigurations()
    # Amount of rainfall represented by each trigger (102mm x 42 mm)
    rainfall_constant=.01
    # RPi.GPIO Layout 
    GPIO.setmode(GPIO.BCM)

    sensorpin=int(configurations["sensorgpios"][0]["gpiosensor5"])
    GPIO.setup(sensorpin, GPIO.IN)
    GPIO.add_event_detect(sensorpin, GPIO.RISING, callback = interrupt, bouncetime = 5)  
    global impulses
    
    ctr = 60
    while ctr > 0:
        
        rainfallpermin = float(impulses * rainfall_constant)
        # insert values to db
        sqlCommand = "INSERT INTO rainfalldata SET dateandtime='%s',rainfall='%s'" % (currentTime,rainfallpermin)
        databaseHelper(sqlCommand,"Insert")
        impulses = 0
        for x in events:
            x.set()
        ctr = ctr - 1
        time.sleep(60)
    
if __name__ == "__main__":
    main()    
