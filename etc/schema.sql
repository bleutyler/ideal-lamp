drop   table if exists application_default_values ;
create table application_default_values (
    id                          serial          primary key ,
    application          varchar(50)     not null,
    ini_file_section            varchar(50)     not null,
    ini_field_name              varchar(50)     not null,
    ini_value                   varchar(300)     not null,
    application_version         varchar(20)     not null,       -- example: 1.0.34
    changed_by_user             varchar(20)     not null,       -- username of who changed it
    changed_by_timestamp        integer         not null        -- epoch timestamp when the above user updated this value
);
drop sequence application_default_values_id_sequence;
create sequence application_default_values_id_sequence;


drop   table if exists current_configuration_values ;
create table current_configuration_values (
    id                          serial          primary key ,
    server                  varchar(50)     not null,
    application          varchar(50)     not null,
    ini_file_section            varchar(50)     not null,
    ini_field_name              varchar(50)     not null,
    ini_value                   varchar(300)     ,
    constraints_for_value       varchar(100)    ,
    application_version         varchar(20)     not null,       -- example: 1.0.34
    configured_by_user_flag     boolean         not null default True,
    changed_by_user             varchar(20)     not null,       -- username of who changed it
    changed_by_timestamp        integer         not null        -- epoch timestamp when the above user updated this value
);
drop sequence current_configuration_values_id_sequence; 
create sequence current_configuration_values_id_sequence; 

--               -                         -                             -
--               -                         -                             -
--               -                         -                             -
-- If a user manually changes a field, this can be used to store the reason why the change happened. It will map to
--      configuration_values.config_value_id.  Later, when the value is stored historically, then the new entry in this
--      table is then stored in
drop   table if exists manual_change_reason ;
create table manual_change_reason (
    id                      serial          primary key ,
    configuration_change_id integer         not null,
    change_text             varchar(1000)   not null
);
drop sequence manual_change_reason_id_sequence;  
create sequence manual_change_reason_id_sequence;  


--               -                         -                             -
--               -                         -                             -
--               -                         -                             -
--- very similar schema to configuration_values but with the end date attahced and the change_reason_id
--- THis could have TRIGGERS made in PSQL to say when an insert happens to configuration_values, then a matching row
---    is created here
drop   table if exists configuration_history ;
create table configuration_history (
    id                      serial          primary key ,
    server                  varchar(50)     not null,
    application      varchar(50)     not null,
    ini_file_section        varchar(50)     not null,
    ini_field_name          varchar(50)     not null,
    ini_value               varchar(300)     not null,
    application_version         varchar(20)     not null,       -- example: 1.0.34
    changed_by_user         varchar(20)     not null,       -- username of who changed it
    start_timestamp         integer         not null,       -- epoch timestamp when the above user updated this value
    change_reason_id        integer
);
drop sequence configuration_history_id_sequence;
create sequence configuration_history_id_sequence ;

drop   table if exists application_state ;
create table application_state (
    id          serial  primary key,
    server              varchar(50)     not null,
    application      varchar(50)     not null,
    state           varchar(1)  not null default 'I',    -- One of: (I)nstalled, (C)onfigured, (R)unning, (O)ffline, (U)pdated
    software_version    varchar(20) not null 
);

-- I think it would be good to have a user for installation and webapp configs would be ideal.  THat way the changed_by fields will contain
--   a user like 'CM-webapp' or 'cwinstaller' for when the scripts are run automatically.  And then when someone changes a value manually
--   the field will say: 'tslijboom'


-- create a schema named "audit"
CREATE schema audit;
REVOKE CREATE ON schema audit FROM public;
 
CREATE TABLE audit.logged_actions (
    schema_name text NOT NULL,
    TABLE_NAME text NOT NULL,
    user_name text,
    action_tstamp TIMESTAMP WITH TIME zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('I','D','U')),
    original_data text,
    new_data text,
    query text
) WITH (fillfactor=100);
 
