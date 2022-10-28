import epics
import time
from siriuspy import search

#Servidor 10.0.6.46 - Sala SEI
#export SIRIUS_URL_CONSTS="http://localhost:20080/control-system-constants/"
#udcname = "ET-RaCtrl:PS-UDC"
#psname = "ET-RaCtrl:PS-CH-1"



# Define função que receberá as mensagens de Exception do EPICS
def epics_ca_no_print(epics_ca_warnings):
    return

# Escolhe direcionamento das mensagens de Exception
epics.ca.replace_printf_handler(fcn=epics_ca_no_print)


sala = input("Sala: ")
rack = input("Rack: ")
tipo_fonte = input("FBP(1) ou FBP-DCLink(2): ")

if (len(sala) < 2):
    sala = "0"+sala

if (len(rack) < 2):
    rack = "0"+rack


if ((int(tipo_fonte) == 1) or (tipo_fonte=="FBP")):
    encerrar = False
    while(encerrar == False):
        bastidor = input("Bastidor: ")
        if (int(bastidor) <= 5):
            udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI"+bastidor
        if (int(bastidor) == 6):
            if (int(sala) == 14):
                udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI6"
            else:
                udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-BO"
        if (int(bastidor) > 7):
            print("Bastidor não encontrado")

        psnames = []
        psnames = search.PSSearch.conv_udc_2_bsmps(udcname)
        print("UDC name: ",udcname)
        print("PS names: ",psnames)

        print("\n")

        size = len(psnames) 
            
        #Verifica nomes das fontes
        nomes_fontes = []
        temp = ''
            
        for i in range(0,size):
            print("Solicitando Update de parametros para: ",psnames[i][0])
           # epics.caput(psnames[i][0]+":ParamUpdate-Cmd",1)
           # time.sleep(1)
            psname_epics = epics.caget(psnames[i][0]+":ParamPSName-Cte")
        for v in psname_epics:
            temp = temp + chr(v)
        nomes_fontes.append(temp)
            
        print("Nomes lidos: ", nomes_fontes)
        print("Nomes esperados: ",psnames)
            
            
        nome = ''.join(nomes_fontes)
        nomes_lidos = nome.split("/")
            
        print('\n')

        for i in range(0,size):
            str1 = nomes_lidos[i]
            str2 = psnames[i][0]

            index = str1.find(str2)

            if (index != -1):
                print("Ok. Fonte  é a esperada: ",str2)
            else:
                print("Erro. Fonte não é a esperada: ",str2)
        print('\n')


            #Verifica estado do interlock

        for i in range(0,size):

            interlock_signal_hard = epics.caget(psnames[i][0]+":IntlkHard-Mon")
            interlock_signal_soft = epics.caget(psnames[i][0]+":IntlkSoft-Mon")
                
            if(int(interlock_signal_hard) !=0):
                print("Hard Interlock: ",psnames[i][0])

            if(int(interlock_signal_soft) !=0):
                print("Soft Interlock: ",psnames[i][0])

            epics.caput(psnames[i][0]+":Reset-Cmd",1)


            #Conferir versão do firmware
        firmware_version_origin = "0.44.01    08/220.44.01    08/22"
        firmware_version = psnames[0][0]+":Version-Cte"
        firmware= epics.caget(firmware_version)

        if (firmware_version_origin == firmware):
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
            set_current = epics.caput(current,0)

        time.sleep(2)


            #Ler 1A das fontes
        for i in range(0,size):
            read_current = psnames[i][0]+":Current-Mon"
            current_value = epics.caget(read_current)
            print(psnames[i][0],"Current value:",current_value)


        
    #Verifica sinal de sincronismo

        for i in range(0,size):

            epics.caput(psnames[i][0]+":Src-Sel",1) 
            print(epics.caget(psnames[i][0]+":Src-Sts"))

            leitura_anterior = epics.caget(psnames[i][0]+":WfmSyncPulseCount-Mon")

            #Usa nome do trigger e não nome da fonte

            #str_fonte = psnames[i][0]  #le o nome das fontes
            str_fonte = "BO-Fam:PS-QF"
            #str_udc = udcname    #le o nome do UDC
            str_udc = "PA-RaPSC03:PS-UDC-BO1"

            #Identificar nome do trigger 
            
            if(str_udc.find("SI") !=-1):

                if(str_udc.find("IA") !=-1):
                
                    if((str_fonte.find("CV")!=-1) or (str_fonte.find("CH")!=-1)):
                        trigger_name = "SI-Glob:TI-Mags-Corrs"

                    if(str_fonte.find("QS") !=-1):
                        trigger_name = "SI-Glob:TI-Mags-Skews"
                    
                    if((str_fonte.find("QF") !=-1) or (str_fonte.find("Q1") !=-1) or (str_fonte.find("Q2") !=-1) or (str_fonte.find("Q3") !=-1) or (str_fonte.find("Q4") !=-1) or (str_fonte.find("QD") != -1)):
                        trigger_name = "SI-Glob:TI-Mags-QTrims"
                    
                    

            if(str_udc.find("BO")!=-1):

                if(str_udc.find("IA") != -1):

                    if((str_fonte.find("CV")!=-1) or (str_fonte.find("CH")!=-1)):
                        trigger_name = "BO-Glob:TI-Mags-Corrs"
                
                    if(str_fonte.find("QS") !=-1):
                        trigger_name = "BO-Glob:TI-Mags-Skews"

            print(trigger_name)
            epics.caput(trigger_name+":ExtTrig-Cmd")

            leitura_atual = epics.caget(psnames[i][0]+":WfmSyncPulseCount-Mon")

            if(int(leitura_atual) == int(leitura_anterior) + 1):

                epics.caput(psnames[i][0]+":Src-Sel",0)
                print(epics.caget(psnames[i]+[0]+":Src-Sts"))

            else:
                print("Erro no teste de sincronismo")

        print('\n')

            #Desligar fontes
        desligar = input("Desligar fontes?")


        if (desligar == "y" or desligar == "yes"):
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

        var = int(input("Trocar bastidor(1) Encerrar Programa(2)"))

        if(var == 2):
            encerrar = True


