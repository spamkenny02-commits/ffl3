"""FFL3 French + supplied color IPS, no expansion beyond the color patch size."""
import argparse, hashlib, json
from pathlib import Path
from expanded_builder import build_expanded, checksum, ips_expanded, SHORT_TABLE, DICT_FR
from ffl3_editor import load_rom, Codec
from font_fr import install_font
FIXED=0x3FD1
CODE_BANK=31
CODE_CPU=0x4000
SHORT_CPU=0x4200
DICT_CPU=0x4400
COLOR_SHA='2358ef460d1259e89db7201ca8bf5b5d241d093010061983e348fa7814cabc77'

class Assembly:
 def __init__(self,base):self.base=base;self.data=bytearray();self.labels={};self.fix=[]
 def emit(self,*v):self.data.extend(v)
 def label(self,n):self.labels[n]=len(self.data)
 def branch(self,opcode,name):
  self.emit(opcode,0,0);self.fix.append((len(self.data)-2,name))
 def done(self):
  for pos,n in self.fix:self.data[pos:pos+2]=(self.base+self.labels[n]).to_bytes(2,'little')
  return bytes(self.data)

def fixed_code():
 # Copy the five following source bytes before switching away from their bank.
 # Parent HL is saved on the stack; the banked handler advances that saved HL.
 entry=bytes.fromhex('c5 d5 e5 2a 47 2a 4f 2a 57 2a 5f 2a 67 3e 1f e7 cd 00 40 ef e1 d1 c1 37 c9')
 fetch=bytes.fromhex('e7 2a f5 ef f1 c9')
 render=bytes.fromhex('e7 78 fe 88 dc cb 32 d4 ea 32 ef c9')
 return entry+fetch+render,FIXED+len(entry),FIXED+len(entry)+len(fetch)

def handler(fetch,render):
 a=Assembly(CODE_CPU)
 # Arguments: B=first byte, C=second, D=third, E=fourth, H=fifth.
 a.emit(0x78,0xFE,0x8A);a.branch(0xCA,'accent')
 a.emit(0xFE,0x89);a.branch(0xCA,'short')
 a.emit(0xFE,0xFF);a.branch(0xC2,'legacy')
 a.emit(0x79,0xFE,0xF9);a.branch(0xC2,'legacy')
 # Long marker: D=bank, E=pointer low, H=pointer high.
 a.emit(0x7A,0x6B,0xF5,0xE5,0x0E,5);a.branch(0xC3,'advance')
 a.label('short')
 # Fetch a bank+pointer triple from this bank's short reference table.
 a.emit(0x69,0x26,0,0x54,0x5D,0x29,0x19,0x11,0,0x42,0x19,0x2A,0x5E,0x23,0x56,0x62,0x6B,0xF5,0xE5,0x0E,2)
 a.label('advance')
 # SP+6 points at the parent HL saved by the bank-zero trampoline.
 a.emit(0xF8,6,0x7E,0x81,0x22,0x7E,0xCE,0,0x77,0xE1)
 a.label('loop')
 # The target bank is kept on the CPU stack, immune to nested text commands.
 a.emit(0xE5,0xF8,3,0x7E,0xE1,0xCD,fetch&255,fetch>>8,0xB7);a.branch(0xCA,'finish')
 a.emit(0xFE,0x10);a.branch(0xCA,'wait')
 a.emit(0x47,0xE5,0xF8,3,0x7E,0xE1,0xCD,render&255,render>>8,0xFA,8,0xCD,0xB7)
 a.branch(0xCA,'loop')
 a.label('finish');a.emit(0xF1,0xC9)
 a.label('wait');a.emit(0xCD,0x5C,0x27);a.branch(0xC3,'loop')
 a.label('accent')
 # Render C as one glyph from the stack; advance the parent script by two.
 a.emit(0xC5,0xF8,0,0x54,0x5D,0x06,1,0xCD,4,0x33,0xC1,0xF8,2,0x7E,0xC6,2,0x22,0x7E,0xCE,0,0x77,0xC9)
 a.label('legacy');a.emit(0xC9)
 return a.done()

def apply_ips(original,patch):
 if patch[:5]!=b'PATCH':raise ValueError('Invalid IPS header')
 out=bytearray(original);i=5
 while patch[i:i+3]!=b'EOF':
  if i+5>len(patch):raise ValueError('Truncated IPS')
  at=int.from_bytes(patch[i:i+3],'big');n=int.from_bytes(patch[i+3:i+5],'big');i+=5
  if n:
   raw=patch[i:i+n];i+=n
   if len(raw)!=n:raise ValueError('Truncated IPS data')
  else:
   n=int.from_bytes(patch[i:i+2],'big');raw=patch[i+2:i+3]*n;i+=3
   if len(raw)!=n:raise ValueError('Truncated IPS RLE')
  if at+n>len(out):out.extend(bytes(at+n-len(out)))
  out[at:at+n]=raw
 tail=patch[i+3:]
 if tail:
  if len(tail)!=3:raise ValueError('Invalid IPS tail')
  size=int.from_bytes(tail,'big');out=out[:size]+bytearray(max(0,size-len(out)))
 return bytes(out)

