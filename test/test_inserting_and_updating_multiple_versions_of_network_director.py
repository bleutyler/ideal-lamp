import unittest
from   unittest.mock import patch
import sys
import configparser
import os
import time

sys.path.append( '../bin' )

import table_definitions
import config_manager

class DefaultApplicationTester( unittest.TestCase ):
    applicationName = 'networkDirectoryAppTest'
    serverName      = 'testServer'
    app_homefolder  = '/home/bleutyler/git/tools--ini-config-manager/test/input_files'
    user            = 'testClass'
    test_configuration_file = '/home/tslijboom/git/tools--ini-config-manager/test/config_manager_tester.ini'

    list_of_items_to_delete_at_the_end_of_testing = []

    @classmethod
    def setup_class( self ):
        # INSERTING NETWORK DIRECTORY V.2.0.0
        # Iterate through the config file of V2.0.0
        sourceVersion = '2.0.0'
        sourceConfigFile = self.app_homefolder + '/config/network-directory.v.' + sourceVersion
        sourceConfig = configparser.ConfigParser()
        sourceConfig.read( sourceConfigFile )
        print( 'read in ' + sourceConfigFile )
        for section in sourceConfig.sections():
            for field, value in sourceConfig.items( section ):
                print( 'hey i am inserting - sec: ' + section + ' field: ' 
                    + field + ' val: ' + value )
                currentRowItem = table_definitions.currentConfigurationValues( 
                    application_version = sourceVersion,
                    application = self.applicationName,
                    ini_file_section = section, 
                    ini_field_name = field, ini_value = value,
                    changed_by_user = self.user,
                    changed_by_timestamp = time.time() )
                table_definitions.session.add( currentRowItem )

        table_definitions.session.commit()
        """
        hpna_username   = table_definitions.applicationDefaultValues( 
            application_version = self.overwrite_version, application = self.application,
            ini_file_section = self.section, ini_field_name = 'username', 
            ini_value = 'theHPNAuser', changed_by_user = self.user,
            changed_by_timestamp = time.time()

        """
        pass
        # SETUP NEEDS TO INSTALL v2.1.1 

    @classmethod
    def teardown_class( self ):
        currentConfigsSetByThisTestModule = table_definitions.session.query( 
            table_definitions.currentConfigurationValues ).filter(
            table_definitions.currentConfigurationValues.changed_by_user == self.user ).all()

        # now look for the values and make sure they exist now
        if currentConfigsSetByThisTestModule:
            for item in currentConfigsSetByThisTestModule:
                table_definitions.session.delete( item )

        table_definitions.session.commit()

        for item in self.list_of_items_to_delete_at_the_end_of_testing:
            table_definitions.session.delete( item )

        table_definitions.session.commit()


    
    def test_installation_of_application_no_previous_data( self ):                                
    # Verify that an application is not already configured in the DB
        testVersion = '1.0.0'
        applicationName = 'nonExistantApp'
        pass


    # SETUP NEEDS IN INSTALL v2.0.0 for this
    def test_installation_of_application_adding_new_fields_previous_data ( self ):
        oldTestVersion = '2.0.0'
        newTestVersion = '2.1.0'
        pass

    # SETUP NEEDS IN INSTALL v2.1.1 for this
    def test_installation_of_application_adding_new_fields_and_changing_previous_data ( self ):
        oldTestVersion = '2.1.1'
        newTestVersion = '3.0.0'
        pass

    def test_installation_that_finds_default_data_to_use( self ):
        newTestVersion = '4.0.0'
        pass

    def test_file_system_errors( self ):
        pass

    def test_database_errors( self ):
        pass
