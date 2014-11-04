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

from subprocess import Popen, PIPE
import subprocess

def run_cmd(args=[], async=False, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE):
    p = Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell)
    if not async:
        out, err = p.communicate()
        if p.returncode == 0:
            if out and len(out)>0: 
                return out
            else: 
                return err
        else:
            raise Exception("return code: %d\nSTDOUT: %s\nSTDERR: %s" % (p.returncode, out, err))

def sudo(cmd):
    return subprocess.call('sudo %s' % cmd, shell=True)
