#  Copyright 2009-2014 Eucalyptus Systems, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
# Please contact Eucalyptus Systems, Inc., 6755 Hollister Ave., Goleta
# CA 93117, USA or visit http://www.eucalyptus.com/licenses/ if you need
# additional information or have any questions.

#
# Order matters here. We want to make sure we initialize logging before anything
# else happens. We need to initialize the logger that boto will be using.
#
import config
import os
import eucadb
import time
from eucadb.euca_db import EucaDatabase

pg_dir=config.PGSQL_DIR
pg_run_dir=config.PG_RUN_DIR
pg_bin_dir=os.path.join(pg_dir,"bin")
pg_initdb=os.path.join(pg_bin_dir,"initdb")
pg_psql=os.path.join(pg_bin_dir,"psql")
pg_createdb=os.path.join(pg_bin_dir, "createdb")
pg_encoding="--encoding=UTF8"
pg_locale="--locale=C"
pg_user_opt="-U eucalyptus"
pg_trust_opt = "--auth=password"
pg_pwd_file = "--pwfile="+config.DB_PASSWORD_FILE
pg_db_dir = config.PG_DATA_DIR
pg_db_opt = "-D"+pg_db_dir
pg_x_dir = os.path.join(pg_run_dir, "tx")
pg_x_opt = "-X"+pg_x_dir
pg_ctl = os.path.join(pg_bin_dir,"pg_ctl")
pg_start = "start"
pg_stop = "stop"
pg_status = "status"
pg_mode = "-mf"
pg_pid  = os.path.join(pg_db_dir, "postmaster.pid")
pg_w_opt = "-w"
pg_s_opt = "-s"
pg_port_opts = "-o -p%s" % (config.DB_PORT)

