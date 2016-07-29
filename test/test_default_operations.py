import unittest
from   unittest.mock import patch
import sys
import os
import time

sys.path.append( '../bin' )

import table_definitions
import config_manager

#unittest.TestLoader.sortTestMethodsUsing = None

class DefaultApplicationTester( unittest.TestCase ):
    application     = 'defaultTester' 
    server          = 'TSFDAT_test'
    #app_homefolder  = '/home/tslijboom/git/tools--ini-config-manager/test/input_files'
    app_homefolder  = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files'
    user            = 'testClass'
    section         = 'hpna'
    #test_configuration_file = '/home/tslijboom/git/tools--ini-config-manager/test/config_manager_tester.ini'
    test_configuration_file = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/config_manager_tester.ini'
    list_of_items_to_delete_at_the_end_of_testing = []

    @classmethod
    def setup_class( self ):
        #############
        # make sure the values are not already there
        print( 'running setupclass' )
        test_values_dict = { 'username' : 0, 'servername' : 0 , 'serverip' : 0 }
        defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                    table_definitions.applicationDefaultValues.application_version == '1.0.0' ).filter(
                    table_definitions.applicationDefaultValues.application         == self.application ).all()

        if defaultsSetByThisTestModule:
            for item in defaultsSetByThisTestModule:
                if item.ini_field_name in test_values_dict:
                    test_values_dict[ item.ini_field_name ] = 1
                    print( 'setup Hey found item ' + item.application + '::' + item.ini_file_section + '::' + item.ini_field_name )

        for field in test_values_dict:
            if str(test_values_dict[ field ]) != str(0):
                self.assertTrue( 0, msg='default HPNA v1.0.0 field is absent before insertion' )

        # insert any data you want into the DB
        hpna_username   = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = self.application,
                ini_file_section = self.section, ini_field_name = 'username', ini_value = 'theHPNAuser', changed_by_user = self.user,
                changed_by_timestamp = time.time()
                )
        hpna_servername = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = self.application,
                ini_file_section = self.section, ini_field_name = 'servername', ini_value = 'theHPNAserver', changed_by_user = self.user,
                changed_by_timestamp = time.time()
                )
        hpna_serverip   = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = self.application,
                ini_file_section = self.section, ini_field_name = 'serverip', ini_value = 'theHPNAserverIP', changed_by_user = self.user,
                changed_by_timestamp = time.time()
                )

        table_definitions.session.add( hpna_username )
        self.list_of_items_to_delete_at_the_end_of_testing.append( hpna_username )
        table_definitions.session.add( hpna_servername )
        self.list_of_items_to_delete_at_the_end_of_testing.append( hpna_servername )
        table_definitions.session.add( hpna_serverip )
        self.list_of_items_to_delete_at_the_end_of_testing.append( hpna_serverip )
        table_definitions.session.commit()
        table_definitions.session.flush()

    @classmethod
    def teardown_class( self ):
        """
        defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                        table_definitions.applicationDefaultValues.application_version == '1.2.0' ).filter(
                        table_definitions.applicationDefaultValues.application         == self.application ).all()

        if defaultsSetByThisTestModule:
                for row in defaultsSetByThisTestModule:
                        table_definitions.session.delete( row )

        """
        for item in self.list_of_items_to_delete_at_the_end_of_testing:
            table_definitions.session.delete( item )

        table_definitions.session.commit()

    def test_adding_new_default_with_no_version_specified( self ):
        #############
        # make sure the values are not already there
        test_values_dict = { 'username' : 0, 'servername' : 0 , 'serverip' : 0 }
        defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                    table_definitions.applicationDefaultValues.application_version == '1.0.0' ).filter(
                    table_definitions.applicationDefaultValues.application         == self.application ).all()

        table_definitions.session.flush()
        if defaultsSetByThisTestModule:
            for item in defaultsSetByThisTestModule:
                if item.ini_field_name in test_values_dict:
                    print( 'testmethod: Hey found item ' + item.application + '::' + item.ini_file_section + '::' + item.ini_field_name )
                    test_values_dict[ item.ini_field_name ] = 1

        for field in test_values_dict:
            self.assertEqual( test_values_dict[ field ] , 0, 'default HPNA v1.0.0 field (' + field + ') is absent before insertion' )

        #############
        # Insert new defaults via the command line, and make sure it is defaulted to version 1.0.0
        #input_file      = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/config/default_setting_v.1.0.0.ini'
        #template_file   = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/template/default_setting_v.1.0.0.ini'
        input_file      = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/config/default_setting_v.1.0.0.ini'
        template_file   = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/template/default_setting_v.1.0.0.ini'
        command_arguments_list   = [ '-a', self.application, '-c', self.test_configuration_file, '-m', 'setdefaults',
                                    '-s', self.server, '-i', input_file, '-t', template_file, ]
        with unittest.mock.patch( 'sys.argv', command_arguments_list ):
            print( 'testing with: ' + str( command_arguments_list ) )
            #now do the test
            config_manager.main()

            # Now check the tables, (ALL have the same section) 
            defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                        table_definitions.applicationDefaultValues.application_version == '1.0.0' ).filter(
                        table_definitions.applicationDefaultValues.application         == self.application ).all()

            # now look for the values and make sure they exist now
            if defaultsSetByThisTestModule:
                for item in defaultsSetByThisTestModule:
                    if item.ini_field_name in test_values_dict:
                        test_values_dict[ item.ini_field_name ] = 1
                    self.list_of_items_to_delete_at_the_end_of_testing.append( item )

            for field in test_values_dict:
                self.assertEqual( test_values_dict[ value ], 1, 'default HPNA v1.0.0 field (' + field + ') has been uploaded' )

    def test_adding_new_default( self ):
        #############
        # make sure the values are not already there
        test_values_dict = { 'username' : 0, 'servername' : 0 , 'serverip' : 0 }
        defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                    table_definitions.applicationDefaultValues.application_version == '1.0.0' ).filter(
                    table_definitions.applicationDefaultValues.application         == self.application ).all()

        if defaultsSetByThisTestModule:
            for item in defaultsSetByThisTestModule:
                if item.ini_field_name in test_values_dict:
                    test_values_dict[ item.ini_field_name ] = 1

        for value in test_values_dict:
            self.assertEqual( test_values_dict[ value ] , 0, 'default HPNA v1.0.0 value (' + value + ') is absent before insertion' )

        #############
        # Insert new defaults via the command line, and make sure it is defaulted to version 1.0.0
        #input_file      = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/config/default_setting_v.1.0.0.ini'
        #template_file   = '/home/tslijboom/git/tools--ini-config-manager/test/input_files/template/default_setting_v.1.0.0.ini'
        input_file      = '/home/bleutyler/tools--ini-config-manager/ideal-lamp/test/input_files/config/default_setting_v.1.0.0.ini'
        template_file   = '/home/bleutyler/git/tools--ini-config-manager/ideal-lamp/test/input_files/template/default_setting_v.1.0.0.ini'
        command_arguments_list   = [ '-a', self.application, '-c', self.test_configuration_file, '-m', 'setdefaults',
                                    '-s', self.server, '-i', input_file, '-t', template_file, ]
        with unittest.mock.patch( 'sys.argv', command_arguments_list ):
            print( 'testing with: ' + str( command_arguments_list ) )
            #now do the test
            config_manager.main()

            # Now check the tables, (ALL have the same section) 
            defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                        table_definitions.applicationDefaultValues.application_version == '1.0.0' ).filter(
                        table_definitions.applicationDefaultValues.application         == self.application ).all()

            # now look for the values and make sure they exist now
            if defaultsSetByThisTestModule:
                for item in defaultsSetByThisTestModule:
                    if item.ini_field_name in test_values_dict:
                        test_values_dict[ item.ini_field_name ] = 1
                    self.list_of_items_to_delete_at_the_end_of_testing.append( item )

            for value in test_values_dict:
                self.assertEqual( test_values_dict[ value ], 1, 'default HPNA v1.0.0 value (' + value + ') has been uploaded' )

