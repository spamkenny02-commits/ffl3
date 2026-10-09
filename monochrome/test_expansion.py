import hashlib,json,sys,unittest,os
from pathlib import Path
from expanded_builder import *
ROOT=Path(__file__).parent
ORIGINAL=Path(os.environ.get('FFL3_ORIGINAL_FILE',str(ROOT/'original.gb')))
class ExpansionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rom=load_rom(ORIGINAL);cls.out=(ROOT/'FFL3_FR_512K.gb').read_bytes();cls.report=json.loads((ROOT/'FFL3_FR_512K.report.json').read_text(encoding='utf8'));cls.project=json.loads((ROOT/'project_fr.json').read_text(encoding='utf8'))
 def test_mapper_checksums(self):
  o=self.out;self.assertEqual(len(o),524288);self.assertEqual(o[0x147:0x14A],bytes([3,4,2]))
  self.assertEqual(o[0x14D],(-sum(o[0x134:0x14D])-25)&255)
  self.assertEqual(int.from_bytes(o[0x14E:0x150],'big'),(sum(o)-o[0x14E]-o[0x14F])&65535)
 def test_ips_replays_exactly(self):
  ips=(ROOT/'FFL3_FR_512K.ips').read_bytes();o=bytearray(self.rom);i=5;self.assertEqual(ips[:5],b'PATCH')
  while ips[i:i+3]!=b'EOF':
   at=int.from_bytes(ips[i:i+3],'big');n=int.from_bytes(ips[i+3:i+5],'big');i+=5;self.assertGreater(n,0)
   if at+n>len(o):o.extend(bytes(at+n-len(o)))
   o[at:at+n]=ips[i:i+n];i+=n
  self.assertEqual(int.from_bytes(ips[i+3:i+6],'big'),len(self.out));self.assertEqual(bytes(o),self.out)
 def test_pointers_commands_far_strings(self):
  self.assertEqual(self.out[0x28004:0x281E2],self.rom[0x28004:0x281E2]);self.assertFalse(self.report['blocked'])
  c=Codec(self.rom)
  for code,t in DICT_FR.items():c.dictionary[code]=c.encode(t,False)
  entries={f"{e['offset']:05X}":e for e in self.project['entries']}
  for ch in self.report['changes']:
   e=entries[ch['offset']];self.assertEqual(protected(ch['french']),protected(e['english']))
   if ch['mode']!='far':continue
   a=e['offset'];n=e['length']
   if n>=6:
    self.assertEqual(self.out[a:a+3],MARKER);bank=self.out[a+3];ptr=int.from_bytes(self.out[a+4:a+6],'little');used=6
   else:
    self.assertEqual(self.out[a:a+2],SHORT_MARKER);tab=SHORT_TABLE+3*self.out[a+2];bank=self.out[tab];ptr=int.from_bytes(self.out[tab+1:tab+3],'little');used=3
   self.assertEqual(self.out[a+used:a+n],b'\x4c'*(n-used));self.assertIn(bank,[16,17]);raw=c.encode(ch['french']);at=bank*0x4000+ptr-0x4000
   self.assertEqual(self.out[at:at+len(raw)+1],raw+b'\x00');self.assertLessEqual(ptr+len(raw)+1,0x8000)
 def test_modified_project_rebuild(self):
  approved={f"{e['offset']:05X}" for e in self.project['entries'] if e.get('notes','').startswith('Traduction relue')}
  rebuilt,report=build_expanded(self.rom,self.project,{},approved)
  self.assertEqual(rebuilt,self.out);self.assertFalse(report['blocked'])
 def test_dictionary_loader_and_contents(self):
  self.assertEqual(self.out[0x3094:0x309A],bytes.fromhex('21 00 40 3e 1f e7'))
  c=Codec(self.rom);at=DICT_BANK*0x4000
  for m in c.dictionary_meta:
   code=int(m['code'],16);want=c.encode(DICT_FR[code],False) if code in DICT_FR else c.dictionary[code]
   n=self.out[at];self.assertEqual(self.out[at+1:at+1+n],want);at+=n+1
