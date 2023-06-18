import numpy as np
import os
import tkinter as tk
import time
import pandas as pd
import RPi.GPIO as GPIO
import pigpio

def GPIOCleanup():
    '''
    Cleans up all uses GPIO pins, inclduing putting pwm high to turn of the heat and cool
    '''
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(12,GPIO.OUT)
    GPIO.setup(13,GPIO.OUT)
    GPIO.output([12,13],[1,1])
    time.sleep(1)
    pi.spi_close(adc)
    pi.stop()

def init(design_num):
    '''
    design_num = hvilket design skal brges
    Initialisering af design 1 eller 2
    '''
    global adc, Vref, pi, MUXpins, channels, NTC_channels,design, Ns, Vntc, R1, Sensors, gaincal
    global SHconstants, LED_pins

    pi = pigpio.pi()
    #print(pi)
    if not pi.connected:
        exit()
    adc = pi.spi_open(0,800_000,0)
    Vref = 3.3
    Vntc = 3.3
    design = design_num
    Ns = 50  #number of samples pr reading
    R1 = 20000   
    GPIO.setmode(GPIO.BCM)
    if design_num==1: #opsætning for design 1
        
        #Deffinering af pins til mux
        Epin = 6
        pin0 = 17
        pin1 = 27
        pin2 = 5
        pin3 = 22

        NTC_channels = [12, 13, 14, 15] #kanaler med externe sensorer
        GPIO.setup(Epin, GPIO.OUT)
        GPIO.output(Epin, 0) #sikre at mux er aktiv
        Sensors = {"Int 0": 11, #dictionary for sensor and mux channel
                   "Int 1": 8,
                   "Int 2": 9,
                   "Int 3": 10,
                   "Int 4": 7,
                   "Int 5": 6,
                   "Int 6": 5,
                   "Int 7": 4,
                   "Int 8": 3,
                   "Int 9": 2,
                   "Int 10": 1,
                   "Int 11": 0,
                   "Ext 0": 12,
                   "Ext 1": 13,
                   "Ext 2": 14,
                   "Ext 3": 15}
        gaincal=pd.read_csv("../Design1cal.csv") #indlæs kalibreringsdata for design 1
        # LED opsætnig
        GPIO.setup(23,GPIO.OUT)
        GPIO.setup(25,GPIO.OUT)
        GPIO.setup(24,GPIO.OUT)
        LED_pins = (23, 25, 24)
    else: #opsætning af design 2

        #Deffinering af pins til mux
        pin0 = 27
        pin1 = 17
        pin2 = 6
        pin3 = 5
        Epin1 = 14
        Epin2 = 23
        Epin3 = 22

        NTC_channels = [4, 5, 6, 7] #kanaler med externe sensorer

        Sensors = {"Int 0": 8, #dictionary for sensor og mux kanal
                   "Int 1": 10,
                   "Int 2": 11,
                   "Int 3": 9,
                   "Int 4": 2,
                   "Int 5": 1,
                   "Int 6": 0,
                   "Int 7": 7,
                   "Int 8": 15,
                   "Int 9": 12,
                   "Int 10": 13,
                   "Int 11": 14,
                   "Ext 0": 4,
                   "Ext 1": 6,
                   "Ext 2": 7,
                   "Ext 3": 5}
        gaincal=pd.read_csv("../Design2cal.csv") #indlæs kalibreringsdata for design 2
        GPIO.setup(Epin1, GPIO.OUT)
        GPIO.setup(Epin2, GPIO.OUT)
        GPIO.setup(Epin3, GPIO.OUT)
        GPIO.output([Epin1, Epin2, Epin3], [0, 0, 0]) #sikre at mux er aktiv
        # LED opsætnig
        GPIO.setup(4,GPIO.OUT)
        GPIO.setup(3,GPIO.OUT)
        GPIO.setup(2,GPIO.OUT)
        LED_pins = (4,2,3)
    
    GPIO.output(LED_pins, (0,0,0))
    SHconstants = pd.read_csv("../SHConstantsB.csv") #indlæs kalibreringsdata til NTC modstande
    MUXpins = (pin0,pin1,pin2,pin3)
    channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for i in range(8): #LED kører igennem alle farver
        GPIO.output(LED_pins, (i&1, i&2, i&4))
        time.sleep(0.1)
    
    
    #Setting desired pins as output on RPi.
    GPIO.setup(pin0,GPIO.OUT)
    GPIO.setup(pin1,GPIO.OUT)
    GPIO.setup(pin2,GPIO.OUT)
    GPIO.setup(pin3,GPIO.OUT)

    

