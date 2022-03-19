#!/usr/bin/python2

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

# function for turning on power to DHT22 sensors
def powerOnSensors(gpiopin):
        print("Sensor POWERON received on GPIO ", gpiopin )
        GPIO.output(gpiopin,1)

# function for turning off power to DHT22 sensors
def powerOffSensors(gpiopin):
        print("Sensor POWEROFF received on GPIO ", gpiopin )
        GPIO.output(gpiopin,0)

# function for reading DHT22 sensors ( rewritten to access the library directly by GSC }
def sensorReadings(pin):
    
    configurations = getConfigurations()
    if configurations["sensortype"] == "2302":
         sensor = Adafruit_DHT.AM2302
    elif configurations["sensortype"] == "22":
         sensor = Adafruit_DHT.DHT22
    else:
         sensor = Adafruit_DHT.DHT11   
    temperature=0  
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    # Convert to Fahrenheit and float
    intTemp = float(temperature*9/5+32)
    intHumidity = float(humidity)
    if intHumidity < 0 or intHumidity > 100:
        emailWarning("Out of range Humidity on {0} sensor".format(pin))
        intHumidity = 50
    return intTemp, intHumidity

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
           
    # Sensor names to add to database, e.g. carage, outside
    sensor1 = configurations["sensors"][0]["sensor1"]
    
    # Sensor gpios
    gpioForSensor1 = configurations["sensorgpios"][0]["gpiosensor1"]

    # Relay gpios
    gpioForRelay1 = int(configurations["relaygpios"][0]["gpiorelay1"])
    
    # Default value for message type, not configurable
    msgType = "Warning"

    d = datetime.date.weekday(datetime.datetime.now())
    h = datetime.datetime.now()

    # Setup GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpioForRelay1,GPIO.OUT)


    # Power on sensors
    #powerOnSensors(gpioForRelay1)

    # Delay to wait for sensors
    #time.sleep(3)

          

    # default message type to send as email. DO NOT CHANGE
    msgType = "Warning" 

    sensor1error = 0
    okToUpdate = False
    # Sensor 1 readings and limit check
    sensor1temperature, sensor1humidity = sensorReadings(gpioForSensor1)
        
    #print "Inside: %d Outside: %d" % (insidevalue,outsidevalue)
    # insert values to db
    sqlCommand = "UPDATE currentdata SET temperature='%s', humidity='%s' WHERE record=1" % (sensor1temperature,sensor1humidity)
    databaseHelper(sqlCommand,"Insert")
    
    
if __name__ == "__main__":
    main()
