# import pygame module in this program
import pygame
import time
import sys
import math
import os
import re
import datetime
from datetime import timedelta
import json
import subprocess
import MySQLdb
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


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

    pygame.init()

    # define the RGB value for white,
    # green, blue colour .
    white = (255, 255, 255)
    green = (0, 255, 0)
    blue = (0, 0, 128)
    black = (0,0,0)
    red = (255,0,0)
    yellow = (255,255,0)
    fw_cyan = (0,206,209)
    filled=0

    # assigning values to X and Y variable
    X = 640
    Y = 480

    # create the display surface object
    # of specific dimension..e(X, Y).
    display_surface = pygame.display.set_mode((640,480))

    # set the pygame window name
    pygame.display.set_caption('Show Text')

    # create a font object.
    # 1st parameter is the font file
    # which is present in pygame.
    # 2nd parameter is size of the font
    font = pygame.font.Font('freesansbold.ttf', 14)
    cornerfont = pygame.font.Font('freesansbold.ttf', 10)
    datafont = pygame.font.Font('freesansbold.ttf', 60)
    smalldatafont = pygame.font.Font('freesansbold.ttf', 30)

    #Opening Sound
    openSound=pygame.mixer.Sound('./tada.wav')
    openSound.play()
    time.sleep(1)
    openSound.stop()
    clock = pygame.time.Clock()
    #logoimg=pygame.image.load('./yt-ferretworx-profile-new.png').convert()
    
    # box rects
    databoxwidth=245
    databoxheight=65
    #box1a
    box1arect = pygame.Rect(259,209,63,28)
    #box2
    box2rect = pygame.Rect(344,17,databoxwidth,databoxheight)
    #box2a
    box2arect = pygame.Rect(344,97,databoxwidth,databoxheight)
    #box2b
    box2brect = pygame.Rect(344,177,databoxwidth,databoxheight)
    #box3
    box3rect = pygame.Rect(17,265,databoxwidth,databoxheight)
    #box3a
    box3arect = pygame.Rect(17,345,databoxwidth,databoxheight)
    #box4
    box4rect = pygame.Rect(344,259,databoxwidth,databoxheight)
    #box4arect = pygame.Rect(8,8,databoxwidth,databoxheight)



    # empty screen labels
    box1label = cornerfont.render("Wind Direction",True,yellow)
    box2label = cornerfont.render("Wind Speed",True,yellow)
    box2alabel = cornerfont.render("Average Speed",True,yellow)
    box2blabel = cornerfont.render("Gust Speed",True,yellow)
    box3label = cornerfont.render("Temperature",True,yellow)
    box3alabel = cornerfont.render("Humidity",True,yellow)
    box4label = cornerfont.render("Pressure",True,yellow)
    box4alabel = cornerfont.render("Rainfall",True,yellow)
    
    #initialize screen
    # clear the screen
    display_surface.fill(black)
    # draw empty screen
    #outerbox
    pygame.draw.rect(display_surface, white, (0,0,639,479), 2)
    #box1-upper left
    pygame.draw.rect(display_surface, white, (5,5,318,238), 2)
    #box2-upper right
    pygame.draw.rect(display_surface, white, (327,5,308,238), 2)
    #box3-lower left
    pygame.draw.rect(display_surface, white, (5,246,318,228), 2)
    #box4-lower right
    pygame.draw.rect(display_surface, white, (327,246,308,228), 2)
    #wind direction 
    pygame.draw.circle(display_surface, white, (165,125),100,2)
    #fake wind direction vane
    #pygame.draw.line(display_surface, blue, (165,215), (165,40),4)
    #fake wind direction arrowhead
    northarrow=((150, 215),(165,200),(180, 215),(165, 35))
    pygame.draw.polygon(display_surface, blue,northarrow)
    #display_surface.blit(text, (300,460))
    display_surface.blit(box1label,(8,8))
    display_surface.blit(box2label,(330,8))
    display_surface.blit(box2alabel,(330,88))
    display_surface.blit(box2blabel,(330,168))
    display_surface.blit(box3label,(8,250))
    display_surface.blit(box3alabel,(8,330))
    display_surface.blit(box4label,(330,250))
    display_surface.blit(box4alabel,(330,330))
    #display_surface.blit(logoimg, (235,335))
    pygame.display.update()

    # infinite loop
    while True:
        clock.tick(3) # run at 1 fps
	#Wind Direction Character
	pygame.draw.rect(display_surface, black, (259,209,63,28), filled)
	#Wind Speed - box 2
	pygame.draw.rect(display_surface, black, (344,17,databoxwidth,databoxheight), filled)
	#Wind Average Speed- box 2a
	pygame.draw.rect(display_surface, black, (344,97,databoxwidth,databoxheight), filled)
	#Wind Gust Speed - box 2b
	pygame.draw.rect(display_surface, black, (344,177,databoxwidth,databoxheight), filled)
	#Temperture - box 3
	pygame.draw.rect(display_surface, black, (17,265,databoxwidth,databoxheight), filled)
	#Humidity - box 3a
	pygame.draw.rect(display_surface, black, (17,345,databoxwidth,databoxheight), filled)
	#Pressure - box 4
	pygame.draw.rect(display_surface, black, (344,259,databoxwidth,databoxheight), filled)
	#Wind Direction Graphical
	pygame.draw.circle(display_surface, white, (167,127),98,filled)


	# populate sensor data
	sqlCommand = "SELECT * FROM currentdata WHERE record=1"
    	sqldata = databaseHelper(sqlCommand,"Select")
	sqlCommand = "SELECT * FROM windspeeddata order by record desc limit 1"
    	sqldata2 = databaseHelper(sqlCommand,"Select")

    	windspeed_mph = float(sqldata2[2])
	windaverage = float(sqldata[7])
	windgust = float(sqldata[8])
	pressininches=float(sqldata[3])
	temperaturef = float(sqldata[1])
	humidity = float(sqldata[2])
	windspeed_data= "%.1f mph " % windspeed_mph
	windspeedavg_data= "%.1f mph " % windaverage
	windspeedgust_data= "%.1f mph " % windgust
	winddirection = sqldata[5]  
	temperature_data= "%.1f F " % temperaturef
	humidity_data = "%.1f pct " % humidity
	pressure_data= "%.2f in " % pressininches
	box1adata = smalldatafont.render(winddirection,True,green)
	box2data = datafont.render(windspeed_data,True,green)
	box2adata = datafont.render(windspeedavg_data,True,green)
	box2bdata = datafont.render(windspeedgust_data,True,green)
	box3data = datafont.render(temperature_data,True,green)
	box3adata = datafont.render(humidity_data,True,green)
	box4data = datafont.render(pressure_data,True,green)
	display_surface.blit(box1adata,(260,210))
	display_surface.blit(box2data,(345,15))
	display_surface.blit(box2adata,(345,99))
	display_surface.blit(box2bdata,(345,179))
	display_surface.blit(box3data,(15,260))
	display_surface.blit(box3adata,(15,340))
	display_surface.blit(box4data,(345,260))

	# iterate over the list of Event objects
	# that was returned by pygame.event.get() method.
	for event in pygame.event.get():
		
		# if event object type is QUIT
		# then quitting the pygame
		# and program both.
		if event.type == pygame.QUIT:

			# deactivates the pygame library
			pygame.quit()
			quit()
		# if event object is the Q key pressed, quit
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_q:
				pygame.quit()
				quit()
		# Draws the surface object to the screen.
	pygame.display.update(box1arect)
	pygame.display.update(box2rect)
	pygame.display.update(box2arect)
	pygame.display.update(box2brect)
	pygame.display.update(box3rect)
	pygame.display.update(box3arect)
	pygame.display.update(box4rect)
	#pygame.display.update()
	
if __name__ == "__main__":
    main()  

		

