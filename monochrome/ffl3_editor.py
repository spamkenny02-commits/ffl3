#!/usr/bin/env python3
"""FFL3 USA text editor. ROM-specific verified tables and original dictionary codec."""
import argparse, hashlib, json, re, sys
from pathlib import Path

SHA256='5ed87f65225b72a74c3c04a4e5d67683fb5cc33e5f1266157350828ab973fc1d'
ROM_SIZE=262144
FONT=0xC000
DICT_START=0xF1C5
SPECIAL=[0x01,0x02,0x03,0x04,0x16,0x17,0x18,0x19,0x1A,0x1B,0x40,0x41,0x42,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x0E,0x0F]
GLYPHS={0xB0+i:c for i,c in enumerate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')}
GLYPHS.update({0xFF:' ',0xAC:',',0xAD:"'",0xAE:'…',0xAF:'.',0xEE:'”',0xEF:'“',0xF0:'.”',0xF1:'/',0xF2:'-',0xF3:'!',0xF4:'?',0xF5:'○',0xF6:'×',0xF7:'&',0xF8:'※',0xFB:'(',0xFC:')',0xFD:'©',0xFE:':',6:'\n'})
from font_fr import ACCENT_CODES,ACCENT_ESCAPE,install_font,display_codes
GLYPHS[0xAB]='é'
REVERSE={v:bytes([k]) for k,v in GLYPHS.items()}
REVERSE.update({char:(bytes([code]) if code>=0x88 else ACCENT_ESCAPE+bytes([code])) for char,code in ACCENT_CODES.items()})
TABLES=[('classes',0x3AD4F,6,6,0),('status',0x3AD73,10,4,0),('spells',0x3AD9B,48,6,1),('items_equipment',0x3AEBB,203,8,1),('enemies',0x3B513,199,8,0),('stats',0x267BF,8,7,0),('talents',0x267F7,141,8,0),('worlds',0x272B3,7,11,0)]
KNOWN_SCRIPT_OPERANDS={0x261F1} # command 13 parameter, confirmed by execution
SCAN_REGIONS=[('intro',0x25EAC,0x267BF),('menus_battle',0x26C5F,0x27E99),('dialogue_events',0x281E2,0x2BD99),('credits',0x3BB4B,0x3BD70)]

def load_rom(path,strict=True):
 b=Path(path).read_bytes()
 if len(b)!=ROM_SIZE:raise ValueError(f'Taille invalide : {len(b)} ; attendu {ROM_SIZE}')
 if strict and hashlib.sha256(b).hexdigest()!=SHA256:raise ValueError('ROM differente de la version USA analysee (SHA-256).')
 return b

class Codec:
 def __init__(self,rom):
  self.dictionary={};self.dictionary_meta=[];a=DICT_START
  for i in range(80):
   n=rom[a];raw=rom[a+1:a+1+n];code=0x4E+i if i<58 else SPECIAL[i-58]
   self.dictionary[code]=raw;self.dictionary_meta.append(dict(index=i,code=f'{code:02X}',offset=a,raw=raw.hex(),text=self.literal(raw)));a+=n+1
  if a!=0xF31C:raise ValueError('Dictionnaire inattendu')
 def literal(self,raw):return ''.join(next((ch for ch,code in ACCENT_CODES.items() if code==v),GLYPHS.get(v,f'[{v:02X}]')) for v in display_codes(raw))
 def decode(self,raw,compressed=True):
  result=[];i=0
  while i<len(raw):
   if raw[i:i+2]==ACCENT_ESCAPE and i+2<len(raw) and raw[i+2] in range(128,136):
    result.append(next(ch for ch,code in ACCENT_CODES.items() if code==raw[i+2]));i+=3;continue
   v=raw[i];result.append(self.literal(self.dictionary[v]) if compressed and v in self.dictionary else GLYPHS.get(v,f'[{v:02X}]'));i+=1
  return ''.join(result)
 def encode(self,text,compressed=True):
  # Shortest exact encoding; no lossy transliteration or silent accent removal.
  options=[(s,v) for s,v in REVERSE.items()]
  if compressed:options += [(self.literal(raw),bytes([code])) for code,raw in self.dictionary.items()]
  size=len(text);dp=[None]*(size+1);dp[size]=b''
  for i in range(size-1,-1,-1):
   opts=list(options);m=re.match(r'\[([0-9A-Fa-f]{2})\]',text[i:])
   if m:
    value=int(m[1],16)
    if compressed and value in self.dictionary:raise ValueError('Code de dictionnaire brut interdit ; utiliser son texte decode.')
    opts.append((m[0],bytes([value])))
   for s,raw in opts:
    j=i+len(s)
    if text.startswith(s,i) and dp[j] is not None:
     v=raw+dp[j]
     if dp[i] is None or len(v)<len(dp[i]):dp[i]=v
  if dp[0] is None:
   unsupported=sorted(set(c for c in text if c not in ''.join(REVERSE)))
   raise ValueError('Texte non encodable. Caracteres non pris en charge : '+repr(unsupported))
  return dp[0]


 def encode_exact(self,text,target):
  """Select compression/literal alternatives to fill a slot without padding glyphs."""
  options=[(s,v) for s,v in REVERSE.items()]
  options += [(self.literal(raw),bytes([code])) for code,raw in self.dictionary.items()]
  dp=[{} for _ in range(len(text)+1)];dp[0][0]=b''
  for i in range(len(text)):
   if not dp[i]:continue
   opts=list(options);m=re.match(r'\[([0-9A-Fa-f]{2})\]',text[i:])
   if m and int(m[1],16) not in self.dictionary:opts.append((m[0],bytes([int(m[1],16)])))
   for segment,raw in opts:
    if text.startswith(segment,i):
     j=i+len(segment)
     for size,prefix in dp[i].items():
      n=size+len(raw)
      if n<=target and n not in dp[j]:dp[j][n]=prefix+raw
  if target not in dp[-1]:raise ValueError(f'Impossible de remplir exactement {target} octets sans ajouter de caracteres. Ajuster le texte ou ses espaces explicites.')
  return dp[-1][target]

def record(codec,rom,group,a,n,compressed,verified):
 raw=rom[a:a+n];text=codec.decode(raw,compressed)
 return dict(id=f'{group}_{a:05X}',category=group,offset=a,length=n,bank=a//0x4000,cpu_address=a%0x4000+(0x4000 if a>=0x4000 else 0),compressed=compressed,verified=verified,source_hex=raw.hex(),english=text,french='',notes='')

def extract(rom,observed=()):
 codec=Codec(rom);entries=[];occupied=set();observed=set(observed)
 for group,start,count,stride,prefix in TABLES:
  for i in range(count):
   a=start+i*stride+prefix;n=stride-prefix
   e=record(codec,rom,group,a,n,False,True);e['index']=i
   entries.append(e);occupied.update(range(a,a+n))
 occupied.update(KNOWN_SCRIPT_OPERANDS)
 allowed=set(GLYPHS)|set(codec.dictionary)
 for group,start,end in SCAN_REGIONS:
  a=start
  while a<end:
   if a in occupied or rom[a] not in allowed:a+=1;continue
   st=a
   while a<end and a not in occupied and rom[a] in allowed:a+=1
   raw=rom[st:a];text=codec.decode(raw)
   letters=sum(c.isalpha() for c in text)
   if letters<3:continue
   # A runtime hook records literal and compressed source bytes. Newline is a
   # confirmed parameter-free opcode; it can join two observed runs.
   verified=all(x in observed or rom[x]==6 for x in range(st,a))
   entries.append(record(codec,rom,group,st,a-st,True,verified))
 # Known literal title strings also independently verified in emulator.
 for literal in ['New Game','Continue','Which data\n  will you play?']:
  needle=codec.encode(literal,False);a=rom.find(needle)
  for e in entries:
   if e['offset']==a:e['verified']=True
 return dict(format='ffl3-editor-project',version=1,rom_sha256=SHA256,rom_size=ROM_SIZE,dictionary=codec.dictionary_meta,entries=entries,coverage='Fixed-width tables verified; script candidates require runtime or manual validation. Not a complete pointer/event decompilation.')

def protected(text):return re.findall(r'\[[0-9A-Fa-f]{2}\]',text)

def build(rom,project,allow_candidates=False):
 if project.get('rom_sha256')!=SHA256:raise ValueError('Projet pour une autre ROM')
 codec=Codec(rom);out=bytearray(rom);changes=[];ranges=[]
 for e in project['entries']:
  text=e.get('french','')
  if not text or text==e['english']:continue
  if not e['verified'] and not allow_candidates:raise ValueError(f"{e['id']}: candidat non valide ; reinsertion bloquee")
  a=e['offset'];n=e['length']
  if a<0 or a+n>len(rom) or bytes.fromhex(e['source_hex'])!=rom[a:a+n]:raise ValueError('Octets source ou limites incorrects : '+e['id'])
  if codec.decode(rom[a:a+n],e['compressed'])!=e['english']:raise ValueError('Texte anglais/encodage modifie : '+e['id'])
  if protected(text)!=protected(e['english']):raise ValueError('Commandes protegees modifiees : '+e['id'])
  raw=codec.encode(text,e['compressed'])
  if len(raw)>n:raise ValueError(f"{e['id']}: {len(raw)} octets pour {n} disponibles (depassement)")
  if e['compressed']:raw=codec.encode_exact(text,n)
  if any(a<y and x<a+n for x,y in ranges):raise ValueError('Entrees qui se chevauchent')
  ranges.append((a,a+n));out[a:a+n]=raw+b'\xff'*(n-len(raw))
  changes.append(dict(id=e['id'],offset=a,capacity=n,used=len(raw),padding=n-len(raw),verified=e['verified'],french=text))
 if changes:
  # GB global checksum (big endian), excluding its own two bytes.
  checksum=(sum(out)-out[0x14E]-out[0x14F])&65535;out[0x14E:0x150]=checksum.to_bytes(2,'big')
 assert len(out)==len(rom)
 return bytes(out),changes

def ips(original,modified):
 if len(original)!=len(modified):raise ValueError('IPS : taille differente')
 result=bytearray(b'PATCH');i=0
 while i<len(original):
  if original[i]==modified[i]:i+=1;continue
  st=i
  while i<len(original) and original[i]!=modified[i] and i-st<65535:i+=1
  result += st.to_bytes(3,'big')+(i-st).to_bytes(2,'big')+modified[st:i]
 return bytes(result+b'EOF')

def preview(rom,text,scale=4,width=18,rows=4):
 from PIL import Image,ImageDraw
 im=Image.new('RGB',(160,144),(230,235,211));draw=ImageDraw.Draw(im)
 draw.rounded_rectangle((0,100,159,143),radius=5,fill=(255,255,255),outline=(35,40,30),width=2)
 raw=Codec(rom).encode(text,False);rom=install_font(rom);x=8;y=106
 for value in display_codes(raw):
  if value==6:x=8;y+=8;continue
  if value<0x88 and value not in ACCENT_CODES.values():continue
  if x>=8+width*8 or y>=106+rows*8:continue # Deliberately no automatic wrap.
  tile=value&127;off=FONT+16*tile
  for r in range(8):
   lo,hi=rom[off+r*2:off+r*2+2]
   for c in range(8):
    v=((lo>>(7-c))&1)+2*((hi>>(7-c))&1)
    im.putpixel((x+c,y+r),(255-v*85,)*3)
  x+=8
 return im.resize((160*scale,144*scale),Image.Resampling.NEAREST)

def emulator(rom_path,out=None,frames=180,window=False):
 from pyboy import PyBoy
 p=PyBoy(str(rom_path),window='SDL2' if window else 'null',sound_emulated=False)
 try:
  if window:
   while p.tick():pass
  else:p.set_emulation_speed(0);p.tick(frames);p.screen.image.save(str(out))
 finally:p.stop(save=False)


def trace_game(rom_path,project_path,output):
 from pyboy import PyBoy
 rom=load_rom(rom_path);p=PyBoy(str(rom_path),window='SDL2',sound_emulated=False);seen=set()
 if Path(output).exists():seen.update(json.loads(Path(output).read_text(encoding='utf8')))
 def collect_literals(p):
  h=p.register_file.HL-1;bank=p.memory[0xC0B1]
  if not 0<=h<0x8000:return
  a=h if h<0x4000 else bank*0x4000+h-0x4000
  while h<0x8000 and p.memory[h]>=0x88:seen.add(a);a+=1;h+=1
 def collect_dictionary(p):
  h=p.register_file.HL-1;bank=p.memory[0xC0B1]
  if 0<=h<0x8000:seen.add(h if h<0x4000 else bank*0x4000+h-0x4000)
 p.hook_register(0,0x32EA,collect_literals,p);p.hook_register(0,0x308C,collect_dictionary,p)
 try:
  while p.tick():pass
 finally:
  p.stop(save=False);Path(output).write_text(json.dumps(sorted(seen)))
  project=json.loads(Path(project_path).read_text(encoding='utf8'));fresh=extract(rom,seen);verified={e['id']:e['verified'] for e in fresh['entries']}
  for e in project['entries']:e['verified']=e['verified'] or verified.get(e['id'],False)
  Path(project_path).write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf8')
  print(f'{len(seen)} octets de texte observes ; projet mis a jour.')

def gui(rom_path,project_path):
 import tkinter as tk
 from tkinter import ttk,messagebox,filedialog
 root=tk.Tk();root.withdraw()
 if not rom_path:
  rom_path=filedialog.askopenfilename(parent=root,title='Choisir la ROM USA originale (256 Ko)',filetypes=[('ROM Game Boy','*.gb'),('Tous les fichiers','*.*')])
  if not rom_path:root.destroy();return
 try:
  rom=load_rom(rom_path);project=json.loads(Path(project_path).read_text(encoding='utf8'));codec=Codec(rom)
  from PIL import ImageTk
 except (OSError,ValueError,ImportError) as ex:
  messagebox.showerror('Ouverture impossible',str(ex)+'\n\nROM requise : Final Fantasy Legend III (USA), originale de 256 Ko.\nPour installer les dependances : python -m pip install -r requirements.txt',parent=root)
  root.destroy();return False
 root.title('Final Fantasy Legend III — atelier FR');root.geometry('1120x850');root.deiconify()
 toolbar=ttk.Frame(root);toolbar.pack(fill='x');query=tk.StringVar();ttk.Label(toolbar,text='Recherche :').pack(side='left');ttk.Entry(toolbar,textvariable=query,width=42).pack(side='left')
 verified_only=tk.BooleanVar(value=False);ttk.Checkbutton(toolbar,text='Valides seulement',variable=verified_only).pack(side='left')
 frame=ttk.PanedWindow(root,orient='horizontal');frame.pack(fill='both',expand=True)
 left=ttk.Frame(frame);right=ttk.Frame(frame);frame.add(left,weight=1);frame.add(right,weight=2)
 listing=tk.Listbox(left,width=45);listing.pack(side='left',fill='both',expand=True);scroll=ttk.Scrollbar(left,command=listing.yview);scroll.pack(side='right',fill='y');listing.config(yscrollcommand=scroll.set)
 info=tk.StringVar();ttk.Label(right,textvariable=info,wraplength=700).pack(fill='x')
 ttk.Label(right,text='Anglais / commandes entre crochets :').pack(anchor='w');en=tk.Text(right,height=7);en.pack(fill='x')
 ttk.Label(right,text='Français (é è à ê â î ô ù ç disponibles) :').pack(anchor='w');fr=tk.Text(right,height=7);fr.pack(fill='x')
 budget=tk.StringVar();ttk.Label(right,textvariable=budget,wraplength=700).pack(fill='x');canvas=ttk.Label(right);canvas.pack()
 ttk.Label(right,text='Apercu de police : 18 colonnes, 4 lignes. Les commandes, variables et pauses ne sont pas simulees.').pack()
 selected=[None];visible=[]
 def keep():
  if selected[0] is not None:selected[0]['french']=fr.get('1.0','end-1c')
 def filter_entries(*_):
  keep();listing.delete(0,'end');visible.clear();q=query.get().lower()
  for e in project['entries']:
   if verified_only.get() and not e['verified']:continue
   if q and q not in (e['id']+' '+e['english']+' '+e['french']).lower():continue
   visible.append(e);listing.insert('end',('✓ ' if e['verified'] else '? ')+e['id']+' '+e['english'].replace('\n',' / ')[:35])
 def refresh(*_):
  e=selected[0]
  if e is None:return
  text=fr.get('1.0','end-1c') or e['english']
  try:
   raw=codec.encode(text,e['compressed']);warnings=[]
   if not e['compressed'] and len(raw)>e['length']:warnings.append('DEPASSEMENT : export refuse')
   if protected(text)!=protected(e['english']):warnings.append('COMMANDES MODIFIEES : export refuse')
   if max(map(len,text.split('\n')),default=0)>18:warnings.append('Verifier largeur : une ligne depasse 18 caracteres')
   budget.set(f"{len(raw)} octets ; emplacement {e['length']} octets. "+('Texte deplace en banque additionnelle. ' if e['compressed'] and e['length']>=3 else '')+' ; '.join(warnings))
   pic=ImageTk.PhotoImage(preview(rom,text,3));canvas.configure(image=pic);canvas.image=pic
  except ValueError as ex:budget.set(str(ex))
 def choose(_):
  ids=listing.curselection()
  if not ids:return
  keep();e=visible[ids[0]];selected[0]=e;en.configure(state='normal');en.delete('1.0','end');en.insert('1.0',e['english']);en.configure(state='disabled');fr.delete('1.0','end');fr.insert('1.0',e['french'])
  info.set(f"{e['id']} — ROM {e['offset']:05X}, banque {e['bank']:02X}, CPU {e['cpu_address']:04X} — "+('relu' if e['verified'] or e.get('notes','').startswith('Traduction relue') else 'candidat, export bloque'));refresh()
 def save():
  keep();Path(project_path).write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf8');messagebox.showinfo('Projet','Projet enregistre')
 def export():
  keep()
  try:
   from expanded_builder import build_expanded,ips_expanded
   approved={f"{e['offset']:05X}" for e in project['entries'] if e.get('notes','').startswith('Traduction relue')}
   patched,report=build_expanded(rom,project,{},approved)
   if report['blocked']:raise ValueError(str(report['blocked']))
   changes=report['changes'];name=filedialog.asksaveasfilename(defaultextension='.gb',initialfile='FFL3_FR_512K.gb')
   if name:
    Path(name).write_bytes(patched);Path(name).with_suffix('.ips').write_bytes(ips_expanded(rom,patched));messagebox.showinfo('Export',f'{len(changes)} textes modifies ; {len(patched)} octets')
  except ValueError as ex:messagebox.showerror('Export refuse',str(ex))
 def play():
  import subprocess
  path=filedialog.askopenfilename(title='Choisir une ROM exportee',filetypes=[('Game Boy','*.gb')])
  if path:subprocess.Popen([sys.executable,__file__,'emulate',path,'--window'])
 for label,cmd in [('Enregistrer projet',save),('Exporter ROM + IPS',export),('Jouer ROM',play)]:ttk.Button(toolbar,text=label,command=cmd).pack(side='left')
 listing.bind('<<ListboxSelect>>',choose);fr.bind('<KeyRelease>',refresh);query.trace_add('write',filter_entries);verified_only.trace_add('write',filter_entries);filter_entries();root.mainloop()

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 x=sub.add_parser('extract');x.add_argument('rom');x.add_argument('output');x.add_argument('--trace')
 x=sub.add_parser('build');x.add_argument('rom');x.add_argument('project');x.add_argument('output');x.add_argument('--allow-candidates',action='store_true')
 x=sub.add_parser('trace');x.add_argument('rom');x.add_argument('project');x.add_argument('--output',default='runtime_text_offsets.json')
 x=sub.add_parser('gui');x.add_argument('rom',nargs='?');x.add_argument('project',nargs='?',default=str(Path(__file__).resolve().with_name('project_fr.json')))
 x=sub.add_parser('preview');x.add_argument('rom');x.add_argument('project');x.add_argument('entry');x.add_argument('output')
 x=sub.add_parser('emulate');x.add_argument('rom');x.add_argument('--output',default='screen.png');x.add_argument('--frames',type=int,default=180);x.add_argument('--window',action='store_true')
 a=p.parse_args()
 try:
  if a.command=='trace':trace_game(a.rom,a.project,a.output);return
  if a.command=='gui':
   if gui(a.rom,a.project) is False:p.exit(1)
   return
  if a.command=='emulate':emulator(a.rom,a.output,a.frames,a.window);return
  rom=load_rom(a.rom)
  if a.command=='extract':
   observed=json.loads(Path(a.trace).read_text(encoding='utf8')) if a.trace else []
   result=extract(rom,observed);Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(f"{len(result['entries'])} entrees, {sum(e['verified'] for e in result['entries'])} validees")
  elif a.command=='build':
   project=json.loads(Path(a.project).read_text(encoding='utf8'));from expanded_builder import build_expanded,ips_expanded
   approved={f"{e['offset']:05X}" for e in project['entries'] if e.get('notes','').startswith('Traduction relue')}
   patched,report=build_expanded(rom,project,{},approved);changes=report['changes']
   if report['blocked']:raise ValueError(str(report['blocked']))
   Path(a.output).write_bytes(patched);Path(a.output).with_suffix('.ips').write_bytes(ips_expanded(rom,patched));Path(a.output).with_suffix('.changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf8');print(f'{len(changes)} entrees modifiees ; {len(patched)} octets')
  elif a.command=='preview':
   project=json.loads(Path(a.project).read_text(encoding='utf8'));e=next(e for e in project['entries'] if e['id']==a.entry);preview(rom,e['french'] or e['english']).save(a.output)
 except (OSError,ValueError,StopIteration,ImportError) as ex:p.exit(1,str(ex)+'\n')
if __name__=='__main__':main()
