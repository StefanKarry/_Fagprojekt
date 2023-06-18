import numpy as np   


# Porporitonal
def P_control(temp, Tw, CP, Full):
    '''
    temp = Temperature\n
    Tw = wanter Temperature\n
    CP = P controller constant\n
    Full = distance from Tw where gain should be 100
    '''
    error = Tw - temp
    if abs(error) > Full: #hvis fejlen er er større end full sættes gain = 100
        p_output = 100*(error/abs(error))
    elif error == 0: # hvis fejlen er 0 er gain=0
        p_output = 0
    else:
        p_output = CP*(error) #det "normale" P gain udregne
    return p_output

#Integral
def I_control(temp, Tw, CI, I_period,error_list):
    '''
    temp = Temperature\n
    Tw = wanter Temperature\n
    CI = I controller constant\n
    I_period = Numbers in the sum\n
    error_list = array to store errors
    '''
    global error_sum
    error_sum = error_list
    error = Tw - temp    
    if len(error_sum) < I_period: #hvis ikke array er I_period langt, ligges nye værdier i
        error_sum = np.append(error_sum, error)
        I_output = 0
    else: # opdatere værdier i summen
        error_sum = np.delete(error_sum, I_period-1)
        error_sum = np.insert(error_sum,0,error)
        if abs(error) < 2: #fejlen er mindre end 2 grader regnes P gainen
            I_output = CI*np.sum(error_sum)
        else:
            error_sum = np.zeros(I_period) # hvis over, overskrives error_list med nuller
            I_output = 0
    return I_output, error_sum


#derivative
def D_control(T,Tw,D_period,CD,error_list):#temp, Tw, not in use
    '''
    temp = Temperature\n
    Tw = wanter Temperature\n
    error_list = list of error\n
    D_period = what value should the the difference be calculated with
    CI = I controller constant
    '''
    if len(error_list) < D_period:
        D_output = 0
    else:
        if len(error_list) > D_period:# and  error_list[D_period] != 0 and error_list[0]: #regner d outputtet
            d_error = error_list[D_period]-error_list[0]
            D_output = d_error*CD
        else:
            D_output = 0
    return D_output