class AccentTests(unittest.TestCase):
 setUpClass=classmethod(ExpansionTests.setUpClass.__func__)
 def test_accent_roundtrip_and_original_dictionary_code(self):
  from font_fr import ACCENT_CODES
  c=Codec(self.rom);text='é è à ê â î ô ù ç'
  self.assertEqual(c.decode(c.encode(text)),text)
  self.assertEqual(c.decode(bytes([0x80])),'ight')
 def test_font_changes_only_blank_slots(self):
  from font_fr import FONT,ACCENT_CODES,install_font
  patched=install_font(self.rom);allowed=set()
  for code in ACCENT_CODES.values():
   at=FONT+(code-128)*16;self.assertEqual(self.rom[at:at+16],bytes.fromhex('ff00'*8));allowed.update(range(at,at+16))
  self.assertTrue(all(a in allowed for a,(x,y) in enumerate(zip(self.rom,patched)) if x!=y))
  self.assertEqual(patched[FONT+(0xf9-128)*16:FONT+(0xfb-128)*16],self.rom[FONT+(0xf9-128)*16:FONT+(0xfb-128)*16])
 def test_runtime_accent_escape_and_bank_restore(self):
  import tempfile
  from pyboy import PyBoy
  from font_fr import ACCENT_CODES
  out=bytearray(self.out);c=Codec(self.rom);raw=c.encode('é è à ê â î ô ù ç\nAccents français !\n[10]')
  out[30*0x4000:30*0x4000+len(raw)+1]=raw+b'\0'
  entry=next(e for e in self.report['changes'] if e['mode']=='far');at=int(entry['offset'],16)
  out[at+3:at+6]=bytes([30,0,64]);checksum(out)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'test.gb';path.write_bytes(out)
   p=PyBoy(str(path),window='null',sound_emulated=False);p.set_emulation_speed(0);banks=set()
   def bank(p):banks.add(p.register_file.A)
   p.hook_register(0,0x38e1,bank,p)
   try:
    p.tick(500);p.button('start');p.tick(3);p.button_release('start');p.tick(60);p.button('a');p.tick(3);p.button_release('a');p.tick(1000)
    seq=bytes([0xab,255,128,255,129,255,130,255,131,255,132,255,133,255,134,255,135])
    self.assertIn(seq,bytes(p.memory[0x9800:0xa000]));self.assertTrue({30,31}<=banks);self.assertEqual(p.memory[0xc0b1],30)
    # Leave the explicit wait, finish the temporary string and restore the parent bank.
    p.button('a');p.tick(3);p.button_release('a');p.tick(500)
    self.assertNotEqual(p.memory[0xc0b1],30)
   finally:p.stop(save=False)
class GameRouteTests(unittest.TestCase):
 def test_layout_operand_kept_outside_translation(self):
  rom=load_rom(ORIGINAL);out=(ROOT/'FFL3_FR_512K.gb').read_bytes()
  self.assertEqual(rom[0x261f0:0x261f2],bytes.fromhex('13 16'))
  self.assertEqual(out[0x261f0:0x261f2],rom[0x261f0:0x261f2])
  self.assertEqual(out[0x261f2:0x261f5],MARKER)
 def test_reinsertion_rejects_command_operand(self):
  import copy
  rom=load_rom(ORIGINAL);project=json.loads((ROOT/'project_fr.json').read_text(encoding='utf8'));bad=copy.deepcopy(project)
  e=next(e for e in bad['entries'] if e['offset']==0x261f2)
  e.update(offset=0x261f1,length=11,source_hex=rom[0x261f1:0x261fc].hex(),english=Codec(rom).decode(rom[0x261f1:0x261fc]),verified=True)
  out,report=build_expanded(rom,bad,{},set())
  self.assertTrue(any(e['reason']=='overlaps known script operand' for e in report['blocked']))
  self.assertEqual(out[0x261f1],rom[0x261f1])
 def test_first_combat_story_save_and_reload(self):
  import tempfile,shutil
  from runtime_audit import run
  from pyboy import PyBoy
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder);audit=path/'audit.json'
   result=run(ROOT/'FFL3_FR_512K.gb',ROOT/'FFL3_FR_512K.report.json',audit,1000)
   self.assertFalse(result['invalid_reads'])
   words=''.join(x['text'] for x in result['chunks'])
   self.assertIn('Gagné !14 EXP augmente !Reçu : 560GP.',words)
   self.assertIn('monde de la noyade.',words);self.assertNotIn('de from',words)
   self.assertIn('Sharon...',words);self.assertNotIn("Sharon's",words)
   self.assertIn('Des monstres yrodent. Soyezprudents.',words)
   probe=path/'probe.gb';shutil.copyfile(ROOT/'FFL3_FR_512K.gb',probe)
   p=PyBoy(str(probe),window='null',sound_emulated=False);p.set_emulation_speed(0)
   def press(p,key,frames=8,after=60):
    p.button(key);p.tick(frames);p.button_release(key);p.tick(after)
   try:
    with open(audit.with_suffix('.state'),'rb') as f:p.load_state(f)
    press(p,'start',after=90);party=p.screen.image.copy();party.save(str(ROOT/'party_before_save.png'))
    for i in range(6):press(p,'down')
    press(p,'a',after=180)
    self.assertIn(Codec(load_rom(ORIGINAL)).encode('quel fichier ?',False),bytes(p.memory[0x9800:0xa000]))
    p.screen.image.save(str(ROOT/'save_menu.png'))
    press(p,'a',after=240)
   finally:p.stop(save=True)
   self.assertEqual(probe.with_suffix('.gb.ram').stat().st_size,8192)
   p=PyBoy(str(probe),window='null',sound_emulated=False);p.set_emulation_speed(0)
   try:
    p.tick(500);press(p,'start',after=90);press(p,'a',after=180);press(p,'a',after=180)
    p.screen.image.save(str(ROOT/'world_after_load.png'));press(p,'start',after=90)
    p.screen.image.save(str(ROOT/'party_after_load.png'))
    self.assertEqual(p.screen.image.crop((40,0,88,144)).tobytes(),party.crop((40,0,88,144)).tobytes())
    p.screen.image.save(str(ROOT/'party_after_load.png'))
   finally:p.stop(save=False)
if __name__=='__main__':unittest.main()
