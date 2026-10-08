'Original comic muted-brass fail, frame-zero onset, plunger filtering, dry short room, silence by 2.6 s. Never the stock four falling-semitone sad-trombone tune.\nTake 3: A4 at 0, G4 at 5, F4 at 12, D4 at 30 with talking-mute flutter.\n48 kHz stereo PCM16; deterministic seed 44.\nRun: python take-3.py [OUT.wav]. Only numpy/scipy/stdlib required.'
SLUG='wah-wah-fail'
TAKE=3
DURATION=2.8
TARGET=-14

import sys, json, wave, subprocess, shutil, re
from pathlib import Path
import numpy as np
from scipy import signal

SR = 48000
SEED = 41 + TAKE
rng = np.random.default_rng(SEED)
N = round(DURATION * SR)

def filt(x, hz, kind='lowpass', order=3):
    return signal.sosfilt(signal.butter(order, hz, kind, fs=SR, output='sos'), x, axis=0)

def time(n): return np.arange(n) / SR
def stereo(x): return np.column_stack((x, x)) if x.ndim == 1 else x.copy()
def fade(x, attack=.002, release=.02):
    x = x.copy(); a = min(len(x), round(attack*SR)); b = min(len(x), round(release*SR))
    if a: x[:a] *= np.sin(np.linspace(0, np.pi/2, a))[:, None]**2 if x.ndim==2 else np.sin(np.linspace(0,np.pi/2,a))**2
    if b: x[-b:] *= np.cos(np.linspace(0, np.pi/2, b))[:, None]**2 if x.ndim==2 else np.cos(np.linspace(0,np.pi/2,b))**2
    return x

def put(dst, src, start, gain=1):
    i=round(start*SR); m=min(len(src),len(dst)-i)
    if m>0: dst[i:i+m] += src[:m]*gain