class EucaDatabasePostgresql(EucaDatabase):
    def __init__(self):
        self.created_dbs = []

    def start(self):
        if not self.check_version():
            eucadb.log.error('Version check failed')
            return False

        if not self.init_db():
            eucadb.log.error('Initdb failed')
            return False

        if not self.start_server():
            eucadb.log.error('Start-server failed')
            return False
        
        try:
            time.sleep(10)
        except Exception, err:
            pass

        if not self.create_db(config.DATABASES):
            eucadb.log.error('Creating DBs failed')
            return False
 
        if not self.create_users():
            eucadb.log.error('Creating users failed')
            return False

        if not self.verify():
            eucadb.log.error('Verification failed')
            return False

        eucadb.log.info('Postgresql successfuly launched with databases: %s' % str(config.DATABASES))

        return True
    def check_version(self):
        expected = "9.1"
        version = self.run_cmd([pg_initdb, "--version"])
        tokens = version.split()
        version = tokens[len(tokens)-1]
        eucadb.log.info("postgresql version: "+version)
        if not version.startswith(expected):
            return False
        return True
       
    def init_db(self):
        # check if the data directory is empty; if not return True
        conf_file = os.path.join(pg_db_dir, 'postgresql.conf')
        if os.path.exists(conf_file):
            eucadb.log.info('Existing database is found; skipping initdb')
        else:
            if not os.path.exists(pg_run_dir):
                os.mkdir(pg_run_dir)
            # do initdb
            try:
                cmdline = [pg_initdb, pg_pwd_file, pg_encoding, pg_locale, pg_user_opt, pg_trust_opt, pg_db_opt, pg_x_opt]
                # for mysterious reason, pwfile option is not being honored correctly when popen.call is invoked
                # workaround is to run a bash with the command line as a whole
                sh_file = os.path.join(config.RUN_ROOT, "initdb.sh")
                with open(sh_file, "w+") as fp:
                    fp.writelines(['#!/bin/bash\n', ' '.join(cmdline) + '\n'])
                    fp.close()
                self.run_cmd(['bash', sh_file])
                eucadb.log.info('Initialized the database')
            except Exception, err:
                eucadb.log.error('Failed to initialize the database: %s' % str(err))
                return False
  
        # update pg_hba.conf
        try:
            pghba_file = os.path.join(pg_db_dir, "pg_hba.conf")
            self.update_pghba(pghba_file)
            eucadb.log.info('Updated pg_hba.conf')
        except Exception, err:
            eucadb.log.error('Failed to update pg_hba.conf: %s' % str(err))
            return False

        # update postgresql.conf 
        try:
            conf_file = os.path.join(pg_db_dir, "postgresql.conf")
            self.update_conf(conf_file)
            eucadb.log.info('Updated postgresql.conf')
        except Exception, err:
            eucadb.log.error('Failed to update postgresql.conf: %s' % str(err))
            return False

        # get the cert/key ready for ssl
        cert_file=os.path.join(config.PG_DATA_DIR, "server.crt")
        with open(cert_file, "w+") as fp:
            fp.writelines([config.SERVER_CERT_CRT])
            fp.close()

        key_file=os.path.join(config.PG_DATA_DIR, "server.key")
        with open(key_file, "w+") as fp:
            fp.writelines([config.SERVER_CERT_KEY])
            fp.close()
        os.chmod(key_file, 0600)

        return True
    
    def start_server(self): 
        # look for the pid file; if found; stop the process
        if self.is_running() and os.path.exists(pg_pid):
            eucadb.log.info('Shutting down the existing database')
            try:
                self.run_cmd([pg_ctl, pg_stop, pg_mode, pg_db_opt])
            except Exception, err:
                eucadb.log.error('Failed to shutdown the database: %s' % str(err))
                return False 
  
        try:
           eucadb.log.info('Starting up Postgresql')
           self.run_cmd([pg_ctl, pg_start, pg_w_opt, pg_s_opt, pg_db_opt, pg_port_opts], async=True)
        except Exception, err:
           eucadb.log.error('Failed to start Postgresql: %s' % str(err))
           return False

        max_wait = 10 # wait upto 10 sec
        for i in range(0, max_wait):
            try:
                eucadb.log.debug('Waiting for postgresql: %d' % i)
                time.sleep(1)
                if self.is_running():
                    break
            except Exception, err:
                continue
            if i >= max_wait-1:
                eucadb.log.error('Failed to start Postgresql')
                return False
        eucadb.log.info('Postgre started successfully')

        return True

    def create_db(self, databases):
        if not databases or len(databases) <= 0:
            eucadb.log.error('Databases must be specified')
            return False

        if not self.is_running():
            eucadb.log.error('Postgresql must be running to create a database')
            return False

        for db in databases:
            eucadb.log.info('Creating database: %s' % db)
            if self.db_exists(db):
                eucadb.log.info('Database [%s] already exists' % db)
                if db not in self.created_dbs:
                    self.created_dbs.append(db)
                continue
   
            try:
                self.run_cmd([pg_createdb, "-h%s" % pg_db_dir, "-p%s" % config.DB_PORT, db]) 
                if db not in self.created_dbs:
                    self.created_dbs.append(db)
            except Exception, err:
                eucadb.log.error('Failed to create database: %s' % str(err))
                return False
        return True

    def create_users(self):
        if not self.is_running():
            eucadb.log.error('Postgresql must be running to create users')
            return False

        for db in self.created_dbs:
            try:
                self.run_cmd([pg_psql,"-h%s" % pg_db_dir, "-p%s" % config.DB_PORT, db, "-c CREATE USER root WITH CREATEUSER"])
            except Exception, err:
                if str(err) and str(err).find('already exists'):
                    return True
                eucadb.log.error('Failed to create users for database: %s ' % db)
                return False
        return True

    def verify(self):
        for db_name in self.created_dbs:
            if not self.db_exists(db_name):
                eucadb.log.error('Verification failed for database: %s' % db_name)
                return False
        return True


    def status(self):
        if self.is_running():
            pid='-1'
            try:
                with open(pg_pid, "r") as fp:
                    contents = fp.readlines()
                    fp.close()
                pid = contents[0]
                pid = pid.strip('\n')
            except Exception,err:
                pass
            return 'Postgresql is running (pid=%s)' % pid
        else:
            return '[Failed] Postgresql is not running'

    def stop(self):
        if self.is_running() and os.path.exists(pg_pid):
            eucadb.log.info('Shutting down the database')
            try:
                self.run_cmd([pg_ctl, pg_stop, pg_mode, pg_db_opt])
            except Exception, err:
                eucadb.log.error('Failed to shutdown the database: %s' % str(err))
                return False 
        return True
  

    def db_exists(self, db_name):
        try:
            self.run_cmd([pg_psql,"-h%s" % pg_db_dir, "-p%s" % config.DB_PORT, db_name, "-c Select User"]) 
            return True
        except Exception, err:
            return False


    def is_running(self):
        try:
            self.run_cmd([pg_ctl, pg_status, pg_db_opt])
            return True
        except Exception, err:
            return False  
      
    def update_pghba(self, conf_file):
        if not os.access(conf_file, os.R_OK|os.W_OK):
            raise Exception("No rw permission to the file: "+conf_file)
        new_contents = []
        with open(conf_file, "r") as fp:
            contents = fp.readlines()
            fp.close()
        for line in contents:
            if line.startswith('#'):
                new_contents.append(line) 

        # TODO: restrict to only from the clc? 
        new_lines = ["local   all             eucalyptus                                     peer\n",\
                     "host    all             eucalyptus             all            md5\n" ]
        new_contents.extend(new_lines)
        backup=conf_file+".orig"
        os.rename(conf_file, backup)
        with open(conf_file, "w+") as fp:
            fp.writelines(new_contents)
            fp.close()

    def update_conf(self, conf_file):
        if not os.access(conf_file, os.R_OK|os.W_OK):
            raise Exception("No rw permission to the file: "+conf_file) 
        with open(conf_file, "r") as fp:
            contents = fp.readlines()
            fp.close()

        new_contents = []
        for line in contents:
            if line.startswith('#listen_addresses') or line.startswith('listen_addresses'):
                line = 'listen_addresses = \'*\'\n'
            elif line.startswith('#unix_socket_directory') or line.startswith('unix_socket_directory'):
                line = 'unix_socket_directory = \'%s\'\n' % pg_db_dir
            elif line.startswith('#ssl =') or line.startswith('ssl ='):
                line = 'ssl = on\n'
            elif line.startswith('#ssl_ciphers =') or line.startswith('ssl_ciphers ='):
                line = 'ssl_ciphers = \'AES128-SHA:AES256-SHA\'\n'
            new_contents.append(line)
        backup = conf_file + ".orig" 
        os.rename(conf_file, backup)

        with open(conf_file, "w") as fp:
            fp.writelines(new_contents)
            fp.close()
      
