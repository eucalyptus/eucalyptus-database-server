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
import httplib2
def query_user_data():
    resp, content = httplib2.Http().request("http://169.254.169.254/latest/user-data")
    if resp['status'] != '200' or len(content) <= 0:
        raise Exception('could not query the userdata')
    #remove extra euca-.... line
    return content

def query_meta_data(key):
    resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/%s" % key)
    if resp['status'] != '200' or len(content) <= 0:
        raise Exception('could not query the userdata')
    #remove extra euca-.... line
    return content
