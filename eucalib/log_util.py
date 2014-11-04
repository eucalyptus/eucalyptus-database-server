# Copyright 2009-2013 Eucalyptus Systems, Inc.
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

import logging
import os
from logging.handlers import RotatingFileHandler
#
# We can't specify the log file in the config module since that will
# import boto and keep us from initializing the boto logger.
#

# Log level will default to WARN
# If you want more information (like DEBUG) you will have to set the log level
log  = None
def init_log(log_dir, log_name, log_level=logging.INFO):
    global log
    LOG_FILE = os.path.join(log_dir, '%s.log' % log_name)
    LOG_FORMAT = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
    LOG_BYTES = 1024 * 1024 # 1MB
    logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT)
    log = logging.getLogger(log_name)
    LOG_HANDLER = RotatingFileHandler(LOG_FILE, maxBytes=LOG_BYTES, backupCount=5)
    log.setLevel(log_level)
    log.addHandler(LOG_HANDLER)

def set_loglevel(lvl):
    global log
    lvl_num = None
    if isinstance(lvl, str):
        try:
            lvl_num = logging.__getattribute__(lvl.upper())
        except AttributeError:
            log.warn("Failed to set log level to '%s'" % lvl)
            return
    else:
        lvl_num = lvl
    log.setLevel(lvl_num)
