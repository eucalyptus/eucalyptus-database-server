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
import subprocess
import commands
import os
import json
import libconfig

class FloppyCredential(object):
    def __init__(self, floppy_mount_dir=None):
        #check if floppy is mounted. if not mount it
        if not floppy_mount_dir:
            floppy_mount_dir = libconfig.RUN_DIRECTORY+'/floppy'
        try:
            if not self.is_floppy_mounted():
                self.mount_floppy(dir=floppy_mount_dir)
            f = None
            f = open('%s/credential' % floppy_mount_dir)
            cred = None
            if f:
                cred = json.load(f)
                f.close()
            self.unmount_floppy(dir=floppy_mount_dir)
            self.iam_pub_key = cred['iam_pub_key']
            self.iam_pub_key = self.iam_pub_key.strip().decode('base64')
            self.instance_pub_key = cred['instance_pub_key']
            self.instance_pub_key = self.instance_pub_key.strip().decode('base64')
            self.instance_pk = cred['instance_pk']
            self.instance_pk = self.instance_pk.strip().decode('base64')
            self.iam_token = cred['iam_token']
            self.iam_token = self.iam_token.strip()
            try:
                self.euca_cert = cred['euca_pub_key']
                self.euca_cert = self.euca_cert.strip().decode('base64')
            except Exception, err:
                pass
        except IOError, err:
            raise Exception('failed to read credential file on floppy: ' + str(err))
        except Exception, err:
            raise Exception('failed to parse credential file: ' + str(err))

    @staticmethod
    def is_floppy_mounted(dev_str='/dev/fd0'):
        cmd_line = 'sudo /bin/mount | grep %s > /dev/null' % dev_str
        if subprocess.call(cmd_line, shell=True) == 0:
            return True
        else:
            return False

    def mount_floppy(self, dev='/dev/fd0', dir=None):
        if not os.path.exists(dir):
            os.makedirs(dir)
        cmd_line = 'sudo /bin/mount %s %s' % (dev, dir)
        if subprocess.call(cmd_line, shell=True) != 0:
            raise Exception('failed to mount floppy')

    def unmount_floppy(self, dir=None):
        if not os.path.exists(dir):
            return
        cmd_line = 'sudo /bin/umount %s' % dir
        if subprocess.call(cmd_line, shell=True) != 0:
            raise Exception('failed to unmount floppy')

    def get_iam_pub_key(self):
        return self.iam_pub_key

    def get_cloud_cert(self):
        return self.euca_cert

    def get_instance_pub_key(self):
        return self.instance_pub_key

    def get_instance_pk(self):
        return self.instance_pk

    def get_iam_token(self):
        return self.iam_token 
