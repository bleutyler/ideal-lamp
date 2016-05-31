# ####################################################################
# 
#    CONFIG_MANAGER_LIB.PY
#
#    > Support: Tyler Slijboom
#    > Company: Blackberry
#    > Contact: tslijboom@juniper.net
#    > Version: 0.2.4
#    > Revision Date: 2015-05-30
#       
# ####################################################################
# ----------[ IMPORTS ]----------
import configparser
import ipaddress
import os
import table_definitions
import time

# ----------[ GLOBAL CONSTANTS ]----------
final_ini_file_header  = """ """
final_ini_file_footer  = """ """
sample_ini_file_header = """ """
sample_ini_file_footer = """ """

def isAnIPAddress( testValue ):
    """  The value must be an IPv4 or IPv6 address  """
    try:
        ipTest = ipaddress.ipaddress( testValue )
    except ValueError:
        return False 
    return True



def isAnInteger( testValue ):
    """  The value must be an integer  """
    try:
        integerTest = int( testValue )
    except ValueError:
        return False
    return True

def isAlphaNumericString( testValue ):
    """  The value must be made up of letters and/or digits """
    if testValue == '':
        return True
    #return testValue.isalpha()
    return True

# This is a Jinja2 template string, at least the __doc__ is
def inRange( testValue, minimumValue, maximumValue ):
    """  The value must be in the range of {{minimumValue}} and {{ maximumValue }} """
    if isAnInteger( minimumValue ):
        if isAnInteger( maximumValue ):
            if testValue <= maximumValue and testValue >= minimumValue:
                return True
            else:
                return False
        else:
            raise TypeError( 'maximum value "' + str( maximumValue ) + '" is not an integer' )
    else:
        raise TypeError( 'minimum value "' + str( minimumValue ) + '" is not an integer' )


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
        sys.exit(4)

    return iniConfigurationSettings


def readInDatabaseConfiguration( applicationName, serverName ):
    """  Get the database version of the configuration , return it as a configparser object """
    configurationItemsFromDB = table_definitions.session.query( table_definitions.currentConfigurationValues ).all()
    print( repr( configurationItemsFromDB ) )
    iniConfigurationSettings = configparser.ConfigParser()
    for row in configurationItemsFromDB:
        print( 'Found row.id from the DB' )
        

    return iniConfigurationSettings 



def updateDatabase( applicationName, serverName, finalIniConfig ):
    """ Iterate through a config parser object, and update the config manager database with the items inside.  """
    print( "GOING TO UPDATE THE DB with the new config" )
    # Does there already exist such an object?  If so, delete them (because there may be items that changed)
    itemAlreadyInTheDBTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                                 table_definitions.currentConfigurationValues.target_box == serverName ).filter( 
                                 table_definitions.currentConfigurationValues.target_application == applicationName ).all()

    if itemAlreadyInTheDBTest:
        for row in itemAlreadyInTheDBTest:
            table_definitions.session.delete( row )

    listOfDBConfigsToInsert = []
    for sectionName in finalIniConfig.sections():
        for configItem in finalIniConfig.items( sectionName ):
            itemField = configItem[0]
            itemValue = configItem[1]
            newConfigRow = table_definitions.currentConfigurationValues( target_box = serverName, target_application = applicationName,
                                                        ini_file_section = sectionName, ini_field_name = itemField, 
                                                        ini_value = itemValue, changed_by_user = 'tslijboom', 
                                                        changed_by_timestamp = time.time() )
            listOfDBConfigsToInsert.append( newConfigRow )
    
    table_definitions.session.add_all( listOfDBConfigsToInsert )
    table_definitions.session.commit()
    print( 'Added items to the DB' )
