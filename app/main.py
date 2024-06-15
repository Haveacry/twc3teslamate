from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import os
import sys
import paho.mqtt.client as mqtt

app = FastAPI()

#tasmota_ip = os.getenv('TASMOTA_IP', '172.16.90.72')
MQTT_HOST = os.getenv('MQTT_HOST', None)
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
TESLAMATE_CAR_ID = os.getenv('TESLAMATE_CAR_ID', 1)
TESLAMATE_GEO_HOME = os.getenv('TESLAMATE_GEO_HOME', 'Home')

if MQTT_HOST is None:
    print("No MQTT broker specified. Please set the MQTT_HOST environment variable")
    sys.exit(1)

# Define the data structure
class Vitals(BaseModel):
    contactor_closed: bool
    vehicle_connected: bool
    session_s: int
    grid_v: float
    grid_hz: float
    vehicle_current_a: float
    currentA_a: float
    currentB_a: float
    currentC_a: float
    currentN_a: float
    voltageA_v: float
    voltageB_v: float
    voltageC_v: float
    relay_coil_v: float
    pcba_temp_c: float
    handle_temp_c: float
    mcu_temp_c: float
    uptime_s: int
    input_thermopile_uv: int
    prox_v: float
    pilot_high_v: float
    pilot_low_v: float
    session_energy_wh: float
    config_status: int
    evse_state: int
    current_alerts: list

state = ""

# Data dictionary for MQTT message values
data = {
  "plugged_in": False,
  "soc": 0,
  "is_charging": 0,
  "is_dcfc": 0,
  "is_parked": 0,
  "voltage": 0,
  "current": 0,
  "kwh_charged": 0,
  "inside_temp": 0,
  "phases": 1,
  "session_start": "2024-01-01T00:00:00.000000Z"
}

# Initialize MQTT client and connect
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,f"twc3teslamate-{TESLAMATE_CAR_ID}")
if MQTT_USERNAME is not None:
    if MQTT_PASSWORD is not None:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    else:
        client.username_pw_set(MQTT_USERNAME)

client.connect(MQTT_HOST,MQTT_PORT)

def on_connect(client, userdata, flags, reason_code, properties):  # The callback for when the client connects to the broker
    if reason_code != "Success":
        print("Unable to connect to MQTT broker, result code {0}".format(str(reason_code)))
        sys.exit(1)

    print("Connected with result code {0}".format(str(reason_code)))  # Print result of connection attempt
    client.subscribe(f"teslamate/cars/{TESLAMATE_CAR_ID}/#")

