#!/usr/bin/env python3

import sys
import requests
import time
import logging
import json
import base64
import concurrent.futures
from optparse import OptionParser

try:
    from zappix.sender import Sender
except ImportError:
    sys.exit('Failed to import zappix module. Try "pip3 install zappix"')

requests.packages.urllib3.disable_warnings()


logger      = logging.getLogger()


def parseCommandOptions():

    # Parsing input parameters
    p = OptionParser(add_help_option=False,
                     usage = '%prog [options]'
    )
    p.add_option('--help',
                 action = 'store_true',
                 dest = 'help',
                 help = 'Show this message and exit'
    )
    p.add_option("--vcloud",
                 dest="vcloud",
                 help="vCloud IP address/DNS name. Mandatory option."
    )
    p.add_option("--apiversion",
                 dest="apiversion",
                 help="vCloud Api Version. Mandatory option."
    )
    p.add_option("--username",
                 dest="username",
                 help="vCloud username. Mandatory option."
    )
    p.add_option("--password",
                 dest="password",
                 help="vCloud password. Mandatory option."
    )
    p.add_option('--zabbix',
                 dest = 'zabbix',
                 default = '127.0.0.1', 
                 help = 'Zabbix server to send data. Default = 127.0.0.1',
    )
    p.add_option('--zabbixport',
                 dest = 'zabbixport',
                 default = '10051', 
                 help = 'Zabbix server port to send data. Default = 10050',
    )
    p.add_option('--zabbixhostname',
                 dest = 'zabbixhostprefix', 
                 help = 'Zabbix hosts name. Determine host that contain item',
    ) 
    p.add_option('--zabbixkey',
                 dest = 'zabbixkey', 
                 help = 'Zabbix item that recieve data',
    ) 
    p.add_option('-l', '--logging',
                 dest = 'enablelogging',
                 help = 'Enable logging to STDOUT',
                 action='store_true'
    )

    (options, args) = p.parse_args()

    if options.help:
        p.print_help()
        exit()

    ## Setup logging
    if options.enablelogging:
        loglevel = 'INFO'
        logFormatStr = '%(asctime)s - %(levelname)-8s - %(message)s'
        logger.setLevel(loglevel)
        chandler = logging.StreamHandler()
        formatter = logging.Formatter(logFormatStr)
        chandler.setFormatter(formatter)
        logger.addHandler(chandler)
    else:
        logging.getLogger('urllib3').setLevel(logging.ERROR)

    main(
            options.vcloud,
            options.username,
            options.password,
            options.apiversion,
            options.zabbix,
            options.zabbixport,
            options.zabbixhostprefix,
            options.zabbixkey
        )


