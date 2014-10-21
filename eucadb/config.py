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
PARTITION_SCRIPT = os.path.join(SCRIPT_ROOT, "vol-partition")
PG_RUN_DIR = os.path.join(RUN_ROOT, "pgsql")
PG_DATA_DIR = os.path.join(PG_RUN_DIR, "data")
DB_PASSWORD_FILE = os.path.join(RUN_ROOT, "db_pass.in")
DB_PORT = "5432"
DATABASES = ["eucalyptus_cloudwatch_backend", "eucalyptus_reporting_backend"]

DEFAULT_PID_ROOT = "/var/run/eucalyptus-database-server"
DEFAULT_PIDFILE = os.path.join(DEFAULT_PID_ROOT, "eucadb.pid")
pidfile = DEFAULT_PIDFILE
SERVER_CERT_ARN = None
MASTER_PASSWORD_ENCRYPTED = None
VOLUME_ID = None
DEVICE_TO_ATTACH = '/dev/vdc'
def set_pidfile(filename):
    global pidfile
    global pidroot
    pidfile = filename
    pidroot = os.path.dirname(pidfile)
