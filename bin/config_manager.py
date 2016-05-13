#!/usr/bin/python3
import logging
import argparse
import configparser
import os
from socket import gethostname

###################################################################################
##### Script setup, arguments, configuration file, db connection and logging
##### Declare Local Variables
###################################################################################

argumentsParser = argparse.ArgumentParser( description='Manage application configurations without editing code' )
argumentsParser.add_argument( '-c', dest='configurationFile', action='store', help='Use this as the configuration file for this script' )
argumentsParser.add_argument( '-m', dest='action', action='store', default='install',
                                help='Mode, can be one of (i)nstall, (u)pgrade, (v)erify note: install is default')
argumentsParser.add_argument( '-d', dest='localconfigurationdictionary', action='store', 
                                help='INI file that contains values to be inserted into the final.ini file' )
argumentsParser.add_argument( '-s', dest='servername', default=gethostname(), help='The Machine name when update/insert/select from the DB' )
argumentsParser.add_argument( '-a', dest='applicationname', help='The Applicationname when update/insert/select from the DB' )

commandLineArguments = argumentsParser.parse_args()

# Convert short-hands to full name, and check only valid values are used
if commandLineArguments.action == 'u' or commandLineArguments.action == 'upgrade':
    commandLineArguments.action = 'upgrade'
elif commandLineArguments.action == 'i' or commandLineArguments.action == 'install':
    commandLineArguments.action = 'install'
elif commandLineArguments.action == 'v' or commandLineArguments.action == 'verify':
    commandLineArguments.action = 'verify'
else:
    print( 'Mode value passed is not valid' )
    argumentsParser.print_help() 
    exit(1)

# This value is just a set of key/values that will be used when creating the final.ini file.  The keys will match
#   THe names used in the ini file.  THE ini file section will match as well!


configurationFile = os.getcwd().replace( 'bin', 'etc' ) + '/' + __file__.replace( '.py', '.ini' )
if ( commandLineArguments.configurationFile ):
    configurationFile = commandLineArguments.configurationFile 
    print( configurationFile );

if ( not os.path.exists( configurationFile ) ):
    print( 'Unable to open configuration file: ' + configurationFile )

applicationConfiguration = configparser.ConfigParser()
applicationConfiguration.read( configurationFile )

loggingFile = os.getcwd().replace( 'bin', '' ) + applicationConfiguration.get( 'logging', 'destinationFile' )
logging.basicConfig(    filename = loggingFile,
                        level    = applicationConfiguration.get( 'logging', 'level' )
                        )
logging.info( 'Script Starting, running in mode: ' + commandLineArguments.action )
logging.debug( 'script servername is: ' + commandLineArguments.servername )
logging.debug( 'using the configuration file: ' + configurationFile )

###################################################################################
##### Main Logic
###################################################################################



# If run from the command line, we need: (argparse)
# username for changes example: (tslijboom)
# application_name              (tools--carrier-dmz)
# server_name                   (uname -n maybe enough?)
# custom_values_dict            dictionary of new values to set in this INI file,
#                               ( version2: --interactive terminal )
#   Should we get this dict from a seperate INI file?  YES!  It can be parsed from the
#   application and then ANY variables that exist in sample.ini, regardless of
#   a matching line in the DB.application_default_values table, then that value must come
#   from custom_values_dict.  If no such ini file exists to populate values for this particular
#   installation, then just ask for them from the terminal.
