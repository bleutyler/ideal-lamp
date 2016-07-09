# ####################################################################
# 
#    CONFIG_MANAGER_LIB.PY
#
#    > Support: Tyler Slijboom
#    > Company: Blackberry
#    > Contact: tslijboom@juniper.net
#    > Version: 0.4.2
#    > Revision Date: 20160705 
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

###################################################################################

def isAnIPAddress( testValue ):
    """  The value must be an IPv4 or IPv6 address  """
    print( 'isAnIPAddress( "' + testValue + '" )' )
    if testValue == 'localhost':
        return True
    try:
        ipTest = ipaddress.ip_address( testValue )
    except ValueError:
        return False 
    return True



def isAnInteger( testValue ):
    """  The value must be an integer  ,
        The value must not contain decimal points."""
    testValue_is_str = isinstance(testValue, str)
    if testValue_is_str:
        try:
            int(testValue)
            return True
        except ValueError:
            return False
    else:
        return isinstance(testValue, int)


def isAlphaNumericString( testValue ):
    """  The value must be made up of letters and/or digits """

    testValue = str(testValue)
    testValue_is_valid = re.compile("^[a-zA-Z0-9,-\/* ]*$")
    if testValue_is_valid.search(testValue) is not None:
        return True
    else:
        return False


# This is a Jinja2 template string, at least the __doc__ is
def inRange( testValue, minimumValue, maximumValue ):
    """  The value must be in the range of {{minimumValue}} and {{ maximumValue }} """
    if isAnInteger( minimumValue ):
        if isAnInteger( maximumValue ):
            if isAnInteger( testValue ):
                if int(testValue) <= int(maximumValue) and int(testValue) >= int(minimumValue):
                    return True
                else:
                    return False
            else:
                raise TypeError( 'test value "' + str( testValue ) + '" is not an integer' )
        else:
            raise TypeError( 'maximum value "' + str( maximumValue ) + '" is not an integer' )
    else:
        raise TypeError( 'minimum value "' + str( minimumValue ) + '" is not an integer' )

def selectFromList( testValue, *listOfAcceptableValues ):
    """ The value must be one of: {{ listOfValues }} """
    print( 'checking if ' + testValue + ' is in one of: ' + str( listOfAcceptableValues ) )
    if testValue in listOfAcceptableValues:
        return True
    return False 

def canBeNull( testValue ):
    """ This value can be empty """
    return True

def isAnEmailAddress( testValue ):
    """ The value must be an email address """
    testValue = str(testValue)
    testValue_is_valid = re.compile("^[a-zA-Z0-9-@]*$")
    if testValue_is_valid.search(testValue) is not None:
        return True
    else:
        return False
