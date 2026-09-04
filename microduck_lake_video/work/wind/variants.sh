#!/bin/zsh
# Wind = low-frequency rumble (<150 Hz). Variants = steep high-pass on 0-8 s of the cut, crossfaded (0.5 s) to the untouched audio at 8 s.
set -e
IN=dlg_orig.wav
build(){ name=$1; flt=$2
  ffmpeg -y -loglevel error -i $IN -filter_complex "
   [0:a]asplit=2[o1][o2];
   [o1]${flt},atrim=0:8.5,asetpts=PTS-STARTPTS[pa];
   [o2]atrim=8:,asetpts=PTS-STARTPTS[pb];
   [pa][pb]acrossfade=d=0.5:c1=tri:c2=tri[out]" -map "[out]" -c:a pcm_s16le dlg_${name}.wav
  echo "built $name"; }
build G_hp160       "highpass=f=160:poles=2,highpass=f=160:poles=2"
build H_hp220       "highpass=f=220:poles=2,highpass=f=220:poles=2"
build I_hp220_dn    "highpass=f=220:poles=2,highpass=f=220:poles=2,afftdn=nr=15:nf=-35:tn=1"
build J_hp300_dn    "highpass=f=300:poles=2,highpass=f=300:poles=2,afftdn=nr=20:nf=-35:tn=1"
build K_hp220_dn_gate "highpass=f=220:poles=2,highpass=f=220:poles=2,afftdn=nr=15:nf=-35:tn=1,agate=threshold=0.02:ratio=3:attack=15:release=300:knee=4"
# Reachy is far from the phone in the opening, so after removing the rumble the two first lines are ~18 dB under the later ones: add makeup gain on 0-8 s.
build L_hp220_dn_gain10 "highpass=f=220:poles=2,highpass=f=220:poles=2,afftdn=nr=15:nf=-35:tn=1,volume=10dB"
build M_hp220_dn_gain14 "highpass=f=220:poles=2,highpass=f=220:poles=2,afftdn=nr=15:nf=-35:tn=1,volume=14dB"
