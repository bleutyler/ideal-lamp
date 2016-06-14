import unittest
import sys
import ipaddress

# Module for the method to work

sys.path.append( '/home/tslijboom/tools--config-manager-ini/bin' )
import config_manager_lib


class configParserTest( unittest.TestCase ):
    def test_a_valid_string( self ):
        self.assertEqual( config_manager_lib.getVariableNameAndVerificationFunctions( "level isAnInteger" )
                , ( 'level', [ 'isAnInteger( {0} )' ] ) )

    def test_variable_name_only( self ):
        self.assertEqual(  config_manager_lib.getVariableNameAndVerificationFunctions( "level" )
                , ( 'level', [ ] ) )


    def test_function_name_that_does_not_exist( self ):
        self.assertEqual(  config_manager_lib.getVariableNameAndVerificationFunctions( "serverName IAmNotAFunction" )
                , ( 'serverName', [ ] ) )

    def test_in_range_function_syntax( self ):
        self.assertEqual(  config_manager_lib.getVariableNameAndVerificationFunctions( "theNumber inRange 10 1" )
                , ( 'theNumber', [ 'inRange( {0}, 1,10 )' ] ) )

    def test_in_range_function_reversed_max_and_min_order_syntax( self ):
        self.assertEqual(  config_manager_lib.getVariableNameAndVerificationFunctions( "theNumber inRange 1 10" )
                , ( 'theNumber', [ 'inRange( {0}, 10,1 )' ] ) )

    def test_invalid_variable_name( self ):
        pass

    def test_2_functions_names_and_correct_syntax( self ):
        pass

    def test_in_range_function_with_invalid_max_value_input( self ):
        pass

    def test_invalid_variable_name( self ):
        pass

cpt = configParserTest()
cpt.test_a_valid_string()
cpt.test_variable_name_only()
cpt.test_function_name_that_does_not_exist()
cpt.test_in_range_function_syntax()
cpt.test_in_range_function_reversed_max_and_min_order_syntax()
