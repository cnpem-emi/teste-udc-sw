import epics
import time
from siriuspy import search
import sys
from termcolor import colored, cprint

#Servidor 10.0.6.46 - Sala SEI
#export SIRIUS_URL_CONSTS="http://localhost:20080/control-system-constants/"
#udcname = "ET-RaCtrl:PS-UDC"
#psname = "ET-RaCtrl:PS-CH-1"

udc_ps_la = {
    1:"LA-RaPS06:PS-UDC-TB1",
    2:"LA-RaPS06:PS-UDC-TB2",
    3:"LA-RaPS06:PS-UDC-TB3",
    4:"LA-RaPS06:PS-UDC-TB4",
    5:"LA-RaPS06:PS-UDC-TB5",
    6:"LA-RaPS06:PS-UDC-TB6",
    7:"LA-RaPS06:PS-UDC-TS1",
    8:"LA-RaPS06:PS-UDC-TS2",
    9:"LA-RaPS06:PS-UDC-TS3",
}
udc_dclink_la = {
    1:"LA-RaPS06:PS-UDC-AS1",
    2:"LA-RaPS06:PS-UDC-AS2",
}

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
        if (sala.upper() != "LA"):
            if (int(bastidor) <= 5):
                udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI"+bastidor
            elif (int(bastidor) == 6):
                if (int(sala) == 14):
                    udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI6"
                else:
                    udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-BO"
            elif (int(bastidor) > 7):
                print("Bastidor não encontrado")

        elif(sala.upper() == "LA"):
           udcname = udc_ps_la[int(bastidor)]

        psnames = []
        psnames = search.PSSearch.conv_udc_2_bsmps(udcname)

        print("UDC name: ",udcname)
        print("PS names: ",psnames)

        print("\n")

        size = len(psnames) 

        # Verifica se ha timeout na conexao EPICS - 0 se comunicando sem errros
        ps_status = epics.PV(psnames[0][0]+":Current-Mon")
        if (not ps_status.status):
            text = colored("UDC {} conectado!\n".format(udcname),'green')
        else:
            text = colored("ATENCAO! UDC {} nao esta comunicando!\n".format(udcname),'red')
        print(text)


        #Verifica nomes das fontes
        nomes_fontes = []
        temp = ''
            
        for i in range(0,size):
            print("Solicitando Update de parametros para:",psnames[i][0])
           # epics.caput(psnames[i][0]+":ParamUpdate-Cmd",1)
            time.sleep(1)
            psname_epics = epics.caget(psnames[i][0]+":ParamPSName-Cte")
        for v in psname_epics:
            temp = temp + chr(v)
        nomes_fontes.append(temp)
            
        print("Nomes lidos: ", nomes_fontes)
        print("Nomes esperados: ",psnames)
        print('\n')    
            
        nome = ''.join(nomes_fontes)
        nomes_lidos = nome.split("/")
            
        

        for i in range(0,size):
            str1 = nomes_lidos[i]
            str2 = psnames[i][0]

            index = str1.find(str2)

            if (index != -1):
                text = colored("Ok. Fonte  é a esperada:",'green')
            else:
                text = colored("Ok. Fonte  nao é a esperada:",'red')
        print(text,str2, '\n')


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

        if(firmware_version_origin == firmware):
            text =  colored("Versao correta\n",'green')
        else:
            text =  colored("Versao incorreta\n",'red')
        print("Firmware version:",firmware,text)


        ligar_fonte = input("Ligar fontes? (y) or (n)")
        if((ligar_fonte=="y") or (ligar_fonte=="yes")):
            #Ligar fontes de um mesmo bastidor em sequência
            for i in range(0,size):
                turn_on = psnames[i][0]+":PwrState-Sel"
                turn_on_ps = epics.caput(turn_on,0)
                print("Fonte ligada:",psnames[i][0])
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

        sincronismo = input("Testar sincronismo? yes(y) no(n)")
        if((sincronismo == "y") or (sincronismo == "yes")):
            for i in range(0,size):

                leitura_anterior = epics.caget(psnames[i][0]+":WfmSyncPulseCount-Mon")

                #Usa nome do trigger e não nome da fonte

                str_fonte = psnames[i][0]  #le o nome das fontes
                str_udc = udcname    #le o nome do UDC
    
                #Identificar nome do trigger 
                
                if(str_udc.find("SI") !=-1):

                    if(str_udc.find("IA") !=-1):
                    
                        if((str_fonte.find("CV")!=-1) or (str_fonte.find("CH")!=-1)):
                            trigger_name = "SI-Glob:TI-Mags-Corrs"

                        if(str_fonte.find("QS") !=-1):
                            trigger_name = "SI-Glob:TI-Mags-Skews"
                        
                        if((str_fonte.find("QF") !=-1) or (str_fonte.find("Q1") !=-1) or (str_fonte.find("Q2") !=-1) or (str_fonte.find("Q3") !=-1) or (str_fonte.find("Q4") !=-1) or (str_fonte.find("QD") != -1)):
                            trigger_name = "SI-Glob:TI-Mags-QTrims"
                        
                elif(str_udc.find("BO")!=-1):

                    if(str_udc.find("IA") != -1):

                        if((str_fonte.find("CV")!=-1) or (str_fonte.find("CH")!=-1)):
                            trigger_name = "BO-Glob:TI-Mags-Corrs"
                    
                        if(str_fonte.find("QS") !=-1):
                            trigger_name = "BO-Glob:TI-Mags-Skews"

                elif(str_udc.find("TB")!=-1):
                    trigger_name = "TB-Glob:TI-Mags"

                elif(str_udc.find("TS")!=-1):
                    trigger_name = "TS-Glob:TI-Mags"


                print("Trigger: ", trigger_name, "\n")

                src_anterior = epics.caget(trigger_name+":Src-Sts")
                state_anterior = epics.caget(trigger_name+":State-Sts")

                epics.caput(trigger_name+":Src-Sel", "Study")
                epics.caput(trigger_name+":State-Sel", 1)
                time.sleep(1)
                
                leitura_anterior = epics.caget(psnames[i][0]+":WfmSyncPulseCount-Mon")
                
                epics.caput("AS-RaMO:TI-EVG:StudyExtTrig-Cmd",1)

                time.sleep(2)

                leitura_atual = epics.caget(psnames[i][0]+":WfmSyncPulseCount-Mon")

                epics.caput(trigger_name+":Src-Sel", src_anterior)
                epics.caput(trigger_name+":State-Sel", state_anterior)

                print(leitura_anterior, leitura_atual)

                if(int(leitura_atual) != int(leitura_anterior) + 1):
                    text = colored("Erro no teste de sincronismo",'red')

                else:
                    text = colored("Teste de sincronismo.Ok!",'green')
                    
                print(text, '\n')

        #Desligar fontes
        desligar = input("Desligar fontes?")


        if (desligar == "y" or desligar == "yes"):
            for i in range(0,size):
                turn_off = psnames[i][0]+":PwrState-Sel"
                set_turn_off = epics.caput(turn_off,0)
                print("Fonte desligada:",psnames[i][0], '\n')
                time.sleep(1)
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
    
    if(sala.upper() == "LA"):
        bastidor = input("Bastidor: ")
        dc_link_name= search.PSSearch.conv_udc_2_bsmps(udc_dclink_la[int(bastidor)])[0][0]
    else:
        udcname = "IA-"+sala+"RaPS"+rack+":PS-UDC-SI1"
        psnames = []
        psnames = search.PSSearch.conv_udc_2_bsmps(udcname)
        dc_link_name = search.PSSearch.conv_psname_2_dclink(psnames[0][0])[0]

    print("DCLink name:",dc_link_name)


    #Verifica estado do interlock
    interlock_signal_hard = epics.caget(dc_link_name+":IntlkHard-Mon")
    interlock_signal_soft = epics.caget(dc_link_name+":IntlkSoft-Mon")
    
    if(int(interlock_signal_hard) !=0):
        print("Hard Interlock: ",dc_link_name)

    if(int(interlock_signal_soft) !=0):
        print("Soft Interlock: ",dc_link_name)

    epics.caput(dc_link_name+":Reset-Cmd",1)

    #Conferir versão do firmware
    firmware_dclink_origin = "0.44.01    08/220.44.01    08/22"
    firmware_version = dc_link_name +":Version-Cte"
    firmware= epics.caget(firmware_version)

    if (firmware_dclink_origin == firmware):
        print("Firmware version:",firmware,"Versão correta\n")
    else:
        print("Firmware version:",firmware,"Versão incorreta\n")

    #Ligar DCLink
    turn_on = dc_link_name+":PwrState-Sel"
    turn_on_ps = epics.caput(turn_on,1)
    print("DCLink ligado:",dc_link_name, '\n')

    #Ler Tensao
    time.sleep(3) 
    read_voltage = dc_link_name+":Voltage-Mon"
    voltage_value = epics.caget(read_voltage)
    print(dc_link_name,"Voltage value:",voltage_value, '\n')

    #Desligar DCLink
    desligar = input("Desligar DCLink?")

    if (desligar.lower() == "y" or desligar.lower() == "yes"):
        turn_off = dc_link_name+":PwrState-Sel"
        set_turn_off = epics.caput(turn_off, 0)
        print("DCLink desligado:", dc_link_name, '\n')

    time.sleep(3)

    #Ler 0V 
    read_voltage = dc_link_name+":Voltage-Mon"
    voltage_value = epics.caget(read_voltage)
    print(dc_link_name,"Voltage:",voltage_value)

