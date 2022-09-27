import epics
import time
from siriuspy import search

#Servidor 10.0.6.46 - Sala SEI
#export SIRIUS_URL_CONSTS="http://localhost:20080/control-system-constants/"
#udcname = "ET-RaCtrl:PS-UDC"
#psname = "ET-RaCtrl:PS-CH-1"

sala = input("Sala: ")
rack = input("Rack: ")
tipo_fonte = input("FBP(1) ou FBP-DCLink(2): ")

if(len(sala)< 2):
    sala = "0"+sala

if(len(rack) <2 ):
    rack = "0"+rack


if((int(tipo_fonte) == 1) or (tipo_fonte=="FBP")):
    bastidor = input("Bastidor: ")
    if(int(bastidor) <= 5):
        udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI"+bastidor
    if(int(bastidor) == 6):
        if(int(sala) == 14):
            udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI6"
        else:
            udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-BO"
    if(int(bastidor) >7):
        print("Bastidor não encontrado")
    psnames = []
    psnames = search.PSSearch.conv_udc_2_bsmps(udcname)
    print("UDC name: ",udcname)
    print("PS names: ",psnames)

    size = len(psnames) 
    ''''
    #Conferir nomes das fontes
    psnames_udc = []
    for i in range(0,size):
        var = epics.caget(psnames[i][0]+":ParamPSName-Cte")
        print("PS name", str(var),'utf8', "OK")
    '''  

    #Conferir versão do firmware
    firmware_version_origin = "0.44.01    08/220.44.01    08/22"
    firmware_version = psnames[0][0]+":Version-Cte"
    firmware= epics.caget(firmware_version)
    if(firmware_version_origin == firmware):
        print("Firmware version:",firmware,"Versão correta\n")
    else:
        print("Firmware version:",firmware,"Versão incorreta\n")


    #Ligar fontes de um mesmo bastidor em sequência
    for i in range(0,size):
        turn_on = psnames[i][0]+":PwrState-Sel"
        turn_on_ps = epics.caput(turn_on,1)
        print("Fonte ligada:",psnames[i][0] )
        time.sleep(1)
        
    print('\n')

    #Colocar 1A para FBPs
    for i in range(0,size):
        current = psnames[i][0]+":Current-SP"
        set_current = epics.caput(current,1)

    time.sleep(2)


    #Ler 1A das fontes
    for i in range(0,size):
        read_current = psnames[i][0]+":Current-Mon"
        current_value = epics.caget(read_current)
        print(psnames[i][0],"Current value:",current_value)

    print('\n')

    #Desligar fontes
    desligar = input("Desligar fontes?")


    if(desligar == "y" or desligar == "yes"):
        for i in range(0,size):
            turn_off = psnames[i][0]+":PwrState-Sel"
            set_turn_off = epics.caput(turn_off,0)
            print("Fonte desligada:",psnames[i][0])
            time.sleep(1)

    print('\n')

    time.sleep(2)

    #Ler 0A das fontes
    for i in range(0,size):
        read_current = psnames[i][0]+":Current-Mon"
        current_value = epics.caget(read_current)
        print(psnames[i][0],"Current value:",current_value)



else:
    
    udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI1"
    psnames = []
    psnames = search.PSSearch.conv_udc_2_bsmps(udcname)
    dc_link_name = search.PSSearch.conv_psname_2_dclink(psnames[0][0])
    print("DCLink name:",dc_link_name)

    #Conferir versão do firmware
    firmware_version_origin = "0.44.01    08/220.44.01    08/22"
    firmware_version = psnames[0][0]+":Version-Cte"
    firmware= epics.caget(firmware_version)
    if(firmware_version_origin == firmware):
        print("Firmware version:",firmware,"Versão correta\n")
    else:
        print("Firmware version:",firmware,"Versão incorreta\n")

    #Ligar DCLink
    turn_on = dc_link_name[0]+":PwrState-Sel"
    turn_on_ps = epics.caput(turn_on,1)
    print("Fonte ligada:",dc_link_name[0])

    print('\n')

    #Ler 1V 
    read_voltage = dc_link_name[0]+":Voltage-Mon"
    voltage_value = epics.caget(read_voltage)
    print(dc_link_name[0],"Voltage value:",voltage_value)

    print('\n')

    #Desligar DCLink
    desligar = input("Desligar DCLink?")

    if(desligar == "y" or desligar == "yes"):
        turn_off = dc_link_name[0]+":PwrState-Sel"
        set_turn_off = epics.caput(turn_off,0)
        print("DCLink desligado:",dc_link_name[0])

    print('\n')

    time.sleep(2)

    #Ler 0V 
    read_voltage = dc_link_name[0]+":Voltage-Mon"
    voltage_value = epics.caget(read_voltage)
    print(dc_link_name[0],"Voltage:",voltage_value)

