# ####################################################################
# 
#    CONFIG_MANAGER.PY
#
#    > Support: Tyler Slijboom
#    > Company: Blackberry
#    > Contact: tslijboom@juniper.net
#    > Version: 0.2.8
#    > Revision Date: field will have to remain completely emptu:015-06-16
#       
# ####################################################################
# ----------[ IMPORTS ]----------
import logging
import ipaddress
import time
import argparse
import configparser
import os
import sys
import table_definitions
import getpass
import re
import jinja2
import inspect

from socket import gethostname
from config_manager_lib import *

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
argumentsParser.add_argument( '--test', action='store' )

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

serverName = str(os.uname().nodename)
if commandLineArguments.servername:
    serverName = str(commandLineArguments.servername)

#parse the application name from the CWD :  /home/username/WE_WANT_THIS_PART
applicationName = os.getcwd().split( '/' )[3]
if commandLineArguments.applicationname:
    applicationName = str(commandLineArguments.applicationname)

###############
# Internal configuration
configurationFile = os.getcwd().replace( 'bin', 'etc' ) + '/' + __file__.replace( '.py', '.ini' )
if ( commandLineArguments.configurationFile ):
    configurationFile = commandLineArguments.configurationFile

if ( not os.path.exists( configurationFile ) ):
    print( 'Unable to open configuration file: ' + configurationFile )

applicationConfiguration = configparser.ConfigParser()
applicationConfiguration.read( configurationFile )

###############
# Logging
loggingFile = applicationConfiguration.get( 'logging', 'destinationFile' )
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
##### Helper Functions
###################################################################################
def readInIniFile( iniFileLocation ):
    """  Read in an INI file and return a configparser object (which is like a namespace object) that has the sections
         Iterate through that object with the methods .sections() and getitems()
    """
    iniConfigurationSettings = configparser.ConfigParser()
    if not os.path.exists( iniFileLocation ):
        print( 'Unable to open INI file ' + iniFileLocation )
        sys.exit(3)
    try:
        iniConfigurationSettings.read( iniFileLocation )
    except Exception as errorEncountered:
        print( 'Failed to create ini File object' )
        print( str( errorEncountered ) )
        sys.exit(4)

    return iniConfigurationSettings


def readInDatabaseConfiguration( applicationName, serverName ):
    """  Get the database version of the configuration , return it as a configparser object """
    configurationItemsFromDB = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter( 
        table_definitions.currentConfigurationValues.server == serverName ).filter( 
        table_definitions.currentConfigurationValues.application == applicationName ).order_by( 
        table_definitions.currentConfigurationValues.ini_file_section )
    iniConfigurationSettings = configparser.ConfigParser()
    for row in configurationItemsFromDB:
        if not iniConfigurationSettings.has_section( row.ini_file_section ):
            iniConfigurationSettings.add_section( row.ini_file_section )
        iniConfigurationSettings.set( row.ini_file_section, row.ini_field_name, row.ini_value )

    return iniConfigurationSettings 



def updateDatabase( applicationName, serverName, finalIniConfig, signals_for_values_that_need_to_be_confirmed ):
    """ Iterate through a config parser object, and update the config manager database with the items inside.  """
    # Does there already exist such an object?  If so, delete them (because there may be items that changed)
    itemAlreadyInTheDBTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                                 table_definitions.currentConfigurationValues.server == serverName ).filter( 
                                 table_definitions.currentConfigurationValues.application == applicationName ).all()

    logging.debug( 'does this app/server combo already exists in the db? ' ) 
    if itemAlreadyInTheDBTest:
        logging.debug( 'yes it does , delete them!' )
        for row in itemAlreadyInTheDBTest:
            table_definitions.session.delete( row )

    table_definitions.session.flush()

    logging.debug( 'creating a list of SQLAlch objects to insert into the DB' )
    listOfDBConfigsToInsert = []
    for sectionName in finalIniConfig.sections():
        logging.debug( 'Okay, logging items in section: ' + sectionName )
        for configItem in finalIniConfig.items( sectionName ):
            logging.debug( 'Okay, logging item: ' + str( configItem ) )
            itemField = configItem[0]
            itemValue = configItem[1]
            configured_flag = signals_for_values_that_need_to_be_confirmed[  sectionName + itemField ]
            newConfigRow = table_definitions.currentConfigurationValues( server = serverName, application = applicationName,
                                                        ini_file_section = sectionName, ini_field_name = itemField, 
                                                        configured_by_user_flag = configured_flag, 
                                                        ini_value = itemValue, changed_by_user = 'tslijboom', 
                                                        changed_by_timestamp = time.time() )
            listOfDBConfigsToInsert.append( newConfigRow )
    
    table_definitions.session.add_all( listOfDBConfigsToInsert )
    table_definitions.session.commit()

