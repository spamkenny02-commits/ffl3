"""512 KiB MBC1 builder, far-text escape preserves source/event addresses."""
import json,sys,hashlib,re
from pathlib import Path

from ffl3_editor import Codec,load_rom,protected,KNOWN_SCRIPT_OPERANDS
from font_fr import install_font,ACCENT_ESCAPE
STUB=0x3E6B
MARKER=bytes.fromhex('4c ff f9')
DICT_BANK=31
DICT_ADDR=0x4000
DICT_FR={0x6D:'Ancien',0x71:'Mamie',0x03:'Tu es nouveau.\n',0x81:'épée sacrée'}
class Asm:
 def __init__(self):self.data=bytearray();self.labels={};self.fix=[]
 def emit(self,*x):self.data.extend(x)
 def label(self,name):self.labels[name]=len(self.data)
 def jr(self,opcode,label):self.emit(opcode,0);self.fix.append((len(self.data)-1,label))
 def result(self):
  for off,name in self.fix:
   v=self.labels[name]-off-1
   if not -128<=v<128:raise ValueError('JR out of range')
   self.data[off]=v&255
  return bytes(self.data)
SHORT_TABLE=0x3F00
SHORT_MARKER=bytes.fromhex('4c 89')
def stub_code():
 a=Asm();a.emit(0xC5,0xD5,0xE5,0x2A,0xFE,0x8A);a.jr(0x28,'accent')
 a.emit(0xFE,0x89);a.jr(0x28,'short')
 a.emit(0xFE,0xFF);a.jr(0x20,'legacy')
 a.emit(0x2A,0xFE,0xF9);a.jr(0x20,'legacy')
 a.emit(0x2A,0x5E,0x23,0x56,0x23,0xC1,0xE5,0x62,0x6B);a.jr(0x18,'call')
 a.label('short');a.emit(0x2A,0xC1,0xE5,0x6F,0x26,0,0x54,0x5D,0x29,0x19)
 a.emit(0x11,SHORT_TABLE&255,SHORT_TABLE>>8,0x19,0x2A,0x5E,0x23,0x56,0x62,0x6B)
 a.label('call');a.emit(0xE7,0xCD,0,0);call_fix=len(a.data)-2
 a.emit(0xEF,0xE1,0xD1,0xC1,0x37,0xC9)
 a.label('legacy');a.emit(0xE1,0xD1,0xC1,0x37,0xC9)
 a.label('accent');a.emit(0xE1,0x54,0x5D,0x13,0x23,0x23,0xE5,0x06,1,0xCD,0x04,0x33,0xE1,0xD1,0xC1,0x37,0xC9)
 a.label('loop');a.emit(0x2A,0xB7,0xC8,0xFE,0x10);a.jr(0x28,'wait')
 a.emit(0xFE,0x88,0xDC,0xCB,0x32,0xD4,0xEA,0x32,0xFA,0x08,0xCD,0xB7)
 a.jr(0x28,'loop');a.emit(0xC9)
 a.label('wait');a.emit(0xCD,0x5C,0x27);a.jr(0x18,'loop')
 a.data[call_fix:call_fix+2]=(STUB+a.labels['loop']).to_bytes(2,'little')
 return a.result()
def checksum(out):
 h=0
 for v in out[0x134:0x14D]:h=(h-v-1)&255
 out[0x14D]=h
 c=(sum(out)-out[0x14E]-out[0x14F])&65535;out[0x14E:0x150]=c.to_bytes(2,'big')
