import sys,json
from pathlib import Path
sys.path.insert(0,'ffl3_next')
from ffl3_editor import GLYPHS
from font_fr import ACCENT_CODES
from pyboy import PyBoy
root=Path('ffl3_next');p=PyBoy(str(root/'FFL3_FR_512K.gb'),window='null',sound_emulated=False);p.set_emulation_speed(0)
state={'again':False,'chunks':[]}
def text(p):
 a=(p.register_file.D<<8)|p.register_file.E;n=p.register_file.B
 if not n or n>128:return
 raw=bytes(p.memory[a:a+n]);t=''.join(GLYPHS.get(v, next((ch for ch,code in ACCENT_CODES.items() if code==v),f'[{v:02X}]')) for v in raw)
 state['chunks'].append(t)
 if '[F9]' in t:
  bank=p.memory[0xc0b1];print('F9',p.frame_count,'bank',bank,'cpu',hex(a),'raw',raw.hex(),'HL',hex(p.register_file.HL),'SP',hex(p.register_file.SP))
  print('stack',bytes(p.memory[p.register_file.SP:p.register_file.SP+24]).hex());p.screen.image.save(str(root/'unexpected_glyph.png'))
 if 'Recombattre' in t:state['again']=True
p.hook_register(0,0x3304,text,p)
p.tick(500);p.button('start');p.tick(3);p.button_release('start')
for i in range(160):
 p.button('a');p.tick(3);p.button_release('a');p.tick(50)
for i in range(6):
 p.button('start');p.tick(3);p.button_release('start');p.tick(120)
for i in range(1800):
 p.button('a');p.tick(3);p.button_release('a');p.tick(50)
 if '[F9]' in state['chunks'][-1:] or state['again']:
  p.screen.image.save(str(root/'combat_victory_prompt.png'));print('victory prompt at',i,'bank',p.memory[0xc0b1]);break
else:print('No repeat prompt reached')
with open('combat_checkpoint.state','wb') as f:p.save_state(f)
(root/'combat_route_trace.json').write_text(json.dumps(state,ensure_ascii=False,indent=2));p.screen.image.save(str(root/'combat_route_end.png'));p.stop(save=False)