def getDefaultValueFromDB( application, section, field):
    defaultValueRow = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                             table_definitions.applicationDefaultValues.application == applicationName ).filter(
                             table_definitions.applicationDefaultValues.ini_file_section == section ).filter(
                             table_definitions.applicationDefaultValues.ini_field_name == field ).first()
    if defaultValueRow:
        logging.debug( 'There is a DEFAULT value for: ' + applicationName + '::[' + section + ']::' + field + ' = ' + str( defaultValueRow.ini_value) )
        return defaultValueRow.ini_value
    logging.debug( 'No DEFAULT' )
    return None


""" ALPHA, NOT READY YET DO NOT TEST"""
def getFunctionDocumentationString( parsedListOfVerificationFunctions ):
    # Now we have the value set, but does it pass all the verifcation functions?
    tempStringForFunctionDocumentation = """"""
    for testFunctionString in parsedListOfVerificationFunctions:
            testFunctionName                               = re.split( '[(\.),]', testFunctionString ).pop(1) 
            if testFunctionName == 'inRange':
                max = re.split( '[(\.),]', testFunctionString ).pop(4) 
                min = re.split( '[(\.),]', testFunctionString ).pop(3) 
                docStringTemplate = jinja2.Template( testFunctionName.__doc__ )
                tempStringForFunctionDocumentation = tempStringForFunctionDocumentation + ';' + docStringTemplate.render( minimumValue=min, maximumValue=max ) + '\n'
            else:
                tempStringForFunctionDocumentation = tempStringForFunctionDocumentation + ';' + testFunctionName.__doc__ + '\n'

    return tempStringForFunctionDocumentation



def testConfigValueAgainstFunctions( value, parsedListOfVerificationFunctions ):
    """ Given a value and a list of strings to eval agains that value, return true or false if the value passes all the functions """
    """ This will take the output of getVariableNameAndVerificationFunctions( ) and test all functions against the value.  
        All passed returns True, otherwise False 
    """
    # Now we have the value set, but does it pass all the verifcation functions?
    valuePassedAllTestFunctions = True
    for testFunctionString in parsedListOfVerificationFunctions:
        try: 
            if not eval( testFunctionString.format( value ) ):
                #print( 'Unable to verify ' + ' ' + testFunctionString.format( value ) )
                valuePassedAllTestFunctions = False
                break
        except:
            valuePassedAllTestFunctions = False
            break

    if not valuePassedAllTestFunctions:
        # ALready printed error reason when it was discovered
        return False

    return True

            
