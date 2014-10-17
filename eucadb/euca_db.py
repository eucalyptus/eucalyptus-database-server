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
from subprocess import Popen, PIPE
import eucadb

class EucaDatabase (object):
    def __init__(self):
        raise NotImplementedError
 
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
 
    def check_version(self):
        raise NotImplementedError
        
    def init_db(self):
        raise NotImplementedError

    def create_db(self, databases):
        raise NotImplementedError

    def create_users(self):
        raise NotImplementedError
    
    def start_server(self):
        raise NotImplementedError

    def verify(self):
        raise NotImplementedError

    def run_cmd(self, args=[], async=False, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE):
        eucadb.log.debug("command line: %s" % ' '.join(args))
        p = Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell)
        if not async:
            out, err = p.communicate()
            if p.returncode == 0:
                if out and len(out)>0: return out
                else: return err
            else:
                eucadb.log.debug('STDOUT: %s\nSTDERR: %s' % (out , err))
                raise Exception("return code: %d\nSTDOUT: %s\nSTDERR: %s" % (p.returncode, out, err))

    def status(self):
        raise NotImplementedError

    def is_running(self):
        raise NotImplementedError
