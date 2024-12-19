# zabbix-cloud-director-leases
Tool to search for Organizations in VMware Cloud Director with active lease expiration enabled and Zabbix template to use with.

This script is designed for searching Organisation in VMware Cloud Director with active leases and sendig result to Zabbix. 

    Installed and working python3 with standart library
    Installed zappix:

python3 -m pip install setuptools --upgrade
python3 -m pip install zappix

Usage of script (copypaste from '--help'):

Usage: vCloud-GetOrgsWithLeases.py [options]

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

Use with zabbix

    Clone repository
    Import .xml file into Zabbix as Template
    Deploy .py script on to Zabbix server to externalscripts folder
    Edit script attributes, eg:

chmod +x vCloud-GetOrgsWithLeases.py
chown zabbix:zabbix vCloud-GetOrgsWithLeases.py

    Check that zappix module installed on server (see Prerequiements)
    Apply template Template module VMware VCSA old snapshots to host
