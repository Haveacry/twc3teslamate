# twc3teslamate (Tesla Wall Connector 3 Teslamate output)

This program simulates the API output of a Tesla Wall Connector 3, using data obtained from Teslamate. Checks the car's geofence location
 and only sets connected/charging output to True if the vehicle is in the geofence location (default "Home")

I use this as a workaround to get evcc working with the mobile charger, as evcc requires a proper charger. The twc3 template is special because it lets evcc use Tesla's own api to start/stop and adjust the current level. 

Adapted from [laenglea/twc3simulator](https://github.com/laenglea/twc3simulator), MQTT subscription code from [letienne/teslamate-abrp](https://github.com/letienne/teslamate-abrp)


## requirements

- Teslamate setup with MQTT integration (default MQTT publishing path)
- a MQTT broker
- Docker (amd64 and arm64 only)


## Installation

via docker (amd64 and arm64):

    docker run --name twc3teslamate -p 80:80 -e MQTT_HOST=mosquitto ghcr.io/haveacry/twc3teslamate

where `MQTT_HOST` is the hostname or IP of your MQTT broker where teslamate logs data.

> **Note: 32-bit Raspberry Pi OS is not supported, you MUST use the 64-bit version to run this container**

or as part of your teslamate/evcc compose so you could access it via port 80 without exposing this port at all just with the name of the container 

```
    version: "3"
    services:
      teslamate:
        image: teslamate/teslamate:latest
        restart: always
        environment:
          - ENCRYPTION_KEY=secretkey #replace with a secure key to encrypt your Tesla API tokens
          - DATABASE_USER=teslamate
          - DATABASE_PASS=password #insert your secure database password!
          - DATABASE_NAME=teslamate
          - DATABASE_HOST=database
          - MQTT_HOST=mosquitto
        ports:
          - 4000:4000
        volumes:
          - ./import:/opt/app/import
        cap_drop:
          - all

      database:
        image: postgres:16
        restart: always
        environment:
          - POSTGRES_USER=teslamate
          - POSTGRES_PASSWORD=password #insert your secure database password!
          - POSTGRES_DB=teslamate
        volumes:
        - teslamate-db:/var/lib/postgresql/data

      grafana:
        image: teslamate/grafana:latest
        restart: always
        environment:
          - DATABASE_USER=teslamate
          - DATABASE_PASS=password #insert your secure database password!
          - DATABASE_NAME=teslamate
          - DATABASE_HOST=database
        ports:
          - 3000:3000
        volumes:
          - teslamate-grafana-data:/var/lib/grafana

      mosquitto:
        image: eclipse-mosquitto:2
        restart: always
        command: mosquitto -c /mosquitto-no-auth.conf
        # ports:
        #   - 1883:1883
        volumes:
          - mosquitto-conf:/mosquitto/config
          - mosquitto-data:/mosquitto/data

      evcc:
        command:
          - evcc
        container_name: evcc
        image: evcc/evcc:latest
        ports:
          - 7070:7070/tcp
          - 8887:8887/tcp
          - 7090:7090/udp
          - 9522:9522/udp
        volumes:
          - /etc/evcc.yaml:/etc/evcc.yaml
          - /home/[user]/.evcc:/root/.evcc
        restart: unless-stopped

      twc3teslamate:
        container_name: twc3teslamate
        image: ghcr.io/haveacry/twc3teslamate
        environment:
          - MQTT_HOST=mosquitto
	ports:
          - 8080:80
        restart: unless-stopped

    volumes:
      teslamate-db:
      teslamate-grafana-data:
      mosquitto-conf:
      mosquitto-data:
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
| TESLAMATE_NAMESPACE | Teslamate MQTT namespace | None |


## EVCC configuration

Setup a TWC3 charger and use the name of the twc3teslamate container (if in the same stack) or the IP address the container is exposed on, that is accessible from EVCC

```
  chargers:
  - name: TWC
    type: template
    template: twc3
    host: twc3teslamate # IP address or hostname
``` 


## run it

to run it native you have to first install the requirements with pip or your package manager

native:

    pip3 install -r requirements.txt
    sudo uvicorn app.main:app --reload --host 0.0.0.0 --port 80

   
## validate

if it's running properly you should get something back when looking at

http://IP_ADDRESS(:port)/api/1/vitals
