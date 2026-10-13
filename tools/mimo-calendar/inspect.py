#!/usr/bin/env python3
import json, plistlib, urllib.request
ID='77505cb6f9854801a5cfd77ab8781b2f'
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as f:return f.read()
rec=json.loads(get(f'https://www.icloud.com/shortcuts/api/records/{ID}'))
obj=plistlib.loads(get(rec['fields']['shortcut']['value']['downloadURL']))
act=obj['WFWorkflowActions']
for i in [2,16,53,58,60,83,329,340,389,397,544,549,550,557,579,582,583,584,585,586,587,588,589,590,591,592,593,594,595,596,597,598,599,600,601,602,603,604,605,606,607,608,609,610,611,612,613,614,615,616,617,618,619,620,621,622]:
 a=act[i];p=a.get('WFWorkflowActionParameters',{})
 print('INDEX',i,'ID',a['WFWorkflowActionIdentifier'])
 if i in [58,329,389,587,599]:
  print('URL',p.get('WFURL'),'HTTP',p.get('WFHTTPMethod'),'PARAM_JSON',json.dumps(p.get('WFJSONValues',{}),ensure_ascii=False,default=str)[:6500])
 elif i in [586]:
  print('SYSTEM_PROMPT_PREFIX',str(p.get('WFTextActionText',''))[:1250])
 elif i in [2,16,549,585,588,589,590,591,592,593,594,595,596,597,598,600,601,602,603,604,605,606,607,608,609,610,611,612,613,614,615,616,617,618,619,620,621,622]:
  print('PARAM',json.dumps(p,ensure_ascii=False,default=str)[:1200])
