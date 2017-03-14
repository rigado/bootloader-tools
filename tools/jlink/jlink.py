import os
import binascii
import sys
import platform
import subprocess
import re
import stat
import struct
import time

sys.path.append('../')
sys.path.append('../nrfjprog')

from utils import Utils
from nrfjprog import Nrfjprog

utils = Utils()
nrfjprog = Nrfjprog()

jlinkUICRFile = "uicr.bin"
jlinkMACFile = "mac.bin"
jlinkDatapageFile = "datapage.bin"
jlinkBlSettingsFile = 'blsettings.bin'
jlinkICFile = 'ic.bin'
jlinkICRevFile = 'icrev.bin'
jlinkScriptFile = 'jlink.script'
jlinkScriptReadMAC = 'jlink_scripts/jlink_readmacuicr.script'
jlinkScriptReadData = 'jlinkdata.script'

class JLink(object):
    def make_uicr_bin(self, device, bootloader_addr):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_uicr_bin")
        try:
            uicr = binascii.a2b_hex(bootloader_addr)[::-1]
            if device == "NRF52832_XXAA":
                uicr += binascii.a2b_hex('0007d000')[::-1]

            utils.log(utils.LOG_LEVEL_VERBOSE, "Write rigdfu2_uicr.bin")
            utils.deleteIfExists(jlinkUICRFile, self.cleanup)

            # create and write file
            fd = os.open(jlinkUICRFile, os.O_RDWR | os.O_CREAT)

            bin_size = 4
            if device == "NRF52832_XXAA":
                bin_size = 8

            if os.write(fd, bytes(uicr)) != bin_size:
                utils.errorHandler("Write error, wrote " + str(bytesWritten) + " expected 8", self.cleanup)

            # close file
            os.close(fd)
        except:
            utils.errorHandler('UICR binary creation failed!', self.cleanup)

    def make_bl_settings_bin(self, appSize):
        try:
            utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_bl_settings_bin")
            utils.deleteIfExists(jlinkBlSettingsFile, self.cleanup)
            fd = os.open(jlinkBlSettingsFile, os.O_CREAT | os.O_WRONLY)
            if(appSize > 0):
                os.write(fd, struct.pack('BBBB', 0x1, 0xFD, 0, 0))
            else:
                os.write(fd, struct.pack('BBBB', 0xFD, 0xFD, 0, 0))
            os.write(fd, struct.pack('i', appSize))
            for i in range(0, 4):
                os.write(fd, struct.pack('i', 0))
            os.close(fd)
        except:
            utils.errorHandler('Bootloader Settings binary creation failed!', self.cleanup)

        return True



    def make_mac_bin(self, macStr, device):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_mac_bin")
        mac = ''

        if macStr == None and (device == None or device == ''):
            utils.errorHandler("Cannot read MAC without knowing device!", self.cleanup)

        if macStr != None:
            utils.log(utils.LOG_LEVEL_VERBOSE, "Create mac from user input")
            #mac is stored little endian
            try:
                mac = binascii.a2b_hex(macStr)[::-1]
                utils.log(utils.LOG_LEVEL_DEBUG, str(mac))

                #output the mac to a binary file so we can write it from jlink to the UICR...
                utils.log(utils.LOG_LEVEL_VERBOSE, "Delete mac.bin")
                utils.deleteIfExists(jlinkMACFile, self.cleanup)

                #create and write file
                fd = os.open(jlinkMACFile,os.O_RDWR|os.O_CREAT)
                utils.log(utils.LOG_LEVEL_VERBOSE, "Write mac.bin")
                bytesWritten = os.write(fd,bytes(mac))

                if bytesWritten != 6:
                    utils.errorHandler("Write error, wrote " + str(bytesWritten) + " expected 6", self.cleanup)

                #close file
                utils.log(utils.LOG_LEVEL_VERBOSE, "Close mac.bin")
                os.close(fd)
            except:
                utils.errorHandler('MAC Parse Failed!', self.cleanup)
        else:
            utils.log(utils.LOG_LEVEL_VERBOSE, "Reading mac from nrf")
            #delete any old mac_save.bin files
            utils.log(utils.LOG_LEVEL_VERBOSE, "Delete mac.bin")
            utils.deleteIfExists(jlinkMACFile, self.cleanup)

            #ok read the mac out from the UICR and check that the output was generated
            self.__make_read_data_script(device, '0x10001080', '6', jlinkMACFile)
            if self.runJLink(jlinkScriptReadData) != True or os.path.exists(jlinkMACFile) != True:
                utils.errorHandler('Error reading MAC from UICR!', self.cleanup)

            #on osx and linux, jlinkexe creates files with no permissions; add them so we can open
            sys_type = platform.system()
            if(sys_type == "Darwin" or sys_type == "Linux"):
                os.chmod(jlinkMACFile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

            #open the generated file and read
            if os.stat(jlinkMACFile).st_size == 6:
                f = open(jlinkMACFile,'rb')
                mac = f.read()
                f.close()
            else:
                utils.errorHandler('Invalid size for MAC output file!', self.cleanup)

        return mac

    def make_datapage_bin(self, keyStr, device, macStr="unused"):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_datapage_bin")
        outFilelength = self.page_size
        writeOffset = self.write_offset
        utils.log(utils.LOG_LEVEL_VERBOSE, "Setup datapage address and offset")
        outFileData = []
        key = 0

        #save the file to disk
        try:
            if len(keyStr) > 0:
                utils.log(utils.LOG_LEVEL_VERBOSE, "Update datapage with user input key")
                key = binascii.a2b_hex(keyStr)
                outFileData += [0] * writeOffset
                outFileData += key

                if macStr != "unused":
                    mac = binascii.a2b_hex(macStr)[::-1]
                    outFileData += mac
                    outFileData += [0] * 10  # need to advance to next 16 byte-aligned address

                outFileData += [0] * (outFilelength - len(outFileData))

            #delete the old file
            utils.log(utils.LOG_LEVEL_VERBOSE, "Delete old datapage file")
            utils.deleteIfExists(jlinkDatapageFile, self.cleanup)

            #create and write file
            fd = os.open(jlinkDatapageFile,os.O_RDWR|os.O_CREAT)
            bytesWritten = os.write(fd,bytes(outFileData))

            #check everything was ok
            if(bytesWritten != outFilelength):
                utils.errorHandler("Write error, wrote " + str(bytesWritten) + " expected " + str(outFilelength), self.cleanup)
            else:
                os.close(fd)
                utils.log(utils.LOG_LEVEL_DEBUG, "Generated " + jlinkDatapageFile + " successfully!")
        except:
            utils.errorHandler("Filesystem error!", self.cleanup)

        if macStr == "unused":
            return key
        else:
            return (key, mac)



    def set_speed(self, speed):
        self.speed = speed

    def __make_read_data_script(self, device, address, size, binaryFileName):

        utils.deleteIfExists(jlinkScriptReadData, self.cleanup)

        jlink_file = open(jlinkScriptReadData, 'w')

        jlink_file.write('usb 0\nsi 1\nspeed {0}\n'.format(self.speed))
        jlink_file.write('device ' + device + '\n')
        jlink_file.write('r\ng\nsleep 200\n')
        jlink_file.write('savebin ' + binaryFileName + ' ' + address + ' ' + size + '\n')
        jlink_file.write('r\ng\nexit\n')
        jlink_file.close()

    def set_ic_address(self, address):
        self.ic_address = address

    def set_rev_address(self, address):
        self.rev_address = address

    def set_sd_address(self, address):
        self.sd_address = address

    def set_uicr_address(self, address):
        self.uicr_address = address

    def set_mac_address(self, address):
        self.mac_address = address

    def set_page_size(self, size):
        self.page_size = int(size, 16)

    def set_write_offset(self, offset):
        self.write_offset = int(offset, 16)

    def __check_clear_nrf52_readback_protect(self, device):

        self.__make_read_data_script(device, self.ic_address, '1', jlinkICFile)
        self.runJLink(jlinkScriptReadData)
        time.sleep(.125)

        if os.stat(jlinkICFile).st_size == 0:
            utils.log(1, 'Erasing nRF52 due to readback protection or other JLink error')
            nrfjprog.erase(device)
            time.sleep(.125)

        utils.deleteIfExists(jlinkICFile, self.cleanup)

    def read_ic_data(self, device):
        utils.deleteIfExists(jlinkICFile, self.cleanup)
        utils.deleteIfExists(jlinkICRevFile, self.cleanup)

        if device == 'NRF52832_XXAA':
            self.__check_clear_nrf52_readback_protect(device)
        
        self.__make_read_data_script(device, self.ic_address, '1', jlinkICFile)
        self.runJLink(jlinkScriptReadData)
        time.sleep(.125)
        
        self.__make_read_data_script(device, self.rev_address, '1', jlinkICRevFile)
        self.runJLink(jlinkScriptReadData)
        time.sleep(.125)
        
        ic = 0
        rev = 0
        
        if os.stat(jlinkICFile).st_size == 1:
            f = open(jlinkICFile,'rb')
            ic = f.read()
            f.close()    
        else:
            utils.errorHandler('Invalid size for IC data output file!', self.cleanup)
        
        if os.stat(jlinkICRevFile).st_size == 1:
            f = open(jlinkICFile,'rb')
            rev = f.read()
            f.close()
        else:
            utils.errorHandler('Invalid size for IC data output file!', self.cleanup)

        retic = ic[0]
        retrev = rev[0]

        return (retic, retrev)

    def make_script(self, device, softdevice, bootloader,
                    bootloader_addr, app_binary, app_address,
                    datapage_addr, blsettings_addr, disable_protect):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.make_script")
        utils.deleteIfExists(jlinkScriptFile, self.cleanup)

        jlink_file = open(jlinkScriptFile, 'w')

        utils.log(utils.LOG_LEVEL_VERBOSE, "Generate script setup for device " + device)

        jlink_file.write('usb 0\nsi 1\nspeed {0}\n'.format(self.speed))
        jlink_file.write('device {0}\n'.format(device))
        jlink_file.write('r\n')

        # jlink's erase command doesn't work on nrf devices, must write to registers
        if device in 'NRF52832_XXAA NRF51822_XXAA':
            jlink_file.write('w4 4001e504 2\nw4 4001e50c 1\nsleep 200\nr\n')
            jlink_file.write('w4 4001e504 1\n')

        else:
             jlink_file.write('erase\n')
             jlink_file.write('sleep 200\n')


        if len(softdevice) > 0:
            filename, extenstion = os.path.splitext(softdevice)
            if extenstion == '.hex':
                jlink_file.write('loadfile ' + softdevice + '\n')
                jlink_file.write('verifyfile ' + softdevice + '\n')
            else:
                jlink_file.write('loadbin ' + softdevice + ' ' + self.sd_address +'\n')
                jlink_file.write('verifybin ' + softdevice + ' ' + self.sd_address +'\n')

        if len(bootloader) > 0:
            filename, extenstion = os.path.splitext(bootloader)
            if extenstion == '.hex':
                jlink_file.write('loadfile ' + bootloader + '\n')
                jlink_file.write('verifyfile ' + bootloader + '\n')
            else:
                jlink_file.write('loadbin ' + bootloader + ' ' + bootloader_addr + '\n')
                jlink_file.write('verifybin ' + bootloader + ' ' + bootloader_addr + '\n')

                test_for_uicr_address = getattr(self, "uicr_address", "error")
                if test_for_uicr_address != "error":
                    jlink_file.write('loadbin ' + jlinkUICRFile +  ' ' + self.uicr_address +'\n')
                    jlink_file.write('verifybin ' + jlinkUICRFile + ' ' + self.uicr_address +'\n')

        test_for_mac_address = getattr(self, "mac_address", "error")
        if(test_for_mac_address != "error"):
            jlink_file.write('loadbin mac.bin ' + self.mac_address +'\n')
            jlink_file.write('verifybin mac.bin ' + self.mac_address +'\n')

        if app_binary != None:
            filename, extenstion = os.path.splitext(app_binary)
            if extenstion == '.hex':
                jlink_file.write('loadfile ' + app_binary + '\n')
                jlink_file.write('verifyfile ' + app_binary + '\n')
            else:
                jlink_file.write('loadbin ' + app_binary + ' ' + app_address + '\n')
                jlink_file.write('verifybin ' + app_binary + ' ' + app_address + '\n')
                
        jlink_file.write('loadbin ' + jlinkBlSettingsFile + ' ' + blsettings_addr + '\n')
        jlink_file.write('verifybin ' + jlinkBlSettingsFile + ' ' + blsettings_addr + '\n')

        jlink_file.write('loadbin datapage.bin ' + datapage_addr + '\n')
        jlink_file.write('verifybin datapage.bin ' + datapage_addr + '\n')
        jlink_file.write('exit\n')

        jlink_file.close()

        return jlinkScriptFile

    def cleanup(self):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.cleanup")
        utils.deleteIfExists(jlinkMACFile, None)
        utils.deleteIfExists(jlinkUICRFile, None)
        utils.deleteIfExists(jlinkDatapageFile, None)
        utils.deleteIfExists(jlinkScriptFile, None)
        utils.deleteIfExists(jlinkICFile, None)
        utils.deleteIfExists(jlinkICRevFile, None)
        utils.deleteIfExists(jlinkScriptReadData, None)
        utils.deleteIfExists(jlinkBlSettingsFile, None)

    def __getJLinkExe(self):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.__getJLinkExe")
        sys_type = platform.system()

        cmd = ""
        if(sys_type == "Linux"):
            #command to run, jlink must be in same directory
            is_64bits = sys.maxsize > 2**32
            if is_64bits:
                cmd = "../tools/jlink/linux/x86_64/JLinkExe"
            else:
                cmd = "../tools/jlink/linux/i386/JLinkExe"
            use_shell = True
        elif(sys_type == "Windows"):
            #command to run, jlink must be in same directory
            cmd = "..\\tools\\jlink\\windows\\jlink.exe"
            use_shell = False
        elif(sys_type == "Darwin"):
            #command to run, jlink must be in same directory
            cmd = "../tools/jlink/osx/JLinkExe"
            use_shell = True
        else:
            utils.errorHandler("Unknown system", self.cleanup)

        return (cmd, use_shell)

    #run Jlink.exe
    def runJLink(self, scriptFileName):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.runJLink")
        jlink_tuple = self.__getJLinkExe()

        cmd = jlink_tuple[0] + " " + scriptFileName

        output = utils.runCommand(cmd, jlink_tuple[1])

        #once we are done, parse the output
        result = self.__verifyJLinkOutput(output)

        return result

    #verify the output from the jlink script
    def __verifyJLinkOutput(self, jlinkoutput):
        utils.log(utils.LOG_LEVEL_VERBOSE, "jlink.__verifyJLinkOutput")
        result = False

        if len(jlinkoutput) != 0:

            verifyCount = 0
            saveCount = 0
            loadCount = 0
            errorCount = 0
            verifyOK = 0
            saveOK = 0
            loadOK = 0

            result = True

            lines = jlinkoutput.split("\n")
            for line in lines:
                utils.log(utils.LOG_LEVEL_DEBUG, ">>> " + str(line))

                #load
                if re.match("Writing bin data into target memory @ 0x[0-9a-fA-F]+\.", line):
                    loadCount+=1
                if re.match("Info: J-Link: Flash download: Flash programming performed for [1-9] range", line):
                    loadOK+=1

                #save
                if re.match("Opening binary file for writing\.\.\. \[.+\]", line):
                    saveCount+=1
                if re.match("Reading [0-9]+ bytes from addr 0x[0-9a-fA-F]+ into file\.\.\.O\.K\.", line):
                    saveOK+=1

                #verify
                if re.match("Reading [0-9]+ bytes data from target memory @ 0x[0-9a-fA-F]+\.", line):
                    verifyCount+=1
                if re.match("Verify successful", line):
                    verifyOK+=1

                #catch errors...
                if "error" in line.lower():
                    errorCount+=1

            if( verifyCount != verifyOK ):
                utils.log(utils.LOG_LEVEL_ERROR, "verifyJlinkOutput: verifybin error " + str(verifyOK) + "/" +str(verifyCount))
                result = False

            if( saveCount != saveOK ):
                utils.log(utils.LOG_LEVEL_ERROR, "verifyJlinkOutput: savebin error " + str(saveOK) + "/" +str(saveCount))
                result = False

            if( loadCount != loadOK ):
                utils.log(utils.LOG_LEVEL_ERROR, "verifyJlinkOutput: loadbin error " + str(loadOK) + "/" +str(loadCount))
                result = False

            if( errorCount != 0 ):
                utils.log(utils.LOG_LEVEL_ERROR, "verifyJlinkOutput: found errors " + str(errorCount))
                result = False

            if( verifyCount == 0 and saveCount == 0 and loadCount == 0 ):
                utils.log(utils.LOG_LEVEL_DEBUG, "verifyJlinkOutput: no operations")
                result = False

            if(result == True):
                utils.log(utils.LOG_LEVEL_DEBUG, "verifyJlinkOutput: success - load " + str(loadOK) + "/" +str(loadCount) + " verify " + str(verifyOK) + "/" +str(verifyCount) + " save " + str(saveOK) + "/" +str(saveCount))

        #todo verify the results
        return result