def main(srv, login, password, apiVersion, zabbixSrv, zabbixPort, zabbixHostPrefix, zabbixKey):
  logging.info('Script started')

  sender = Sender(server=zabbixSrv, port=int(zabbixPort))


  try:  
    logging.info('Connecting to vCloud {}'.format(srv))
    # basic auth and get token
    authStr = "Basic " + base64.b64encode(f'{login}:{password}'.encode('ascii')).decode('ascii')
    loginUrl = f'https://{srv}/api/sessions'
    headers = {
      "Authorization" : authStr,
      "Accept"        : f'application/*+json;version={apiVersion}',
      "Content-Type"  : "application/json;charset=utf-8"
    }

    try:
      response = requests.post(loginUrl, headers=headers, verify=False)
    except Exception as e:
        logging.error('Error connecting: {}'.format(e))
        raise


    token = response.headers['x-vcloud-authorization']
    logging.info('vCloud token collected')


    # set default header
    headers = {
      "x-vcloud-authorization" : token,
      "Accept"        : f'application/*+json;version={apiVersion}',
      "Content-Type"  : "application/json;charset=utf-8"
    }



    # get id from string like "urn:vcloud:org:002fbc07-500b-41f5-ad02-59dad31b0860"
    def getId(str):
      return str.split(':')[-1]

    def prepareOrg(org):
      return {
        'id': getId(org['id']), 
        'name': org['name'],
        'displayName' : org['displayName']
      }

    # getting one page
    def getPage(url, page=1, pageSize=100):
      logging.info('getPage: {}'.format(page))
      f_url = f'{url}&page={page}&pageSize={pageSize}'
      try:
        response = requests.get(f_url, headers=headers, verify=False).text
        return  json.loads(response)
      except Exception as e:
        logging.error('Error getPage: {}'.format(e))
        raise

    # query list of vORGs page by page, return an array of IDs
    def getOrgDetails():
      logging.info('getOrgDetails')
      url = f'https://{srv}/api/query?format=idrecords&type=organization'
      firstPage = getPage(url)
      pageSize = firstPage["pageSize"]  
      total = firstPage["total"]
      orgIds = []
      for org in firstPage["record"]:
        orgIds.append(prepareOrg(org))

      pagesCount = (total // pageSize + (1 if total % pageSize else 0)) # подсчет количества страниц, минусуем первую которую уже прочитали
      for page in range(2, pagesCount + 1):
        pageData = getPage(url, page, pageSize)
        for org in pageData["record"]:
          orgIds.append(prepareOrg(org))
      return orgIds

    def getOrgSettings(orgId):
      logging.info('getOrgSettings OrgId: {}'.format(orgId))
      url = f'https://{srv}/api/admin/org/{orgId}/settings'
      try:
        response = requests.get(url, headers=headers, verify=False).text
        return  json.loads(response)
      except Exception as e:
        logging.error('Error getPage: {}'.format(e))
        raise

    def thread_fnc(orgList):
      badOrgs = []
      resStr = ''
      index = 0    
      for org in orgList:
        index += 1
        orgSetting = getOrgSettings(org['id'])
        vAppLeaseSettings = orgSetting['vAppLeaseSettings']
        isBad = False
        if vAppLeaseSettings['deploymentLeaseSeconds'] > 0:
          isBad = True
        if vAppLeaseSettings['storageLeaseSeconds'] > 0:
          isBad = True
          
        vAppTemplateLeaseSettings = orgSetting['vAppTemplateLeaseSettings']
        if vAppTemplateLeaseSettings['storageLeaseSeconds'] > 0:
          isBad = True

        if isBad:
          badOrgs.append(org)
          orgName = org['name']
          orgId = org['id']
          resStr += f'{orgName}({orgId}), ' 
          logging.info('bad org: {}'.format(orgName))
      return resStr


    with concurrent.futures.ThreadPoolExecutor() as executor:
      orgsDetails = getOrgDetails()
      THREAD_COUNT = 6
      chunkSize = len(orgsDetails) // THREAD_COUNT

      def divide_chunks(l, n):
        for i in range(0, len(l), n): 
          yield l[i:i + n]
            
      futures = []
      for orgsChunk in divide_chunks(orgsDetails, chunkSize):
        futures.append(executor.submit(thread_fnc, orgList=orgsChunk))

      concurrent.futures.wait(futures)
      finalResponse = ''
      for future in concurrent.futures.as_completed(futures):
        isFault = False
        try:
          finalResponse += future.result()
        except:
          isFault = True
      
      if isFault:
        raise

      if len(finalResponse) > 0:
          logging.info('Send to zabbix: Org list' + finalResponse )
          o = sender.send_value(
              host = zabbixHostPrefix,
              key = zabbixKey,
              value = 'Organization name and ID:' +  finalResponse
              )
      else:
          logging.info('Send to zabbix: Script execution successfull. All lease values are correct')
          o = sender.send_value(
                  host = zabbixHostPrefix,
                  key = zabbixKey,
                  value = 'Script execution successfull. All lease values are correct'
              )
  except:
      logging.info('Send to zabbix: Script execution failed. Check logs')
      o = sender.send_value(
            host=zabbixHostPrefix,
            key = zabbixKey,
            value = 'Script execution failed. Check logs'
        )
    

if __name__ == '__main__':
  parseCommandOptions()
