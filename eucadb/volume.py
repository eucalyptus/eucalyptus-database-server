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
import eucalib.wsclient as ws
import eucalib.util as util
import subprocess
import config
import os
import eucadb

def get_attached_dev():
    candidates = ['vdh','vdg','vdf','vde','vdd','vdc','vdb']
    for dev in candidates:
        if os.path.exists('/dev/%s' % dev):
            return '/dev/%s' % dev
    return None

def attach_volume(volume_id, device_name, instance_id):
    try:
        con = ws.connect_ec2()
        vol = con.describe_volume(volume_id = volume_id)
        if not vol:
            raise Exception('No such volume is found')
        if vol.status != 'available':
             if vol.attachment_state() == 'attached' and vol.attach_data.instance_id == instance_id:
                return get_attached_dev()
             else:
                raise Exception('volume is not available for attachment')
    except Exception, err:
        raise Exception('Unable to find the volume (%s): %s' % (volume_id, str(err)))
 
    try:
        con.attach_volume_and_wait(volume_id, instance_id, device_name) 
    except Exception, err:
        raise Exception('Failed to attach the volume (%s): %s' % (volume_id, str(err))) 
    return get_attached_dev()

def get_mount_point(partition):
    try:
        lines = util.run_cmd(['/bin/df'])
        for line in lines.splitlines():
            if line.startswith(partition):
                tokens = line.split()
                return tokens[len(tokens)-1]
    except Exception, err:
        return None 

def partition(device_name):
    sh_file = config.PARTITION_SCRIPT
    try:
        out = util.run_cmd(['bash', sh_file, device_name])
        lines=out.splitlines()
        partition = lines[len(lines)-1]
        if not partition or not partition.startswith('/dev'):
            raise Exception('fdisk failed')
    except Exception, err:
        raise Exception(err)

    if get_mount_point(partition) != None:
        return partition

    try:
        if util.sudo('/sbin/fsck %s' % partition) != 0:
            if util.sudo('/sbin/mkfs.ext3 %s' % partition) != 0:
                raise Exception('mkfs.ext3 failed on %s' % partition)
        return partition
    except Exception, err: 
        raise Exception('Failed to make file system on %s' % partition)

def mount(partition, location):
    mounted=get_mount_point(partition)
    if mounted and mounted == location:
        return mounted
    elif mounted and mounted != location:
        raise Exception('partition is already mounted on a different location')
    else:
        if not os.path.exists(location):
            os.mkdir(location)
        if util.sudo('/bin/mount %s %s' % (partition, location)) != 0:
            raise Exception('failed to mount the partition')        
        return location
