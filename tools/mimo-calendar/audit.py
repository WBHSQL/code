#!/usr/bin/env python3
import json, plistlib, urllib.request, re, hashlib
from collections import Counter
ID='77505cb6f9854801a5cfd77ab8781b2f'
base=f'https://www.icloud.com/shortcuts/api/records/{ID}'
def get(url):
 r=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'*/*'})
 with urllib.request.urlopen(r,timeout=45) as f:return f.read()
record=json.loads(get(base))
url=record['fields']['shortcut']['value']['downloadURL']
print('ORIGINAL_NAME',record['fields']['name']['value'])
print('EXPECTED_BYTES',record['fields']['shortcut']['value']['size'])
try:raw=get(url)
except Exception as e:
 print('DIRECT_DOWNLOAD_FAILED',repr(e))
 for f in ['shortcut.shortcut','',record['fields']['name']['value']+'.shortcut']:
  try:raw=get(url.replace('${f}',f));print('SUCCEEDED_WITH_REPLACEMENT',f);break
  except Exception as exc:print('RETRY_FAILED',f,repr(exc))
 else:raise RuntimeError('Cannot download shortcut from public link')
print('RECEIVED_BYTES',len(raw),'SHA256',hashlib.sha256(raw).hexdigest(),'HEADER',raw[:6].hex())
try:obj=plistlib.loads(raw)
except Exception as exc:raise RuntimeError('Not a raw plist; alternative extraction needed') from exc
actions=obj.get('WFWorkflowActions',[])
print('ACTION_COUNT',len(actions))
print('ACTION_IDS',Counter(a['WFWorkflowActionIdentifier'] for a in actions).most_common())
for i,a in enumerate(actions):
 s=str(a.get('WFWorkflowActionParameters',{}))
 matches=re.findall(r'.{0,80}(?:api[.]openai[.]com|openai|gpt[-_]|chat/completions|responses|Authorization|bearer).{0,80}',s,re.I)
 if matches or any(z in a['WFWorkflowActionIdentifier'].lower() for z in ['url','http','dictionary','getvalue','getcontents']):
  print('STEP',i,a['WFWorkflowActionIdentifier'],'MATCHES',matches[:6],'PARAM_KEYS',sorted(a.get('WFWorkflowActionParameters',{})))