def getVariableNameAndVerificationFunctions( lineFromTheFile ):
    """ Takes an input line from a sample.ini and extracts the variable name and verification questions """
    """ So the example level line below:
        [logging]
        level isAnInteger nextSampleFunctionName

        is extracted and comes back as:
        ( 'level', ( 'isAnInteger( "{0}" )', 'nextSampleFunctionName( "{0}" )' ) )
        This function is checking if correct number of arguments are given to a function.
        If there is a problem in arguments or function name it will return as
        ('level',[])
    """
    # Will build this and return it at the end
    parsedListOfVerificationFunctions = []  

    # temporary, used to build parsed version
    listOfValuePropertyFunctions = re.split( '[ \n]', lineFromTheFile )   
    logging.debug( '     The line is split into: ' + str(listOfValuePropertyFunctions) )

    equationBuffer = []  # Functions like inRange have other values to add, so put those in this temporary array while we extract

    for item in reversed( listOfValuePropertyFunctions ):
        if item == '\n' or len( item ) < 1 or repr( item ) == '':
            continue
        try:
            numberTest = int( item )
            equationBuffer.append( str( item ) )
            continue
        except ValueError:

            # This item is not an integer
            pass
        try:
            logging.debug( '     I think that "' + item + '" contains a function!' )
            eval( item )
            if equationBuffer:
                logging.debug( '     there are other arguments' )
                if(len(equationBuffer) > (len(inspect.getargspec(eval( item ))[0])-1)):
                    print("WARNING : Function arguments are more than expected. "+
                          "Skipping function.")
                    break
                if(len(equationBuffer) < (len(inspect.getargspec(eval( item ))[0])-1)):
                    print("WARNING : Function arguments are less than expected. "+
                          "Skipping function.")
                    break

                parsedListOfVerificationFunctions.append( str( item ).replace( '\n', '' )
                    + '( {0}, ' + ','.join(equationBuffer) + ' )' )

                equationBuffer = []
            else:
                logging.debug( '     {0} is the only argument ' )
                if((len(inspect.getargspec(eval( item ))[0])-1) > 1):
                    print("WARNING: No arguments provided to the function. "+
                          "Skipping function.")
                    break
                functionName = str( item ).replace( '\n', '' )
                if functionName == 'isAlphaNumericString':
                    parsedListOfVerificationFunctions.append( functionName  + '( "{0}" )' )
                else:
                    parsedListOfVerificationFunctions.append( functionName  + '( {0} )' )

        except Exception as errorEncountered:
            equationBuffer.append( str( item ) )

    fieldName = listOfValuePropertyFunctions.pop(0)
    return( fieldName, parsedListOfVerificationFunctions )

###################################################################################
##### Main Logic
###################################################################################

