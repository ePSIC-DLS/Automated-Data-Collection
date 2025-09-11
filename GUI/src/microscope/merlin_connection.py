import socket
import select
import sys
import re
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import struct
from queue import Queue


class ImageHeader:

    def __init__(self, header_str='', dac=-1, TH='0'):
        ''' LALALA. If DAC=1 if we are using this from DAC scan. It does not seem as if
        we are getting data aproproately from TCP as the DAC that is running is set to zero'''

        list = header_str.split(b',')

        self.params = {}
        chips = []

        if len(list) > 13:
            self._Params(list, dac)

    def _Params(self, list, dac):

        self.params['acqNumber'] = int(list[1])
        self.params['Offset'] = int(list[2])
        self.params['Nchips'] = int(list[3])
        self.params['NpixX'] = int(list[4])
        self.params['NpixY'] = int(list[5])
        self.params['dataType'] = list[6]
        self.params['detLayout'] = list[7]
        self.params['TimeStamp'] = list[9]
        self.params['FrameTime'] = float(list[10])  # in secodns
        self.params['Counter'] = int(list[11])  # in secodns
        self.params['Colour'] = int(list[12])  # in secodns
        self.params['Gain'] = int(list[13])  # in secodns

        self.params['Threshold_DACS'] = {}
        self.params['DACs'] = {}
        self.params['Thresholds'] = {}

        if b'1x1' in self.params['detLayout']:
            chips = ['Chip1']

        if (b'2x2' in self.params['detLayout']) or (b'Nx1G' in self.params['detLayout']) or (
                b'Nx1' in self.params['detLayout']):
            chips = ['Chip1', 'Chip2', 'Chip3', 'Chip4']

        intdict = {}

        counter = 15

        if b'U' in self.params['dataType']:
            print(" Getting through here ")
            self.params['Thresholds'] = list[14:21]

            counter = 22

            for i, chip in enumerate(chips):

                intdict[chip] = []
                initial = counter

                for j in range(initial, initial + 28):

                    item = list[j]

                    if int(j) == initial:
                        intdict[chip].append(item)
                    else:
                        intdict[chip].append(int(item))

                    counter += 1

                self.params['DACs'][chip] = intdict[chip]
                self.params['Threshold_DACS'][chip] = intdict[chip][1:9]

                # trick for DAC scans via TCP ip
                if dac > -1: self.params['Threshold_DACS'][chip][self.params['Counter']] = dac

        self.params['head_extens'] = list[counter]
        self.params['TimeStamp_ext'] = list[counter + 1]
        self.params['FrameTimens'] = list[counter + 3]
        self.params['bitdepth'] = int(list[counter + 3])

    def Print(self):
        for param, value in list(self.params.items()):
            print(" - INFO : ", param, " = ", value)

        return


