# ####################################################################
# 
#    CONFIG_MANAGER.PY
#
#    > Support: Tyler Slijboom
#    > Company: Blackberry
#    > Contact: tslijboom@juniper.net
#    > Version: 0.4.2
#    > Revision Date: 2016-07-22
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

logging.basicConfig( level = logging.INFO)

###################################################################################
##### Helper Functions
###################################################################################
def readInSampleIni( iniFileLocation ):
    """  Read in an INI file and return a dictionary of dictionaries that map the following:
         ini_file_section -> ini_value -> rest of the line
         Iterate through that object with the methods .sections() and getitems()
    """
    if not os.path.exists( iniFileLocation ):
        print( 'Unable to open INI file ' + iniFileLocation )
        sys.exit(3)
     
    logging.debug( 'readinSampleIni() with: ' + iniFileLocation )
    sampleIniFileHandle = open( iniFileLocation , 'r' )
    #returnDictionary        = { 'dank' : { 'internet' :'memes' } }
    returnDictionary        = dict()
    currentSectionInTheFile = None
    currentFieldName        = None
    for line in sampleIniFileHandle:
        # A comment line or whitespace only line
        if line[0:1] == '#' or line[0:1] == ';' or line.isspace() or line == '\n':
            pass
        elif line[0:1] == '[':
            # have to trim off newline and ]
            logging.debug( 'Found section ' + line[1:-2] )
            currentSectionInTheFile = line[1:-2]
        else: 
            # So this is a line of a field to be evaluated.  get the value name and then the verification Functions
            ( fieldName, parsedListOfVerificationFunctions ) = getVariableNameAndVerificationFunctions( line )
            if currentSectionInTheFile in returnDictionary:
                returnDictionary[ currentSectionInTheFile ][ fieldName ] = parsedListOfVerificationFunctions 
            else:
                tempDictionary = dict()
                tempDictionary[ fieldName ] = parsedListOfVerificationFunctions 
                returnDictionary[ currentSectionInTheFile ] = tempDictionary
                
    logging.debug( ' =|=|= okay real news: we have a dictionary of dictionaries and it looks like: ' + str( returnDictionary ) )
    return returnDictionary
                
                


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


def readInDatabaseConfigurationAsA2dDictionary( applicationName, serverName, version ):
    """  Get the database version of the configuration , return it as a 2d dictionary 
        section  ->  fieldname  -> value
    """
    logging.debug( 'readInDatabaseConfigurationAsA2dDictionary()' + applicationName + serverName )
    configurationItemsFromDB = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter( 
        table_definitions.currentConfigurationValues.server == serverName ).filter( 
        table_definitions.currentConfigurationValues.application_version == version ).filter( 
        table_definitions.currentConfigurationValues.application == applicationName ).order_by( 
        table_definitions.currentConfigurationValues.ini_file_section )
    returnDictionary = dict()
    for row in configurationItemsFromDB:
        if not row.ini_file_section in returnDictionary:
            #returnDictionary[ row.ini_file_section ] = { row.ini_field_name : row.ini_value }
            returnDictionary[ row.ini_file_section ] = { row.ini_field_name : row }
        else: 
            #returnDictionary[ row.ini_file_section ][ row.ini_field_name ] = row.ini_value
            returnDictionary[ row.ini_file_section ][ row.ini_field_name ] = row
    logging.debug( 'so returning: ' + str( returnDictionary ) )
    return returnDictionary


## DEPRECATED
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



def updateeDatabase( listOfSQLAlchemyObjects ):
    """ Iterate through a list of SQL Alchemy Objects that contain the data """
    # start by flushing what is already in the DB for the server/app combo
    #  No, some of these are from the DB so do nothing of the sort!!
    table_definitions.session.flush()
    table_definitions.session.add_all( listOfSQLAlchemyObjects )
    table_definitions.session.commit()

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
                                                        application_version = applicationVersion,
                                                        ini_value = itemValue, changed_by_user = 'tslijboom', 
                                                        changed_by_timestamp = time.time() )
            listOfDBConfigsToInsert.append( newConfigRow )
    
    table_definitions.session.add_all( listOfDBConfigsToInsert )
    table_definitions.session.commit()

def getDefaultValueFromDB( application, section, field, version ):
    defaultValueRow = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                             table_definitions.applicationDefaultValues.application == applicationName ).filter(
                             table_definitions.applicationDefaultValues.ini_file_section == section ).filter(
                             table_definitions.applicationDefaultValues.application_version == version ).filter(
                             table_definitions.applicationDefaultValues.ini_field_name == field ).first()
    if defaultValueRow:
        logging.debug( 'There is a DEFAULT value for: ' + applicationName + '::[' + section + ']::' + field + ' = ' + str( defaultValueRow.ini_value) )
        return defaultValueRow.ini_value
    logging.debug( 'No DEFAULT' )
    return None


