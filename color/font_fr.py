"""Accent tiles in nine originally blank slots; eight use a guarded text escape."""
FONT=0xC000
ACCENT_ESCAPE=bytes.fromhex('4c 8a')
ACCENT_CODES={'é':0xAB,'è':0x80,'à':0x81,'ê':0x82,'â':0x83,'î':0x84,'ô':0x85,'ù':0x86,'ç':0x87}
BASE={'é':0xD8,'è':0xD8,'à':0xD4,'ê':0xD8,'â':0xD4,'î':0xDC,'ô':0xE2,'ù':0xE8,'ç':0xD6}
def install_font(rom):
 out=bytearray(rom)
 for char,code in ACCENT_CODES.items():
  at=FONT+(code-128)*16
  if rom[at:at+16]!=bytes.fromhex('ff00'*8):raise ValueError('Accent tile is occupied')
  base=FONT+(BASE[char]-128)*16;raw=bytearray(rom[base:base+16])
  if char=='ç':
   for row in range(1,6):raw[row*2:row*2+2]=rom[base+(row+1)*2:base+(row+2)*2]
   raw[12:16]=bytes.fromhex('ff08ff10')
  else:
   top=(0x06,0x0C) if char=='é' else (0x30,0x18) if char in 'èàù' else (0x18,0x24)
   raw[0:4]=bytes([255,top[0],255,top[1]])
   if char=='î':raw[4:6]=bytes([255,0])
  out[at:at+16]=raw
 return bytes(out)
def display_codes(raw):
 i=0
 while i<len(raw):
  if raw[i:i+2]==ACCENT_ESCAPE and i+2<len(raw) and raw[i+2] in range(128,136):
   yield raw[i+2];i+=3
  else:yield raw[i];i+=1
