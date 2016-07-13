import unittest
import sys
import os
import ipaddress

# Module for the method to work
sys.path.append(os.path.abspath('../bin'))
#sys.path.append( '/home/tslijboom/tools--config-manager-ini/bin' )

from config_manager import getVariableNameAndVerificationFunctions
from config_manager import testConfigValueAgainstFunctions

class getVariableNameAndVerificationFunctionsTest( unittest.TestCase ):
    def test_a_valid_string( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "level isAnInteger" )
                , ( 'level', [ 'isAnInteger( {0} )' ] ) )

    def test_variable_name_only( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "level" )
                , ( 'level', [ ] ) )


    def test_function_name_that_does_not_exist( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "serverName IAmNotAFunction" )
                , ( 'serverName', [ ] ) )

    def test_in_range_function_syntax( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "theNumber inRange 10 1" )
                , ( 'theNumber', [ 'inRange( {0}, 1,10 )' ] ) )

    def test_in_range_function_reversed_max_and_min_order_syntax( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "theNumber inRange 1 10" )
                , ( 'theNumber', [ 'inRange( {0}, 10,1 )' ] ) )

    def test_invalid_variable_name( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "iDoNotExist 1 10" )
                , ( 'theNumber', [ 'inRange( {0}, 10,1 )' ] ) )
                #, ( 'theNumber', [ 'inRange( {0}, 10,1 )' ] ) )

    def test_2_functions_names_and_correct_syntax( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "theNumber isAnInteger inRange 1 10" )
                , ( 'theNumber', [ 'inRange( {0}, 10,1 )', 'isAnInteger( {0} )' ] ) )

    # better improve on this, this should fail, right?
    def test_in_range_function_with_invalid_max_value_input( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "theNumber isAnInteger inRange 1000 10" )
                , ( 'theNumber', [ 'inRange( {0}, 10,1000 )' , 'isAnInteger( {0} )' ] ) )

    def test_invalid_variable_name( self ):
        self.assertEqual( getVariableNameAndVerificationFunctions( "******** isAnInteger" )
                , () )


class testConfigValueAgainstFunctionsTest( unittest.TestCase ):
    #############################################
    ### testConfigValueAgainstFunctions
    #############################################
    def test_isAnInteger_with_string( self ):
        self.assertEqual( ( 'a string', [ 'isAnInteger( {0} )' ] )
            , False )

    def test_isAnInteger_with_positive_number( self ):
        self.assertEqual( testConfigValueAgainstFunctions( 6 , [ 'isAnInteger( {0} )' ] )
            , True )
        
    def test_isAnInteger_with_negative_number( self ):
        self.assertEqual( testConfigValueAgainstFunctions( -6 , [ 'isAnInteger( {0} )' ] )
            , True )
        
def main():
        cpt = configParserTest()
        for item in dir( cpt ):
            if item[ :5 ] == 'test_':
                print( 'executing test: ' + item )
                method_to_run = getattr( cpt, item )
                method_to_run()

if ( __name__ == '__main__' ):
    main()
