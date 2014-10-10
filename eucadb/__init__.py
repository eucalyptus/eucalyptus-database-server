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
import M2Crypto

import eucadb.config
from eucadb.euca_db_factory import get_database
from eucalib.boto_config import set_boto_config
from eucadb.config import set_pidfile
import eucalib.log_util as log_util
import eucalib.ssl as ssl
import eucalib.userdata as userdata
import eucalib.libconfig
import subprocess
import os

__version__ = '1.0.0.-dev'
Version = __version__
log_util.init_log(config.LOG_ROOT, 'eucadb')
log = log_util.log
set_loglevel = log_util.set_loglevel

def run_as_sudo(cmd):
    return subprocess.call('sudo %s' % cmd, shell=True)

def spin_locks():
    try:
        while not (os.path.exists("/var/lib/eucalyptus-database-server/ntp.lock")) :
            time.sleep(2)
            log.debug('waiting on ntp setup (reboot if continued)')
        os.remove("/var/lib/eucalyptus-database-server/ntp.lock")
    except Exception, err:
        log.error('failed to spin on locks: %s' % err)

def setup_config():
    if run_as_sudo('modprobe floppy > /dev/null') != 0:
        raise('failed to load floppy driver')

    contents = userdata.query_user_data()
    lines = contents.split('\n')
    if len(lines) < 4:
        raise Exception('malformed user data')
    eucadb.config.SERVER_CERT_ARN=lines[1].strip('\n') 
    eucadb.config.MASTER_PASSWORD_ENCRYPTED=lines[2].strip('\n')

    kvlist = lines[3].split(';')
    for word in kvlist:
        kv = word.split('=')
        if len(kv) != 2:
            continue
        if kv[0] == 'compute_service_url':
            eucalib.libconfig.COMPUTE_SERVICE_URL= kv[1]
        elif kv[0] == 'euare_service_url':
            eucalib.libconfig.EUARE_SERVICE_URL=kv[1]
    eucalib.libconfig.RUN_DIRECTORY=eucadb.config.RUN_ROOT

    # tmp fix 
def download_server_cert():
    return ssl.download_server_certificate(eucadb.config.SERVER_CERT_ARN)

def decrypt_master_password(server_cert):
    cert = server_cert.get_certificate()
    pk = server_cert.get_private_key()
    rsa = M2Crypto.RSA.load_key_string(pk)
    passwd = None
    try:
        passwd = rsa.private_decrypt(eucadb.config.MASTER_PASSWORD_ENCRYPTED.decode('base64'), M2Crypto.RSA.pkcs1_padding)
    except Exception, err:
        raise Exception('failed to decrypt: %s' % str(err))
    return passwd

def write_master_password(password):
    pwd_file = eucadb.config.DB_PASSWORD_FILE
    with open(pwd_file, "w+") as fp:
        fp.writelines([password])
        fp.close()
 
def start_database():
    try:
        spin_locks()
        setup_config()
    except Exception, err:
        log.error('[critical] failed to setup service parameters: %s' % str(err))
        return

    # download server certificate
    cert = None
    try:
        cert = download_server_cert()
    except Exception, err:
        log.error('[critical] failed to download server certificate: %s' % str(err))
        return        

    # decrypt the master password
    password = None
    try:
        password = decrypt_master_password(cert)
    except Exception, err:
        log.error('[critical] failed to decrypt master database password: %s' % str(err))
        return
    
    # write the master password to the password file
    try:
        write_master_password(password)
    except Exception, err:
        log.error('[critical] failed to write the master password: %s' % str(err))
        return

    try:
        get_database().start()
    except Exception, err:
        log.error('[critical] failed to start the postgresql database: %s' % str(err))
        return
