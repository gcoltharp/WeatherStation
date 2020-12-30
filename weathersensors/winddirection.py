#!/usr/bin/python2
#coding=utf-8
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
# Import the ADS1x15 module.
import Adafruit_ADS1x15

def sensorReadings():
    # Create an ADS1115 ADC (16-bit) instance.
    adc = Adafruit_ADS1x15.ADS1115()

    GAIN = 2/3 
    value = 0
    value = adc.read_adc(0, gain=GAIN)
    voltage=value * 0.000187
    #print "Voltage: %.2f" % voltage
    if voltage > 0.29 and voltage < 0.88:
        direction = "SW"
    elif voltage > 0.89 and voltage < 1.46:
        direction = "W"
    elif voltage > 1.47 and voltage < 2.05:
        direction = "NW"
    elif voltage > 2.06 and voltage < 2.64:
        direction = "N"
    elif voltage > 2.65 and voltage < 3.23:
        direction = "NE"
    elif voltage > 3.24 and voltage < 3.81:
        direction = "E"
    elif voltage > 3.82 and voltage < 4.40:
        direction = "SE" 
    else:
        direction = "S	"
    return direction

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

    
   
    # Sensor 3 readings
    sensor3direction = sensorReadings()
        
    # insert values to db
    sqlCommand = "UPDATE currentdata SET winddirection='%s' WHERE record=1" % (sensor3direction)
    databaseHelper(sqlCommand,"Insert")
    
    
if __name__ == "__main__":
    main()

    
