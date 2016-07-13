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
        print( 'hey I got a ' + str( self ) )
        version = '1.2.0'
        command_arguments_to_run = '-a ' + self.application + '-c /home/tslijboom/git/tools--ini-config-manager/test/config_manager_tester.ini -s ' + self.server +
            '