def osc(freq, kind='sine', duty=.5):
    f=np.asarray(freq); f=np.full(N,float(f)) if f.ndim==0 else f
    phase=np.cumsum(f)/SR; y=np.zeros(len(f))
    count=1 if kind=='sine' else min(96, int(20000/max(25,np.min(f))))
    for k in range(1,count+1):
        if kind=='triangle' and k%2==0: continue
        a=1 if kind=='sine' else ((-1)**((k-1)//2)/k**2 if kind=='triangle' else 1/k if kind=='saw' else 2*np.sin(np.pi*k*duty)/(np.pi*k))
        y += a*np.sin(2*np.pi*k*phase) * np.clip((21000-k*f)/1500,0,1)
    return y

def moving(x, center, bw=1.0, lowpass=False):
    # Time-varying spectral filter, overlapping Hann windows, no sample loop.
    f,t,z=signal.stft(x,SR,nperseg=512,noverlap=448)
    c=np.interp(t,time(len(x)),center)
    h=1/np.sqrt(1+(f[:,None]/np.maximum(c,20))**8) if lowpass else np.exp(-.5*(np.log2(np.maximum(f[:,None],1)/np.maximum(c,20))/bw)**2)
    _,out=signal.istft(z*h,SR,nperseg=512,noverlap=448)
    return out[:len(x)]

def room(x, decay=.7, dark=3000, wet=.25, mode='hall'):
    x=stereo(x); out=x.copy()
    # Dense algorithmic impulse response: decaying noise and modal early echoes.
    m=round(decay*SR); tt=time(m)
    for ch in range(2):
        ir=filt(rng.normal(size=m),dark)*np.exp(-7*tt/decay)
        ir[:round(.023*SR)]=0
        ir /= max(np.sqrt(np.sum(ir*ir)),1e-12)
        for d,a in [(0.041,.3),(.073,.22),(.113,.13),(.181,.1)]:
            j=round((d+.003*ch)*SR)
            if j<m: ir[j]+=a
        out[:,ch]+=wet*signal.fftconvolve(x[:,ch],ir)[:len(x)]
    return out

def fdn(x):
    # Four mutually coupled delay lines, evaluated in frequency domain.
    # H is a normalized Hadamard feedback scattering matrix.
    m=2**int(np.ceil(np.log2(len(x)*3))); f=np.fft.rfftfreq(m,1/SR)
    delays=np.array([.0437,.0593,.0719,.0893])
    z=np.exp(-2j*np.pi*f[:,None]*delays)
    damping=.78/(1+1j*f[:,None]/1500)
    H=np.array([[1,1,1,1],[1,-1,1,-1],[1,1,-1,-1],[1,-1,-1,1]])/2
    matrix=np.eye(4)[None,:,:]-damping[:,:,None]*z[:,:,None]*H
    transfer=np.linalg.solve(matrix,z[:,:,None]*np.ones((1,4,1))*.5)[:,:,0]
    spec=np.fft.rfft(x,m)
    return np.column_stack([np.fft.irfft(spec*np.sum(transfer*v,axis=1),m)[:len(x)] for v in [np.array([.5,.5,-.5,.5]),np.array([.5,-.5,.5,.5])]])

def boom():
    t=time(N); subf=42+68*np.exp(-t/.033)
    sub=np.tanh(1.5*osc(subf))*np.exp(-t/.16)+.18*np.sin(2*np.pi*84*t)*np.exp(-t/.2)
    body=np.zeros(N)
    ratios=[1,1.59,2.14,2.65,3.17,3.89] if TAKE!=2 else [1,1.59,2.14,2.30,2.65,2.92]
    for k,r in enumerate(ratios):
        f=(95 if TAKE==1 else 70 if TAKE==2 else 155)*r
        body+=osc(f*(1+.12*np.exp(-t/.04)) if TAKE==2 else np.full(N,f))*np.exp(-t/(.14+.025*k))/(1+k*.5)
    body=filt(body,120,'highpass')
    click=filt(rng.normal(size=N),700 if TAKE==2 else 6500)*np.exp(-t/(.004 if TAKE==2 else .0008))
    dry=.8*sub+.35*body+.18*click
    if TAKE==1: out=room(dry,1.1,3000,.3)
    elif TAKE==2: out=stereo(dry)+.28*fdn(filt(dry,120,'highpass'))
    else:
        dry=.55*sub+.55*filt(np.tanh(2*body),120,'highpass')+.16*click
        out=stereo(dry)
        put(out,stereo(filt(dry,1800)),.14,.30); put(out,stereo(filt(dry,900)),.29,.13)
    out[round(1.45*SR):]=0
    out[:round(1.45*SR)]=fade(out[:round(1.45*SR)],0,.08)
    return out

def whoosh():
    t=time(N); d=t-.6
    center=np.interp(t,[0,.6,1.2],[300,3500,900])
    env=np.exp(-(d/(.19 if TAKE!=3 else .095))**2)
    noises=[]
    for ch in range(2):
        white=rng.normal(size=N); pink=signal.lfilter([1],[1,-.94],white)
        pink/=np.std(pink)
        n=moving(pink,center,.65)
        n=moving(n,1800+7200*np.exp(-(d/.22)**2),lowpass=True)
        delay=(.00035+.0012*(1-t/1.2))*SR
        n+=.35*np.interp(np.arange(N)-delay,np.arange(N),n,left=0)
        noises.append(n)
    air=np.column_stack(noises)*env[:,None]
    if TAKE==2:
        velocity=100; closest=15; r=np.sqrt(closest**2+(velocity*d)**2)
        radial=velocity**2*d/r; freq=220*343/(343+radial)
        tone=osc(freq)+.25*osc(freq*2)+.1*osc(freq*3)
        brown=filt(signal.lfilter([1],[1,-.995],rng.normal(size=N)),[100,400],'bandpass')
        brown/=np.std(brown)
        air+=stereo((.22*tone+.2*brown)*closest/r*env)
    elif TAKE==3:
        grains=np.zeros((N,2))
        for onset in rng.uniform(.29,.91,150):
            span=rng.uniform(.007,.027); nt=round(span*SR); g=rng.normal(size=nt)*np.hanning(nt)
            g=filt(g,[1500,11000],'bandpass'); p=rng.uniform(.1,.9)
            put(grains,np.column_stack((g*np.sqrt(1-p),g*np.sqrt(p))),onset,.23*np.exp(-((onset-.6)/.12)**2))
        air=.45*air+grains
    else: air+=stereo(.045*osc(700*2**(-.25*np.tanh(d/.022)))*env)
    pan=.5+.49*np.tanh(d/(.11 if TAKE==3 else .23))
    air*=np.column_stack((np.sqrt(1-pan),np.sqrt(pan)))
    air[:,1]=np.interp(np.arange(N)-19.2,np.arange(N),air[:,1],left=0)
    return fade(filt(air,80,'highpass',5),.08,.18)

def cozy():
    out=np.zeros((N,2)); names=['tap','toggle-on','toggle-off','bubble-pop','success','error','notification','delete-swoosh']
    # F-major pentatonic F,G,A,C,D; error F5-D5 is a falling minor third.
    notes=[[698.456],[698.456,880],[880,698.456],[1046.502],[698.456,880,1046.502],[698.456,587.33],[880,1174.659],[]]
    for j,seq in enumerate(notes):
        m=round(.29*SR); t=time(m); y=np.zeros(m)
        for k,f in enumerate(seq):
            q=t-k*.045; active=q>=0; q=np.maximum(q,0)
            glide=(-1 if j in [2,5] else 1)*.025
            phase=2*np.pi*f*(q-glide*.015*np.exp(-q/.015))
            if TAKE==1: tone=np.sin(phase)+.10*np.sin(3*phase)
            elif TAKE==2:
                ratios=[1,3.99,9.83] if j%2 else [1,2.76,5.40]
                tone=sum(a*np.sin(r*phase)*np.exp(-q/(.13/(1+k2*3))) for k2,(r,a) in enumerate(zip(ratios,[1,.25,.10])))
            else: tone=np.sin(phase+.55*np.exp(-q/.018)*np.sin(phase*2.7))+.08*np.sin(phase*2.13)*np.exp(-q/.04)
            y+=tone*active*(1-np.exp(-q/.001))*np.exp(-q/(.04 if j==0 else .055))
        if j==3:
            f=650+1150*(1-np.exp(-t/.008)); y=osc(f)*np.exp(-t/.033)*(1-np.exp(-t/.001))
            y+=.15*moving(rng.normal(size=m),f,.15)*np.exp(-t/.025)
        if j==7:
            y=moving(rng.normal(size=m),2500*np.exp(-t/.09)+300,.7)*np.sin(np.pi*np.clip(t/.23,0,1))**2*np.exp(-t/.06)
        y=filt(y,2200 if j==5 else 8000,order=5); y=fade(y,.001,.035)
        y/=max(np.sqrt(np.mean(y*y)),1e-9)
        put(out,stereo(y),j*.5,.13)
    print(json.dumps([dict(slot=j+1,name=name,start_sample=j*24000,end_sample=j*24000+13920) for j,name in enumerate(names)]))
    return out

def riser():
    # Absolute gliss phase makes octave lane k at u=1 equal lane k+2 at u=0.
    # Ten lanes; compact log-frequency window vanishes outside 55..3520 Hz.
    u=np.arange(N)/N; t=time(N); out=np.zeros((N,2))
    for k in range(10):
        f0=13.75*2**k; f=f0*4**u; log=np.log2(f/440)
        w=np.where(abs(log)<3,.5+.5*np.cos(np.pi*log/3),0)
        phase=2*np.pi*f0*DURATION/np.log(4)*4**u
        for ch in range(2):
            p=phase+.08*np.sin(2*np.pi*(t/DURATION)*(3+ch))
            tone=np.sin(p)
            if TAKE==2:
                tone+=.22*np.sin(2*p)+.10*np.sin(3*p)+.05*np.sin(4*p)
            if TAKE==3: tone+=.2*np.sin(3*p+.1*np.sin(2*np.pi*u*(ch+1)))
            out[:,ch]+=w*tone*.16
    # Tempo-octave handoff: raised-cosine log-rate window gives two audible layers.
    for k in range(4):
        r0=.5*2**k; r=r0*2**u; q=np.log2(r/2)
        w=np.where(abs(q)<1,.5+.5*np.cos(np.pi*q),0)
        phase=r0*DURATION/np.log(2)*2**u
        age=(phase%1)/r
        pulse=np.sin(2*np.pi*(62*age+1.1*(1-np.exp(-age/.02))))*np.exp(-age/.045)
        # Tick phase is itself continuous under octave relabeling.
        tick=np.sin(2*np.pi*2200*age)*np.exp(-age/.002)*(1-np.exp(-age/.00015))
        if TAKE==2: tick+=.3*np.sin(2*np.pi*3711*age)*np.exp(-age/.005)
        out+=stereo(w*(.27*pulse+.07*tick if TAKE!=3 else .12*pulse+.16*tick))
    if TAKE==3:
        # Dense random-phase oscillator bands migrate with the Shepard lanes.
        # Reusing offsets across octaves preserves phase at the loop handoff.
        ratios=2**rng.uniform(-.32,.32,24); phases=rng.uniform(0,2*np.pi,(24,2))
        for k in range(10):
            f0=13.75*2**k; f=f0*4**u; q=np.log2(f/440)
            w=np.where(abs(q)<3,.5+.5*np.cos(np.pi*q/3),0)
            base=2*np.pi*f0*DURATION/np.log(4)*4**u
            for j,r in enumerate(ratios):
                for ch in range(2): out[:,ch]+=.009*w*np.sin(base*r+phases[j,ch])
    # Circular hall and processing: three cycles, keep middle.
    triple=np.tile(out,(3,1)); triple=room(triple,.7,4200,.12)
    return triple[N:2*N]

def modem():
    out=np.zeros((N,2)); tt=time(N)
    def segment(start,end,freqs,amp=.25,side=0):
        t=time(round((end-start)*SR)); y=sum(np.sin(2*np.pi*f*t) for f in freqs)*amp
        y=fade(y,.004,.004); p=.5+side*(.15 if TAKE==3 else 0)
        put(out,np.column_stack((y*np.sqrt(1-p),y*np.sqrt(p))),start)
    segment(0,1,[350,440],.2,-1)
    digits=[(697,1336),(770,1477),(852,1209),(941,1336),(697,1477),(852,1336),(770,1209)]
    for j,pair in enumerate(digits): segment(1+j*.2,1.1+j*.2,pair,.25,-1)
    segment(2.6,3.6,[440,480],.2,1)
    t=time(round(2.2*SR)); rev=(-1.)**np.floor(t/.45)
    y=np.sin(2*np.pi*2100*t)*rev*(1+.16*np.sin(2*np.pi*15*t))*.3
    put(out,stereo(fade(y,.005,.005)),3.8)
    for j in range(4):
        t=time(round(.21*SR)); bits=rng.integers(0,2,int(np.ceil(len(t)/160)))
        f=1650+200*np.repeat(bits,160)[:len(t)]
        y=fade(osc(f)*.28,.003,.003)
        p=.35 if j%2==0 and TAKE==3 else .65 if TAKE==3 else .5
        put(out,np.column_stack((y*np.sqrt(1-p),y*np.sqrt(p))),6+j*.25)
    for j in range(8):
        t=time(round(.21*SR)); y=np.zeros(len(t))
        for f in np.arange(150,3751,150):
            y+=np.sin(2*np.pi*f*t+rng.uniform(0,2*np.pi))*(-1.)**np.floor(t/(.04+j*.003))
        y/=6; y*=np.exp(-t/(.085 if TAKE==2 else .15))
        if TAKE==2: y+=.24*osc(1600+400*np.sin(2*np.pi*23*t))*np.exp(-t/.1)
        put(out,stereo(fade(y,.002,.008)),7+j*.25,.36)
    t=time(3*SR); noise=filt(rng.normal(size=len(t)),[350,3400],'bandpass'); noise/=np.std(noise)
    gate=.35+.65*(np.sin(2*np.pi*(7 if TAKE==2 else 4)*t)>-.4)
    gate=filt(gate,300); y=noise*gate*(.2+.13*t/3)
    if TAKE==2: y=np.tanh(y*2)*.4
    put(out,stereo(y),9)
    out+=stereo(filt(rng.normal(size=N),[400,3200],'bandpass'))*.008
    if TAKE==3:
        echo=np.zeros_like(out); put(echo,out,.03,.126); out+=echo
        hole=1-.75*np.exp(-((tt-6.48)/.06)**4); out*=hole[:,None]
    out=out+.08*out*out if TAKE!=2 else np.tanh(out*1.5)+.14*out*out
    out=filt(out,[400,3200] if TAKE==2 else [300,3400],'bandpass',6)
    # Broad attenuation tames answer-tone harshness without removing its identity.
    out-=.25*filt(out,[1900,2900],'bandpass',2)
    return fade(out,.002,.003)

def fail():
    out=np.zeros((N,2))
    events=[(0,329.628,.32),(.4,277.183,.35),(26/30,261.626,1.7)] if TAKE==1 else [(0,195.998,.29),(10/30,146.832,.31),(22/30,155.563,1.86)] if TAKE==2 else [(0,440,.13),(5/30,391.995,.17),(.4,349.228,.51),(1,293.665,1.59)]
    for j,(start,f,dur) in enumerate(events):
        t=time(round(dur*SR)); last=j==len(events)-1
        drop=(3 if TAKE in [1,2] else .4)*np.clip((t-(dur-1))/1,0,1) if last else 0
        vibr=(.025 if TAKE==2 else .012)*np.clip(t/dur,0,1)*np.sin(2*np.pi*(4*t+2*t*t/dur))
        freq=f*2**((-drop-.6*np.exp(-t/.025))/12+vibr)
        y=osc(freq,'saw'); y+=.045*rng.normal(size=len(t))*np.exp(-t/.025)
        cycles=2 if TAKE==1 and last else 6*dur if TAKE==3 and last else 1
        c=500+900*np.sin(np.pi*np.clip(t/dur,0,1)*cycles)**2
        y=.23*y+.85*moving(y,c,.32)
        y*=np.exp(-t/(dur*.8)); y=fade(y,.001,.12 if last else .045)
        if TAKE==2 and last: y+=fade(rng.normal(size=len(t))*np.exp(-((t-dur+.12)/.025)**2)*.07,.002,.02)
        put(out,stereo(y),start,.4)
    out=room(out,.085,4000,.035); out[round(2.6*SR):]=0
    out[:round(2.6*SR)]=fade(out[:round(2.6*SR)],0,.04)
    return out

def arcade():
    out=np.zeros(N)
    def chip(start,dur,f,kind='pulse',duty=.25,gain=.35):
        t=time(round(dur*SR)); freq=f(t) if callable(f) else np.full(len(t),f)
        y=osc(freq,kind,duty)
        steps=np.floor(t*60)/60; env=np.round(15*np.exp(-steps/max(.035,dur*.45)))/15
        env=signal.lfilter(np.ones(48)/48,[1],env)
        put(out,fade(y*env,.001,.008),start,gain)
    if TAKE==1:
        at=0
        for j in range(8):
            dur=.14-j*.08/7; hi=1100-j*680/7; lo=500-j*350/7
            chip(at,dur,lambda t,hi=hi,lo=lo,dur=dur: (hi+(lo-hi)*t/dur)*(1+.012*np.sin(2*np.pi*35*t)))
            at+=dur+.025
        for at,f in [(1.13,146.832),(1.4,110)]:
            chip(at,.25,lambda t,f=f:f*(1+.3*np.exp(-t/.025)))
            chip(at,.25,f/2,'triangle',gain=.2)
    elif TAKE==2:
        for at,f,d in [(0,783.991,.15),(.183333,622.254,.15),(.366667,523.251,.15),(.55,493.883,.15),(.766667,391.995,.70)]:
            chip(at,d,lambda t,f=f:f*(1+.006*np.sin(2*np.pi*5*t)),duty=.5)
            chip(at,d,f/2**(9/12),duty=.125,gain=.13)
        for at,f in [(0,130.813),(.5,97.999),(1,65.406)]: chip(at,.42,f,'triangle',gain=.22)
        t=time(9600); put(out,fade(filt(rng.normal(size=len(t)),1500)*np.exp(-t/.025),.001,.02),1.5,.2)
    else:
        chip(0,1.1,lambda t:880*2**(-3*t/1.1+.13*np.sin(2*np.pi*(12*t-3*t*t))),duty=.5)
        for at,f in [(1.15,110),(1.35,82.407),(1.55,55)]:chip(at,.17,f,duty=.5)
        t=time(7200); put(out,fade(filt(rng.normal(size=len(t)),5000)*np.exp(-t/.015),.001,.015),1.64,.18)
    return stereo(fade(filt(filt(out,90,'highpass',1),12000,order=4),0,.025))

def braam():
    out=np.zeros((N,2)); t=time(round(.46*SR))
    suck=moving(rng.normal(size=len(t)),500+6000*(t/.46)**2,.8)*(t/.46)**3
    put(out,stereo(fade(suck,.02,.008)),0,.12)
    def hit(start,shift,gain,second=False):
        n=N-round(start*SR); t=time(n); body=np.zeros((n,2))
        notes=np.array([32.7032,65.4064,97.9989,130.8128,155.5635])*2**(shift/12)
        for f in notes:
            for detune in ([-8,-4,0,4,8] if TAKE==3 else [-6,0,6]):
                freq=f*2**((detune-60*np.exp(-t/.035))/1200)
                voice=osc(freq,'saw'); pan=.5+detune/30
                body+=voice[:,None]*np.array([np.sqrt(1-pan),np.sqrt(pan)])[None,:]/len(notes)
        cutoff=200+3300*(1-np.exp(-t/.018))*np.exp(-t/(1.6 if TAKE==2 else 1))
        for ch in range(2):
            body[:,ch]=moving(body[:,ch],cutoff,lowpass=True)
            body[:,ch]+=.45*filt(body[:,ch],[350,600] if TAKE==2 else [550,850],'bandpass',2)
        if TAKE==2:
            body+=.16*body*np.sin(2*np.pi*277*t)[:,None]
            body=np.tanh(body*2)
        body*=(1+(.10 if second else .23)*np.sin(2*np.pi*30*t))[:,None]
        body=np.tanh(body*.9)*np.exp(-t/.95)[:,None]
        if second: body*=np.minimum(t/.16,1)[:,None]
        else:
            sub=osc(30+25*np.exp(-t/.09) if TAKE==2 else np.full(n,49))*np.exp(-t/.1)
            crack=filt(rng.normal(size=n),6000)*np.exp(-t/.003)
            body+=stereo(.45*sub+.13*crack)
        put(out,room(fade(body,.0003,.1),3,2400,.3),start,gain)
    hit(.5,0,.55)
    if TAKE==3: hit(2,3,.34,True)
    out[round(3.95*SR):]=0; out[:round(3.95*SR)]=fade(out[:round(3.95*SR)],0,.13)
    # Suck is fully off for 40 ms before the frame-15 attack.
    out[round(.46*SR):round(.5*SR)]=0
    return out

def coin():
    out=np.zeros((N,2))
    if TAKE==1:
        for at,f,dur in [(0,1174.7,.045),(.045,1975.5,.4)]:
            t=time(round(dur*SR)); p=2*np.pi*f*t
            y=np.sin(p+.65*np.exp(-t/.009)*np.sin(3.5*p))*np.exp(-t/(.017 if at==0 else .073))
            put(out,stereo(fade(y,.0005,.015)),at,.45)
        for k in range(6):
            at=.06+k*.024; t=time(4800); f=rng.uniform(2700,6400)
            y=fade(np.sin(2*np.pi*f*t)*np.exp(-t/.018),.001,.02); pan=rng.uniform(.1,.9)
            put(out,np.column_stack((y*np.sqrt(1-pan),y*np.sqrt(pan))),at,.08)
    elif TAKE==2:
        for at,f in [(0,830.6),(.055,1046.5)]:
            t=time(round(.36*SR)); y=np.zeros(len(t))
            for k,r in enumerate([1,2.08,3.87,5.36]): y+=np.sin(2*np.pi*f*r*t)*np.exp(-t/(.07/(1+k)))/(1+k)
            y+=.06*filt(rng.normal(size=len(t)),[3000,8000],'bandpass')*np.exp(-t/.001)
            put(out,stereo(fade(y,.0005,.02)),at,.4)
        for k in range(8):
            t=time(3360); y=fade(np.sin(2*np.pi*(2000+k*280)*t)*np.exp(-t/.015),.001,.01)
            put(out,stereo(y),.075+k*.013,.045)
    else:
        t=time(N); f=1396.9*2**((7/12)*np.minimum(t/.03,1)); p=2*np.pi*np.cumsum(f)/SR
        y=(np.sin(p)+.065*np.sin(3*p))*np.exp(-t/.09)
        out=stereo(y)*.5
        out[:,1]+=.035*np.sin(p+.16*np.sin(2*np.pi*7*t))*np.exp(-t/.08)
        glint=filt(rng.normal(size=4800),[4500,9500],'bandpass')*np.exp(-time(4800)/.005)
        put(out,stereo(fade(glint,.0005,.02)),.03,.1)
    out=filt(filt(out,350,'highpass',4),9500,order=6)
    out[round(.48*SR):]=0; out[:round(.48*SR)]=fade(out[:round(.48*SR)],.0003,.045)
    return out

def integrated(x):
    # BS.1770 K-weighting coefficients for exactly 48 kHz; 400 ms/100 ms gates.
    y=signal.lfilter([1.53512485958697,-2.69169618940638,1.19839281085285],[1,-1.69065929318241,.73248077421585],x,axis=0)
    y=signal.lfilter([1,-2,1],[1,-1.99004745483398,.99007225036621],y,axis=0)
    energy=np.sum(y*y,axis=1); c=np.r_[0,np.cumsum(energy)]
    starts=np.arange(0,len(x)-19200+1,4800)
    block=(c[starts+19200]-c[starts])/19200
    loud=-.691+10*np.log10(np.maximum(block,1e-30))
    valid=block[loud>-70]
    if not len(valid): return -120.
    relative=-.691+10*np.log10(np.mean(valid))-10
    valid=block[(loud>-70)&(loud>relative)]
    return float(-.691+10*np.log10(np.mean(valid)))

def tp(x): return float(np.max(np.abs(signal.resample_poly(x,4,1,axis=0))))
def master(x):
    loop=SLUG=='endless-riser-shepard'
    def process(z):
        z=filt(z,25,'highpass',2)
        mid=z.mean(axis=1); side=(z[:,0]-z[:,1])/2
        side=filt(side,250 if SLUG=='trailer-braam-hit' else 120,'highpass',6)
        return np.column_stack((mid+side,mid-side))
    x=process(np.tile(x,(3,1)))[N:2*N] if loop else process(x)
    # Preserve the explicitly silent regions after all recursive filters.
    if SLUG=='ui-cozy-sprite':
        for j in range(8):
            a=j*24000; x[a:a+13920]=fade(x[a:a+13920],0,.006); x[a+13920:a+24000]=0
    silence={'heavy-boom-meme':1.45,'wah-wah-fail':2.6,'trailer-braam-hit':3.95,'game-coin-pickup':.48}
    if SLUG in silence:
        end=round(silence[SLUG]*SR); x[:end]=fade(x[:end],0,.012); x[end:]=0
    if SLUG=='trailer-braam-hit': x[22080:24000]=0
    if not loop: x=fade(x,0,.003)
    x/=max(np.max(np.abs(x)),1e-12)
    # Gentle memoryless crest reduction only where needed, measured after each pass.
    for drive in [1,1.4,2,3,4,6,8]:
        z=x if drive==1 else np.tanh(x*drive)/np.tanh(drive)
        z*=10**((TARGET-integrated(z))/20)
        peak=tp(np.tile(z,(3,1))[N-128:2*N+128] if loop else z)
        if peak<=10**(-1.05/20): break
    z*=min(1,10**(-1.05/20)/peak)
    assert z.shape==(N,2) and np.isfinite(z).all()
    return z

def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_suffix('.wav')
    functions={'heavy-boom-meme':boom,'whoosh-pass-by':whoosh,'ui-cozy-sprite':cozy,'endless-riser-shepard':riser,'dialup-modem-56k':modem,'wah-wah-fail':fail,'arcade-game-over':arcade,'trailer-braam-hit':braam,'game-coin-pickup':coin}
    x=master(functions[SLUG]()); pcm=np.rint(x*32767).astype('<i2')
    with wave.open(str(out),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(json.dumps(dict(file=str(out),samples=N,lufs=integrated(pcm.astype(float)/32768),true_peak_db=20*np.log10(tp(pcm.astype(float)/32768)))))
    if shutil.which('ffmpeg'):
        result=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(out),'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True)
        if result.returncode: raise RuntimeError(result.stderr[-2000:])
        print(result.stderr[result.stderr.rfind('Summary:'):])

if __name__=='__main__': main()
