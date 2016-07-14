import unittest
import sys
import os
import time

sys.path.append( '../bin' )

import table_definitions
import config_manager

class DefaultApplicationTester( unittest.TestCase ):
    application     = 'defaultTester' 
    server          = 'TSFDAT_test'
    app_homefolder  = '/home/bleutyler/ini_test_area/defaultTester'
    user            = 'testClass'
    section         = 'hpna'
    test_configuration_file = '/home/tslijboom/git/tools--ini-config-manager/test/config_manager_tester.ini'

    @classmethod
    def setup_class( cls ):
        # insert any data you want into the DB
        hpna_username   = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = cls.application,
                ini_file_section = cls.section, ini_field_name = 'username', ini_value = 'theHPNAuser', changed_by_user = cls.user,
                changed_by_timestamp = time.time()
                )
        hpna_servername = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = cls.application,
                ini_file_section = cls.section, ini_field_name = 'servername', ini_value = 'theHPNAserver', changed_by_user = cls.user,
                changed_by_timestamp = time.time()
                )
        hpna_serverip   = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = cls.application,
                ini_file_section = cls.section, ini_field_name = 'serverip', ini_value = 'theHPNAserverIP', changed_by_user = cls.user,
                changed_by_timestamp = time.time()
                )

        table_definitions.session.add( hpna_username )
        table_definitions.session.add( hpna_servername )
        table_definitions.session.add( hpna_serverip )
        table_definitions.session.commit()

    @classmethod
    def teardown_class( cls ):
        defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                        table_definitions.applicationDefaultValues.application_version == '1.2.0' ).filter(
                        table_definitions.applicationDefaultValues.application         == cls.application ).all()

        if defaultsSetByThisTestModule:
                for row in defaultsSetByThisTestModule:
                        table_definitions.session.delete( row )

    def test_adding_new_default( self ):
        # SHOULD DEFAULT TO VERSION 1.0.0
        input_file      = 'input_files/default_setting_v.1.0.0.ini'
        template_file   = 'input_files/default_setting_v.1.0.0.ini'
        command_arguments_list   = ( '-a', self.application, '-c', self.test_configuration_file, '-m set_defaults',
                                    '-s', self.server, '-i', input_file, '-t', template_file )
        with unittest.mock.patch( 'sys.argv', command_arguments_list ):
            #now do the test
            config_manager.main()
