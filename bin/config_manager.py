# ####################################################################
# 
#    CONFIG_MANAGER.PY
#
#    > Support: Tyler Slijboom
#    > Company: Blackberry
#    > Contact: tslijboom@juniper.net
#    > Version: 0.2.4
#    > Revision Date: 2015-05-30
#       
# ####################################################################
# ----------[ IMPORTS ]----------
import logging
import argparse
import configparser
import os
import sys
import config_manager_lib
import table_definitions
import getpass
import re
import jinja2

from socket import gethostname

###################################################################################
##### Script setup, arguments, configuration file, db connection and logging
##### Declare Local Variables
###################################################################################
###############
# command line arguments
argumentsParser = argparse.ArgumentParser( description='Manage application configurations without editing code' )
argumentsParser.add_argument( '-a', dest='applicationname', help='The Applicationname when update/insert/select from the DB' )
argumentsParser.add_argument( '-c', dest='configurationFile', action='store', help='Use this as the configuration file for this script' )
argumentsParser.add_argument( '-d', dest='localconfigurationdictionary', action='store',
                                help='INI file that contains values to be inserted into the final.ini file' )
argumentsParser.add_argument( '-i', dest='inputinifile', help='The current INI file of the application to be upgraded.  Only used for upgrades.' )
argumentsParser.add_argument( '-m', dest='action', action='store', default='upgrade',
                                help='Mode, can be one of (i)nstall, (u)pgrade, (v)erify note: install is default')
argumentsParser.add_argument( '-o', dest='outputinifile', help='The file to output the final INI file to' )
argumentsParser.add_argument( '-s', dest='servername', help='The Machine name when update/insert/select from the DB' )
argumentsParser.add_argument( '-t', dest='templateinifile', help='The template INI file used as the base for the application ini file' )

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
    sys.exit(1)


###############
# Local Variables

# This value is just a set of key/values that will be used when creating the final.ini file.  The keys will match
#   THe names used in the ini file.  THE ini file section will match as well!
iniValuesThatAreManuallySupplied = configparser.ConfigParser()
if commandLineArguments.localconfigurationdictionary:
    try:
        iniValuesThatAreManuallySupplied.read( commandLineArguments.localconfigurationdictionary )
    except:
        print( 'Failed to open file: ' + commandLineArguments.localconfigurationdictionary )
        sys.exit( 2 )

serverName = str(os.uname)
if commandLineArguments.servername:
    serverName = str(commandLineArguments.servername)

applicationName = str(os.getcwd())
#getpass.getuser()
if commandLineArguments.applicationname:
    applicationName = str(commandLineArguments.applicationname)

###############
# Internal configuration
configurationFile = os.getcwd().replace( 'bin', 'etc' ) + '/' + __file__.replace( '.py', '.ini' )
if ( commandLineArguments.configurationFile ):
    configurationFile = commandLineArguments.configurationFile
    print( configurationFile );

if ( not os.path.exists( configurationFile ) ):
    print( 'Unable to open configuration file: ' + configurationFile )

applicationConfiguration = configparser.ConfigParser()
applicationConfiguration.read( configurationFile )

###############
# Logging
loggingFile = os.getcwd().replace( 'bin', '' ) + applicationConfiguration.get( 'logging', 'destinationFile' )
logging.basicConfig(    filename = loggingFile,
                        level    = applicationConfiguration.get( 'logging', 'level' )
                        )
logging.info( '################################################################' )
logging.info( 'Script Starting, running in mode: ' + commandLineArguments.action )
if commandLineArguments.servername:
        logging.debug( 'script servername is: ' + commandLineArguments.servername )
logging.debug( 'using the configuration file: ' + configurationFile )
logging.debug( 'The APP and SERV names are: "' + applicationName + '" and "' + serverName + '" respectively' )


###############
# The DB connection
# See table_definitions.py

###################################################################################
##### Main Logic
###################################################################################


