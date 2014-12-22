%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           eucalyptus-database-server
Version:        %{build_version}
Release:        0%{?build_id:.%build_id}%{?dist}
Summary:        Configuration tool for the Eucalyptus DB

Group:          Applications/System
License:        GPLv3 
URL:            http://www.eucalyptus.com
Source0:        %{tarball_basedir}.tar.xz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch

BuildRequires:  python%{?__python_ver}-devel
BuildRequires:  python%{?__python_ver}-setuptools

Requires:       python%{?__python_ver}
Requires:       python%{?__python_ver}-boto
Requires:       python%{?__python_ver}-httplib2
Requires:       python%{?__python_ver}-m2ext
Requires:       python%{?__python_ver}-lxml
Requires:       sudo
Requires:       crontabs
Requires:       ntp
Requires:       ntpdate
Requires:       postgresql92-server
Requires(pre):  %{_sbindir}/useradd
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts

%description
Configuration tool for the Eucalyptus DB

%prep
%setup -q -n %{tarball_basedir}

%build
# Build CLI tools
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT

# Install CLI tools
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

#
# There is no extension on the installed sudoers file for a reason
# It will only be read by sudo if there is *no* extension
#
install -p -m 0440 -D scripts/eucadb-sudoers.conf $RPM_BUILD_ROOT/%{_sysconfdir}/sudoers.d/eucadb
install -p -m 755 -D scripts/eucalyptus-database-server-init $RPM_BUILD_ROOT/%{_initddir}/eucalyptus-database-server
install -p -m 755 -D scripts/server-ntp-update $RPM_BUILD_ROOT%{_libexecdir}/%{name}/ntp-update
install -p -m 755 -D scripts/vol-partition $RPM_BUILD_ROOT%{_libexecdir}/%{name}/vol-partition
install -m 6700 -d $RPM_BUILD_ROOT/%{_var}/{run,lib,log}/eucalyptus-database-server
install -p -m 0750 -D scripts/database-server.cron $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/%{name}
chmod 0640 $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent passwd eucalyptus >/dev/null || \
    useradd -d %{_var}/lib/eucalyptus-database-server \
    -M -s /sbin/nologin eucalyptus

# Stop running services for upgrade
if [ "$1" = "2" ]; then
    /sbin/service %{name} stop 2>/dev/null || :
fi

%post
/sbin/chkconfig --add %{name}

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%files
%defattr(-,root,root,-)
%doc README.md LICENSE
%{python_sitelib}/*
%{_bindir}/eucalyptus-database-server
%{_sysconfdir}/sudoers.d/eucadb
%{_initddir}/eucalyptus-database-server
%{_libexecdir}/%{name}
%config(noreplace) %{_sysconfdir}/cron.d/%{name}

%defattr(-,eucalyptus,eucalyptus,-)
%dir %{_sysconfdir}/eucalyptus-database-server
%dir %{_var}/run/eucalyptus-database-server
%dir %{_var}/log/eucalyptus-database-server
%dir %{_var}/lib/eucalyptus-database-server
%config(noreplace) %{_sysconfdir}/eucalyptus-database-server/boto.cfg

%changelog
* Thu Dec 22 2014 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.0.0-0
- Initial build