def build_expanded(rom,project,translations,approved,compact=None):
 codec=Codec(rom)
 for code,text in DICT_FR.items():codec.dictionary[code]=codec.encode(text,False)
 out=bytearray(install_font(rom))+bytearray([255])*len(rom);stub=stub_code()
 if STUB+len(stub)>SHORT_TABLE:raise ValueError('Stub overlaps short table')
 if any(rom[STUB:STUB+len(stub)]):raise ValueError('Stub location occupied')
 if rom.count(MARKER) or rom.count(SHORT_MARKER) or rom.count(ACCENT_ESCAPE):raise ValueError('Escape conflicts with original ROM')
 out[STUB:STUB+len(stub)]=stub
 table=0x3175+0x4C*2
 if rom[table:table+2]!=bytes.fromhex('74 31'):raise ValueError('Unexpected text command table')
 out[table:table+2]=STUB.to_bytes(2,'little');out[0x148]=4
 dictionary=bytearray()
 for meta in codec.dictionary_meta:
  raw=codec.dictionary[int(meta['code'],16)];dictionary+=bytes([len(raw)])+raw
 out[DICT_BANK*0x4000:DICT_BANK*0x4000+len(dictionary)]=dictionary
 if rom[0x3094:0x309A]!=bytes.fromhex('21 c5 71 3e 03 e7'):raise ValueError('Unexpected dictionary loader')
 out[0x3095:0x3097]=DICT_ADDR.to_bytes(2,'little');out[0x3098]=DICT_BANK
 short_count=0
 cursor=len(rom);changes=[];blocked=[];occupied=[];compact=compact or {}
 # Preserve potential entry points explicitly exposed by the bank A root table.
 roots={0x28000+int.from_bytes(rom[a:a+2],'little')-0x4000 for a in range(0x28004,0x281E2,2)}
 for e in project['entries']:
  a=e['offset'];n=e['length'];key=f'{a:05X}';text=translations.get(key,e.get('french',''))
  if not text or text==e['english']:continue
  if e['compressed'] and key not in approved and not e['verified']:
   blocked.append(dict(offset=key,reason='unreviewed candidate',french=text));continue
  if any(a<=operand<a+n for operand in KNOWN_SCRIPT_OPERANDS):
   blocked.append(dict(offset=key,reason='overlaps known script operand',french=text));continue
  if rom[a:a+n]!=bytes.fromhex(e['source_hex']):raise ValueError('Invalid original bytes')
  if protected(text)!=protected(e['english']):raise ValueError('Protected commands changed: '+key)
  if any(a<y and x<a+n for x,y in occupied):raise ValueError('Overlapping entries')
  raw=codec.encode(text,e['compressed'])
  mode='fixed'
  if not e['compressed']:
   if ACCENT_ESCAPE in raw:blocked.append(dict(offset=key,reason='accent escape not allowed in a fixed field',french=text));continue
   if len(raw)>n:blocked.append(dict(offset=key,reason='fixed name overflow',french=text,used=len(raw),capacity=n));continue
   out[a:a+n]=raw+b'\xff'*(n-len(raw))
  elif n>=3:
   if any(a<r<a+n for r in roots):blocked.append(dict(offset=key,reason='root enters interior of span',french=text));continue
   if len(raw)+1>0x4000:raise ValueError('Text exceeds one bank')
   if cursor//0x4000!=(cursor+len(raw))//0x4000:cursor=(cursor//0x4000+1)*0x4000
   if cursor+len(raw)+1>DICT_BANK*0x4000:raise ValueError('Expansion full')
   bank=cursor//0x4000;ptr=0x4000+cursor%0x4000
   out[cursor:cursor+len(raw)+1]=raw+b'\x00'
   if n>=6:
    out[a:a+n]=MARKER+bytes([bank])+ptr.to_bytes(2,'little')+b'\x4c'*(n-6)
   else:
    if short_count>=85:raise ValueError('Short table full')
    at=SHORT_TABLE+short_count*3
    if any(rom[at:at+3]):raise ValueError('Short table occupied')
    out[at:at+3]=bytes([bank])+ptr.to_bytes(2,'little')
    out[a:a+n]=SHORT_MARKER+bytes([short_count])+b'\x4c'*(n-3)
    short_count+=1
   mode='far';cursor+=len(raw)+1
  else:
   if key in compact:text=compact[key];raw=codec.encode(text)
   try:raw=codec.encode_exact(text,n)
   except ValueError:
    blocked.append(dict(offset=key,reason='source too short for far pointer',french=text,used=len(raw),capacity=n));continue
   out[a:a+n]=raw;mode='inline'
  occupied.append((a,a+n));changes.append(dict(offset=key,category=e['category'],mode=mode,french=text,used=len(raw),capacity=n,bank=bank if mode=='far' else a//0x4000))
 checksum(out)
 return bytes(out),dict(changes=changes,blocked=blocked,source_size=len(rom),output_size=len(out),storage_used=cursor-len(rom),stub_offset=STUB,stub_hex=stub.hex(),mapper='MBC1 RAM BATTERY (03), ROM size 04, RAM size unchanged',expansion_banks=sorted({e['bank'] for e in changes if e['mode']=='far'}))
def ips_expanded(original,modified):
 out=bytearray(b'PATCH');i=0
 while i<len(modified):
  old=original[i] if i<len(original) else None
  if old==modified[i]:i+=1;continue
  st=i
  while i<len(modified) and (i>=len(original) or original[i]!=modified[i]) and i-st<65535:i+=1
  out+=st.to_bytes(3,'big')+(i-st).to_bytes(2,'big')+modified[st:i]
 out+=b'EOF'+len(modified).to_bytes(3,'big');return bytes(out)
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('rom');ap.add_argument('project');ap.add_argument('output');args=ap.parse_args()
 rom=load_rom(args.rom);project=json.loads(Path(args.project).read_text(encoding='utf8'))
 approved={f"{e['offset']:05X}" for e in project['entries'] if e.get('notes','').startswith('Traduction relue')}
 out,report=build_expanded(rom,project,{},approved)
 Path(args.output).with_suffix('.report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 if report['blocked']:raise SystemExit('Export refuse : consulter le rapport des textes bloques.')
 Path(args.output).write_bytes(out);Path(args.output).with_suffix('.ips').write_bytes(ips_expanded(rom,out))
 print('changes',len(report['changes']),'storage',report['storage_used'],'banks',report['expansion_banks'])
