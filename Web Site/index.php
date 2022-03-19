<?php

set_error_handler("customError");
// Settings
// host, user and password settings
$host = "localhost";
$user = "logger";
$password = "l0gg3r";
$database = "weatherstation";
// make connection to database
$connectdb = mysqli_connect($host,$user,$password)
	or die ("Can not reach database");
// select db
mysqli_select_db($connectdb,$database)
	or die ("Can not select database");


show_form($connectdb);

function show_form($connectdb) {
	
	$type1 = "Temperature";
	$type2 = "Humidity";
	$type3 = "Pressure";
		
	//how many hours backwards do you want results to be shown in web page.
	$hours = 48;	
	
	
	// sql commands to get current data whenever setInterval runs
	$sql="SELECT * FROM currentdata WHERE record=1";
	
	$sql_windspeed="SELECT round(windspeedmph,2) AS windspeed FROM windspeeddata order by record desc limit 1";
	
	//how many hours backwards do you want results to be shown in web page.
	$hours = 24;
	// sql command that selects all entires from current time and X hours backwards
	$sql2="SELECT year(dateandtime) AS year, month(dateandtime) AS month, day(dateandtime) AS day, hour(dateandtime) AS hour, minute(dateandtime) AS minute, temperature, humidity, pressure FROM historicdata WHERE dateandtime >= (NOW() - INTERVAL $hours HOUR) order by dateandtime desc";
	// set query to variable
	$data = mysqli_query($connectdb,$sql2);
	$currentdataraw = mysqli_query($connectdb,$sql);
	$currentdata=mysqli_fetch_assoc($currentdataraw);
	$windspeedraw = mysqli_query($connectdb,$sql_windspeed);
	$windspeed=mysqli_fetch_assoc($windspeedraw);
	
	$today = date("D M j, Y G:i:s T");


	?>
	<html>
	<head>
	<meta http-equiv="refresh" content="30">
	<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
	<script type="text/javascript">
		google.charts.load('current', {'packages':['corechart']});
		google.charts.setOnLoadCallback(drawChart);
		function drawChart() {
			var data = new google.visualization.DataTable();
			data.addColumn('datetime', 'Datetime');
			data.addColumn('number', '<?php echo $type1 ?>');
			data.addColumn('number', '<?php echo $type2 ?>');
			data.addColumn('number', '<?php echo $type3 ?>');
			
			data.addRows([
	<?php
	
	// loop all the results that were read from database and "draw" to web page
	
	while ($row=mysqli_fetch_assoc($data)) {
		echo " [ ";
		echo "new Date(".$row['year'].", ";
		echo ($row['month']-1).", "; // adjust month from mysql to javascript format
		echo $row['day'].", ";
		echo $row['hour'].", ";
		echo $row['minute']."), ";
		echo $row['temperature'].", ";
		echo $row['humidity'].", ";
		echo $row['pressure']." ";
		echo "],\n";
		//$lasttemp=number_format((float)$row['temp1'],1, '.','');
		//$lasthum=number_format((float)$row['hum1'],1, '.','');

	}
	?>
			]);
	
	var options = {
		title: '24 Hour View - <?php echo $today ?>',
		width: 580,
		height: 200,
		backgroundColor: '#f2f6f5',
		curveType: 'function',
		legend: { position: 'bottom' },
		crosshair: { trigger: 'both' },
		series: {
			0: { targetAxisIndex: 0 },
			1: { targetAxisIndex: 1 }
		},
		vAxes: {
			0: {
				title: 'Temp \u00B0F / Press (in)',
				viewWindowMode: 'explicit',
				viewWindow: {
					max: 100,
					min: 0
				}
			},
			1: {
				title: 'Humidity %',
				viewWindowMode: 'explicit',
				viewWindow: {
					max: 100,
					min: 0
				}
			}
		},
		hAxis: { title: 'Time of Day' }
	};
	
	var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));
	
	chart.draw(data, options);
	
	}
	</script>

	<title>FerretWorx Weatherstation</title>
	<link rel="stylesheet" type="text/css" href="styles.css"/>
	<link rel="stylesheet" href="gauge.min.css" />
	</head>
	<body>
	<div id="header">
		<h1>Raspberry Pi Weatherstation</h1>
	</div>
	<div id="container">
		<br>
		<br>
		<br>
		<br>
	</div>
	<div id="page">
		<div id="rightside">
			<div id="gaugebox" >
				<center>
				<h1>Temperature/Humidity/Pressure</h1>
				</center>
				<div id="tempgauge" class="gauge" style="
     					--gauge-value:<?php printf("%.2f",$currentdata['temperature']);?>;
     					--gauge-display-value:<?php printf("%.2f",$currentdata['temperature']);?>;">
  					<div class="ticks">
    						<div class="tithe" style="--gauge-tithe-tick:1;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:2;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:3;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:4;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:6;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:7;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:8;"></div>
    						<div class="tithe" style="--gauge-tithe-tick:9;"></div>
    						<div class="min"></div>
    						<div class="mid"></div>
    						<div class="max"></div>
  					</div>
  					<div class="tick-circle"></div>
  					<div class="needle">
    						<div class="needle-head"></div>
  					</div>
  					<div class="labels">
    						<div class="value-label"><?php printf("%.2f",$currentdata['temperature']);?></div>
						<h4>Temperature (&degF)</h4>
  					</div>
				</div>
				<div id="humgauge" class="gauge2" style="
     					--gauge2-value:<?php printf("%.2f",$currentdata['humidity']);?>;
     					--gauge2-display-value:<?php printf("%.2f",$currentdata['humidity']);?>;">
  					<div class="ticks2">
    						<div class="tithe" style="--gauge2-tithe-tick:1;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:2;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:3;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:4;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:6;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:7;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:8;"></div>
    						<div class="tithe" style="--gauge2-tithe-tick:9;"></div>
    						<div class="min"></div>
    						<div class="mid"></div>
    						<div class="max"></div>
  					</div>
  					<div class="tick-circle2"></div>
  					<div class="needle2">
    						<div class="needle-head"></div>
  					</div>
  					<div class="labels2">
    						<div class="value-label"><?php printf("%.2f",$currentdata['humidity']);?></div>
						<h4>Humidity (%)</h4>
  					</div>
				</div>
				<div id="pressgauge" class="gauge3" style="
     					--gauge3-value:<?php printf("%.2f",$currentdata['pressure']);?>;
     					--gauge3-display-value:<?php printf("%.2f",$currentdata['pressure']);?>;">
  					<div class="ticks3">
    						<div class="tithe" style="--gauge3-tithe-tick:1;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:2;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:3;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:4;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:6;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:7;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:8;"></div>
    						<div class="tithe" style="--gauge3-tithe-tick:9;"></div>
    						<div class="min"></div>
    						<div class="mid"></div>
    						<div class="max"></div>
  					</div>
  					<div class="tick-circle3"></div>
  					<div class="needle3">
    						<div class="needle-head"></div>
  					</div>
  					<div class="labels3">
    						<div class="value-label"><?php printf("%.2f",$currentdata['pressure']);?></div>
						<h4>Barometric Pressure (in)</h4>
  					</div>
				</div>
								
			</div>
			
			<div id="linechart">
				<h1>Last 24 Hours</h2>
				<div id="curve_chart">Unable to reach Google. :(</div>
			</div>
		</div>
		<div id="leftside">
			<div id="windbox">
				<center>
				<h1>Wind</h1>
				</center>
				<div id="windstatus">
					<table>
						<tr><th>Wind Speed</th><td id="windspeed"><?php echo $windspeed['windspeed'];?> mph</td></tr>
						<tr><th>Wind Gust</th><td><?php printf("%.2f",$currentdata['windgust']);?> mph</td></tr>
						<tr><th>Wind Avg</th><td><?php printf("%.2f",$currentdata['windavg']);?> mph</td></tr>
					</table>

				</div>	
				<div class="compass">
					<div class="direction">
    					<p id="winddirection"><?php print $currentdata['winddirection']; ?></p>
  					</div>
  					<div class="arrow <?php print strtolower($currentdata['winddirection']); ?>"></div>
				</div>	
			
			</div>
			<div id="rainbox">
				<center>
				<h1>Conditions and Precipitation</h1>
				
				<div id="rainstatus">
					<table>
						<tr><th>Current Precipitation</th><td><?php echo $currentdata['rainfall_5minute'];?> in</td></tr>
						<tr><th>Precipitation Last Hour</th><td><?php echo $currentdata['rainfall_hour'];?> in</td></tr>
						<tr><th>Precipitation 24 Hours</th><td><?php echo $currentdata['rainfall_day'];?> in</td></tr>
					</table>

				</div>	
				<div id="conditions">
					<img src="./images/ws-sunny.png" height=100>
					<p>Sunny and Clear.</p>
				</div>
				</center>
			</div>
		</div>
		<div id="footer">
			<div id="footerright" >
				<h4>Links</h4>

				<div class="tooltip1"><a href="mailto:gary@ferretworx.com" ><img  src="./images/email.png"><span class="tooltiptext1">Email FerretWorx</span></a></div>
				<div class="tooltip2"><a href="https://www.youtube.com/user/MisterB071965" ><img src="./images/youtube.png"><span class="tooltiptext2">Youtube</span></a></div>
				<div class="tooltip3"><a href="https://www.thingiverse.com/ferretworx/designs" ><img src="./images/thingiverse.png"><span class="tooltiptext3">Thingiverse</span></a></div>
				<div class="tooltip4"><a href="https://github.com/gcoltharp"><img src="./images/github.png"><span class="tooltiptext4">Github</span></a></div>
				<div class="tooltip5"><a href="https://www.paypal.com/donate?hosted_button_id=YBW7HJYB5AF5Y"><img src="./images/paypal.png"><span class="tooltiptext5">Donate to FerretWorx via Paypal</span></a></div>
			</div>
			<div id="footerleft">
				<h4>Credits</h4>
				<ul>
					<li><a href='https://www.w3schools.com'>Lots of help from w3schools.com</a></li>
					<li><a href='https://www.freepik.com/vectors/snow'>Weather vectors created by bamdewanto<br>www.freepik.com</a></li>
				</ul>
			</div>
			<img src="./images/ferretworx-header-newslogan-noshadow-t-cropped.png" height="70px">
			<a href="http://ferretworx.com"><h4>ferretworx.com</h4></a>
			


		</div>
	</div>
	
	
	</body>
	</html>
<?php	

}

function customError($errno , $errstr )	{
	if($errno != '8') {
		print '<table id="error"><tr><td><b>Error:</b></td><td>' . $errstr  . '</td></tr></table>';
	}
}

?>