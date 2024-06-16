# twc3teslamate (Tesla Wall Connector 3 Teslamate output)

This program simulates the API output of a Tesla Wall Connector 3, using data obtained from Teslamate. Checks the car's geofence location
 and only sets connected/charging output to True if the vehicle is in the geofence location (default "Home")

I use this as a workaround to get evcc working with the mobile charger, as evcc requires a proper charger. The twc3 template is special because it lets evcc use Tesla's own api to start/stop and adjust the current level. 

Adapted from [laenglea/twc3simulator](https://github.com/laenglea/twc3simulator), MQTT subscription code from [letienne/teslamate-abrp](https://github.com/letienne/teslamate-abrp)


## requirements

- Teslamate setup with MQTT integration (default MQTT publishing path)
- a MQTT broker
- Docker 


## Installation

via docker:

    docker run --name twc3teslamate -p 80:80 -e MQTT_HOST=mosquitto haveacry/twc3teslamate

where `MQTT_HOST` is the hostname or IP of your MQTT broker where teslamate logs data.

or as part of your evcc so you could access it via port 80 without exposing this port at all just with the name of the container 

```
    services:
    twc3teslamate:
      container_name: twc3teslamate
      image: haveacry/twc3teslamate
      environment:
        - MQTT_HOST=mosquitto
      restart: unless-stopped
```      

## Environment variables

| Variable | Description | Default |
| :---- | --- | --- |
| MQTT_HOST | hostname or IP of MQTT broker | None |
| MQTT_PORT | MQTT broker port | 1883 |
| MQTT_USERNAME | Username for MQTT broker (optional) | None |
| MQTT_PASSWORD | Password for MQTT broker (optional) | None |
| TESLAMATE_CAR_ID | Teslamate car ID (where multiple cars in account) | 1 |
| TESLAMATE_GEO_HOME | Teslamate Geofence name where car is charged | "Home" |

for tweaking:

first clone it to the machine you want to run it

    git clone https://github.com/haveacry/twc3teslamate.git


## run it

to run it native you have to first install the requirements with pip or your package manager

native:

    pip3 install -r requirements.txt
    sudo uvicorn app.main:app --reload --host 0.0.0.0 --port 80

   
## validate

if it's running properly you should get something back when looking at

http://IP_ADDRESS/api/1/vitals
