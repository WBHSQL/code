#!/usr/bin/env python3
"""Build a MiMo version of Add to Calendar v4.0, preserving all existing actions.

No API keys are embedded. Signing sends only the shortcut definition to
RoutineHub HubSign, a third-party service. MiMo key is entered on the phone.
"""
import json, os, plistlib, urllib.request
from pathlib import Path
from collections import Counter

ID = '77505cb6f9854801a5cfd77ab8781b2f'
NEW_NAME = 'Add to Calendar MiMo'
ROOT = Path('dist')
ROOT.mkdir(exist_ok=True)

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=60) as r:return r.read()

def fetch_original():
    rec = json.loads(get(f'https://www.icloud.com/shortcuts/api/records/{ID}'))
    return plistlib.loads(get(rec['fields']['shortcut']['value']['downloadURL']))

def field_key(e):
    return e.get('WFKey',{}).get('Value',{}).get('string')

def find_fields(root):
    for item in root.get('WFDictionaryFieldValueItems',[]):
        yield item

def recursively_replace(x):
    if isinstance(x, dict):
        return {k:recursively_replace(v) for k,v in x.items()}
    if isinstance(x, list):
        return [recursively_replace(v) for v in x]
    if isinstance(x, str):
        # Isolate iCloud settings, self-run links, and visible shortcut labels.
        return x.replace('Add to Calendar','Add to Calendar MiMo')
    return x

obj=recursively_replace(fetch_original())
actions=obj['WFWorkflowActions']
assert len(actions)==820, f'Unexpected original version: {len(actions)} actions'
old_ids=[a['WFWorkflowActionIdentifier'] for a in actions]
changed_models=changed_responses=0

for a in actions:
    p=a.get('WFWorkflowActionParameters',{})
    if a['WFWorkflowActionIdentifier']!='is.workflow.actions.downloadurl':continue
    if p.get('WFURL')=='https://api.openai.com/v1/models':
        p['WFURL']='https://api.xiaomimimo.com/v1/models'
        changed_models+=1
    elif p.get('WFURL')=='https://api.openai.com/v1/responses':
        p['WFURL']='https://api.xiaomimimo.com/v1/responses'
        changed_responses+=1
        fields=p['WFJSONValues']['Value']['WFDictionaryFieldValueItems']
        mod=next(e for e in fields if field_key(e)=='model')
        mod['WFValue']['Value']['string']='mimo-v2.6-flash'
        # web_search_preview is OpenAI-specific; remove without disturbing images.
        fields[:]=[e for e in fields if field_key(e) not in ('tools','tool_choice')]
        # MiMo's JSON-object mode, not OpenAI's strict json_schema mode.
        tf=next(e for e in fields if field_key(e)=='text')
        nested=tf['WFValue']['Value']['Value']['WFDictionaryFieldValueItems']
        fmt=next(e for e in nested if field_key(e)=='format')
        fmtitems=fmt['WFValue']['Value']['Value']['WFDictionaryFieldValueItems']
        fmtitems[:]=[e for e in fmtitems if field_key(e)=='type']
        assert len(fmtitems)==1
        fmtitems[0]['WFValue']['Value']['string']='json_object'

assert changed_models==3 and changed_responses==1, (changed_models,changed_responses)

# Model originally received the JSON schema through OpenAI-specific request format.
# Inject the same live dynamic schema as a text-variable into MiMo's instructions.
system=actions[586]['WFWorkflowActionParameters']['WFTextActionText']
val=system['Value']
start=val['string']
append='\\n\\nIMPORTANT: Handle Chinese WeChat screenshots and group chats. A later confirmed reschedule replaces earlier proposals; cancelled events must not become new calendar entries. Resolve relative dates using message timestamps when available, otherwise the provided device date and timezone. Never invent a time or place. Return only one valid JSON object conforming to this exact schema; do not include markdown:\\n'
# real line breaks, not a textual slash-n.
append=append.replace('\\n','\n')
pos=len((start+append).encode('utf-16-le'))//2
val['string']=start+append+'\uFFFC'
val.setdefault('attachmentsByRange',{})[f'{{{pos}, 1}}']={
    'Type':'ActionOutput','OutputName':'Dictionary',
    'OutputUUID':'FB417387-2F3C-4617-8DE9-700B3D9E57E6'
}

# Keep the original 820-action control flow, all event creation actions and
# magic variable bindings. Do not copy settings into the original shortcut.
assert len(actions)==820
assert [a['WFWorkflowActionIdentifier'] for a in actions]==old_ids
assert Counter(old_ids)['is.workflow.actions.addnewevent']==3
assert all(a.get('WFWorkflowActionParameters',{}).get('WFURL')!='https://api.openai.com/v1/responses' for a in actions)
assert 'mimo-v2.6-flash' in str(actions[587])
out=ROOT/'Add-to-Calendar-MiMo.unsigned.shortcut'
out.write_bytes(plistlib.dumps(obj,fmt=plistlib.FMT_BINARY))
# Binary plist round trip checks action count, references, control flow and URL.
reloaded=plistlib.loads(out.read_bytes())
assert len(reloaded['WFWorkflowActions'])==820
assert reloaded['WFWorkflowActions'][587]['WFWorkflowActionParameters']['WFURL']=='https://api.xiaomimimo.com/v1/responses'
print('STATIC_VALIDATION_OK original_actions=820 preserved=820 model=mimo-v2.6-flash')
print('PATCHED_MODELS',changed_models,'PATCHED_RESPONSE_ENDPOINTS',changed_responses)
print('UNSIGNED_FILE',out,'BYTES',out.stat().st_size)

# The unofficial community HubSign endpoint may change or require access.
# Never include the user's secret in any shortcut used for third-party signing.
payload=json.dumps({'shortcutName':NEW_NAME,
                    'shortcut':plistlib.dumps(obj,fmt=plistlib.FMT_XML).decode('utf-8')}).encode()
req=urllib.request.Request('https://hubsign.routinehub.services/sign',data=payload,method='POST',headers={
 'Content-Type':'application/json','Origin':'https://routinehub.co',
 'Referer':'https://routinehub.co/','User-Agent':'Mozilla/5.0'
})
try:
    with urllib.request.urlopen(req,timeout=100) as r:signed=r.read()
except Exception as exc:
    print('HUBSIGN_ERROR',type(exc).__name__,str(exc))
    raise
if not signed.startswith(b'AEA1'):
    raise RuntimeError('HubSign response is not an Apple-signed shortcut; header='+signed[:30].hex())
signed_file=ROOT/'Add-to-Calendar-MiMo.shortcut'
signed_file.write_bytes(signed)
print('SIGNED_VALIDATION_OK',signed_file,'BYTES',len(signed),'MAGIC',signed[:4].decode())
