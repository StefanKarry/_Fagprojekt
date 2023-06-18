#Importering af pakker
import numpy as np
import os
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import (FormatStrFormatter,MaxNLocator)
import pandas as pd
import RPi.GPIO as GPIO
import pigpio
import datetime


#Funktioner fra de af scripts bliver her importeret, så de kan bruges i GUI'en
from Design1_ny2 import init, read_ADC, channel_select, mesure_temps, GPIOCleanup, LED

from PID_functions import P_control, I_control, D_control

from Regulering import regInit, regulering, GAIN_PID


def center(win):
    '''
    Funktionen centrerer vinduerne efter en  given skærms størrelse.
    Det gøres at hente skærmens højde og bredde.
    '''
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('+{}+{}'.format(x, y))
    win.deiconify()

def file_saver(Tw,GAIN,temps):
        '''
        Til at gemme det data som bliver lavet undervejs, er der lavet en funktion
        som tager en forlavet .csv fil, og skriver til denne for hver iteration.
        På den måde risikerer man ikke at alt data går tabt, hvis nu RPi'en skulle miste forbindelsen.-
        '''
        with open('../GUI_ting/Design1_stoejtest2.csv','a') as f: #Åbning af skabelon-fil
            x = np.array([[datetime.datetime.now()]])
            vals = np.hstack((x,Tw,GAIN,temps))
            np.savetxt(f,vals,fmt='%s',delimiter=',') #Skriver til skabelon-filen

def plotter(x,y0,y1):
    '''
    Funktionen plotter temperaturen og gainet af systemet.
    Alle de korrekte aksetitler mm. laves også her.
    '''
    global graph, ax0, ax1
    ax0.cla()
    ax1.cla()

    ax0.set_ylabel(r'Temperature [$C^\circ$]')
    ax0.set_title('Temperature graph')
    ax0.tick_params(axis = 'x',which = 'both', bottom = False, top = False, labelbottom = False)
    ax0.tick_params(axis = 'y',labelsize = 'small')
    ax0.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))


    ax1.set_xlabel("Timestamp") 
    ax1.set_ylabel("Gain")
    ax1.set_title('Gain graph')
    ax1.tick_params(axis = 'x', rotation = 45,labelsize = 'small')
    ax1.tick_params(axis = 'y',labelsize = 'small')

    ax0.plot(x,y0,color = 'blue')
    ax1.plot(x,y1,color = 'red')
    ax0.grid()
    ax1.grid()
    graph.draw()

'''
Nedenfor er nogle parametre forvalgt. Herunder at den ønskede starttemperatur som udgangspunkt er 35 grader. 
Herudover laves der tomme arrays, hvori temperatur, gain og timestamp bliver gemt, samt et count.
'''
Tw = 35
T410 = []
t = []
c = 0
GAIN = []