else:
    
    udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI1"
    psnames = []
    psnames = search.PSSearch.conv_udc_2_bsmps(udcname)
    dc_link_name = search.PSSearch.conv_psname_2_dclink(psnames[0][0])
    print("DCLink name:",dc_link_name[0])



    #Verifica estado do interlock

    interlock_signal_hard = epics.caget(dc_link_name[0]+":IntlkHard-Mon")
    interlock_signal_soft = epics.caget(dc_link_name[0]+":IntlkSoft-Mon")
    
    if(int(interlock_signal_hard) !=0):
        print("Hard Interlock: ",dc_link_name[0])

    if(int(interlock_signal_soft) !=0):
        print("Soft Interlock: ",dc_link_name[0])

    epics.caput(dc_link_name[0]+":Reset-Cmd",1)

    #Conferir versão do firmware
    firmware_dclink_origin = "0.44.01    08/220.44.01    08/22"
    firmware_version = dc_link_name[0] +":Version-Cte"
    firmware= epics.caget(firmware_version)

    if (firmware_dclink_origin == firmware):
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

    if (desligar == "y" or desligar == "yes"):
        turn_off = dc_link_name[0]+":PwrState-Sel"
        set_turn_off = epics.caput(turn_off,0)
        print("DCLink desligado:",dc_link_name[0])

    print('\n')

    time.sleep(2)

    #Ler 0V 
    read_voltage = dc_link_name[0]+":Voltage-Mon"
    voltage_value = epics.caget(read_voltage)
    print(dc_link_name[0],"Voltage:",voltage_value)

