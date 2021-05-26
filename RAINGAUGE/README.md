# Digital-Rain-Gauge
A digital tipping bucket rain gauge that outputs a JSON formatted message containing the current rainfall rate.

This code has been developed to run on a Raspberry Pi with a tipping bucket rain sensor connected to the GPIO pins of the Pi.
The current rainfall rate is calculated based on the occurence of bucket tips and the time between those tips, also taking
account of the elapsed time since the last tip. 

The results are output on a serial port in the form of a JSON formatted message e.g:

`{"raintip": 0.3, "rainrate": 12, "units": "mm/hr"}`

`"raintip": 0.3` indicates that a 'tip' event has just occurred (the amount is that required to tip the bucket). This will be
reset to zero before the next message is transmitted.

`"rainrate": 12` represents the current rainfall rate in mm/hr (as these units have been selected). 

Units can be inches/hr or mm/hr, message transmission and bucket tip amount can be set via Docker environment variables.

The project has been setup to use the Balena Cloud IoT device management and development framework whereby the application
runs and is managed inside a Docker container running on BalenaOS. For more info see https://www.balena.io

