import time
import RPi.GPIO as GPIO
from grove.i2c import Bus
from w1thermsensor import W1ThermSensor
from azure.iot.device import IoTHubDeviceClient
import datetime

#grove.i2c adc predefined variables for Pi_hat_adc class
ADC_DEFAULT_IIC_ADDR = 0X04
ADC_CHAN_NUM = 8

REG_VOL_START = 0x20
REG_SET_ADDR = 0XC0

#GPIO preset for program start
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW) #GPIO pin 8 output pin, initial value set to LOW/OFF
GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)#GPIO pin 12 output pin, initial value set to LOW/OFF

DS18B20 = W1ThermSensor()

#Class to get analog mV values from ADC. Returns all 8 channel readings in array
#Channel A0 in use for thermal sensor
class Pi_hat_adc():
    def __init__(self, bus_num=1, addr=ADC_DEFAULT_IIC_ADDR):
        self.bus = Bus(bus_num)
        self.addr = addr
    
    
    def get_all_vol_milli_data(self):
        array = []
        for i in range(ADC_CHAN_NUM):
            data  = self.bus.read_i2c_block_data(self.addr, REG_VOL_START+i, 2)
            val = data[1]<<8|data[0]
            array.append(val)
        return array       

def main():
    ADC = Pi_hat_adc()
    global vol_data   
    
    global maxLimit
    maxLimit = setMaxParameter()
    global minLimit
    minLimit = setMinParameter()
    
    #Connecting to Azure IoT Hub
    cs = "YOUR CONNECTION STRING HERE"
    cd = IoTHubDeviceClient.create_from_connection_string(cs)
    cd.connect()
    
    try:
        
        #Main loop to read temperature and light up the LED lights
        #And sending data to Azure IoT hub
        while True:
            vol_data = ADC.get_all_vol_milli_data()
            print('Temperature from DS18B20 is: {} C'.format(getDigitalTemp()))
            print('Temperature from MCP9701 is: {} C'.format(getAnalogTemp()))

            print ("Average temperature between analog and digital sensors is: %s C" %temperatureAverage())
                        
            date = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())           
            message = '{'+f"'DeviceId': 'MyPythonDevice', 'analogTemp': '{getAnalogTemp()}', 'digitalTemp': '{getDigitalTemp()}', 'avgTemp': '{temperatureAverage()}', 'Timestamp': '{date}'"+'}'
            #print(message)
            cd.send_message(message)
            
            time.sleep(5)            
            
            
    except KeyboardInterrupt:
        #Call parameter change function
        print("Program interrupted with CTRL + C, Cleaning GPIO and exiting now.")
        
    #except:
        #print("Unexpected interruption happened!")
        
        
    finally:
        GPIO.cleanup()
        cd.disconnect()

#Setters and getters for temp threshold parameters
def setMaxParameter():
    print("setParameters function called")
    global maxLimit
    maxLimit = float(input("Give maximum temperature threshold value: "))
    return maxLimit

def setMinParameter():
    print("SetMinParameter function called")
    minLimit = float(input("Give minimum temperature threshold value: "))
    return minLimit

def getMaxLimit():
    return maxLimit
    
def getMinLimit():
    return minLimit


#Check temperature from MCP9701 analog sensor
def getAnalogTemp():
    analogRead = float(vol_data[0])
    analogRead2 = float(analogRead) - 400
    analogTemperature = round(float(analogRead2/19.53),2)
    #print("Temperature from MCP9701 is : %.2f C" %analogTemperature)
    return analogTemperature
    
#Check temperature from DS18B20 digital sensor
def getDigitalTemp():
    temperature = round(DS18B20.get_temperature(),2)
    #print("Temperature from DS18B20 is: %.2f C" %temperature)
    return temperature
                    
#Get analog and digital temperature and set average value                    
def temperatureAverage():

    tempAverage = round(float((DS18B20.get_temperature() + getAnalogTemp()) / 2),2)
        
    #Compare temp average to limit thresholds and blink lights accordingly
    if tempAverage > getMaxLimit():
        GPIO.output(8, GPIO.HIGH)
        time.sleep(1)
    elif tempAverage < getMinLimit():
        GPIO.output(12, GPIO.HIGH)
        time.sleep(1)
    GPIO.output(8, GPIO.LOW)
    GPIO.output(12, GPIO.LOW)
        
    return tempAverage

if __name__ == "__main__":
    main()
    

