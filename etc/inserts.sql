insert into current_configuration_values ( server, application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp, configured_by_user_flag) VALUES ( 'tslijboom-VirtualBox', 'application_to_update', 'g', 'password', 'pinkfloyd', 'tslijboom', 1465531245, True );

insert into current_configuration_values ( server, application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp, configured_by_user_flag) VALUES ( 'tslijboom-VirtualBox', 'application_to_update', 'g', 'username', 'tslijboom', 'tslijboom', 1465531245, True );

insert into current_configuration_values ( server, application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp, configured_by_user_flag) VALUES ( 'tslijboom-VirtualBox', 'application_to_update', 'repo-gerrit', 'type', 'gerrit', 'tslijboom', 1465531245, True );

insert into current_configuration_values ( server, application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp, configured_by_user_flag) VALUES ( 'tslijboom-VirtualBox', 'application_to_update', 'repo-gerrit', 'port', '29418', 'tslijboom', 1465531245, True );

insert into current_configuration_values ( server, application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp, configured_by_user_flag) VALUES ( 'tslijboom-VirtualBox', 'application_to_update', 'repo-gerrit', 'defaultrepo', 'netmd', 'tslijboom', 1465531245, True );

insert into current_configuration_values ( server, application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp, configured_by_user_flag) VALUES ( 'tslijboom-VirtualBox', 'application_to_update', 'repo-gerrit', 'username', 'tslijboom', 'tslijboom', 1465531245, True ); 

alter sequence current_configuration_values_id_sequence RESTART 13; 

insert into application_default_values ( application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp ) VALUES ( 'new_application_to_install', 'hpna', 'server', 'tools-db-wldb.service.ntw.blackberry', 'tslijboom', '1466006583' );

insert into application_default_values ( application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp ) VALUES ( 'new_application_to_install', 'hpna', 'username', 'bbtyler', 'tslijboom', '1466006593' );

insert into application_default_values ( application, ini_file_section, ini_field_name, ini_value, changed_by_user, changed_by_timestamp ) VALUES ( 'new_application_to_install', 'hpna', 'password', '8fhs8udyhrNjKsH28Gfhc3wx1', 'tslijboom', '1466006623' );