class MERLIN_connection:

    def __init__(self, hostname='diamrd', ipaddress='000', channel='cmd',
                 varFile=r'C:\Users\Merlin\Desktop\microscope_control_private\merlin-tcp-connection-master_python3\connection\ListOfCurrentTCPvariables_dev.txt'):

        self.varsTCPcontrolled = {}
        self.hostname = hostname

        self.Header = ''

        self.listofstringvars = ['SOFTWAREVERSION', 'FLATFIELDFILE', 'FILEDIRECTORY', 'FILENAME',
                                 'PIXELMATRIXLoadFILE']
        self.listofFloatVars = ['THSTEP', 'THSTOP', 'THSTART', 'OPERATINGENERGY', 'THRESHOLD7',
                                'THRESHOLD6', 'THRESHOLD5', 'THRESHOLD4', 'THRESHOLD3', 'THRESHOLD2',
                                'THRESHOLD1', 'THRESHOLD0', 'TEMPERATURE', 'HVBIAS', 'SCANX', 'SCANY']

        self.listofArrayvars = ['chiptemps']

        self.listofScientific = ['ACQUISITIONTIME', 'ACQUISITIONPERIOD']

        self.readonly = ['TEMPERATURE', 'DETECTORSTATUS', 'TriggerInLVDS', 'TriggerInTTL', 'SOFTWAREVERSION']

        # Port number is hardcoded :S
        port = 0

        if channel == 'cmd':
            print(' - INFO : Connecting to the command channel')
            port = 6341

        else:
            if channel == 'data':
                print(' - INFO : Connecting to the data channel')
                port = 6342
                # self.displayFigure =  plt.figure('Image Display ')

            else:
                print(' - ERROR : Trying to correct to the wrong channel. No rata or command')
                sys.exit()

        # Creating a socket and connection to MERLIN host machine
        print(' - INFO : Connecting  to ', self.hostname)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Making the socket non-blocking

        except socket.error:
            print('Failed to create socket')
            sys.exit()

        try:

            if hostname == 'diamrd':
                self.remote_ip = ipaddress
            else:
                self.remote_ip = socket.gethostbyname(self.hostname)

            print(' - INFO : with remote ip ', self.remote_ip)
            server_address = (self.remote_ip, port)

            self.sock.connect(server_address)

            print(' - INFO : Connected to MERLIN with remote ip ', self.remote_ip)

        except socket.gaierror:
            print(' Hostname could not be resolved')
            sys.exit()

        # Creating a local copy of all the 'at this point' default values of Variables
        self._get_list_of_vars(varFile)

        self.ongoingAcquisition = True
        # Putting all the values I get
        if channel == 'cmd':
            self.updateValues()

    def __del__(self):

        self.sock.close()
        print(' - INFO :')
        print(' - INFO : Clossing connection to ', self.hostname)
        print(' - INFO :')

    def _get_list_of_vars(self, varFile):

        self.listofTCPvars = []
        with open(varFile) as input:
            for line in input:
                if re.search('#', line): continue
                var = line[:-1].split(' ')[2]
                self.listofTCPvars.append(var)
                print(' VARIABLE *', var, '*')
                if re.search('##', line): return

    def updateValues(self):
        for var in self.listofTCPvars:
            # print ' - INFO : getting ', var
            # sleep(1)
            if var == 'PixelMask': continue
            if 'UseAcquisitionHeaders' in var: continue

            self.varsTCPcontrolled[var] = self.getVariable(var, PRINT='OFF')

        print(' - INFO : ')
        print(' - INFO : These are all the MERLIN default values ')
        print(' - INFO : ------------------------------------------------- ')
        for key, val in self.varsTCPcontrolled.items():
            print(' ------------ INFO : ', key, ' = ', val)

    # print ' - INFO : ------------------------------------------------- '
    #        print ' '

    def getIntNumericVariable(self, varName, PRINT='OFF'):

        var = 0

        if varName not in self.listofTCPvars:
            print(' - WARNING : You are asking for a variable that does not exist ...', varName)

        else:

            # Ugly hack... for some reason when getting it does not recognize GAIN but HIGHGAIN
            # that was the original name of the var (for histogical reasons)
            # if varName == 'GAIN' : varName = 'HIGHGAIN'

            cmnd = ',GET,'
            endofcomdn = cmnd + varName

            lenght = len(endofcomdn)

            str_lenght = str(lenght)

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = 'MPX,00' + str_lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if PRINT == 'ON': print(' - INFO : sending command ', fullcommand)
            self.sock.send(fullcommand.encode('utf-8'))
            data = self.sock.recv(1024).decode('utf-8', 'ignore')
            if PRINT == 'ON':
                print(' - INFO : receiving', data)
            print('TESTING:', data)
            print(data.split(',')[4])
            var = 0 #  int(float(data.split(',')[4]))

            res = 0 # int(float(data.split(',')[5]))

            print(data)

            if res != 0:
                print(' - ERROR : Something has gone badly ')
                if res == 1: print(' - ERROR : The system is busy ')
                if res == 2:
                    print(' - ERROR : The Command was not recognised ')
                    print(' - we are here')
                    print(' -   ', data)
                if res == 3: print(' - ERROR : The Parameter was out of range ')

        return var

    def getFloatNumericVariable(self, varName, PRINT='OFF'):

        var = 0.0

        if varName not in self.listofTCPvars:
            print(' - WARNING : You are asking for a variable that does not exist ...', varName)

        else:

            cmnd = ',GET,'
            endofcomdn = cmnd + varName
            lenght = str(len(endofcomdn))

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = 'MPX,00' + lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if PRINT == 'ON': print(' - INFO : sending command Float ', fullcommand)
            self.sock.send(fullcommand.encode('utf-8'))
            data = self.sock.recv(1024).decode('utf-8', 'ignore')
            if PRINT == 'ON': print(' - INFO : receiving', data)
            var = float(data.split(',')[4])
            res = 0 # int(data.split(',')[5])

            if res != 0:
                print(' - ERROR : Something has gone badly ')
                if res == 1: print(' - ERROR : The system is busy ')
                if res == 2: print(' - ERROR : The Command was not recognised ')
                if res == 3: print(' - ERROR : The Parameter was out of range ')
        return var

    def getstringVariable(self, varName, PRINT='OFF'):

        var = ''

        if varName not in self.listofTCPvars:
            print(' - WARNING : You are asking for a variable that does not exist ...', varName)

        else:
            cmnd = ',GET,'
            endofcomdn = cmnd + varName
            lenght = str(len(endofcomdn))

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = 'MPX,00' + lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if PRINT == 'ON': print(' - INFO : sending command String', fullcommand)
            self.sock.send(fullcommand.encode('utf-8'))
            data = self.sock.recv(1024).decode('utf-8', 'ignore')
            if PRINT == 'ON': print(' - INFO : receiving', data)
            var = data.split(',')[4]
            res = 0 # int(data.split(',')[5])

            if res != 0:
                print(' - ERROR : Something has gone badly ')
                if res == 1: print(' - ERROR : The system is busy ')
                if res == 2: print(' - ERROR : The Command was not recognised ')
                if res == 3: print(' - ERROR : The Paramaeter was out of range ')
        return var

    def getArrayvar(self, varName, PRINT='OFF'):

        var = []

        if varName not in self.listofTCPvars:
            print(' - WARNING : You are asking for a variable that does not exist ...', varName)

        else:
            cmnd = ',GET,'
            endofcomdn = cmnd + varName
            lenght = str(len(endofcomdn))

            # Two zeros added because the string needs to be at least 15 char
            # if I don't do this the GAIN var fails
            fullcommand = 'MPX,00' + lenght + endofcomdn
            # 0000000026,GET,NUMFRAMESTOACQUIRE'
            if 'ON' in PRINT: print(' - INFO : sending command String', fullcommand)
            self.sock.send(fullcommand.encode('utf-8'))
            data = self.sock.recv(1024).decode('utf-8', 'ignore')
            if 'ON' in PRINT: print(' - INFO : receiving', data)
            pre_var = data.split(',')[4]

            for item in pre_var.split('   '):

                if item == '':
                    print(' continuing')

                else:

                    if '.' in item:
                        var.append(float(item))

                    else:
                        var.append(int(item))

            res = int(data.split(',')[5])

            if res != 0:
                print(' - ERROR : Something has gone badly ')
                if res == 1: print(' - ERROR : The system is busy ')
                if res == 2: print(' - ERROR : The Command was not recognised ')
                if res == 3: print(' - ERROR : The Paramaeter was out of range ')

        return var

    def getVariable(self, var, PRINT='OFF'):

        if var in self.listofstringvars:
            return self.getstringVariable(var, PRINT)

        elif var in self.listofArrayvars:
            return self.getArrayvar(var, PRINT)

        else:
            if (var in self.listofFloatVars) or (var in self.listofScientific) or (var in self.readonly):
                # print ' I AM GETTING HERE', var
                return self.getFloatNumericVariable(var, PRINT)

            else:
                # print ' BUT ALSO GETTING HERE ? ', var
                return self.getIntNumericVariable(var, PRINT)

    def setValue(self, varName, value):

        # sleep(1)
        str_value = str(value)

        if varName not in self.listofTCPvars:
            print(' - WARNING : You are asking to set a variable that does not exist ...', varName)

        else:

            if varName in self.readonly:
                print(' - WARNING :  The variable  ...', varName, ' is read only ')

            else:
                cmnd = ',SET,'
                endofcomdn = cmnd + varName + ',' + str_value
                lenght = str(len(endofcomdn))

                fullcommand = 'MPX,000' + lenght + endofcomdn
                # print ' - INFO : sending command ' , fullcommand

                self.sock.send(fullcommand.encode('utf-8'))
                print(' - INFO : sending command ', fullcommand)

                data = self.sock.recv(1024).decode('utf-8', 'ignore')
                print(' - INFO : receiving', data)

                res = 0 #int(data.split(',')[4])

                if res != 0:
                    print(' - ERROR : Something has gone badly ')
                    if res == 1: print(' - ERROR : The system is busy ')
                    if res == 2: print(' - ERROR : The Command was not recognised ')
                    if res == 3: print(' - ERROR : The Paramaeter was out of range ')

                else:
                    # IF proper value I update
                    if ('UseAcquisitionHeaders' not in varName) or 'FILECOUNTER' not in varName:
                        self.varsTCPcontrolled[varName] = self.getVariable(varName)

    def startAcq(self):

        fullcommand = 'MPX,21,CMD,STARTACQUISITION'
        self.sock.send(fullcommand.encode('utf-8'))
        # data = self.sock.recv(1024).decode('utf-8', 'ignore')
        # print(' - INFO : receiving', data)

    def MPX_CMD(self, type_cmd='GET', cmd='DETECTORSTATUS'):
        length = len(cmd)
        tmp = 'MPX,00000000' + str(length + 5) + ',' + type_cmd + ',' + cmd
        print(tmp)
        self.sock.send(tmp.encode('utf-8'))
        return

    #        tmp.encode()

    #    def startAcq_STEM(self):
    #
    ##        fullcommand = 'MPX,21,CMD,ScanStartRecord'
    #        fullcommand = 'MPX,21,CMD,SCANSTARTRECORD'
    #        print(fullcommand)
    #        self.sock.send(fullcommand.encode('utf-8'))
    #        #data = self.sock.recv(1024).decode('utf-8', 'ignore')
    #        #print(' - INFO : receiving', data)
    #
    def setup_4DSTEM(self, scan_size, counter_depth):

        self.setValue('TRIGGERSTART', 1)
        self.setValue('TRIGGERSTOP', 1)
        # print('TRIGGERSTART_STOP set to 1')

        self.setValue('CONTINUOUSRW', 1)
        # print('CONTINUOUSRW set to 1')

        self.setValue('NUMFRAMESTOACQUIRE', scan_size)
        # print('NUMFRAMESTOACQUIRE set to ', scan_size)

        self.setValue('NUMBERFRAMESPERTRIGGER', scan_size)
        # print('NUMBERFRAMESPERTRIGGER set to ', scan_size)

        self.setValue('COUNTERDEPTH', counter_depth)
        # print('COUNTERDEPTH set to ', counter_depth)

    def startDACScan(self):

        fullcommand = 'MPX,12,CMD,DACSCAN'
        self.sock.send(fullcommand.encode('utf-8'))
        data = self.sock.recv(1024).decode('utf-8', 'ignore')
        print(' - INFO : receiving', data)

    def readChipTempt(self):

        fullcommand = 'MPX,18,CMD,ReadChipTemps'
        self.sock.send(fullcommand.encode('utf-8'))
        data = self.sock.recv(1024).decode('utf-8', 'ignore')
        print(' - INFO : receiving', data)

    def imgacqStart(self, n_frames=1, acqTime=100.):

        self.setValue('NUMFRAMESTOACQUIRE', 1)

        # Setting variables
        var = 'ACQUISITIONTIME'
        val = acqTime
        self.setValue(var, val)

        self.startAcq()

    def setPixelFile(self, file_name):
        # file_name is full path and extension of pixel file
        endofcomdn = ',SET,PIXELMATRIXLoadFILE,' + file_name
        lenght = str(len(endofcomdn))

        fullcommand = 'MPX,000' + lenght + endofcomdn
        self.sock.send(fullcommand.encode('utf-8'))
        data = self.sock.recv(1024).decode('utf-8', 'ignore')
        print(' - INFO : receiving', data)

    def dacScan(self, Threshold, acqTime, ini, end, step, fname='default'):

        print(' - starting DAC scan ')
        # sleep(2)

        self.setValue('NUMFRAMESTOACQUIRE', 1)

        # Setting variables
        var = 'ACQUISITIONTIME'
        val = acqTime
        self.setValue(var, val)

        var = 'DACScanDAC'
        val = Threshold
        self.setValue(var, val)

        var = 'DACScanStart'
        val = ini
        self.setValue(var, val)

        var = 'DACScanStop'
        val = end
        self.setValue(var, val)

        var = 'DACScanStep'
        val = step
        self.setValue(var, val)

        # Only will enable
        if fname != 'default':
            var = 'FILEDIRECTORY'
            val = 'U:\QualityControl\\test'
            self.setValue(var, val)

            var = 'FILENAME'
            val = fname
            self.setValue(var, val)

        self.startDACScan()

    def getData(self, timeout=1400.0):  # timeout in millisecons

        # print ' - starting DAQ ', timeout
        # sleep(2)

        Tout = 1.2 * timeout / 1000.

        # interesting but there seems to be a limit
        # there in the 0.010 when I work on localhost
        # whne I work from Alcanyiz seems to be 5 s
        # s so I force it here

        # if Tout<15: Tout = 15

        self.q = Queue()
        self.sock.settimeout(timeout)

        Counter = 0
        # sleep(10)
        self.pseudoData = []

        total = ''
        # socket recieve
        Counter = 0
        self.ongoingAcquisition = True
        while self.ongoingAcquisition:

            ready = select.select([self.sock], [], [], Tout)  # timeout needs to be larger than frame time. I choose 2x

            if ready[0]:
                # there is data to be collected
                self.ongoingAcquisition = True
                try:
                    msg = self.sock.recv(1050000)  # 4096)#.decode('utf-8', 'ignore')
                # print ' Acquiring'

                except SocketError as e:
                    print('Something went wrong with data receiving')
                if msg:
                    # print msg
                    self.pseudoData.append(msg)
                    self.q.put(msg)

            else:
                # The system is no longer waiting for data
                self.ongoingAcquisition = False

        return

    def splitintoImages(self, DAC=-1):
        '''     This function treats the psudo data list,
                and splits it into a list of single images         '''

        first = True
        img_string = ""
        self.dataList = []
        dataList = []
        Counter = 0

        current_dac = DAC

        for piece in self.pseudoData:
            # print(piece)

            if b'' in piece: Counter += 1
            if (b"MPX" in piece):
                list = piece.split(b"MPX")
                if not first:
                    # print(' Entering here every time there is MPX (except the first) ')
                    img_string = img_string + list[0]
                    # print " *- ", img_string
                    dataList.append(img_string)

                    if len(list) > 1:
                        img_string = b"MPX" + list[1]
                    else:  # in the odd case that the string starts on MPX
                        img_string = b"MPX"

                else:
                    # print ' Entering here the firts time only '
                    img_string = piece
                    first = False

            # If there is No MPX I add to the img string
            else:
                img_string = img_string + piece

        # Filling in the last item
        dataList.append(img_string)

        # print ' Final list Length = ', len (self.dataList ), '     ',  Counter
        counter_dac = 0
        for i, item in enumerate(dataList):
            # Storing the header on a different Var
            if b'MQ1' not in item:
                print(" ********* ", item)
                if b'MPX' in item:
                    print(' ***   header *** ', list)
                    self.Header = item

                continue

            list = item.split(b'MQ1,')
            image = b"MQ1," + list[1]  # without the last character
            # testing how to decode this
            # print ' -  size ', sys.getsizeof(item)
            # print ' -  mibfile ', sys.getsizeof(image)
            if DAC > -1: current_dac = DAC + counter_dac

            headr_str = image[:768]
            test_headr = ImageHeader(headr_str, dac=current_dac)

            # bothe header information and image
            img_String = image[test_headr.params['Offset']:]

            tuple = (img_String, test_headr)
            # tuple = (np.fromstring(image[test_headr.params['Offset']:], dtype='>u2').reshape(test_headr.params['NpixX'],test_headr.params['NpixY']) , image[:768])
            self.dataList.append(tuple)
            # self.dataList.append(np.fromstring(image[test_headr.params['Offset']:], dtype='>u2').reshape(test_headr.params['NpixX'],test_headr.params['NpixY']))

            counter_dac += 1
        # return dataList


