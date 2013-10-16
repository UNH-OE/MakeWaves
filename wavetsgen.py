# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 18:48:22 2013

@author: Pete Bachant

This module generates various wave spectra and time series.

Pierson-Moskowitz formula taken from:
http://oceanworld.tamu.edu/resources/ocng_textbook/chapter16/chapter16_04.htm

Needs:
  * Scale ratio logic
  * Correct elev2stroke calculation

Removed parameters:
        elif self.wavetype == "NH Extreme":
            self.sig_height = 6.58
            self.sig_period = 10.5
            self.scale_ratio = 15.2
            self.gamma = 3.95
            self.sigma_A = 0.45
            self.sigma_B = 0.15
            self.P = 4.85
            
        elif self.wavetype == "NH Typical":
            self.sig_height = 1.21
            self.sig_period = 10.0
            self.sig_period2 = 5.34
            self.scale_ratio = 15.2
            self.gamma1 = 6.75
            self.gamma2 = 0.5
            self.P = 4.34

"""

import numpy as np
import matplotlib.pyplot as plt
from numpy import pi, sinh, cosh
from wavemakerlimits import dispsolver


# Define some constants
stroke_cal = 15.7130 # V/m stroke, used to be 7.8564, might need to be 18?
paddle_height = 3.3147
water_depth = 2.44
g = 9.81


def psd(t, data, window=None):
    """Computes one-sided power spectral density.
       Returns f, psd."""
    dt = t[1] - t[0]
    N = len(data)
    data = data - np.mean(data)
    if window == 'Hanning':
        data = data*np.hanning(N)
    f = np.fft.fftfreq(N, dt)
    y = np.fft.fft(data)
    f = f[0:N/2]
    psd = (2*dt/N)*abs(y)**2
    psd = np.real(psd[0:N/2])
    return f, psd


def spec2ts(spec, sr):
    """Create time series with random (normal) phases from power spectrum."""
    phase = np.random.normal(0, pi, len(spec))
    ts = np.fft.irfft(np.sqrt(spec*len(spec)*sr)*np.exp(1j*phase))
    return ts


def elev2stroke(ts_elev, waveheight, waveperiod):
    """Computes piston stroke from elevation time series.
    Still needs to be checked for random waves parameters."""
    k = dispsolver(2*pi/waveperiod, water_depth, decimals=2)
    kh = k*water_depth
    factor = paddle_height/water_depth
    stroke = 4*(sinh(kh)/kh)*(kh*sinh(kh)-cosh(kh)+1)/(sinh(2*kh)+2*kh)
    return ts_elev*factor/stroke
    

def stroke2volts(stroke):
    return stroke*stroke_cal
    

class Wave(object):
    """Object that mathematically represents a wave."""
    def __init__(self, wavetype):
        self.wavetype = wavetype
        self.sr = 1024.0
        self.buffsize = 65538
        self.sbuffsize = 1024
        
        if self.wavetype == "Regular":
            self.height = 0.1
            self.period = 1.0
        
        elif self.wavetype == "Bretschneider":
            self.sig_height = 0.1
            self.sig_period = 1.0
            self.scale_ratio = 1.0
            
        elif self.wavetype == "JONSWAP":
            self.sig_height = 0.1
            self.sig_period = 1.0
            self.scale_ratio = 1.0
            self.gamma = 3.3
            self.sigma_A = 0.07
            self.sigma_B = 0.09
            
        elif self.wavetype == "Pierson-Moskowitz":
            self.windspeed = 2.0
            self.scale_ratio = 1.0

            
    def gen_ts(self):
        if self.wavetype == "Regular":
            """Generate a regular wave time series"""
            self.sr = self.sbuffsize/self.period
            t = np.linspace(0, 2*pi, self.sbuffsize)
            self.ts_elev = self.height/2*np.sin(t)
            
        else:
            """Generate random wave time series"""
            nfreq = self.buffsize/2 
            f_start = self.sr/self.buffsize
            f_end = self.sr/2
            self.f = np.linspace(f_start, f_end, nfreq)
            omega = 2*pi*self.f
    
            if self.wavetype=="Bretschneider":
                sig_omega = 2*pi/self.sig_period
                sig_height = self.sig_height
                self.spec = 0.3125*sig_omega**4/omega**5*sig_height**2*\
                np.exp(-5.0*sig_omega**4/(4.0*omega**4))
                self.height = self.sig_height
                self.period = self.sig_period
                
            elif self.wavetype=="JONSWAP":
                """Compute a JONSWAP spectrum"""
                i_left = np.where(self.f <= 1.0/self.sig_period)[0]
                i_right = np.where(self.f > 1.0/self.sig_period)[0]
                sigma = np.zeros(len(self.f))
                sigma[i_left] = self.sigma_A
                sigma[i_right] = self.sigma_B
                alpha = 0.0624/(0.230 + 0.0336*self.gamma - \
                0.185*(1.9 + self.gamma)**(-1))
                A = np.exp((-((self.f*self.sig_period - 1.0)**2))/(2*sigma**2))
                B = -1.25*(self.sig_period*self.f)**(-4)
                self.spec = alpha*self.sig_height**2*self.sig_period**(-4)* \
                self.f**(-5)*np.exp(B)*self.gamma**A
                self.period = self.sig_period
                self.height = self.sig_height #Don't know about this...
            
            elif self.wavetype == "Pierson-Moskowitz":
                """Needs implementation of scale ratio, or not."""
                U = self.windspeed
                alpha = 8.1e-3
                f = self.f
                B = 0.74*(g/(2*pi*U))**4
                self.spec = alpha*g**2/((2*pi)**4*f**5)*np.exp(-B/f**4)
                self.height = 0.21*self.windspeed**2/g
                self.period = 2*pi*self.windspeed/(0.877*g)
                
            # Final step: compute time series    
            self.ts_elev = spec2ts(self.spec, self.sr)
            
            
    def gen_ts_stroke(self):
        """Needs algorithm for random waves"""
        self.gen_ts()
        self.ts_stroke = elev2stroke(self.ts_elev, self.height, self.period)
        
    def gen_ts_volts(self):
        self.gen_ts_stroke()
        self.ts_volts = stroke2volts(self.ts_stroke)
        
    def comp_spec(self):
        t = np.arange(len(self.ts_elev))/self.sr
        f, spec = psd(t, self.ts_elev, window=None)
        return f, spec
        

def ramp_ts(ts, direction):
    rampfull = np.ones(len(ts))
    ramp = np.hanning(len(ts))
    
    if direction == "up":
        rampfull[:len(ramp)/2] = ramp[:len(ramp)/2]
        
    elif direction == "down":
        rampfull[-len(ramp)/2:] = ramp[len(ramp)/2:]
        
    return ts*rampfull

    
if __name__ == "__main__":
#    wave = Wave("JONSWAP")
    wave = Wave("Bretschneider")
#    wave = Wave("Pierson-Moskowitz")
#    wave = Wave("NH Typical")
#    wave = Wave("NH Extreme")
#    wave = Wave("Regular")
#    wave.height = 0.3
    wave.gen_ts_volts()
    
    ts = wave.ts_elev
    t = np.arange(len(ts))/wave.sr
    
    f, s = wave.comp_spec()
    f2, s2 = wave.f, wave.spec
    
    plt.close("all")
    plt.plot(f, s)
    plt.hold(True)
    plt.plot(f2, s2)
    plt.xlim((0,5))
    plt.show()
    