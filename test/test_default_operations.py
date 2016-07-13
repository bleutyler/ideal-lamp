import unittest
import sys
import os

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
        hpna_username   = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = application,
                ini_file_section = section, ini_field_name = 'username', ini_value = 'theHPNAuser', changed_by_user = user
                )
        hpna_servername = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = application,
                ini_file_section = section, ini_field_name = 'servername', ini_value = 'theHPNAserver', changed_by_user = user
                )
        hpna_serverip   = table_definitions.applicationDefaultValues( application_version = '1.2.0', application = application,
                ini_file_section = section, ini_field_name = 'serverip', ini_value = 'theHPNAserverIP', changed_by_user = user
                )

        session.add( hpna_username )
        session.add( hpna_servername )
        session.add( hpna_serverip )
        session.commit()

    @classmethod
    def teardown_class( cls ):
        defaultsSetByThisTestModule = table_definitions.session.query( table_definitions.applicationDefaultValues ).filter(
                        table_definitions.applicationDefaultValues.application_version == '1.2.0' ).filter(
                        table_definitions.applicationDefaultValues.application         == application ).all()

        if defaultsSetByThisTestModule:
                for row in defaultsSetByThisTestModule:
                        table_definitions.session.delete( row )

    def test_adding_new_default( ):
        version = '1.2.0'
        command_to_ru
