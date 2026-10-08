"""Read back PCM, meter independently, plot each take, and check timing/loop invariants."""
from pathlib import Path
import json, wave, subprocess, re, importlib.util
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
rows=[]; problems=[]
figs=[]
for group in range(3):
    fig,axes=plt.subplots(3,3,figsize=(16,10),layout='constrained')
    figs.append((fig,axes))
for si,entry in enumerate(manifest):
    for take in range(1,4):
        p=ROOT/entry['slug']/f'take-{take}.wav'
        with wave.open(str(p)) as w:
            params=(w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes())
            pcm=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2)
        x=pcm.astype(float)/32768
        assert params==(48000,2,2,round(entry['duration']*48000)), (p,params)
        assert np.max(abs(pcm.astype(int)))<32767 and np.any(pcm)
        overs=signal.resample_poly(x,4,1,axis=0)
        peak=20*np.log10(np.max(abs(overs)))
        r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(p),'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True)
        summary=r.stderr[r.stderr.rfind('Summary:'):]
        p.with_suffix('.ebur128.txt').write_text('\n'.join(line.rstrip() for line in summary.splitlines()).rstrip()+'\n')
        lufs=float(re.search(r'I:\s*([-\d.]+) LUFS',summary)[1])
        assert peak<=-1 and abs(lufs-entry['target_lufs'])<=1,(p,peak,lufs)
        row=dict(slug=entry['slug'],take=take,duration=len(x)/48000,samples=len(x),lufs=lufs,true_peak_dbtp=round(peak,3),sample_peak_dbfs=round(20*np.log10(np.max(abs(x))),3))
        if entry['slug']=='endless-riser-shepard':
            delta=np.max(abs(x[0]-x[-1])); normal=np.quantile(abs(np.diff(x,axis=0)),.999)
            row['loop_seam_step']=float(delta); row['step_99_9_percentile']=float(normal)
            assert delta<normal,(p,'unusual loop seam')
            # Check derivatives around seam as well as sample-value jump.
            join=np.vstack([x[-256:],x[:256]])
            row['loop_seam_second_difference']=float(np.max(abs(np.diff(join[254:259],n=2,axis=0))))
        if entry['slug']=='ui-cozy-sprite':
            for j in range(8): assert not np.any(pcm[j*24000+13920:(j+1)*24000])
        silence={'heavy-boom-meme':1.45,'wah-wah-fail':2.6,'trailer-braam-hit':3.95,'game-coin-pickup':.48}
        if entry['slug'] in silence: assert not np.any(pcm[round(silence[entry['slug']]*48000):])
        if entry['slug']=='trailer-braam-hit': assert not np.any(pcm[22080:24000])
        f,t,s=signal.spectrogram(x.mean(axis=1),48000,nperseg=1024,noverlap=768,scaling='spectrum')
        db=10*np.log10(np.maximum(s,1e-12))
        fig,axes=plt.subplots(2,1,figsize=(10,5.5),gridspec_kw={'height_ratios':[1,3]},layout='constrained')
        step=max(1,len(x)//10000)
        axes[0].plot(np.arange(0,len(x),step)/48000,x[::step,0],lw=.5,label='L')
        axes[0].plot(np.arange(0,len(x),step)/48000,x[::step,1],lw=.4,alpha=.65,label='R')
        axes[0].set(xlim=(0,entry['duration']),ylim=(-1,1),title=f"{entry['slug']} / take {take} — {lufs:.1f} LUFS, {peak:.2f} dBTP")
        axes[0].legend(loc='upper right')
        axes[1].pcolormesh(t,f,db,shading='auto',vmin=-90,vmax=-15,cmap='magma',rasterized=True)
        axes[1].set(yscale='log',ylim=(30,16000),xlim=(0,entry['duration']),xlabel='Seconds',ylabel='Hz')
        fig.savefig(p.with_suffix('.png'),dpi=130); plt.close(fig)
        cfig,caxes=figs[si//3]; ax=caxes[si%3,take-1]
        ax.pcolormesh(t,f,db,shading='auto',vmin=-90,vmax=-15,cmap='magma',rasterized=True)
        ax.set(yscale='log',ylim=(30,16000),title=f"{entry['slug']} / {take}",xlabel='s',ylabel='Hz')
        rows.append(row)
for i,(fig,axes) in enumerate(figs):
    fig.savefig(ROOT/f'contact-sheet-{i+1}.png',dpi=120); plt.close(fig)
(ROOT/'measurements.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(dict(passed=len(rows),lufs_range=[min(r['lufs'] for r in rows),max(r['lufs'] for r in rows)],highest_true_peak=max(r['true_peak_dbtp'] for r in rows),loops=[r for r in rows if 'loop_seam_step' in r]),indent=2))
