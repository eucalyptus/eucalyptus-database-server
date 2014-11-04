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

import boto
import boto.provider
import os

boto_config = None
cred_provider = None
def get_provider():
    global boto_config
    global cred_provider
    if not cred_provider:
        if boto_config:
            boto.provider.config = boto.Config(boto_config)
        cred_provider = boto.provider.get_default()
    return cred_provider

def set_boto_config(filename):
    if not os.path.isfile(filename):
        raise Exception('could not find boto config {0}'.format(filename))
    global boto_config
    boto_config = filename

def get_access_key_id():
    akey = get_provider().get_access_key()
    return akey

def get_secret_access_key():
    skey = get_provider().get_secret_key()
    return skey

def get_security_token():
    token = get_provider().get_security_token()
    return token

