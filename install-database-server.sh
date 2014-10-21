#!/bin/bash
#
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

#
# Simple script to install the servo service without using a package manager

# Install python code
python setup.py install

# Setup eucalyptus user
useradd -s /sbin/nologin -d /var/lib/eucalyptus-database-server -M eucalyptus
install -v -m 0440 scripts/eucadb-sudoers.conf /etc/sudoers.d/eucadb

# Setup needed for eucalyptus db service
install -v -m 755 scripts/eucalyptus-database-server-init /etc/init.d/eucalyptus-database-server
sed -i 's/LOGLEVEL=info/LOGLEVEL=debug/' /etc/init.d/eucalyptus-database-server
# Use set gid for service owned directories
install -v -m 6700 -o eucalyptus -g eucalyptus -d /var/{run,lib,log}/eucalyptus-database-server
chown eucalyptus:eucalyptus -R /etc/eucalyptus-database-server
chmod 700 /etc/eucalyptus-database-server

# NTP cronjob
install -p -m 755 -D scripts/server-ntp-update /usr/libexec/eucalyptus-database-server/ntp-update
install -p -m 755 -D scripts/vol-partition /usr/libexec/eucalyptus-database-server/vol-partition
install -p -m 0750 -D scripts/database-server.cron /etc/cron.d/eucalyptus-database-server
chmod 0640 /etc/cron.d/eucalyptus-database-server
