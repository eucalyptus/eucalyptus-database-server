# Copyright 2009-2014 Eucalyptus Systems, Inc.
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
import os
PGSQL_DIR = "/usr/pgsql-9.1/"
LOG_ROOT = "/var/log/eucalyptus-database-server"
RUN_ROOT = "/var/lib/eucalyptus-database-server"
SCRIPT_ROOT = "/usr/libexec/eucalyptus-database-server"
CONF_ROOT = "/etc/eucalyptus-database-server"
PARTITION_SCRIPT = os.path.join(SCRIPT_ROOT, "vol-partition")
PG_RUN_DIR = os.path.join(RUN_ROOT, "pgsql")
PG_DATA_DIR = os.path.join(PG_RUN_DIR, "data")
DB_PASSWORD_FILE = os.path.join(RUN_ROOT, "db_pass.in")
DB_PORT = "5432"
DATABASES = ["eucalyptus_cloudwatch_backend", "eucalyptus_reporting_backend"]

DEFAULT_PID_ROOT = "/var/run/eucalyptus-database-server"
DEFAULT_PIDFILE = os.path.join(DEFAULT_PID_ROOT, "eucadb.pid")
CONFIG_FILE = CONF_ROOT + "/database-server.conf"
pidfile = DEFAULT_PIDFILE
SERVER_CERT_ARN = None
SERVER_CERT_CRT = None
SERVER_CERT_KEY = None
MASTER_PASSWORD_ENCRYPTED = None
VOLUME_ID = None
DEVICE_TO_ATTACH = '/dev/vdc'
user_data_store = {}

def set_pidfile(filename):
    global pidfile
    global pidroot
    pidfile = filename
    pidroot = os.path.dirname(pidfile)


def read_config_file():
    try:
        f = open(CONFIG_FILE)
        content = f.read()
        lines = content.split('\n')
        for l in lines:
            if len(l.strip()):
                kv = l.split('=')
                if len(kv) == 2:
                    user_data_store[kv[0]] = kv[1]
    except Exception, err:
        raise Exception('Could not read configuration file due to %s' % err)


def get_value(key, optional=False):
    if key in user_data_store:
        return user_data_store[key]
    else:
        read_config_file()
        if key in user_data_store:
            return user_data_store[key]
        else:
            if not optional:
                raise Exception('could not find %s' % key)
            else:
                return None


def get_compute_service_url():
    return get_value('compute_service_url')


def get_euare_service_url():
    return get_value('euare_service_url')


def get_ntp_server_url():
    return get_value('ntp_server')


def get_volume_id():
    return get_value('volume_id')


def get_master_password_encrypted():
    return get_value('master_password_encrypted')


def get_server_cert_arn():
    return get_value('server_cert_arn')