REVOKE ALL ON audit.logged_actions FROM public;
 
-- You may wish to use different permissions; this lets anybody
-- see the full audit data. In Pg 9.0 and above you can use column
-- permissions for fine-grained control.
GRANT SELECT ON audit.logged_actions TO public;
 
CREATE INDEX logged_actions_schema_table_idx 
ON audit.logged_actions(((schema_name||'.'||TABLE_NAME)::TEXT));
 
CREATE INDEX logged_actions_action_tstamp_idx 
ON audit.logged_actions(action_tstamp);
 
CREATE INDEX logged_actions_action_idx 
ON audit.logged_actions(action);
 
--
-- Now, define the actual trigger function:
--

CREATE OR REPLACE FUNCTION audit.if_modified_func() RETURNS TRIGGER AS $body$
DECLARE
    v_old_data TEXT;
    v_new_data TEXT;
BEGIN
    /*  If this actually for real auditing (where you need to log EVERY action),
        then you would need to use something like dblink or plperl that could log outside the transaction,
        regardless of whether the transaction committed or rolled back.
    */
 
    /* This dance with casting the NEW and OLD values to a ROW is not necessary in pg 9.0+ */
 
    IF (TG_OP = 'UPDATE') THEN
        v_old_data := ROW(OLD.*);
        v_new_data := ROW(NEW.*);
        INSERT INTO audit.logged_actions (schema_name,table_name,user_name,action,original_data,new_data,query) 
        VALUES (TG_TABLE_SCHEMA::TEXT,TG_TABLE_NAME::TEXT,session_user::TEXT,substring(TG_OP,1,1),v_old_data,v_new_data, current_query());
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        v_old_data := ROW(OLD.*);
        INSERT INTO audit.logged_actions (schema_name,table_name,user_name,action,original_data,query)
        VALUES (TG_TABLE_SCHEMA::TEXT,TG_TABLE_NAME::TEXT,session_user::TEXT,substring(TG_OP,1,1),v_old_data, current_query());
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        v_new_data := ROW(NEW.*);
        INSERT INTO audit.logged_actions (schema_name,table_name,user_name,action,new_data,query)
        VALUES (TG_TABLE_SCHEMA::TEXT,TG_TABLE_NAME::TEXT,session_user::TEXT,substring(TG_OP,1,1),v_new_data, current_query());
        RETURN NEW;
    ELSE
        RAISE WARNING '[AUDIT.IF_MODIFIED_FUNC] - Other action occurred: %, at %',TG_OP,now();
        RETURN NULL;
    END IF;
 
EXCEPTION
    WHEN data_exception THEN
        RAISE WARNING '[AUDIT.IF_MODIFIED_FUNC] - UDF ERROR [DATA EXCEPTION] - SQLSTATE: %, SQLERRM: %',SQLSTATE,SQLERRM;
        RETURN NULL;
    WHEN unique_violation THEN
        RAISE WARNING '[AUDIT.IF_MODIFIED_FUNC] - UDF ERROR [UNIQUE] - SQLSTATE: %, SQLERRM: %',SQLSTATE,SQLERRM;
        RETURN NULL;
    WHEN OTHERS THEN
        RAISE WARNING '[AUDIT.IF_MODIFIED_FUNC] - UDF ERROR [OTHER] - SQLSTATE: %, SQLERRM: %',SQLSTATE,SQLERRM;
        RETURN NULL;
END;
$body$
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, audit;
 

-- To add this trigger to a table, use:
-- CREATE TRIGGER tablename_audit
-- AFTER INSERT OR UPDATE OR DELETE ON tablename
-- FOR EACH ROW EXECUTE PROCEDURE audit.if_modified_func();

CREATE TRIGGER tablename_audit
AFTER INSERT OR UPDATE OR DELETE ON current_configuration_values
FOR EACH ROW EXECUTE PROCEDURE audit.if_modified_func();