def main():
    if commandLineArguments.action == 'upgrade':
        logging.info( 'Going to perform an upgrade' )
        # 1. Read in the current INI file for the running application
        # I think this needs to be picked up another time and compared against the DB results.
        currentIniFile = os.getcwd().replace( 'bin', '' ) + '/etc/' + applicationName + '.ini'
        if commandLineArguments.inputinifile:
            curentIniFile = commandLineArgments.inputinifile
        logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
        currentIniFileConfiguration = None
        if os.path.exists( currentIniFile ):
            currentIniFileConfiguration = readInIniFile( currentIniFile )
            logging.debug( 'So I found these sections in the current.ini: ' + str( currentIniFileConfiguration.sections() ) )

        # 1.1 Read in iniValuesThatAreManuallySupplied, that was done at the agruments section at the top
        # 2. Read in the INI configuration of the DB
        #databaseCopyOfTheIni = readInDatabaseConfiguration( serverName, applicationName, dbConnectionHandle )
        databaseCopyOfTheIni = readInDatabaseConfiguration( applicationName, serverName )

        # 3. Read in the sample.INI file, iterate through it line by line 
        templateIniFile = None
        if 'etc' in os.getcwd():
            templateIniFile = os.getcwd()  + '/sample.ini'
        elif 'bin' in os.getcwd():
            templateIniFile = os.getcwd().replace( 'bin', '' )  + '/etc/sample.ini'

        if commandLineArguments.templateinifile:
            templateIniFile = commandLineArguments.templateinifile
        logging.debug( 'Going to open the template / sample ini file: ' + templateIniFile )
        finalIniConfig = configparser.ConfigParser()
        finalIniFileOutput = """"""
        sampleIniFileHandle = open( templateIniFile, 'r' )
        currentSectionInTheFile = None
        flag_that_the_item_is_properly_configured = {}
        ## create a list of SQLAlch objects
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
                ( fieldName, parsedListOfVerificationFunctions ) = getVariableNameAndVerificationFunctions( line )
                logging.debug( ' == fieldname: ' + fieldName + ' and ' + str( parsedListOfVerificationFunctions ) )

                # Now, source of this data ?  
                value = None
                try:
                    value = databaseCopyOfTheIni.get( currentSectionInTheFile, fieldName ) 
                    logging.debug( 'vvvvvalue comes from the database, (already configured)' )
                    flag_that_the_item_is_properly_configured[ (currentSectionInTheFile + fieldName).lower() ] = True
                except:  #NoSectionError = not there
                    try:
                        value = currentIniFileConfiguration.get( currentSectionInTheFile, fieldName)
                        # THERE SHOULD BE A WARNING BECAUSE THE DB does not have it, below is NOT that flag
                        logging.debug( 'vvvvvalue comes from the current configuration, (already configured)' )
                        flag_that_the_item_is_properly_configured[ (currentSectionInTheFile + fieldName).lower()  ] = True
                    except:
                        # Okay, this has no value in the applications current INI file, or the DB. 
                        # check if there is a default  -- THIS WILL INCLUDE VERSION LATER
                        logging.debug( 'no Current value or value in the DB, default exists?' )
                        defaultValue = getDefaultValueFromDB( applicationName, currentSectionInTheFile, fieldName )
                        if defaultValue is None:
                            logging.debug( 'Unable to find a value for item (' + fieldName + ') ')
                            # Value here coudl be the empty string but a valid value for the config,
                            finalIniConfig.set( currentSectionInTheFile, fieldName, '' )
                            # Flag that the INI Config is NOT ready to be written - unless forced?
                            flag_that_the_item_is_properly_configured[ (currentSectionInTheFile + fieldName).lower()  ] = False
                        else:
                            # default value could be '' that could be a valid value 
                            value = defaultValue
                            logging.debug( 'vvvvvalue comes from the DEFAULT db ' )
                            flag_that_the_item_is_properly_configured[ (currentSectionInTheFile + fieldName).lower()  ] = True

            
                logging.debug( currentSectionInTheFile + '::' + fieldName + ' with value "' + str( value ) + '"' )
                if testConfigValueAgainstFunctions( value, parsedListOfVerificationFunctions ):
                    logging.debug( 'Passed sample.ini field restrictions' )
                    if value == None:
                        value = ''
                    finalIniConfig.set( currentSectionInTheFile, fieldName, value )
                else:
                    logging.debug( 'Failed sample.ini field restrictions' )
                    if value == None:
                        value = ''
                    finalIniConfig.set( currentSectionInTheFile, fieldName, value )
                    # Need to write the item as NOT CONFIGURED FAILED TO CONFIGURE


        sampleIniFileHandle.close()

        # Now, is the final INI section fill?  Valid?  Can the final INI be written?

        # 5. Update the DB with the current running INI
        logging.debug( 'Okay so the FINAL ini configparser object is: ' + str( finalIniConfig ) )
        logging.debug( 'And the hash is: ' + str( flag_that_the_item_is_properly_configured ) )
        updateDatabase( applicationName, serverName, finalIniConfig, flag_that_the_item_is_properly_configured )

        # 4.5 write the final INI file
        finalIniFileDestination = applicationName.replace( 'bin', '' ) + '/etc/' + applicationName + '.ini' 
        if commandLineArguments.outputinifile:
            finalIniFileDestination = commandLineArguments.outputinifile
        #logging.info( 'FINAL Ini output file: ' + finalIniFileDestination )
        # If we wanted a final output INI with NO comments, do this: #finalIniConfig.write( finalIniFileHandle )
        #finalIniFileHandle = open( finalIniFileDestination, 'w' )
        #finalIniFileHandle.write( finalIniFileOutput )
        #finalIniFileHandle.close()



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
            currentIniFileConfiguration = readInIniFile( currentIniFile )
        except:
            print( 'Failed to read in config file ' + currentIniFile )
            sys.exit( 7 )

    elif commandLineArguments.action == 'sync':
        # 5. Update the DB with the current running INI
        currentIniFile = os.getcwd().replace( 'bin', 'etc' ) + '/' + applicationName + '.ini'
        if commandLineArguments.inputinifile:
            curentIniFile = commandLineArgments.inputinifile
        logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
        try:
            currentIniFileConfiguration = readInIniFile( currentIniFile )
        except:
            print( 'Failed to read in config file ' + currentIniFile )
            sys.exit( 7 )

        updateDatabase( applicationName, serverName, currentIniFileConfiguration )

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


if __name__ == '__main__': 
    main()
