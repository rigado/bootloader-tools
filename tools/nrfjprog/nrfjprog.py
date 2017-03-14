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

from utils import Utils
utils = Utils()

class Nrfjprog:
    def __getFamilyName(self, device):
        family = ''
        if device == 'NRF52832_XXAA':
            family = 'nrf52'
        elif device == 'NRF51822_XXAA':
            family = 'nrf51'
        elif device == 'MKW41Z512XXX4':
            family = 'kw41z'

        return family

    def __getNrfjprog(self):
        utils.log(utils.LOG_LEVEL_VERBOSE, "nrfjprog.__getNrfjprog")
        sys_type = platform.system()

        cmd = ""
        if(sys_type == "Linux"):
            #command to run, jlink must be in same directory
            is_64bits = sys.maxsize > 2**32
            if is_64bits:
                cmd = "../tools/nrfjprog/linux/x86_64/nrfjprog"
            else:
                cmd = "../tools/nrfjprog/linux/i386/nrfjprog"
            use_shell = True
        elif(sys_type == "Windows"):
            #command to run, jlink must be in same directory
            cmd = "..\\tools\\nrfjprog\\windows\\nrfjprog"
            use_shell = False
        elif(sys_type == "Darwin"):
            #command to run, jlink must be in same directory
            cmd = "../tools/nrfjprog/macos/nrfjprog"
            use_shell = True
        else:
            utils.errorHandler("Unknown system", self.cleanup)

        return (cmd, use_shell)

    def erase(self, device):
        utils.log(utils.LOG_LEVEL_VERBOSE, 'nrfjprog.erase')

        erase_args = '-f ' + self.__getFamilyName(device) + ' --recover'

        nrfjprog_tuple = self.__getNrfjprog()
        utils.log(utils.LOG_LEVEL_DEBUG, nrfjprog_tuple)

        cmd = nrfjprog_tuple[0] + " " + erase_args
        utils.log(utils.LOG_LEVEL_DEBUG, cmd)

        output = utils.runCommand(cmd, nrfjprog_tuple[1])

        utils.log(utils.LOG_LEVEL_VERBOSE, output)
        
        time.sleep(.5)

    def protect(self, device):
        utils.log(utils.LOG_LEVEL_VERBOSE, 'nrfjprog.protect')
        family = ''
        if device == 'NRF52832_XXAA':
            family = 'nrf52'
        elif device == 'NRF51822_XXAA':
            family = 'nrf51'

        protect_args = '-f ' + family + ' --rbp ALL'

        nrfjprog_tuple = self.__getNrfjprog()
        utils.log(utils.LOG_LEVEL_DEBUG, nrfjprog_tuple)

        cmd = nrfjprog_tuple[0] + " " + protect_args
        utils.log(utils.LOG_LEVEL_DEBUG, cmd)

        output = utils.runCommand(cmd, nrfjprog_tuple[1])

        utils.log(utils.LOG_LEVEL_VERBOSE, output)

    def reset(self, device):
        utils.log(utils.LOG_LEVEL_VERBOSE, 'nrfjprog.debugreset')

        family = self.__getFamilyName(device)
        if family == 'nrf51':
            reset_cmd = ' --reset'
        elif family == 'nrf52':
            reset_cmd = ' --debugreset'

        args = '-f ' + family + reset_cmd

        nrfjprog_tuple = self.__getNrfjprog()

        utils.log(utils.LOG_LEVEL_DEBUG, nrfjprog_tuple)

        cmd = nrfjprog_tuple[0] + " " + args
        utils.log(utils.LOG_LEVEL_DEBUG, cmd)

        output = utils.runCommand(cmd, nrfjprog_tuple[1])

        utils.log(utils.LOG_LEVEL_VERBOSE, output)

