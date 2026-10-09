"""Deterministic early-game smoke; screenshots need visual inspection."""
from pathlib import Path
from pyboy import PyBoy
ROOT=Path(__file__).parent
p=PyBoy(str(ROOT/'FFL3_FR_512K.gb'),window='null',sound_emulated=False);p.set_emulation_speed(0)
p.tick(500);p.screen.image.save(str(ROOT/'title_final.png'));p.button('start');p.tick(3);p.button_release('start')
for i in range(100):
 p.button('a');p.tick(3);p.button_release('a');p.tick(50)
 if i in [3,12,20,40]:p.screen.image.save(str(ROOT/f'intro_accent_{i}.png'))
p.screen.image.save(str(ROOT/'name_final.png'))
for k in range(6):
 p.button('start');p.tick(3);p.button_release('start');p.tick(120)
for i in range(120):
 p.button('a');p.tick(3);p.button_release('a');p.tick(50)
p.screen.image.save(str(ROOT/'combat_final.png'));print('smoke PC',hex(p.register_file.PC),'SP',hex(p.register_file.SP));p.stop(save=False)