if commandLineArguments.action == 'upgrade':
    logging.info( 'Going to perform an upgrade' )
    # 1. Read in the current INI file for the running application
    #currentIniFile = applicationName.replace( 'bin', 'etc' ) + '/config_manager.ini'
    currentIniFile = applicationName.replace( 'bin', 'etc' ) + '/old_application_configuration.ini'
    if commandLineArguments.inputinifile:
        curentIniFile = commandLineArgments.inputinifile
    logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
    currentIniFileConfiguration = config_manager_lib.readInIniFile( currentIniFile )
    logging.debug( 'So I found these sections in the current.ini: ' + str( currentIniFileConfiguration.sections() ) )

    # 1.1 Read in iniValuesThatAreManuallySupplied, that was done at the agruments section at the top
    # 2. Read in the INI configuration of the DB
    #databaseCopyOfTheIni = readInDatabaseConfiguration( serverName, applicationName, dbConnectionHandle )
    databaseCopyOfTheIni = config_manager_lib.readInDatabaseConfiguration( serverName, applicationName )

    # 3. Read in the sample.INI file, iterate through it line by line 
    # 4. Using 1 and 2 and iniValuesThatAreManuallySupplied, create final.ini
    templateIniFile = os.getcwd().replace( 'bin', 'etc' )  + '/sample.ini'
    if commandLineArguments.templateinifile:
        templateIniFile = commandLineArguments.templateinifile
    logging.debug( 'Going to open the sample ini file: ' + templateIniFile )
    finalIniConfig = configparser.ConfigParser()
    finalIniFileOutput = """"""
    sampleIniFileHandle = open( templateIniFile, 'r' )
    currentSectionInTheFile = None
    for line in sampleIniFileHandle:
        # A comment line or whitespace only line
        if line[0:1] == '#' or line.isspace() or line == '\n':
            pass
        elif line[0:1] == '[':
            # have to trim off newline and ]
            logging.debug( 'Found section ' + line[1:-2] )
            finalIniConfig.add_section( line[1:-2] )
            currentSectionInTheFile = line[1:-2]
            finalIniFileOutput = finalIniFileOutput + '\n' + line
        else:
            # So this is a line of a field to be evaluated.  First, get the value name and then the verification Functions
            parsedListOfVerificationFunctions = []
            listOfValuePropertyFunctions = re.split( '[ \n]', line )   # temporary, used to build parsed version
            #listOfValuePropertyFunctions = line.split( ' ' )   # temporary, used to build parsed version
            logging.debug( 'THE LIST from the line     IS : ' + repr( listOfValuePropertyFunctions ) )
            #listOfValuePropertyFunctions.pop( -1 )  # remove the \n that comes from a line  # TEST IF A LAST LINE WITH NO \n fails here and inRange()
            logging.debug( 'THE LIST from the line becomes: ' + repr( listOfValuePropertyFunctions ) )
            equationBuffer = []
            for item in reversed( listOfValuePropertyFunctions ):
                logging.debug( '       all right so the ITEM is ' )
                logging.debug( item )
                if item == '\n' or len( item ) < 1 or repr( item ) == '':
                    logging.debug( 'skipped' )
                    continue
                logging.debug( 'Checking for config_manager_lib.' + str( item ) )
                if item in vars( config_manager_lib ):
                    logging.debug( '    it exists' )
                    if equationBuffer:
                        logging.debug( 'Found a function with additional parameters' )
                        parsedListOfVerificationFunctions.append( 'config_manager_lib.' + str( item ).replace( '\n', '' ) 
                            + '( {0}, ' + ','.join(equationBuffer) + ' )' ) 
                        
                        equationBuffer = []
                    else:
                        functionName = str( item ).replace( '\n', '' )
                        if functionName == 'isAlphaNumericString':
                            parsedListOfVerificationFunctions.append( 'config_manager_lib.' + functionName  + '( "{0}" )' ) 
                        else:
                            parsedListOfVerificationFunctions.append( 'config_manager_lib.' + functionName  + '( {0} )' ) 
                else:
                    logging.debug( '  added to equation buffer ' )
                    equationBuffer.append( str( item ) )

            fieldName = listOfValuePropertyFunctions.pop(0)
            logging.debug( 'The line is made up of these things: ' + '\n'.join(parsedListOfVerificationFunctions) + ' and the field is: ' + fieldName )

            # Now, source of this data ?  
            value = None
            try:
                value = iniValuesThatAreManuallySupplied.get( currentSectionInTheFile, fieldName ) 
            except:  #NoSectionError = not there
                try:
                    value = currentIniFileConfiguration.get( currentSectionInTheFile, fieldName)
                except:
		    # TODO: value = databasevalue()
                    # Okay, this has no value in the applications current INI file.
                    logging.error( 'We have an item (' + fieldName + ') that does not have a current configuration set for the application' )
                    sys.exit( 5 )

            # Now we have the value set, but does it pass all the verifcation functions?
            # THIS SHOULD BE WRAPPED UP IN A HELPER FUNCTION
            # HELPER FUNCTION
            valuePassedAllTestFunctions = True
            tempStringForFunctionDocumentation = """"""
            for testFunctionString in parsedListOfVerificationFunctions:
                logging.debug( 'Going to run:' + testFunctionString.format( value ) ) 
                logging.debug( eval( testFunctionString.format( value ) ) )
                if not eval( testFunctionString.format( value ) ):
                    print( 'Unable to verify ' + ' ' + testFunctionString.format( value ) )
                    logging.error( 'Unable to verify ' + value + ' ' + testFunctionString + ' for field ' + fieldName  )
                    valuePassedAllTestFunctions = False
                else:
                    logging.debug( 'The functionSTRING IS: ' + repr( re.split( '[(\.),]', testFunctionString ) ) )
                    testFunctionName                               = re.split( '[(\.),]', testFunctionString ).pop(1) 
                    testFunction = getattr( config_manager_lib, testFunctionName )
                    if testFunctionName == 'inRange':
                        logging.debug( 'NOW The functionSTRING IS: ' + repr( re.split( '[(\.),]', testFunctionString ) ) )
                        max = re.split( '[(\.),]', testFunctionString ).pop(4) 
                        min = re.split( '[(\.),]', testFunctionString ).pop(3) 
                        logging.debug( '     giving me max ' + max + ' and min ' + min ) 
                        docStringTemplate = jinja2.Template( testFunction.__doc__ )
                        tempStringForFunctionDocumentation = tempStringForFunctionDocumentation + ';' + docStringTemplate.render( minimumValue=min, maximumValue=max ) + '\n'
                    else:
                        tempStringForFunctionDocumentation = tempStringForFunctionDocumentation + ';' + testFunction.__doc__ + '\n'
                    finalIniConfig.set( currentSectionInTheFile, fieldName, value )
            # / HELPER FUNCTION


            if not valuePassedAllTestFunctions:
                # ALready printed error reason when it was discovered
                sys.exit( 6 )
            else:
                # All is good with this value
                finalIniFileOutput = finalIniFileOutput + tempStringForFunctionDocumentation + '\n' + fieldName + '=' + value + '\n'


    sampleIniFileHandle.close()

    # 4.5 write the final INI file
    finalIniFileDestination = applicationName.replace( 'bin', 'etc' ) + '/final.ini' 
    if commandLineArguments.outputinifile:
        finalIniFileDestination = commandLineArguments.outputinifile
    logging.info( 'FINAL Ini output file: ' + finalIniFileDestination )
    finalIniFileHandle = open( finalIniFileDestination, 'w' )

    # If we wanted a final output INI with NO comments, do this: #finalIniConfig.write( finalIniFileHandle )
    finalIniFileHandle.write( finalIniFileOutput )
    finalIniFileHandle.close()

    # 5. Update the DB with the current running INI
    config_manager_lib.updateDatabase( applicationName, serverName, finalIniConfig )