def TempGUI(window):
        global t, T410, Tw, design_num, c
        global Tr, rows, GAIN, E2, E1, ax0, ax1, graph
        '''
        Funktionen er det hovedsaglige kode til GUI'en.
        Her bliver der lavet 22 'entries' hvori temperatur, gain, ønsket- og nuværende temperatur, bliver vist.
        Det er også i denne funktion værdierne bliver opdateret, ved at køre funktionen igen, og igen efter 100 ms.
        Graferne der blev lavet med den tidligere funktion, bliver her vist i vinduet.
        '''
        if c == 0: #Her bliver vinudet initialiseret. Der laves 20 entries hvori temperaturer og gainet vises. Canvas til graferne bliver også lavet her.
                    #På den måde undgås der hukommelsesfejl på RPi'en.
            #Entries
            rows = []
            for i in range(10):
                cols = []
                for j in range(2):
                    E = tk.Entry(window,relief = tk.GROOVE,font = ('Arial 14'),width = 13)
                    E.grid(row = i, column = j, sticky = tk.NSEW)
                    cols.append(E)
                rows.append(cols)

            E2 = tk.Entry(window, font = ('Arial 14'), width = 25)
            E2.place(relx = 0.01, rely = 0.65)

            #Plots
            fig = Figure(dpi=100, figsize = (5,4),tight_layout = True)
            ax0 = fig.add_subplot(211)
            ax1 = fig.add_subplot(212)

            graph = FigureCanvasTkAgg(fig, master = window)
            graph.get_tk_widget().place(relx = 0.35, rely = 0.01)

            E1 = tk.Entry(window, width = 25, font = ('Arial 14'))
            E1.place(relx = 0.01 , rely = 0.72)

            c += 1
            window.after(1,lambda: TempGUI(window))


        else:
            navne = np.array([['Int 0','Int 1'],['Int 2','Int 3'],
                            ['Int 4','Int 5'],['Int 6','Int 7'],
                            ['Int 8','Int 9'],['Int 10','Int 11'],
                            ['Ext 0','Ext 1'],['Ext 2','Ext 3'],
                            ['P-Gain', 'I-Gain'], ['D-Gain','PID-Gain']])
            deg = u'\u2103'

            temps = np.array([mesure_temps()]) #Temperaturene bliver her aflæst fra de 16 sensorer.
            Tr = (temps[0,4] + temps[0, 10])/2 #Den gennemsnitlige temperatur mellem sensor 4 og 10 bestemmes
            LED(Tr, Tw)
            GAIN = np.round(np.append(GAIN,GAIN_PID(Tr,Tw)[9,1]))
            

            file_saver(np.array([[Tw]]),np.array([[GAIN[-1]]]),temps) #Der bliver skrevet til filen
            regulering(Tr,Tw) #Reguleringssystemet

            t.append(datetime.datetime.now().strftime('%H:%M:%S'))
            T410.append((temps[0,4] + temps[0,10])/2) #Den gennemsnitlige temperatur bliver her gemt, som er nødvendig for PID-controlleren.
            
            T410 = T410[-20:]
            t = t[-20:]
            GAIN = GAIN[-20:]

            temps = np.reshape(temps,(8,2))
            plotter(t,np.round(T410,2),np.round(GAIN)) #Den gennemsnitlige temperatur og gainet plottes.

            #Skriver i entries
            for i in range(8):
                for j in range(2):
                    rows[i][j].delete(0,tk.END)
                    rows[i][j].insert(tk.END, '%s: %.2f%s' % (navne[i,j],temps[i,j],deg))

            for k in range(8,10):
                for l in range(2):
                    rows[k][l].delete(0,tk.END)
                    rows[k][l].insert(tk.END, '%s: %.0f' % (navne[k,l],GAIN_PID(Tr,Tw)[k,l]))

            #Skriver ønsket og nuværende temperatur
            E2.delete(0,tk.END)
            E2.insert(tk.END, '%s: %.2f %s' % ('Current temperature', Tr, deg))

            E1.delete(0,tk.END)
            E1.insert(tk.END, '%s: %.2f %s' % ('Target temperature', Tw, deg))

            c += 1
            window.after(100,lambda: TempGUI(window))

def TempViewer():
    '''
    Funktionen laver det vindue, hvori temperaturer mm. bliver vist.
    Der er tilføjet en knap, som gør det muligt at ændre den ønskede temperatur.
    '''
    global c, Tr
    c = 0

    WIN4 = tk.Toplevel(master)
    width= WIN4.winfo_screenwidth()               
    height= WIN4.winfo_screenheight()   
    WIN4.geometry("%dx%d" % (width, height))
    WIN4.title('Temperatures')
    center(WIN4)

    TempGUI(WIN4) #De aflæste værdier bliver vist.

    #Knap til ændring af temperatur
    B11 = tk.Button(WIN4, text = 'Change the target temperature', width = 25,
                    command = lambda: [TwChanger(WIN4), os.popen('matchbox-keyboard')])
    B11.place(relx = 0.027, rely = 0.8)

def ImgViewer():
    '''
    Funktionen gør det muligt at vise et billede af placeringen af de 12 interne sensorer.
    '''
    WIN3 = tk.Toplevel(master)
    WIN3.title('Sensor layout')
    imgff = tk.PhotoImage(file="/home/fagprojekt/Documents/Fagprojekt/GUI_ting/Sensor_Layout.png")
    labelImgff = tk.Label(WIN3, image=imgff, bg="white")
    labelImgff.grid()
    WIN3.mainloop()

def TwChanger(window):
    '''
    Her bliver vinduet til at ændre temperaturen dannet.
    Ved at trykke på knappen fra 'TempViewer', bliver der åbnet et On-Screen-Keyboard (OSK), således tastatur og mus
    ikke er nødvendigt. Når når der trykkes på knappen 'Ok' gemmes den indtastede temperatur, OSK lukkes og 'TempViewer() vises igen.
    '''
    deg = u'\u2103'
    WIN2 = tk.Toplevel(window)
    center(WIN2)
    window.withdraw()

    #Her laves en entry og en knap til at ændre den ønskede temperatur
    L3 = tk.Label(WIN2,text = f'Insert the wanted temperatur below, in {deg}')
    E0 = tk.Entry(WIN2)
    B11 = tk.Button(WIN2, text = 'Ok', command = lambda: [GetTw(E0), os.system('pkill -f matchbox-keyboard'),window.deiconify(),WIN2.destroy()])

    L3.pack(side = 'top')
    B11.pack(side = 'right')
    E0.pack(side = 'top')
    E0.focus_set()


