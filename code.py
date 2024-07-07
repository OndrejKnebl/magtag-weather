import board
import alarm
from secrets import secrets
import adafruit_requests
import displayio
import wifi
import ssl
import socketpool
import time
import json
from adafruit_display_text import label
import terminalio

lang = "EN"         # CZ / EN
updateEvery = 180   # seconds


def displayData(myObj3):
    display = board.DISPLAY
    time.sleep(display.time_to_refresh)
    main_group = displayio.Group()

    bmp_file = "/bmps/output.bmp"
    bitmap = displayio.OnDiskBitmap(bmp_file)
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
    bg_group = displayio.Group()
    bg_group.append(tile_grid)
    main_group.append(bg_group)

    text_area = label.Label(terminalio.FONT, text="o", color=0x000000)
    text_area.x = 124
    text_area.y = 93
    main_group.append(text_area)

    text_area = label.Label(terminalio.FONT, text="C", scale=2, color=0x000000)
    text_area.x = 130
    text_area.y = 100
    main_group.append(text_area)

    text_area = label.Label(terminalio.FONT, text="%", scale=2, color=0x000000)
    text_area.x = 274
    text_area.y = 100
    main_group.append(text_area)

    if lang == "CZ":
        text_area = label.Label(terminalio.FONT, text="Teplota", scale=3, color=0xFFFFFF)
        text_area.x = 12
        text_area.y = 22
        main_group.append(text_area)

        text_area = label.Label(terminalio.FONT, text="Vlhkost", scale=3, color=0xFFFFFF)
        text_area.x = 160
        text_area.y = 22
        main_group.append(text_area)
    
    else:
        text_area = label.Label(terminalio.FONT, text="TEMP", scale=3, color=0xFFFFFF)
        text_area.x = 12
        text_area.y = 22
        main_group.append(text_area)

        text_area = label.Label(terminalio.FONT, text="HUMI", scale=3, color=0xFFFFFF)
        text_area.x = 160
        text_area.y = 22
        main_group.append(text_area)


    myObj4 = myObj3["decoded_payload"]

    if "temperature_1" in myObj4:
        temp = round(float(myObj4["temperature_1"]),1)
        
        text_area = label.Label(terminalio.FONT, text=str(temp), scale=4, color=0x000000)
        if temp < -9.9:
            text_area.x = 10
            text_area.y = 70
        elif temp >= 0.0 and temp <= 9.9:
            text_area.x = 42
            text_area.y = 70
        elif temp < 0.0 and temp >= -9.9:
            text_area.x = 20 
            text_area.y = 70
        else:
            text_area.x = 28
            text_area.y = 70

        main_group.append(text_area)


    if "relative_humidity_2" in myObj4:
        humi = round(float(myObj4["relative_humidity_2"]),1)
        text_area = label.Label(terminalio.FONT, text=str(humi), scale=4, color=0x000000)

        if humi <= 9.9:
            text_area.x = 188
            text_area.y = 70
        elif humi < 99.9:
            text_area.x = 175
            text_area.y = 70
        else:
            text_area.x = 162
            text_area.y = 70

        main_group.append(text_area)


    receivedAt = myObj3["received_at"]

    myDate = str(receivedAt).split("T")
    myTime = myDate[1].split(".")

    year, month, day = myDate[0].split('-')
    myDate = f"{day}.{month}.{year}"
    
    text_area = label.Label(terminalio.FONT, text=f"UTC {myTime[0]} {myDate}", color=0x000000)
    text_area.x = 155
    text_area.y = 122
    main_group.append(text_area)
            
    display.root_group = main_group
    display.refresh()


def getWeatherData():
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
    headers = {'Authorization':'Bearer ' + secrets["TTN_api"]}
    response = requests.get(secrets["TTN_Storage_Address"], headers=headers)
    dbResponse = response.text.split("\n")
    response.close()

    myObj1 = json.loads(dbResponse[len(dbResponse)-2])
    myObj2 = myObj1['result']
    myObj3 = myObj2['uplink_message']
    receivedAt = myObj3["received_at"]
    

    if(alarm.sleep_memory):
        memoryList = [None] * alarm.sleep_memory[0]

        for i in range(0, alarm.sleep_memory[0]):
            memoryList[i] = alarm.sleep_memory[i+1]

        timeInMemory = str(bytes(memoryList))[2:][:-1]

        if str(receivedAt) != timeInMemory:
            displayData(myObj3)
    

    packed = bytes(str(receivedAt),'utf-8')
    listPacked = list(packed)

    alarm.sleep_memory[0] = len(listPacked)

    for i in range(0, len(listPacked)):
        alarm.sleep_memory[i+1] = listPacked[i]



def main():
    try:
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        getWeatherData()

        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + updateEvery)
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)

    except Exception as e:
        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + updateEvery)
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)

main()