# print time()


if __name__ == '__main__':
    print(' - INFO :       ')
    print(" - INFO : -------------------------------- ")
    print(" - INFO :   A very simple example of       ")
    print(" - INFO :  Talking to Merlin via TCP/IP    ")
    print(" - INFO :  Remember to run the MERLIN      ")
    print(" - INFO :  Software on the target machine  ")
    print(" - INFO : -------------------------------- ")
    print(' - INFO :        ')
    headerRAW = 'MQ1,000001,00384,01,0256,0256,R64,   1x1,01,2018-01-02 15:55:15.323401,0.100000,0,0,0,,MQ1A,2018-01-02T15:55:15.323401404Z,100000000ns,12,'

    header = 'MQ1,000001,00384,01,0256,0256,U16,   1x1,01,2018-01-19 10:35:08.747484,0.010000,0,0,0,0.000000E+0,3.000000E+2,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,3RX,000,511,000,000,000,000,000,000,175,010,200,125,100,100,073,100,080,030,128,004,255,105,128,156,144,511,511,MQ1A,2018-01-19T10:35:08.747484663Z,10000000ns,12,   '
    header_lad = 'MQ1,000001,00768,04,1024,0256,U08,   Nx1,0F,2018-01-11 08:29:52.037681,0.100000,0,0,0,2.000000E+1,5.000000E+2,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,3RX,111,511,000,000,000,000,000,000,175,010,200,125,100,100,105,100,106,030,128,004,255,141,128,194,191,511,511,3RX,111,511,000,000,000,000,000,000,175,010,200,125,100,100,111,100,112,030,128,004,255,158,128,205,204,511,511,3RX,111,511,000,000,000,000,000,000,175,010,200,125,100,100,107,100,112,030,128,004,255,149,128,207,195,511,511,3RX,111,511,000,000,000,000,000,000,175,010,200,125,100,100,093,100,100,030,128,004,255,146,128,196,190,511,511,MQ1A,2018-01-11T08:29:52.037681781Z,100000000ns,6,'
    header_quad = 'MQ1,000001,00768,04,0512,0512,U32,   2x2,0F,2018-01-08 16:27:32.129847,0.100000,0,0,0,1.600000E+1,5.000000E+2,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,0.000000E+0,3RX,089,511,000,000,000,000,000,000,175,010,200,125,100,100,105,100,106,030,128,004,255,141,128,194,191,000,000,3RX,089,511,000,000,000,000,000,000,175,010,200,125,100,100,111,100,112,030,128,004,255,158,128,205,204,000,000,3RX,089,511,000,000,000,000,000,000,175,010,200,125,100,100,107,100,112,030,128,004,255,149,128,207,195,000,000,3RX,089,511,000,000,000,000,000,000,175,010,200,125,100,100,093,100,100,030,128,004,255,146,128,196,190,000,000,MQ1A,2018-01-08T16:27:32.129847918Z,100000000ns,24, '

    test_headr = ImageHeader(header_lad, dac=10)

    # Now testing new Var for toggling RAW
