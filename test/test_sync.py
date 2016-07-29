import unittest
from   unittest.mock import patch
import sys
import time
import os
#import ipaddress

# Module for the method to work
sys.path.append(os.path.abspath('../bin'))
#sys.path.append( '/home/tslijboom/tools--config-manager-ini/bin' )

import config_manager
import table_definitions

class SyncCommandTest( unittest.TestCase ):
    application                     = 'syncTestingApp'
    server                          = 'syncServer'
    overwrite_version               = '2.0.0'
    test_config_parser_ini_file     = ''
    home_folder                     = os.getcwd()
    test_configuration_file         = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/config_manager_tester.ini'
    sync_application_template_file  = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/template/sync_test_template.ini'
    #test_configuration_file         = '/home/tslijboom/git/tools--ini-config-manager/test/config_manager_tester.ini'
    #sync_application_template_file  = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/template/sync_test_template.ini'
    list_of_items_to_delete_at_the_end_of_testing = []
    
    templateFileHandle = open( sync_application_template_file, 'r' )
    contentsOfTemplateFileBeforeTest = templateFileHandle.read()

    

    @classmethod
    def setUpClass( self ):
        sectionName = 'album'
        fields_to_write = { 'filename' : 234, 'important_word' : 'three', 'port' : 888888 }
        for field, value in fields_to_write.items():
            newConfigurationRow = table_definitions.currentConfigurationValues( application = self.application,
                                    ini_file_section = sectionName, ini_field_name = field,
                                    application_version = self.overwrite_version, server = self.server,
                                    ini_value = value, changed_by_user = 'tslijboom',
                                    configured_by_user_flag = True,
                                    changed_by_timestamp = time.time() )

            #self.list_of_items_to_delete_at_the_end_of_testing.append( newConfigurationRow )
            # this is overwritting so these sql instances do not persist, add them to this list_ after the values are overwritten.

    def test_sync_command_overwriting_values_already_there( self ):
        ini_file_with_values = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/config/sync_test_ini_after_test.ini'

        configFileHandle = open( ini_file_with_values, 'r' )
        contentsOfConfigFileBeforeTest = configFileHandle.read()
        #ini_file_with_values = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/config/sync_test_ini_after_test.ini'
        #############
        # make sure the values are not already there
        test_values_dict = {}
        oldConfigurationValuesTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                    table_definitions.currentConfigurationValues.application_version == self.overwrite_version ).filter(
                    table_definitions.currentConfigurationValues.application         == self.application ).all()

        table_definitions.session.flush()
        if oldConfigurationValuesTest:
            for item in oldConfigurationValuesTest:
                test_values_dict[ item.ini_field_name ] = item.ini_value

        #############
        # run the command
        command_arguments_list   = [ '-a', self.application, '-c', self.test_configuration_file, '-m', 'sync', '-v', self.overwrite_version,
                                    '-s', self.server, '-i', ini_file_with_values, '-t', self.sync_application_template_file ]
        with unittest.mock.patch( 'sys.argv', command_arguments_list ):
            print( 'testing with: ' + str( command_arguments_list ) )
            config_manager.main()

            # Now check the tables, (ALL have the same section) 
            configurationValuesTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                        table_definitions.currentConfigurationValues.application_version == self.overwrite_version ).filter(
                        table_definitions.currentConfigurationValues.application         == self.application ).all()

            # now look for the values and make sure they are different from before
            if configurationValuesTest:
                for item in configurationValuesTest:
                    self.list_of_items_to_delete_at_the_end_of_testing.append( item )
                    if item.ini_field_name in test_values_dict:
                        self.assertNotEqual( test_values_dict[ item.ini_field_name ], item.ini_value, 'DB item ' + item.ini_field_name + 'has been synced with a new value' )
        # make sure input files are unchanged.
        configFileHandle = open( ini_file_with_values, 'r' )
        contentsOfConfigFileAfterTest = configFileHandle.read()
        templateFileHandle = open( self.sync_application_template_file, 'r' )
        contentsOfTemplateFileAfterTest = templateFileHandle.read()

        self.assertEqual( contentsOfConfigFileAfterTest, contentsOfConfigFileBeforeTest, 'Configuration File contents are unchanged' )
        self.assertEqual( contentsOfTemplateFileAfterTest, self.contentsOfTemplateFileBeforeTest, 'Template File contents are unchanged' )

    def test_sync_command_before_values_already_exist_for_version( self ):
        # write to the DB from a file
        ini_file_with_values    = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/config/sync_test_ini_before_test.ini'
        #ini_file_with_values    = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/config/sync_test_ini_before_test.ini'
        version_for_blank_write = '1.2.3'
        #############
        # make sure the values are not already there
        test_values_dict = { 'filename' : 0 , 'important_word' : 0 , 'port' : 0 }
        absentConfigurationValuesTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                    table_definitions.currentConfigurationValues.application_version == version_for_blank_write ).filter(
                    table_definitions.currentConfigurationValues.application         == self.application ).all()

        table_definitions.session.flush()
        if absentConfigurationValuesTest:
            for item in absentConfigurationValuesTest:
                if item.ini_field_name in test_values_dict:
                    print( 'testmethod: Hey found item ' + item.application + '::' + item.ini_file_section + '::' + item.ini_field_name )
                    test_values_dict[ item.ini_field_name ] = 1

        for field in test_values_dict:
            self.assertEqual( test_values_dict[ field ] , 0, 'sync test v' + version_for_blank_write + ' field (' + field + ') is absent before insertion' )

        #############
        # run the command
        command_arguments_list   = [ '-a', self.application, '-c', self.test_configuration_file, '-m', 'sync', '-v', version_for_blank_write,
                                    '-s', self.server, '-i', ini_file_with_values, '-t', self.sync_application_template_file ]
        with unittest.mock.patch( 'sys.argv', command_arguments_list ):
            print( 'testing with: ' + str( command_arguments_list ) )
            #now do the test
            config_manager.main()

            # Now check the tables, (ALL have the same section) 
            configurationValuesTest = table_definitions.session.query( table_definitions.currentConfigurationValues ).filter(
                        table_definitions.currentConfigurationValues.application_version == version_for_blank_write ).filter(
                        table_definitions.currentConfigurationValues.application         == self.application ).all()

            # now look for the values and make sure they exist now
            if configurationValuesTest:
                for item in configurationValuesTest:
                    if item.ini_field_name in test_values_dict:
                        test_values_dict[ item.ini_field_name ] = 1
                        self.list_of_items_to_delete_at_the_end_of_testing.append( item )

            for field in test_values_dict:
                self.assertEqual( test_values_dict[ field ], 1, 'default HPNA v' + version_for_blank_write + ' field (' + field + ') has been uploaded' )

        # Test that the template and config files are untouched.
        configFileHandle = open( ini_file_with_values, 'r' )
        contentsOfConfigFileAfterTest = configFileHandle.read()
        templateFileHandle = open( self.sync_application_template_file, 'r' )
        contentsOfTemplateFileAfterTest = templateFileHandle.read()

        self.assertEqual( contentsOfConfigFileAfterTest, contentsOfConfigFileBeforeTest, 'Configuration File contents are unchanged' )
        self.assertEqual( contentsOfTemplateFileAfterTest, self.contentsOfTemplateFileBeforeTest, 'Template File contents are unchanged' )

    @classmethod
    def teardown_class( self ):
        for item in self.list_of_items_to_delete_at_the_end_of_testing:
            table_definitions.session.delete( item )

        table_definitions.session.commit()


if ( __name__ == '__main__' ):
    main()