"""
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
"""


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
                    # But what if the function can take any number of arguements?  ie selectFromList then we are fine
                    if ( inspect.getargspec(eval( item ))[1]) :  #varargs
                        pass
                    else:
                        print("WARNING : Function " + item + " arguments are more than expected. Skipping function.")
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
    ###################################################################################
    ##### Script setup, arguments, configuration file, db connection and logging
    ##### Declare Local Variables
    ###################################################################################
    ###############
    # command line arguments
    argumentsParser = argparse.ArgumentParser( description='Manage application configurations without editing code' )
    argumentsParser.add_argument( '-a', dest='applicationname', help='The Applicationname when update/insert/select from the DB' )
    argumentsParser.add_argument( '-c', dest='configurationFile', action='store', help='Use this as the configuration file for this script' )
    # This is not used
    argumentsParser.add_argument( '-d', dest='localconfigurationdictionary', action='store',
                                    help='INI file that contains values to be inserted into the final.ini file' )
    argumentsParser.add_argument( '-i', dest='inputinifile', help='The current INI file of the application to be upgraded.  Only used for upgrades.' )
    argumentsParser.add_argument( '-m', dest='action', action='store', default='upgrade',
                                    help='Mode, can be one of (i)nstall, (u)pgrade, (v)erify note: install is default')
    argumentsParser.add_argument( '-o', dest='outputinifile', help='The file to output the final INI file to' )
    argumentsParser.add_argument( '-v', dest='version', help='The version of the application that you are managing' )
    argumentsParser.add_argument( '-s', dest='servername', help='The Machine name when update/insert/select from the DB' )
    argumentsParser.add_argument( '-t', dest='templateinifile', help='The template INI file used as the base for the application ini file.  Often referred to as sample.ini' )
    argumentsParser.add_argument( '-f', dest='homefolder', action='store', help='This is the root folder for all application files.  It is assumed that etc/ exists in here' )
    argumentsParser.add_argument( '--test', action='store' )

    commandLineArguments = argumentsParser.parse_args( sys.argv )

    # Convert short-hands to full name, and check only valid values are used
    if commandLineArguments.action == 'u' or commandLineArguments.action == 'upgrade':
        commandLineArguments.action = 'upgrade'
    elif commandLineArguments.action == 'i' or commandLineArguments.action == 'install':
        commandLineArguments.action = 'install'
    elif commandLineArguments.action == 'v' or commandLineArguments.action == 'verify':
        commandLineArguments.action = 'verify'
    elif commandLineArguments.action == 's' or commandLineArguments.action == 'sync':
        commandLineArguments.action = 'sync'
    elif commandLineArguments.action == 'd' or commandLineArguments.action == 'setdefaults':
        commandLineArguments.action = 'setdefaults'
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

    #parse the application name from the CWD :  /home/WE_WANT_THIS_PART
    if commandLineArguments.applicationname:
        applicationName = str(commandLineArguments.applicationname)
    elif commandLineArguments.homefolder:
        try:
            applicationName = commandlineArguments.homefolder.split( '/' )[2]
        except:
            print( 'Failed to get the application name from ' + commandLineArguments.homefolder )
    else:
        try:
            applicationName = os.getcwd().split( '/' )[2]
        except:
            print( 'Failed to get the application name from CWD' )

    # this is the basis for finding files on the system, of the format /home/<applicationname> but can be other.
    #  Assuming that /etc exsits in that folder with relevant files.
    application_home_folder = None
    if commandLineArguments.homefolder:
        application_home_folder = commandLineArguments.homefolder
        logging.debug( '  -1-1-1-1-1 the character is: ' + application_home_folder[:-1] )
        if application_home_folder[:-1] != '/': 
            application_home_folder = application_home_folder + '/'
        application_home_folder = commandLineArguments.homefolder
    else:
        application_home_folder = '/home/' + applicationName + '/'

    applicationVersion = None
    if commandLineArguments.version:
        applicationVersion = commandLineArguments.version
    else:
        applicationVersionObj = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter( 
            table_definitions.currentConfigurationValues.server == serverName ).filter( 
            table_definitions.currentConfigurationValues.application == applicationName ).order_by( 
            table_definitions.currentConfigurationValues.application_version ).first()
        if not applicationVersionObj:
            logging.warn( 'No version for the application found.  Therefore starting at the beginning with 1.0.0' )
            applicationVersion = '1.0.0'
        else:
            applicationVersion = applicationVersionObj.application_version    

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
    logging.basicConfig(    filename = applicationConfiguration.get( 'logging', 'destinationFile' ),
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

    if commandLineArguments.action == 'upgrade':
        logging.info( 'Going to perform an upgrade' )
        # 1. Read in the current INI file for the running application
        # I think this needs to be picked up another time and compared against the DB results.
        currentIniFile = application_home_folder + '/etc/' + applicationName + '.ini'
        if commandLineArguments.inputinifile:
            curentIniFile = commandLineArguments.inputinifile
        logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
        print( 'Going to open the current application ini file which is: ' + currentIniFile )
        currentIniFileConfiguration = None
        if os.path.exists( currentIniFile ):
            currentIniFileConfiguration = readInIniFile( currentIniFile )
            logging.debug( 'So I found these sections in the current.ini: ' + str( currentIniFileConfiguration.sections() ) )

        # 1.1 Read in iniValuesThatAreManuallySupplied, that was done at the agruments section at the top
        # 2. Read in the INI configuration of the DB
        #databaseCopyOfTheIni = readInDatabaseConfiguration( serverName, applicationName, dbConnectionHandle )
        #databaseCopyOfTheIni = readInDatabaseConfiguration( applicationName, serverName )
        databaseCopyOfTheIni = readInDatabaseConfigurationAsA2dDictionary( applicationName, serverName, applicationVersion )

        # 3. Read in the sample.INI file, iterate through it line by line 
        templateIniFile = None
        if commandLineArguments.templateinifile:
            templateIniFile = commandLineArguments.templateinifile
        else:
            templateIniFile = application_home_folder + '/etc/sample.ini' 
            if not os.path.exists( templateIniFile ):
                templateIniFile = application_home_folder + '/etc/' + applicationName + '.sample.ini' 
                if not os.path.exists( templateIniFile ):
                    print( 'no sir, unable to find sample.ini in ' + application_home_folder )
                    exit(9) 
        logging.debug( 'Going to open the template / sample ini file: ' + templateIniFile )

        #finalIniConfig = configparser.ConfigParser()   #remove me
        finalIniFileOutput                          = """"""  # still not populated
        listOfSQLAlchemyObjects                     = []  # table_definitions.currentConfigurationValues
        currentObjectToInsert                       = None           
        sampleIniFileDictionary                     = readInSampleIni( templateIniFile )
        #flag_that_the_item_is_properly_configured   = {}  #remove me
        ### TODO:  This loop has to go back to opening the file and reading line by line to pass through any documentation
        ###       from the file that has to go into the next one ie. lines starting with '#' or ';'
        ###
        for currentSection, fieldNamesAndVerificationFunctionPairs in sampleIniFileDictionary.items():
            for fieldName, verificationFunctions in fieldNamesAndVerificationFunctionPairs.items():
                # Now, find the source of this data
                value = None
                try: 
                    sqlRow = databaseCopyOfTheIni[ currentSection ][ fieldName ]
                    logging.debug( 'vvvvvalue comes from the database, already configured:::' + str(sqlRow) )
                    currentObjectToInsert = sqlRow
                except KeyError:  
                    try:
                        value = currentIniFileConfiguration.get( currentSection, fieldName)
                        # THERE SHOULD BE A WARNING BECAUSE THE DB does not have it, below is NOT that flag
                        logging.debug( 'vvvvvalue comes from the current configuration, (already configured)' )
                        logging.warn( currentSection + '::' + fieldName + ' is set on the machine, but it is not in the database' )
                        logging.info( currentSection + '::' + fieldName + ' will be added to the DB' )
                        currentObjectToInsert = table_definitions.currentConfigurationValues( 
                            server                  = serverName, 
                            application             = applicationName,
                            ini_file_section        = currentSection, 
                            ini_field_name          = fieldName,
                            configured_by_user_flag = 't',
                            application_version     = applicationVersion,
                            ini_value               = value, 
                            changed_by_user         = 'tslijboom',
                            changed_by_timestamp    = time.time() )

                    except:
                        # Okay, this has no value in the applications current INI file, or the DB. 
                        # check if there is a default 
                        logging.debug( 'no Current value or value in the DB, default exists?' )
                        defaultValue = getDefaultValueFromDB( applicationName, currentSection, fieldName, applicationVersion )
                        if not defaultValue is None:
                            logging.debug( 'vvvvvalue comes from the DEFAULT db ' )
                            # APPEND TO THE LIST, NO NEED TO VERIFY ASSUMED IT IS OKAY
                            currentObjectToInsert = table_definitions.currentConfigurationValues( 
                                server                  = serverName, 
                                application             = applicationName,
                                ini_file_section        = currentSection, 
                                ini_field_name          = fieldName,
                                configured_by_user_flag = 't',
                                application_version     = applicationVersion,
                                ini_value               = defaultValue, 
                                changed_by_user         = 'tslijboom',
                                changed_by_timestamp    = time.time() )
                        else:
                            currentObjectToInsert = table_definitions.currentConfigurationValues( 
                                server                  = serverName, 
                                application             = applicationName,
                                ini_file_section        = currentSection, 
                                ini_field_name          = fieldName,
                                configured_by_user_flag = 't',
                                application_version     = applicationVersion,
                                ini_value               = defaultValue, 
                                changed_by_user         = 'tslijboom',
                                changed_by_timestamp    = time.time() )
                         
            
                logging.debug( currentSection + '::' + fieldName + ' with value "' + str( value ) + '"' )
                # now we have a value, test it against the functions listed in the sample ini file

                if currentObjectToInsert.ini_value == None or currentObjectToInsert.ini_value == '':
                    currentObjectToInsert.ini_value = ''
                    if 'canBeNull' in str( verificationFunctions ):
                        currentObjectToInsert.configured_by_user_flag = 't'
                        listOfSQLAlchemyObjects.append( currentObjectToInsert )
                    else:
                        currentObjectToInsert.configured_by_user_flag = 'f'
                        listOfSQLAlchemyObjects.append( currentObjectToInsert )
                elif testConfigValueAgainstFunctions( currentObjectToInsert.ini_value, verificationFunctions ):
                    logging.info( 'Passed sample.ini field restrictions' )
                    currentObjectToInsert.configured_by_user_flag = 't'
                    listOfSQLAlchemyObjects.append( currentObjectToInsert )
                else:
                    logging.debug( 'Failed sample.ini field restrictions' )
                    currentObjectToInsert.configured_by_user_flag = 'f'
                    listOfSQLAlchemyObjects.append( currentObjectToInsert )


        # 5. Update the DB with the current running INI
        logging.debug( 'All configuration items have been iterated through' )
        #updateDatabase( applicationName, serverName, finalIniConfig, flag_that_the_item_is_properly_configured )
        updateeDatabase( listOfSQLAlchemyObjects )

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
            curentIniFile = commandLineArguments.inputinifile
        logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
        try:
            currentIniFileConfiguration = readInIniFile( currentIniFile )
        except:
            print( 'Failed to read in config file ' + currentIniFile )
            sys.exit( 7 )

    elif commandLineArguments.action == 'setdefaults':
        # 5. Update the DB with the current running INI
        currentIniFile = application_home_folder + '/etc/' + applicationName + '.ini'
        if commandLineArguments.inputinifile:
            currentIniFile = commandLineArguments.inputinifile
        logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
        try:
            currentIniFileConfiguration = readInIniFile( currentIniFile )
        except:
            print( 'Failed to read in config file ' + currentIniFile )
            sys.exit( 7 )
        # iterate through the config items, and create a list of SQLAlchemy objects that hold all the information
        listOfConfigurationItems = []
        for sectionName in currentIniFileConfiguration.sections():
            for configItem in currentIniFileConfiguration.items( sectionName ):
                itemField = configItem[0]
                itemValue = configItem[1]
                currentDefaultRow = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                    table_definitions.applicationDefaultValues.application == applicationName ).filter(
                    table_definitions.applicationDefaultValues.ini_file_section == sectionName ).filter(
                    table_definitions.applicationDefaultValues.application_version == applicationVersion ).filter(
                    table_definitions.applicationDefaultValues.ini_field_name == itemField ).first()
 
                if currentDefaultRow:
                    listOfConfigurationItems.append( currentDefaultRow )
                else:
                    newDefaultRow = table_definitions.applicationDefaultValues( application = applicationName,
                                                        ini_file_section = sectionName, ini_field_name = itemField, 
                                                        application_version = applicationVersion,
                                                        ini_value = itemValue, changed_by_user = 'tslijboom', 
                                                        changed_by_timestamp = time.time() )
                    listOfConfigurationItems.append( newDefaultRow )
    
        table_definitions.session.add_all( listOfConfigurationItems )
        table_definitions.session.commit()

 
    elif commandLineArguments.action == 'sync':
        # 5. Update the DB with the current running INI
        currentIniFile = application_home_folder + '/etc/' + applicationName + '.ini'
        if commandLineArguments.inputinifile:
            currentIniFile = commandLineArguments.inputinifile
        logging.debug( 'Going to open the current application ini file which is: ' + currentIniFile )
        listOfConfigurationItemsForTheDB = []
        listOfConfigurationItemsToDeleteFromTheDB = []
        configParserOfItemsMissingFromTheDB = []
        try:
            currentIniFileConfiguration = readInIniFile( currentIniFile )

            #########
            # Does the item already exist is the DB?
            testForApplicationInTheDB = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                table_definitions.currentConfigurationValues.application         == applicationName ).filter(
                table_definitions.currentConfigurationValues.application_version == applicationVersion ).filter(
                table_definitions.currentConfigurationValues.server              == serverName ).order_by(
                table_definitions.currentConfigurationValues.ini_file_section ).all()

            if testForApplicationInTheDB:
                ## We have to update these items and update the DB
                # iterate through the B items and update them as needed.
                configurationItemsFound = configparser.ConfigParser()
                for dbItem in testForApplicationInTheDB:
                    # find the item in the current confitg
                    try: 
                        print( ' Iam llooking for the value of ' + dbItem.ini_file_section + '::' + dbItem.ini_field_name )
                        fileValue = currentIniFileConfiguration.get( dbItem.ini_file_section, dbItem.ini_field_name )
                        if ( fileValue != dbItem.ini_value ):
                            dbItem.ini_value = fileValue
                            listOfConfiguratinItemsForTheDB.append( dbItem )
                            if not configurationItemsFound.has_section( dbItem.ini_file_section ):
                                configurationItemsFound.add_section( dbItem.ini_file_section )
                                print( 'i am adding section: ' + dbItem.ini_file_section )
                            print( 'i am adding field: ' + dbItem.ini_field_name + ' and value: ' + dbItem.ini_value + ' in section: ' + dbItem.ini_file_section )
                            configurationItemsFound.set( dbItem.ini_file_section, dbItem.ini_field_name, dbItem.ini_value )
                        else:
                            # No change, so do nothing
                            pass
                    except:
                        # NoSectionError or NoIndex error, which means the DB has a vlue that the current file does not.  
                        logging.warn( 'DB contains an item that is not in the file.    Removing it.  Section: ' + dbItem.ini_file_section + ' FieldName: ' 
                            + dbItem.ini_field_name + ' Value: ' + dbItem.ini_value )
                        listOfConfigurationItemsToDeleteFromTheDB.append( dbItem )
                
                # Now that we iterated through the DB items found, we have to check for ConfigIniItems that were not in the DB
                for sectionName in currentIniFileConfiguration.sections():
                    for field in currentIniFileConfiguration.items( sectionName ):
                        if configurationItemsFound.has_option( sectionName, field ):
                            pass
                        else:
                            newConfigurationRow = table_definitions.currentConfigurationValues( application = applicationName,
                                ini_file_section = sectionName, ini_field_name = field,
                                application_version = applicationVersion, server = serverName,
                                ini_value = configurationItemsFound.get( sectionName, field ),
                                changed_by_user = 'tslijboom', changed_by_timestamp = time.time() )
                            listOfConfigurationItemsForTheDB.append( newConfigurationRow )


            else:
                ## No current entries in the DB, so just add new SQLAlchemy objects to insert them
                for sectionName in currentIniFileConfiguration.sections():
                    for configItem in currentIniFileConfiguration.items( sectionName ):
                        itemField = configItem[0]
                        itemValue = configItem[1]
                        newConfigurationRow = table_definitions.currentConfigurationValues( application = applicationName,
                                                                                ini_file_section = sectionName, ini_field_name = itemField, 
                                                                                application_version = applicationVersion, server = serverName,
                                                                                ini_value = itemValue, changed_by_user = 'tslijboom', 
                                                                                configured_by_user_flag = True,
                                                                                changed_by_timestamp = time.time() )
                        listOfConfigurationItemsForTheDB.append( newConfigurationRow )
    

        except Exception as e:
            #error = sys.exc_info()[0]
            #print( 'Failed to read in config file ' + currentIniFile )
            print( ':::' + str(e) )
            sys.exit( 7 )

        # This is either updating or inserting to the DB.
        table_definitions.session.add_all( listOfConfigurationItemsForTheDB )
        table_definitions.session.commit()

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
