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
import eucadb.volume as volume
from eucadb.euca_db_factory import get_database
from eucalib.boto_config import set_boto_config
from eucadb.config import set_pidfile
import eucalib.log_util as log_util
import eucalib.ssl as ssl
import eucalib.userdata as userdata
import eucalib.libconfig
import eucalib.util as util
import subprocess
import os
import time

__version__ = '1.0.0.-dev'
Version = __version__
log_util.init_log(config.LOG_ROOT, 'eucadb')
log = log_util.log
set_loglevel = log_util.set_loglevel


def spin_locks():
    try:
        while not (os.path.exists("/var/lib/eucalyptus-database-server/ntp.lock")) :
            time.sleep(2)
            log.debug('waiting on ntp setup (reboot if continued)')
        os.remove("/var/lib/eucalyptus-database-server/ntp.lock")
        log.debug('done ntp sync') 
    except Exception, err:
        log.error('failed to spin on locks: %s' % err)

def setup_config():
    if util.sudo('modprobe floppy > /dev/null') != 0:
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
        elif kv[0] == 'volume_id':
            eucadb.config.VOLUME_ID = kv[1]
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
db=None 

def prepare_volume():
    if not eucadb.config.VOLUME_ID:
        raise Exception('No volume ID is found for storing DB files')

    instance_id = None
    try:
        instance_id = userdata.query_meta_data('instance-id')
    except Exception, err:
        raise Exception('Could not detect the instance ID')

    if not instance_id:
        raise Exception('Could not detect the instance ID')
    volume_id = eucadb.config.VOLUME_ID
    device_name = eucadb.config.DEVICE_TO_ATTACH
    
    log.info('Attaching %s to %s at %s' % (volume_id, instance_id, device_name))

    retry = 20
    attached = False
    while retry > 0:
        try:
            device_name = volume.attach_volume(volume_id, device_name, instance_id)
            attached = True
            break
        except Exception, err:
            time.sleep(5)
        retry -= 1
    if not attached:
        raise Exception('Failed to attach the volume')
    log.info('Volume is attached')        

    partition = None
    try:
        partition = volume.partition(device_name)
    except Exception, err:
        raise Exception('Failed to prepare file system: %s' % str(err))
    if not partition:
        raise Exception('Failed to prepare file system: %s' % str(err))

    log.info('File system is ready at %s' % partition)

    if not os.path.exists(config.PG_RUN_DIR):
        os.mkdir(config.PG_RUN_DIR)

    if not os.path.exists(config.PG_DATA_DIR):
        os.mkdir(config.PG_DATA_DIR)

    try:
        mounted = volume.mount(partition, config.PG_RUN_DIR)
        if mounted != config.PG_RUN_DIR:
            raise Exception()
    except Exception, err:
        raise Exception('Failed to mount the DB data directory: %s' % str(err))

    log.info('Data files are mounted at %s' % mounted) 

    if util.sudo('/bin/chown eucalyptus:eucalyptus %s' % mounted)  != 0:
        raise Exception('Failed to chown the mounted directory')
    
def run_database():
    try:
        spin_locks()
        setup_config()
    except Exception, err:
        log.error('[critical] failed to setup service parameters: %s' % str(err))
        return

    try:
        prepare_volume()
    except Exception, err:
        log.error('[critical] failed to prepare the volume containing db files: %s' % str(err)) 
        return

    # download server certificate
    cert = None
    try:
        cert = download_server_cert()
        config.SERVER_CERT_CRT = cert.get_certificate()
        config.SERVER_CERT_KEY = cert.get_private_key()
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

    db=get_database()
    try:
        db.start()
    except Exception, err:
        log.error('[critical] failed to start the postgresql database: %s' % str(err))
        return

    idx=1
    while True:
        try:
            time.sleep(1)
            if idx % 10 == 0:
                log.info(db.status())
                idx=0
            idx+=1
        except Exception, err:
            pass
    log.info('database server has stopped')

def stop_database():
    db=get_database()
    try:
        if not db.stop():
            log.error('failed to stop the database')
    except Exception, err:
        log.error('failed to stop the database: %s' % str(err))
    return
