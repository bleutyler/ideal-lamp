import unittest
import sys
import ipaddress

# Module for the method to work

sys.path.append( '/home/tslijboom/tools--config-manager-ini/bin' )
from config_manager import getVariableNameAndVerificationFunctions
from config_manager import testConfigValueAgainstFunctions

class configParserTest( unittest.TestCase ):
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
        pass

    def test_2_functions_names_and_correct_syntax( self ):
        pass

    def test_in_range_function_with_invalid_max_value_input( self ):
        pass

    def test_invalid_variable_name( self ):
        pass


    #############################################
    ### testConfigValueAgainstFunctions
    #############################################
    def test_isAnInteger_with_string( self ):
        self.assertEqual( testConfigValueAgainstFunctions( 'a string', [ 'isAnInteger( {0} )' ] )
            , False )

    def test_isAnInteger_with_positive_number( self ):
        self.assertEqual( testConfigValueAgainstFunctions( 6 , [ 'isAnInteger( {0} )' ] )
            , True )
        
    def test_isAnInteger_with_negative_number( self ):
        self.assertEqual( testConfigValueAgainstFunctions( -6 , [ 'isAnInteger( {0} )' ] )
            , True )
        

cpt = configParserTest()
for item in dir( cpt ):
    if item[ :5 ] == 'test_':
        print( item )
        method_to_run = getattr( cpt, item )
        method_to_run()
