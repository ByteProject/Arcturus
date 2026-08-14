"""Stage the emulated SD card for the Agon probe: probe.bin plus the
MOS autoexec that loads and runs it. fab-agon-emulator mounts the
directory directly (--sdcard sdcard/), and real hardware takes the same
two files on a FAT32 card, so the staged directory IS the distribution.

Run after every reassembly: python3 mk_sd.py
Then:  fab-agon-emulator --sdcard sdcard/
"""

import os
import shutil

_HERE = os.path.dirname(os.path.abspath(__file__))
sd = os.path.join(_HERE, "sdcard")
os.makedirs(sd, exist_ok=True)
shutil.copyfile(os.path.join(_HERE, "probe.bin"),
                os.path.join(sd, "probe.bin"))
with open(os.path.join(sd, "autoexec.txt"), "w") as f:
    f.write("load probe.bin\r\nrun\r\n")
print(f"sdcard/ staged: probe.bin "
      f"({os.path.getsize(os.path.join(sd, 'probe.bin'))} bytes) "
      f"+ autoexec.txt")
