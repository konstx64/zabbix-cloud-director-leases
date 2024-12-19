# zabbix-cloud-director-leases
Tool to search for Organizations in VMware Cloud Director with active lease expiration enabled and Zabbix template to use with.

This script is designed for searching Organisation in VMware Cloud Director with active leases and sendig result to Zabbix. 
## Prerequiements

   1) Installed and working python3 with standart library
   2) Installed zappix
```
python3 -m pip install setuptools --upgrade
python3 -m pip install zappix
```
## Usage of script (copypaste from '--help'):

Usage: vCloud-GetOrgsWithLeases.py [options]
```
Options:
  --help                             Show this message and exit
  --vcloud=VCLOUD                    vCloud IP address/DNS name. Mandatory option.
  --apiversion=APIVERSION            vCloud Api Version. Mandatory option.
  --username=USERNAME                vCloud username. Mandatory option.
  --password=PASSWORD                vCloud password. Mandatory option.
  --zabbix=ZABBIX                    Zabbix server to send data. Default = 127.0.0.1
  --zabbixport=ZABBIXPORT            Zabbix server port to send data. Default = 10050
  --zabbixhostname=ZABBIXHOSTPREFIX  Zabbix hosts name. Determine host that contain item
  --zabbixkey=ZABBIXKEY              Zabbix item that recieve data
  -l, --logging                      Enable logging to STDOUT
```
## Use with zabbix

   
1) Clone repository
2) Import .xml file into Zabbix as Template
3) Deploy .py script on to Zabbix server to externalscripts folder
4) Edit script attributes, eg:

```
chmod +x vCloud-GetOrgsWithLeases.py
chown zabbix:zabbix vCloud-GetOrgsWithLeases.py
```
5) Check that zappix module installed on server (see Prerequiements)
6) Apply template Template module to Zabbix host
