#Example sample.ini :
#[hpna] 
#serverIPAddress is_an_ip_address()
#userName alpha_numeric_string() 
#timeoutRetrys is_an_integer() in_range(0, 5)

import ipaddress

def isAnIPAddress( string testValue ):
    """  The value must be an IPv4 or IPv6 address  
    """
    try:
        ipTest = ipaddress.ipaddress( testValue )
    except ValueError:
        return False
    return True



def isAnInteger( string testValue ):
    """  The value must be an integer  
    """
    try:
        integerTest = int( testValue )
    except ValueError:
        return False
    return True

def isAlphaNumericString( string testValue ):
    """  The value must be a letter or digit 
    """
    if testValue == '':
        return True
    return testValue.isalpha()

in_range( string testValue, int minimumValue, int maximumValue ):
    """  The value must be in the range of {{minimumValue}} and {{ maximumValue }}
    """
    if isAnInteger( minimumValue ):
        if isAnInteger( maximumValue ):
            if testValue <= maximumValue and testValue >= minimumValue:
                return True
            else:
                return False
        else:
            raise TypeError( 'maximum value "' + str( maximumValue ) + '" is not an integer' )
    else
        raise TypeError( 'minimum value "' + str( minimumValue ) + '" is not an integer' )