elif commandLineArguments.action == 'install':
    # 2. Read in the INI configuration of the DB
    # 3. Read in the sample.INI file
    # 4. Using 2 and iniValuesThatAreManuallySupplied, create final.ini
    # 5. Update the DB with the current running INI
    pass

elif commandLineArguments.action == 'verify':
    # 1. Read in the current INI file for the running application
    currentIniFile = applicationName.replace( 'bin', 'etc' ) + '/old_application_configuration.ini'
    if commandLineArguments.inputinifile:
        curentIniFile = commandLineArgments.inputinifile
    logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
    try:
        currentIniFileConfiguration = config_manager_lib.readInIniFile( currentIniFile )
    except:
        print( 'Failed to read in config file ' + currentIniFile )
        sys.exit( 7 )

elif commandLineArguments.action == 'sync':
    # 5. Update the DB with the current running INI
    currentIniFile = applicationName.replace( 'bin', 'etc' ) + '/old_application_configuration.ini'
    if commandLineArguments.inputinifile:
        curentIniFile = commandLineArgments.inputinifile
    logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
    try:
        currentIniFileConfiguration = config_manager_lib.readInIniFile( currentIniFile )
    except:
        print( 'Failed to read in config file ' + currentIniFile )
        sys.exit( 7 )

    config_manager_lib.updateDatabase( applicationName, serverName, currentIniFileConfiguration )

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