def read_ADC():
    '''
    funcion to read ADC
    '''
    count, data = pi.spi_xfer(adc,[0x80,0])
    if count == 2:
        val = (data[0]*256+data[1])/2 #værdien fra ADC'en
        V = val*Vref/(2**12) #omregner til spænding
    return(V)

def channel_select(channel):
    '''
    Function for picking a mux channel, using bitwise AND operations
    '''
    GPIO.output(MUXpins,(channel&1, channel&2, channel&4, channel&8))



def mesure_temps():
    '''
    Function for measurering temperatures
    '''
    global adc, Vref, pi, MUXpins, channels, NTC_channels,design, Ns, Vntc, R1, Sensors, gaincal
    global SHconstants
    temps = np.zeros(len(channels))

    Tk = 273.15 #omregningskonstant mellem kelvin og grader celcius

    i=0
    GPIO.output(LED_pins, (0,0,0)) #Slukker LED så denne ikke trækker strøm
    for sensor in Sensors:
        channel_select(Sensors[sensor]) #vælger mux-kanal tilhørende aktuel sensor
        time.sleep(0.0001) #for at sikre ADC'en ikke måler før mux'en har skiftet
        V = 0
        for j in range(Ns): #læser fra ADC'en NS gange
            time.sleep(0.0005)
            V = V + read_ADC()
        Vavg=V/Ns #tager gennemsnit
        #tager højde for kalibrering af pcb
        Vin = (Vavg-gaincal.loc[gaincal["Input"]==sensor,"Offset"])/gaincal.loc[gaincal["Input"]==sensor,"Gain"]

        #omregning til temperatur
        if sensor[0]=="E": # for eksterne sensorer bruges Steinhart-hart
            A = SHconstants.loc[0, sensor]
            B = SHconstants.loc[1, sensor]
            C = SHconstants.loc[2, sensor]
            R = (Vntc*R1)/Vin-R1 #modstand regnes
            temps[i] = (A+B*np.log(R)+C*(np.log(R))**3)**(-1)-Tk  #Steinhart-Hart
        else: #for interne bruge den simple sammenhæng for en LM35
            temps[i] = Vin*100
        time.sleep(0.005)
        i+=1

    return(temps)

def LED(T, Tw):
    '''
    Function to control LED
    '''
    Te = T - Tw #regner fejlen
    if  Te < -1: #er systemet mere end 1 grad for koldt, lyser dioden blåt
        GPIO.output(LED_pins, (0, 0, 1))
    elif Te < -0.1:#er systemet mere end 0.1 grad for koldt, lyser dioden turkis
        GPIO.output(LED_pins, (0, 1, 1))
    elif Te > 1: #er systemet mere end 1 grad for varmt, lyser dioden rødt
        GPIO.output(LED_pins, (1, 0, 0))
    elif Te > 0.1: #er systemet mere end 0.1 grad for varmt, lyser dioden lilla
        GPIO.output(LED_pins, (1, 0, 1))
    else: #Er temperaturen inden for plusminus 0.1 grad af den ønsket lyser LED'en grønt
        GPIO.output(LED_pins, (0, 1, 0))
    

#terminal interface for testing purposes
if __name__ == '__main__':
    # ---Variables---
    done = False
    commands = ["Temps", "Voltages", "exit", "channel"]
    init(1)


    # ---Main Loop---
    while not done:
        try:
            print('Enter command (Temps, Voltages, channel or exit)') #Giver de muligheder som brugeren har. Er udgangspunktet i UI.
            command = input('-> ') 


            if command not in commands:
                print(f"'{command}' is not a valid option, please choose on of the following options:")
                continue
            
            
            
            elif command == 'Temps':
                print(mesure_temps())

            
            elif command == "channel":
                channel = int(input('Enter a channel number (must be between 0 and 15)'))
                channel_select(channel)

            elif command == "Voltages":
                for i in channels:
                    channel_select(i)
                    time.sleep(0.001)
                    V = 0
                    for n in range(Ns):
                        V = V + read_ADC()
                        time.sleep(0.001)
                    Vavg = V/Ns
                    print([i, Vavg])
            
            elif command == "exit":
                GPIO.cleanup()
                print('Quitting...')
                pi.spi_close(adc)
                pi.stop()
                done = True
                continue

        # Handle potential force stop from CTRL+C
        except KeyboardInterrupt:
            print('Stopping...')
            GPIO.cleanup()
            pi.spi_close(adc)
            pi.stop()
            done = True


