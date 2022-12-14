import epics
import time
import pydrs
import argparse
from siriuspy import search
from xlrd import open_workbook
from siriuspy.csdev import get_device_2_ioc_ip

#Servidor 10.0.6.46 - Sala SEI
#export SIRIUS_URL_CONSTS="http://localhost:20080/control-system-constants/"
#udcname = "ET-RaCtrl:PS-UDC"
#psname = "ET-RaCtrl:PS-CH-1"

#ipdict = get_device_2_ioc_ip("LA-RaPS02:CO-PSCtrl-TB")
#print(ipdict)


IP_DRS = "10.0.6.59"
PORT_DRS = 5000


FLOAT_MAX_ERROR = 1e-4 # Usually is 1.1920929e-08

drs = pydrs.pydrs.EthDRS(IP_DRS,PORT_DRS)

# Define função que receberá as mensagens de Exception do EPICS
def epics_ca_no_print(epics_ca_warnings):
    return

# Escolhe direcionamento das mensagens de Exception
epics.ca.replace_printf_handler(fcn=epics_ca_no_print)

modo_teste = input("Escolha o modo de teste BID(1) ou demais testes(2)")
n = int(input("Escolha o numero de testes: "))
i=1
if(modo_teste == "1" or modo_teste == 1):

    while(i <= n):
        print("Iteração numero", i)
        def check_param_bank(csv_file, max_error, memory=1):
            memoria_ram = drs.get_param_bank()
            #print("Memoria RAM",memoria_ram,'\n\n')
            drs.unlock_udc(0xCAFE)
            drs.load_param_bank(type_memory=args.type_mem)
            read_ps_bank = drs.get_param_bank()
            #print("Memoria BID", read_ps_bank,'\n\n')

            csv_ps_bank = drs.read_csv_param_bank(ps_param_path)
            #print("Memoria CSV",csv_ps_bank)

            error_values = {}


            
            for param_name in csv_ps_bank.keys():
                if param_name == "PS_Name":
                    if(csv_ps_bank[param_name] != read_ps_bank[param_name][0] and csv_ps_bank[param_name]!= memoria_ram[param_name][0]):
                        print("{} = {} and {} : param differs!".format(
                            param_name, 
                            csv_ps_bank[param_name], 
                            read_ps_bank[param_name],
                            memoria_ram[param_name]
                            )
                        )

                    if(read_ps_bank[param_name][0].find("ÿ") != -1):
                        print(" ERRO BID corrompida")
                else:
                    for i in range(len(csv_ps_bank[param_name])):
                        if(csv_ps_bank[param_name][i] != read_ps_bank[param_name][i] and csv_ps_bank[param_name][i] != memoria_ram[param_name][i]):
                            if(abs(csv_ps_bank[param_name][i] - read_ps_bank[param_name][i]) > FLOAT_MAX_ERROR and abs(csv_ps_bank[param_name][i] - memoria_ram[param_name][i]) > FLOAT_MAX_ERROR):
                                print("{}[{}] = {} (CSV) and {} (DRS): params differ!".format(
                                    param_name, 
                                    i, 
                                    csv_ps_bank[param_name][i], 
                                    read_ps_bank[param_name][i],
                                    memoria_ram[param_name][i],
                                    )
                                )
                                error_values[param_name] = {"csv":csv_ps_bank[param_name], "read":read_ps_bank[param_name], "ram":memoria_ram[param_name]}
                return error_values

        def check_dsp_module_bank(csv_file, max_error, memory=1):
            memoria_ram = drs.get_dsp_modules_bank()
            drs.unlock_udc(0xCAFE)
            drs.load_dsp_modules_eeprom(type_memory=memory)
            read_dsp_bank = drs.get_dsp_modules_bank()  #BID
            csv_dsp_bank = drs.read_csv_dsp_modules_bank(csv_file)

            error_values = {}

            for param_name in csv_dsp_bank.keys():
                for ninstance in range(pydrs.consts.num_dsp_modules[pydrs.consts.dsp_classes_names.index(param_name)]):
                    if(csv_dsp_bank[param_name]['coeffs'][ninstance] != read_dsp_bank[param_name]['coeffs'][ninstance] and csv_dsp_bank[param_name]['coeffs'][ninstance] != memoria_ram[param_name]['coeffs'][ninstance]):
                        for ncoeff in range(pydrs.consts.num_coeffs_dsp_modules[pydrs.consts.dsp_classes_names.index(param_name)]):
                            if(abs(csv_dsp_bank[param_name]['coeffs'][ninstance][ncoeff] - read_dsp_bank[param_name]['coeffs'][ninstance][ncoeff]) > max_error and abs(csv_dsp_bank[param_name]['coeffs'][ninstance][ncoeff] - memoria_ram[param_name]['coeffs'][ninstance][ncoeff]) > max_error):
                                print("{}[{},{}] = {} (CSV) and {} (DRS): params differ!".format(
                                    param_name, 
                                    ninstance,
                                    ncoeff,
                                    csv_dsp_bank[param_name]['coeffs'][ninstance][ncoeff], 
                                    read_dsp_bank[param_name]['coeffs'][ninstance][ncoeff],
                                    memoria_ram[param_name]['coeffs'][ninstance][ncoeff],
                                    )
                                )
                                error_values[param_name] = {"csv":csv_dsp_bank[param_name], "read":read_dsp_bank[param_name],"ram":memoria_ram[param_name]}
            return error_values



        def read_spreadsheet(datafile = "Inventario.xls", bid = None, pstype = None):
            
            sheet = open_workbook(datafile).sheet_by_name("Inventario")
            keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]
            items = {}
            for row_index in range(1,sheet.nrows):
                
                udc_name = sheet.cell(row_index,keys.index("UDC")).value
                udc_model =sheet.cell(row_index,keys.index("Modelo")).value
                ps_file = sheet.cell(row_index,keys.index("ps_parameters")).value
                dsp_file = sheet.cell(row_index,keys.index("dsp_parameters")).value
                bid_code = int(sheet.cell(row_index,keys.index("# BID")).value)
            
                if "fa" in udc_model.lower():
                    udc_model = udc_model[:3]

                if ("IA-" in udc_name):
                    room_name =  udc_name[:5]
        
                elif ("Development" in udc_name):
                    room_name = "development"
                else:
                    room_name =  udc_name[:2]
                
                if(bid is not None):
                    if((sheet.cell(row_index,keys.index("# BID")).value == bid)):
                        items[udc_name] = [udc_model, ps_file, dsp_file, room_name, bid_code]
                elif(pstype):
                    if((sheet.cell(row_index,keys.index("Modelo")).value == pstype.upper())):
                        items[udc_name] = [udc_model, ps_file, dsp_file, room_name, bid_code]

            return items

        
        if (__name__ == '__main__'):

                parser = argparse.ArgumentParser(description='Process some integers.')
                parser.add_argument('-ps', '--power-supply', dest='ps_type', choices=['fbp', 'fbp-dclink', 'fap'])
                parser.add_argument('-bid', '--bid-id', dest='bid_id', type=int)
                parser.add_argument('-memory', '--type-memory', dest='type_mem', type=int, choices=[1, 2], default=1)
                args = parser.parse_args()

                memoryType = {1: "BID", 2:"on-board"}

                if((args.bid_id is not None) and (args.ps_type is not None)):
                    print("Selecionar apenas a BID ou tipo de fonte!")
                    exit()

                elif(args.ps_type is not None):
                    psinfo = read_spreadsheet(pstype=args.ps_type)

                elif(args.bid_id is not None):
                    psinfo = read_spreadsheet(bid=args.bid_id)

                    drs = pydrs.EthDRS(IP_DRS, PORT_DRS)

                for addr in range(31)[1:]:
                    drs.slave_addr = addr
                    try:
                        drs.get_ps_name()
                        print("Address {} found!".format(addr))
                        break
                    except:
                        pass

                print("UDC ARM VERSION:  ", drs.read_udc_arm_version())
                print("UDC DSP VERSION:  ", drs.read_udc_c28_version())
        

                # psinfo[udc_name] = [udc_model, ps_file, dsp_file, room_name, bid_code]
                if psinfo:
                
                    for ps in psinfo.keys():
                        ps_param_path = 'udc-ps-parameters-db/{}/{}/{}'.format(psinfo[ps][3], psinfo[ps][0].lower().replace("-","_"), psinfo[ps][1])
                        dsp_param_path = 'udc-dsp-parameters-db/{}/{}/{}'.format(psinfo[ps][3], psinfo[ps][0].lower(), psinfo[ps][2])

                       
                        # ------------------------------
                        # READINGS - PS PARAMETERS
                        # ------------------------------
                        
                        print("\n")
                        print("Loading {} into memory, reading PS parameters and comparing them to {} file".format(
                            memoryType[args.type_mem],
                            psinfo[ps][1]
                        ))
                        if(check_param_bank(ps_param_path, FLOAT_MAX_ERROR, memory=args.type_mem)):
                            print("ERRO")
                        else:
                            print("OK")
                        
                        # ------------------------------
                        # READINGS - DSP PARAMETERS
                        # ------------------------------
                        if (psinfo[ps][0].lower() != "fbp-dclink"):
                            print("Loading {} into memory, reading DSP parameters and comparing them to {} file".format(
                            memoryType[args.type_mem],
                            psinfo[ps][2]
                        ))
                            if(check_dsp_module_bank(dsp_param_path, FLOAT_MAX_ERROR, memory=args.type_mem)):
                                print("ERRO")
                            else:
                                print("OK!")
                        
                        # ------------------------------
                        # RESET UDC FOR PARAMETER LOADING
                        # ------------------------------
                        print("Resetting UDC and wait for startup...")
                        drs.reset_udc()
                        time.sleep(5)
                        
                        #drs.slave_addr = int(bid_ps_bank['RS485_Address'][0][0])

                        while(True):
                            try:
                                drs.get_ps_name()
                                print("Address after reboot {} found!".format(drs.slave_addr))
                                break
                            except:
                                print("Waiting addr {}".format(drs.slave_addr))

                    
        i = i+1


if(modo_teste == "2" or modo_teste == 2): 
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

            if(firmware_version_origin == firmware):
                print("Firmware version:",firmware,"Versão correta\n")

            else:
                print("Firmware version:",firmware,"Versão incorreta\n")


            #Ligar fontes de um mesmo bastidor em sequência
            for i in range(0,size):
                turn_on = psnames[i][0]+":PwrState-Sel"
                turn_on_ps = epics.caput(turn_on,1)
                print("Fonte ligada:",psnames[i][0])
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



            #Verifica sinal de sincronismo

            sincronismo = input("Testar sincronismo? yes(y) ou no(n)")
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
                            
                    if(str_udc.find("BO")!=-1):

                        if(str_udc.find("IA") != -1):

                            if((str_fonte.find("CV")!=-1) or (str_fonte.find("CH")!=-1)):
                                trigger_name = "BO-Glob:TI-Mags-Corrs"
                        
                            if(str_fonte.find("QS") !=-1):
                                trigger_name = "BO-Glob:TI-Mags-Skews"

                    print(trigger_name)
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

                        print("Erro no teste de sincronismo")

                    else:
                        print("Teste de sincronismo.Ok!")
                        
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