# Process MQTT messages
def on_message(client, userdata, message):
    global data
    global state
    try:
        #extracts message data from the received message
        payload = str(message.payload.decode("utf-8"))

        #updates the received data
        topic_postfix = message.topic.split('/')[-1]

        if topic_postfix == "plugged_in":
            data["plugged_in"] = payload
        #elif topic_postfix == "latitude":
        #    data["lat"] = payload
        #elif topic_postfix == "longitude":
        #    data["lon"] = payload
        #elif topic_postfix == "elevation":
        #    data["elevation"] = payload
        #elif topic_postfix == "speed":
        #    data["speed"] = int(payload)
        #elif topic_postfix == "power":
        #    data["power"] = int(payload)
        #    if(data["is_charging"]==1 and int(payload)<-22):
        #        data["is_dcfc"]=1
        elif topic_postfix == "charger_power":
            if(payload!='' and int(payload)!=0):
                data["is_charging"]=1
                if int(payload)<-22:
                    data["is_dcfc"]=1
        #elif topic_postfix == "heading":
        #    data["heading"] = payload
        #elif topic_postfix == "outside_temp":
        #    data["ext_temp"] = payload
        #elif topic_postfix == "odometer":
        #    data["odometer"] = payload
        #elif topic_postfix == "ideal_battery_range_km":
        #    data["ideal_battery_range"] = payload
        #elif topic_postfix == "est_battery_range_km":
        #    data["battery_range"] = payload
        elif topic_postfix == "charger_actual_current":
            if payload!='':
                data["current"] = payload
            else:
                data["current"] = 0
        elif topic_postfix == "charger_voltage":
            if(payload!='' and int(payload) > 5):
                data["voltage"] = payload
            else:
                data["voltage"] = 0
        #elif topic_postfix == "shift_state":
        #    if payload == "P":
        #        data["is_parked"]="1"
        #    elif(payload == "D" or payload == "R"):
        #        data["is_parked"]="0"
        elif topic_postfix == "state":
            state = payload
            if payload=="driving":
                data["is_parked"]=0
                data["is_charging"]=0
                data["is_dcfc"]=0
            elif payload=="charging":
                data["is_parked"]=1
                data["is_charging"]=1
                data["is_dcfc"]=0
            elif payload=="supercharging":
                data["is_parked"]=1
                data["is_charging"]=1
                data["is_dcfc"]=1
            elif(payload=="online" or payload=="suspended" or payload=="asleep"):
                data["is_parked"]=1
                data["is_charging"]=0
                data["is_dcfc"]=0
        elif topic_postfix == "battery_level":
            data["soc"] = payload
        elif topic_postfix == "charge_energy_added":
            data["kwh_charged"] = float(payload) * 1000.0
        elif topic_postfix == "inside_temp":
            data["inside_temp"] = payload
        elif topic_postfix == "since":
            data["session_start"] = payload[:-8]
        elif topic_postfix == "geofence":
            data["geofence"] = payload
        elif topic_postfix == "phases":
            data["phases"] = payload
        else:
            pass
            #print("Unneeded topic:", message.topic, payload)
        return

    except:
        print("unexpected exception while processing message:", sys.exc_info()[0], message.topic, message.payload)

# Starts the MQTT loop processing messages
client.on_message = on_message
client.on_connect = on_connect  # Define callback function for successful connection
client.loop_start()


@app.get("/api/1/vitals")
async def get_vitals():

    global data
    global state

    current = data["current"]
    voltage = data["voltage"]

    # Teslamate reports single voltage/current values - assume same on all phases
    if data["phases"] == 3:
        current_b = current
        current_c = current
        voltage_b = voltage
        voltage_c = voltage
    else:
        current_b = 0
        current_c = 0
        voltage_b = 0
        voltage_c = 0


    # If we are at home, set charging/plugged status, else our "wall connector" is not charging the car
    if data.get("geofence") is not None:
        if data["geofence"] == TESLAMATE_GEO_HOME:
            if state == "charging":
                charging = True

                if data.get("session_start") is not None:
                    session_time = int(datetime.utcnow().strftime("%s")) - int(datetime.fromisoformat(data["session_start"]).strftime("%s"))
                else:
                    session_time = 0
            else:
                charging = False
                session_time = 0

            connected = data["plugged_in"]

        else:
            charging = False
            connected = False
            session_time = 0
            current = 0
            current_b = 0
            current_c = 0
            voltage = 0
            voltage_b = 0
            voltage_c = 0

    else:
        charging = False
        connected = False
        session_time = 0
        current = 0
        current_b = 0
        current_c = 0
        voltage = 0
        voltage_b = 0
        voltage_c = 0
    
    vitals = Vitals(
        contactor_closed=charging,
        vehicle_connected=connected,
        session_s=session_time,
        grid_v=voltage,
        grid_hz=49.828,
        vehicle_current_a=current,
        currentA_a=current,
        currentB_a=current_b,
        currentC_a=current_c,
        currentN_a=0.0,
        voltageA_v=voltage,
        voltageB_v=voltage_b,
        voltageC_v=voltage_c,
        relay_coil_v=11.9,
        pcba_temp_c=7.4,
        handle_temp_c=1.8,
        mcu_temp_c=data["inside_temp"],
        uptime_s=26103,
        input_thermopile_uv=-176,
        prox_v=0.0,
        pilot_high_v=11.9,
        pilot_low_v=11.8,
        session_energy_wh=data["kwh_charged"],
        config_status=5,
        evse_state=1,
        current_alerts=[]
        # ... the other static stuf..contactor_closed=True,
    )
    return vitals
