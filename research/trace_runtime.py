import sys,json
from pathlib import Path
sys.path.insert(0,'ffl3_next')
from ffl3_editor import Codec,GLYPHS
from font_fr import ACCENT_CODES
from pyboy import PyBoy
rom=sys.argv[1];out=sys.argv[2]
p=PyBoy(rom,window='null',sound_emulated=False);p.set_emulation_speed(0);log=[]
def record(p):
 a=((p.register_file.D<<8)|p.register_file.E);n=p.register_file.B;b=p.memory[0xc0b1]
 if not n or n>128:return
 raw=bytes(p.memory[a:a+n]);text=''.join(next((ch for ch,code in ACCENT_CODES.items() if code==v),GLYPHS.get(v,f'[{v:02X}]')) for v in raw)
 log.append({'frame':p.frame_count,'bank':b,'cpu':a,'offset':b*0x4000+a-0x4000 if 0x4000<=a<0x8000 else a,'raw':raw.hex(),'text':text})
p.hook_register(0,0x3304,record,p)
p.tick(500);p.button('start');p.tick(3);p.button_release('start')
for i in range(160):
 p.button('a');p.tick(3);p.button_release('a');p.tick(50)
for i in range(6):
 p.button('start');p.tick(3);p.button_release('start');p.tick(120)
for i in range(120):
 p.button('a');p.tick(3);p.button_release('a');p.tick(50)
Path(out).write_text(json.dumps(log,ensure_ascii=False,indent=2));p.stop(save=False)
print('rendered chunks',len(log))
