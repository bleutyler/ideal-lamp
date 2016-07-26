import unittest
from   unittest.mock import patch
import sys
import os
#import ipaddress

# Module for the method to work
sys.path.append(os.path.abspath('../bin'))
#sys.path.append( '/home/tslijboom/tools--config-manager-ini/bin' )

import config_manager
import table_definitions

class SyncCommandTest( unittest.TestCase ):
    application = 'syncTestingApp'
    server      = 'syncServer'
    version     = '2.0.0'
    test_config_parser_ini_file = ''
    home_folder = os.getcwd()
    test_configuration_file = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/config_manager_tester.ini'
    sync_application_template_file = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/template/sync_test_template.ini'

    def test_sync_command_before_values_already_exist_for_version( self ):
        # write to the DB from a file
        ini_file_with_values = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/config/sync_test_ini_before_test.ini'
        #############
        # make sure the values are not already there
        test_values_dict = { 'filename' : 0 , 'important_word' : 0 , 'port' : 0 }
        absentConfigurationValuesTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                    table_definitions.currentConfigurationValues.application_version == self.version ).filter(
                    table_definitions.currentConfigurationValues.application         == self.application ).all()

        table_definitions.session.flush()
        if absentConfigurationValuesTest:
            for item in absentConfigurationValuesTest:
                if item.ini_field_name in test_values_dict:
                    print( 'testmethod: Hey found item ' + item.application + '::' + item.ini_file_section + '::' + item.ini_field_name )
                    test_values_dict[ item.ini_field_name ] = 1

        for field in test_values_dict:
            self.assertEqual( test_values_dict[ field ] , 0, 'sync test v' + self.version + ' field (' + field + ') is absent before insertion' )

        #############
        # run the command
        command_arguments_list   = [ '-a', self.application, '-c', self.test_configuration_file, '-m', 'sync', '-v', self.version,
                                    '-s', self.server, '-i', ini_file_with_values, '-t', self.sync_application_template_file ]
        with unittest.mock.patch( 'sys.argv', command_arguments_list ):
            print( 'testing with: ' + str( command_arguments_list ) )
            #now do the test
            config_manager.main()

            # Now check the tables, (ALL have the same section) 
            configurationValuesTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                        table_definitions.currentConfigurationValues.application_version == self.version ).filter(
                        table_definitions.currentConfigurationValues.application         == self.application ).all()

            # now look for the values and make sure they exist now
            if configurationValuesTest:
                for item in configurationValuesTest:
                    if item.ini_field_name in test_values_dict:
                        test_values_dict[ item.ini_field_name ] = 1

            for field in test_values_dict:
                self.assertEqual( test_values_dict[ field ], 1, 'default HPNA v' + self.version + ' field (' + field + ') has been uploaded' )


    
    def test_sync_command_overwriting_values_already_there( self ):
        ini_file_with_values = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/config/sync_test_ini_after_test.ini'
        pass


        
if ( __name__ == '__main__' ):
    main()
