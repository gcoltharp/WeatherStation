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
import Adafruit_DHT
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import RPi.GPIO as GPIO
import time
import requests
# function to send data to Wunderground
def updateWunderground(outsidetemp,outsidehumidity):
     configurations = getConfigurations()
     
     humidity_str = "{0:.2f}".format(outsidehumidity)
     tempf_str = "{0:.2f}".format(outsidetemp)
     #windspeed_str = "{0:.2f}".format(wind_speed)
     #windgust_str = "{0:.2f}".format(wind_gust)
     #windaverage_str = "{0:.2f}".format(wind_average)
     WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
     WU_station_id = configurations["wunderground"][0]["stationid"]
     WU_station_pwd = configurations["wunderground"][0]["stationpass"]
     WUcreds = "ID=" + WU_station_id + "&PASSWORD="+ WU_station_pwd
     date_str = "&dateutc=now"
     action_str = "&action=updateraw"
     urltosend  = WUurl + WUcreds + date_str + "&humidity=" + humidity_str + "&tempf=" + tempf_str + action_str
     #print urltosend
     r=requests.get(urltosend)
     print("Wunderground Result: " + str(r.status_code) + " " + str(r.text) )

# function for getting weekly average temperatures.
def getAverageWindSpeed():
    date =  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delta = (datetime.date.today() - timedelta(hours=1)).strftime("%Y-%m-%d 00:00:00")
    #print "date %s delta %s" % (date,delta)
    AverageWind=0
    try:
        sqlCommand = "SELECT AVG(windspeedmph) FROM windspeeddata WHERE dateandtime BETWEEN '%s' AND '%s'" % (delta,date)
        AverageWind = databaseHelper(sqlCommand,"Select")
        
    except:
        pass

    #print "AVG %f.2" % (AverageWind)
    
    return AverageWind[0]

# function for getting wind gust.
def getWindGust():
    date =  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delta = (datetime.date.today() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    #print "date %s delta %s" % (date,delta)
    WindGust=0
    try:
        sqlCommand = "SELECT MAX(windspeedmph) FROM windspeeddata WHERE dateandtime BETWEEN '%s' AND '%s'" % (delta,date)
        WindGust = databaseHelper(sqlCommand,"Select")
        
    except:
        pass
    #print "GUST %f.2" % (WindGust)
    return WindGust[0]


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
                print (sqlCommand)
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
        backupbathoftheday = backuppath


        # Checking if backup folder already exists or not. If not exists will create it.
        if not os.path.exists(backupbathoftheday):
            os.makedirs(backupbathoftheday)

        # Dump database
        db = database
        dumpcmd = "mysqldump -u " + user + " -p" + password + " " + db + " > " + backupbathoftheday + "/" + db + ".sql"
        os.system(dumpcmd)

    return data
    
# function to clean up database
def dbCleanup(daystokeep):
    date = datetime.date.today().strftime("%Y-%m-%d")
    sqlCommand = "DELETE FROM historicdata WHERE dateandtime < DATE_SUB(NOW(), INTERVAL %s DAY)" % (daystokeep)
    databaseHelper(sqlCommand,"Cleanup")
    sqlCommand = "DELETE FROM rainfalldata WHERE dateandtime < DATE_SUB(NOW(), INTERVAL %s DAY)" % (daystokeep)
    databaseHelper(sqlCommand,"Cleanup")
    sqlCommand = "DELETE FROM windspeeddata WHERE dateandtime < DATE_SUB(NOW(), INTERVAL %s DAY)" % (daystokeep)
    databaseHelper(sqlCommand,"Cleanup")


def getConfigurations():

    path = os.path.dirname(os.path.realpath(sys.argv[0]))

    #get configs
    configurationFile = path + '/config.json'
    configurations = json.loads(open(configurationFile).read())

    return configurations

def main():

    currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    configurations = getConfigurations()

    # Backup enabled
    backupEnabled = configurations["sqlBackupDump"][0]["backupDumpEnabled"]
    backupHour = configurations["sqlBackupDump"][0]["backupHour"]
    
    # days of data to keep in database
    daystokeep = configurations["daystokeep"]

    # Default value for message type, not configurable
    msgType = "Warning"

    d = datetime.date.weekday(datetime.datetime.now())
    h = datetime.datetime.now()

    # check if it is 5 o clock. If yes, take sql dump as backup
    if backupEnabled == "Y" or backupEnabled == "y":
        if h.hour == int(backupHour):
            databaseHelper("","Backup")

    

    sqlCommand = "SELECT * FROM currentdata WHERE record=1"
    data = databaseHelper(sqlCommand,"Select")
    sqlCommand = "select * FROM windspeeddata order by record desc limit 1;"
    data2 = databaseHelper(sqlCommand,"Select")

    temperature = float(data[1])
    humidity = float(data[2])
    pressure = float(data[3])
    windspeed = float(data2[2])
    winddirection = data[5]

    windspeedavg = getAverageWindSpeed()
    windgustspeed = getWindGust()
    #windspeedavg = 0.00
    #windgustspeed = 0.00
    #print "%s" % (type(windspeedavg))
    #print "%s" % (type(windgustspeed))
    #print "AVG %.2f Gust %.2f" % (float(windspeedavg),float(windgustspeed))

    #Update Wunderground (comment out while testing)
    #updateWunderground(temperature,humidity,pressure,windspeed,winddirection) 

    #Update AVG and Gust in current data
    sqlCommand = "UPDATE currentdata SET windavg='%f',windgust='%f',windspeed='%f' WHERE record=1" % (windspeedavg,windgustspeed,windspeed)
    databaseHelper(sqlCommand,"Insert")

    #Update Historic Data
    sqlCommand = "INSERT INTO historicdata SET dateandtime='%s', temperature='%f', humidity='%f', pressure='%f', windspeed='%f', winddirection='%s',windavg='%f',windgust='%f'" % (currentTime,temperature,humidity,pressure,windspeed,winddirection,windspeedavg,windgustspeed)
    databaseHelper(sqlCommand,"Insert")
        
    
    # cleanup database
    dbCleanup(daystokeep)       
if __name__ == "__main__":
    main()

