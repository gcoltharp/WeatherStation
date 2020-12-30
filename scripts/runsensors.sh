#/bin/bash
flipflop=0
for i in {1..28}
do
	if [ $i -eq 14 ]
	then
		echo "check temp and humidity"
		/usr/bin/python /home/pi/weathersensors/tempandhumidity.py &
	fi
	/usr/bin/python /home/pi/weathersensors/pressure.py 
	/usr/bin/python /home/pi/weathersensors/winddirection.py 
	sleep 2
done
