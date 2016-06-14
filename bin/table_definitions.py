# ####################################################################
# 
#    TABLE_DEFINITIONS.PY
#
#    > Support: Tyler Slijboom
#    > Company: Blackberry
#    > Contact: tslijboom@juniper.net
#    > Version: 0.2.3
#    > Revision Date: 2015-05-27
#       
# ####################################################################
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Sequence

engine = create_engine('postgresql://tslijboom:Kanata89@localhost/ConfigurationManager', echo=False )

Base = declarative_base()

class applicationDefaultValues( Base ):
    __tablename__ = 'application_default_values'

    id                   = Column( Integer, Sequence('application_default_values_id_sequence'), primary_key=True )
    application          = Column( String )
    ini_file_section     = Column( String )
    ini_field_name       = Column( String )
    ini_value            = Column( String )
    changed_by_user      = Column( String )
    changed_by_timestamp = Column( Integer )

class currentConfigurationValues( Base ):
    __tablename__ = 'current_configuration_values'
    id                   = Column( Integer, Sequence('current_configuration_values_id_sequence'), primary_key=True )
    server               = Column( String )
    application          = Column( String )
    ini_file_section     = Column( String )
    ini_field_name       = Column( String )
    ini_value            = Column( String )
    changed_by_user      = Column( String )
    changed_by_timestamp = Column( Integer )


class manualChangeReason( Base ):
    __tablename__ = 'manual_change_reason'
    id                      = Column( Integer, Sequence('manual_change_reason_id_sequence'), primary_key=True )
    configuration_change_id = Column( String )
    change_text             = Column( String )


class configurationHistory( Base ):
    __tablename__ = 'configuration_history'
    id                 = Column( Integer, Sequence('configuration_history_id_sequence'), primary_key=True )
    server             = Column( String )   
    application        = Column( String )
    ini_file_section   = Column( String )
    ini_field_name     = Column( String )
    ini_value          = Column( String )
    changed_by_user    = Column( String )
    start_timestamp    = Column( Integer )
    change_reason_id   = Column( Integer )


Session = sessionmaker( bind = engine )
session = Session()
