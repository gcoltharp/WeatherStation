#!/usr/bin/env python

import os
import re
import sys
import datetime
from datetime import timedelta
import json
import subprocess
import MySQLdb
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import time
from bmp280 import BMP280

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus


# Initialise the BMP280
def sensorReadings():
    bus = SMBus(1)
    bmp280 = BMP280(i2c_dev=bus)
    #temperature = bmp280.get_temperature()
    pressure = bmp280.get_pressure()
    pressininches = pressure * 0.02953
    return pressininches

# function that sends emails, either warning or weekly averages in order to see that pi is alive
def emailWarning(msg, msgType):
    
    configurations = getConfigurations()
    
    fromaddr = configurations["mailinfo"][0]["senderaddress"]
    toaddrs = configurations["mailinfo"][0]["receiveraddress"]
    username = configurations["mailinfo"][0]["username"]
    password = configurations["mailinfo"][0]["password"]
    subj = configurations["mailinfo"][0]["subjectwarning"]
        
    if msgType is 'Info':
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
                print sqlCommand
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
    
    d = datetime.date.weekday(datetime.datetime.now())
    h = datetime.datetime.now()

    # default message type to send as email. DO NOT CHANGE
    msgType = "Warning" 

    
   
    # Sensor 2 readings and limit check
    sensor2pressure = sensorReadings()
        
    # insert values to db
    sqlCommand = "UPDATE currentdata SET pressure='%s' WHERE record=1" % (sensor2pressure)
    databaseHelper(sqlCommand,"Insert")
    
    
if __name__ == "__main__":
    main()