def build_color(original,color_patch,project):
 if hashlib.sha256(color_patch).hexdigest()!=COLOR_SHA:raise ValueError('Utiliser le patch couleur fourni avec cet atelier (SHA-256 different).')
 base=apply_ips(original,color_patch)
 if len(base)!=524288 or base[0x147:0x14A]!=bytes([0x1B,4,2]):raise ValueError('Unexpected supplied color ROM size or mapper')
 fixed,fetch,render=fixed_code();code=handler(fetch,render)
 if len(fixed)>47 or any(base[FIXED:FIXED+len(fixed)]):raise ValueError('Bank zero code space occupied')
 if len(code)>0x200:raise ValueError('Handler overlaps short table')
 for bank in [18,19,31]:
  area=base[bank*0x4000:(bank+1)*0x4000-(1 if bank==31 else 0)]
  if any(area):raise ValueError(f'Color bank {bank} occupied')
 approved={f"{e['offset']:05X}" for e in project['entries'] if e.get('notes','').startswith('Traduction relue')}
 french,report=build_expanded(original,project,{},approved)
 if report['blocked']:raise ValueError('Blocked translation entries')
 out=bytearray(install_font(base));entries={f"{e['offset']:05X}":e for e in project['entries']}
 for ch in report['changes']:
  e=entries[ch['offset']];at=e['offset'];n=e['length']
  if base[at:at+n]!=original[at:at+n]:raise ValueError('Color patch overlaps text: '+ch['offset'])
  raw=bytearray(french[at:at+n])
  if ch['mode']=='far':
   ch['bank']+=2
   if n>=6:raw[3]+=2
  out[at:at+n]=raw
 # Move the French text banks from 16/17 to the color patch's unused 18/19.
 used=report['storage_used'];out[18*0x4000:18*0x4000+used]=french[16*0x4000:16*0x4000+used]
 out[FIXED:FIXED+len(fixed)]=fixed
 out[31*0x4000:31*0x4000+len(code)]=code
 short_count=sum(c['mode']=='far' and c['capacity']<6 for c in report['changes'])
 for i in range(short_count):
  raw=bytearray(french[SHORT_TABLE+i*3:SHORT_TABLE+i*3+3]);raw[0]+=2
  at=31*0x4000+SHORT_CPU-0x4000+i*3;out[at:at+3]=raw
 c=Codec(original)
 for key,text in DICT_FR.items():c.dictionary[key]=c.encode(text,False)
 dictionary=b''.join(bytes([len(c.dictionary[int(m['code'],16)])])+c.dictionary[int(m['code'],16)] for m in c.dictionary_meta)
 at=31*0x4000+DICT_CPU-0x4000;out[at:at+len(dictionary)]=dictionary
 out[0x320D:0x320F]=FIXED.to_bytes(2,'little')
 out[0x3095:0x3097]=DICT_CPU.to_bytes(2,'little');out[0x3098]=31
 checksum(out)
 assert len(out)==len(base)
 report.update(mapper='MBC5 RAM BATTERY (1B), unchanged from supplied color patch',output_size=len(out),color_base_size=len(base),expansion_banks=[18,19],stub_offset=FIXED,stub_hex=fixed.hex(),handler_offset=31*0x4000,handler_hex=code.hex(),short_table_offset=31*0x4000+0x200,dictionary_offset=31*0x4000+0x400,color_patch_sha256=hashlib.sha256(color_patch).hexdigest(),output_sha256=hashlib.sha256(out).hexdigest(),additional_size_bytes=0)
 return bytes(out),base,report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('original');p.add_argument('color_ips');p.add_argument('project');p.add_argument('output');args=p.parse_args()
 original=load_rom(args.original);out,base,report=build_color(original,Path(args.color_ips).read_bytes(),json.loads(Path(args.project).read_text(encoding='utf8')))
 dest=Path(args.output);dest.write_bytes(out);dest.with_suffix('.ips').write_bytes(ips_expanded(original,out));dest.with_name(dest.stem+'_sur_couleur.ips').write_bytes(ips_expanded(base,out));dest.with_suffix('.report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print('Built',len(out),'bytes, color base',len(base),'bytes; additional size 0')