def GetTw(entry):
    '''
    Henter den indtastede værdi fra feltet hvori den blev skrevet.
    '''
    global Tw, c
    Tw = float(entry.get()) #Henter værdi fra en entry'en i 'TwChanger()'
    c = 0
    return Tw

def CleanUp():
    '''
    Når der trykkes på exit, lukker den master vinduet men udover det, sætter den også 
    '''
    GPIOCleanup()
    master.destroy()

def design1():
    '''
    Her laves vinduet hvis der trykkes på knappen 'Design 1'. Denne kører en intialisering, således GPIO-pinsne
    passer til design 1. I vinduet er det muligt at få vist temperaturene, vist et layout af sensorene, gå tilbage
    til valg af design, eller lukke GUI'en helt.
    '''
    global design_num, c, t
    master.withdraw()
    c = 0
    design_num = 1
    init(design_num)
    regInit()

    WIN1 = tk.Toplevel(master)
    center(WIN1)
    WIN1.geometry('300x165')


    L2 = tk.Label(WIN1,text = 'You are using design version 1', font = ('Arial, 14'))
    B7 = tk.Button(WIN1, text = 'View temperatures',width = 17, font = ('Arial 14'), command = TempViewer)
    B8 = tk.Button(WIN1, text = 'Exit', width = 17, font = ('Arial 14'), command = CleanUp, fg = 'red')
    B9 = tk.Button(WIN1, text = 'Sensor layout', width = 17, font = ('Arial 14'), command = ImgViewer)
    B10 = tk.Button(WIN1, text = 'Return to the previous page', width = 17, font = ('Arial 14'), command = lambda: [CleanUp, master.deiconify(), WIN1.destroy()])

    L2.pack()
    B7.pack(fill = 'both')
    B9.pack(fill = 'both')
    B10.pack(fill = 'both')
    B8.pack(fill = 'both')

#Creates a window for choosing design version 2
def design2():
    '''
    Her laves vinduet hvis der trykkes på knappen 'Design 2'. Denne kører en intialisering, således GPIO-pinsne
    passer til design 2. I vinduet er det muligt at få vist temperaturene, vist et layout af sensorene, gå tilbage
    til valg af design, eller lukke GUI'en helt.
    '''
    master.withdraw()
    global design_num, c, t
    design_num = 2
    c = 0
    init(design_num) #Initialsering af valgte design
    regInit()

    WIN0 = tk.Toplevel(master)
    center(WIN0)
    WIN0.geometry('300x165')

    L1 = tk.Label(WIN0,text = 'You are using design version 2', font = ('Arial, 14'))
    B3 = tk.Button(WIN0, text = 'View temperatures',width = 20, font = ('Arial 14'),command = TempViewer)
    B4 = tk.Button(WIN0, text = 'Exit', width = 20, font = ('Arial 14'), command = CleanUp, fg = 'red')
    B5 = tk.Button(WIN0, text = 'Sensor layout', font = ('Arial 14'), width = 20, command = ImgViewer)
    B6 = tk.Button(WIN0, text = 'Return to the previous page', width = 20, font = ('Arial 14'), command = lambda: [CleanUp, master.deiconify(), WIN0.destroy()])
    
    L1.pack()
    B3.pack(fill = 'both')
    B5.pack(fill = 'both')
    B6.pack(fill = 'both')
    B4.pack(fill = 'both')


'''
Nedenfor laves 'master' vinduet, som er det første vindue man støder på, når koden køres.
Her bliver der vist mulighederne 'Design-1' og 'Design-2' samt en 'Exit' knap.
Knapperne for 'Design-1' og 'Design-2' sikrer at den rigtige initialsering bliver kørt for den respektive designs.
'''
master = tk.Tk()
center(master)

L0 = tk.Label(master, text='Choose your design', font = ('Arial','14'))
B0 = tk.Button(master,text = 'Design 1', width = 17, font = ('Arial 14'),command = design1)
B1 = tk.Button(master, text = 'Design 2', width = 17, font = ('Arial 14'),command = design2)
B2 = tk.Button(master, text = 'Exit',width = 17, font = ('Arial 14'), command = master.destroy, fg = 'red')

L0.grid()
B0.grid()
B1.grid()
B2.grid()

master.mainloop()



