import json,os,tempfile,unittest,sys
from pathlib import Path
from color_builder import build_color,apply_ips,checksum
from ffl3_editor import load_rom,Codec,protected
from expanded_builder import DICT_FR
ROOT=Path(__file__).parent
ORIGINAL=Path(os.environ.get('FFL3_ORIGINAL_FILE',str(ROOT/'original.gb')))
class ColorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=load_rom(ORIGINAL);cls.patch=(ROOT/'FFL3_color_source.ips').read_bytes();cls.project=json.loads((ROOT/'project_fr.json').read_text(encoding='utf8'))
  cls.out=(ROOT/'FFL3_FR_Color.gb').read_bytes();cls.base=apply_ips(cls.original,cls.patch);cls.report=json.loads((ROOT/'FFL3_FR_Color.report.json').read_text(encoding='utf8'))
 def test_size_mapper_checksums_and_rebuild(self):
  self.assertEqual(len(self.out),len(self.base));self.assertEqual(len(self.out),524288);self.assertEqual(self.out[0x143:0x14D],self.base[0x143:0x14D]);self.assertEqual(self.out[0x147],0x1B)
  check=bytearray(self.out);checksum(check);self.assertEqual(check,self.out)
  rebuilt,base,report=build_color(self.original,self.patch,self.project);self.assertEqual(rebuilt,self.out);self.assertFalse(report['blocked'])
 def test_both_patch_routes_and_color_changes_preserved(self):
  self.assertEqual(apply_ips(self.original,(ROOT/'FFL3_FR_Color.ips').read_bytes()),self.out)
  self.assertEqual(apply_ips(self.base,(ROOT/'FFL3_FR_Color_sur_couleur.ips').read_bytes()),self.out)
  for at,value in enumerate(self.base):
   old=self.original[at] if at<len(self.original) else 0
   if value!=old and at not in [0x14D,0x14E,0x14F]:self.assertEqual(self.out[at],value,f'Color byte changed at {at:05X}')
  self.assertEqual(self.out[0x28004:0x281E2],self.original[0x28004:0x281E2])
 def test_far_pointers_and_commands(self):
  entries={f"{e['offset']:05X}":e for e in self.project['entries']};c=Codec(self.original)
  for code,text in DICT_FR.items():c.dictionary[code]=c.encode(text,False)
  for ch in self.report['changes']:
   e=entries[ch['offset']];self.assertEqual(protected(ch['french']),protected(e['english']))
   if ch['mode']!='far':continue
   a=e['offset']
   if e['length']>=6:bank=self.out[a+3];ptr=int.from_bytes(self.out[a+4:a+6],'little')
   else:
    t=self.report['short_table_offset']+3*self.out[a+2];bank=self.out[t];ptr=int.from_bytes(self.out[t+1:t+3],'little')
   self.assertIn(bank,[18,19]);at=bank*0x4000+ptr-0x4000;raw=c.encode(ch['french']);self.assertEqual(self.out[at:at+len(raw)+1],raw+b'\0')
 def test_accent_render_and_bank_restore(self):
  from pyboy import PyBoy
  c=Codec(self.original);raw=c.encode('é è à ê â î ô ù ç\nAccents français !\n[10]');out=bytearray(self.out);out[30*0x4000:30*0x4000+len(raw)+1]=raw+b'\0'
  entry=next(e for e in self.report['changes'] if e['mode']=='far' and e['capacity']>=6);a=int(entry['offset'],16);out[a+3:a+6]=bytes([30,0,64]);checksum(out)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'test.gb';path.write_bytes(out);p=PyBoy(str(path),window='null',sound_emulated=False);p.set_emulation_speed(0)
   try:
    p.tick(500);press(p,'start',after=60);press(p,'a',after=1000)
    seq=bytes([0xAB,255,128,255,129,255,130,255,131,255,132,255,133,255,134,255,135]);self.assertIn(seq,bytes(p.memory[0x9800:0xA000]));p.screen.image.save(str(ROOT/'color_accents.png'))
    # The relocated renderer executes in bank 31 between reads from bank 30.
    self.assertEqual(p.memory[0xC0B1],31);press(p,'a',after=500);self.assertLess(p.memory[0xC0B1],16)
   finally:p.stop(save=False)
 def test_story_save_and_cold_reload(self):
  from pyboy import PyBoy
  audit=json.loads((ROOT/'color_audit.json').read_text(encoding='utf8'));self.assertFalse(audit['invalid_reads']);words=''.join(x['text'] for x in audit['chunks'])
  for text in ['Gagné !14 EXP augmente !Reçu : 560GP.','monde de la noyade.','Des monstres yrodent. Soyezprudents.']:self.assertIn(text,words)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'save.gb';path.write_bytes(self.out);p=PyBoy(str(path),window='null',sound_emulated=False);p.set_emulation_speed(0)
   try:
    with (ROOT/'color_audit.state').open('rb') as f:p.load_state(f)
    press(p,'start',after=90);party=p.screen.image.copy();party.save(str(ROOT/'color_party.png'))
    for i in range(6):press(p,'down')
    press(p,'a',after=180);self.assertIn(Codec(self.original).encode('quel fichier ?',False),bytes(p.memory[0x9800:0xA000]));p.screen.image.save(str(ROOT/'color_save.png'));press(p,'a',after=240)
   finally:p.stop(save=True)
   self.assertEqual(path.with_suffix('.gb.ram').stat().st_size,8192)
   p=PyBoy(str(path),window='null',sound_emulated=False);p.set_emulation_speed(0)
   try:
    p.tick(500);press(p,'start',after=90);press(p,'a',after=180);press(p,'a',after=180);p.screen.image.save(str(ROOT/'color_reload_world.png'));press(p,'start',after=90);p.screen.image.save(str(ROOT/'color_reload_party.png'))
    self.assertEqual(p.screen.image.crop((40,0,88,144)).tobytes(),party.crop((40,0,88,144)).tobytes())
   finally:p.stop(save=False)
def press(p,key,frames=3,after=60):
 p.button(key);p.tick(frames);p.button_release(key);p.tick(after)
if __name__=='__main__':unittest.main()
