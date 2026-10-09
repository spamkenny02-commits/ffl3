"""Observe rendered glyphs and detect reads into relocated original text slots.
Run: python runtime_audit.py translated.gb translated.report.json output.json
"""
import argparse,json
from pathlib import Path
from pyboy import PyBoy
from ffl3_editor import GLYPHS
from font_fr import ACCENT_CODES

def run(rom_path,report_path,output,cycles=1800):
 report=json.loads(Path(report_path).read_text(encoding='utf8'));project=json.loads(Path(report_path).with_name('project_fr.json').read_text(encoding='utf8'))
 entries={f"{e['offset']:05X}":e for e in project['entries']}
 relocated=[(entries[ch['offset']]['offset'],entries[ch['offset']]['offset']+entries[ch['offset']]['length'],ch['offset']) for ch in report['changes'] if ch['mode']=='far']
 result={'chunks':[],'invalid_reads':[],'frames':0,'full_playthrough':False}
 p=PyBoy(str(rom_path),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def observe(p):
  a=(p.register_file.D<<8)|p.register_file.E;n=p.register_file.B;bank=p.memory[0xc0b1]
  if not n or n>128:return
  raw=bytes(p.memory[a:a+n]);text=''.join(GLYPHS.get(v,next((ch for ch,code in ACCENT_CODES.items() if code==v),f'[{v:02X}]')) for v in raw)
  physical=bank*0x4000+a-0x4000 if 0x4000<=a<0x8000 else a
  item={'frame':p.frame_count,'bank':bank,'cpu':a,'offset':physical,'raw':raw.hex(),'text':text}
  result['chunks'].append(item)
  if 0x4000<=a<0x8000 and bank<16:
   for start,end,key in relocated:
    if physical<end and start<physical+n:
     result['invalid_reads'].append(dict(item,entry=key))
 p.hook_register(0,0x3304,observe,p)
 try:
  p.tick(500);p.button('start');p.tick(3);p.button_release('start')
  for i in range(160):
   p.button('a');p.tick(3);p.button_release('a');p.tick(50)
  for i in range(6):
   p.button('start');p.tick(3);p.button_release('start');p.tick(120)
  for i in range(cycles):
   p.button('a');p.tick(3);p.button_release('a');p.tick(50)
  result['frames']=p.frame_count
  p.screen.image.save(str(Path(output).with_suffix('.png')))
  with open(Path(output).with_suffix('.state'),'wb') as f:p.save_state(f)
 finally:p.stop(save=False)
 Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print('rendered',len(result['chunks']),'invalid reads',len(result['invalid_reads']),'frames',result['frames'])
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('rom');ap.add_argument('report');ap.add_argument('output');ap.add_argument('--cycles',type=int,default=1800);a=ap.parse_args()
 run(a.rom,a.report,a.output,a.cycles)
