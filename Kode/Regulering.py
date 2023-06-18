import RPi.GPIO as GPIO #import the RPi.GPIO library
import time #import the sleep from time library
from PID_functions import P_control, I_control, D_control #PID functions
import numpy as np

#initialisering skal stå et andet sted


def regInit():
    global CP, CI, CD, error_sum2, t, pwm_heat, pwm_cool, P_gain, I_gain, D_gain, PID_gain, t0, error_sum2
    #setup
    #GPIO.setmode(GPIO.BCM)
    GPIO.setup(12,GPIO.OUT)
    GPIO.setup(13,GPIO.OUT)
    GPIO.setwarnings(False)
    pwm_heat = GPIO.PWM(12,1000)
    pwm_cool = GPIO.PWM(13,1000)
    pwm_heat.start(0)
    pwm_cool.start(0)
    pwm_heat.ChangeDutyCycle(100)
    pwm_cool.ChangeDutyCycle(100)

    #setup reguleringssystem
    CP,CI,CD = 45,8,50
    error_sum2 = []
    t0 = 4

def GAIN_PID(T,Tw):
    '''
    T = Temperature
    Tw = wanted temperature
    '''
    global P_gain, I_gain, D_gain, PID_gain, t0, error_sum2
    #Regner gains for hvert system ved brug af funnktion fra PID_functions
    P_gain = P_control(T,Tw,CP,2)
    I_gain, error_sum2 = I_control(T,Tw,CI,25,error_sum2)
    D_gain = D_control(5,CD,error_sum2)
    PID_gain = P_gain + I_gain + D_gain #summere de respektive gains
    if PID_gain < -100: #sørger for at mindste gain er gain=-100
        PID_gain = -100
    elif PID_gain > 100:
        PID_gain = 100 #sørger for maks at have gain=100
        
    #array til at gemme gains
    return np.array([[0, 0], [0, 0],
                     [0, 0], [0, 0],
                     [0, 0], [0, 0],
                     [0, 0], [0, 0],
                     [P_gain, I_gain], [D_gain, PID_gain]])
 

def regulering(T,Tw):
    '''
    T = Temperature
    Tw = wanted temperature
    '''
    global P_gain, I_gain, D_gain, PID_gain, t0, error_sum2
    if PID_gain > 0: #turn on heat
        pwm_heat.ChangeDutyCycle(100-PID_gain)
        pwm_cool.ChangeDutyCycle(100)
    elif PID_gain < 0: #turn on cooling
        pwm_cool.ChangeDutyCycle((100-abs(PID_gain))*3.6/5)
        pwm_heat.ChangeDutyCycle(100)
    return PID_gain

