#!/usr/bin/env python3

'''
TI waveform illustration for publication 

Ido Haber
July 2024

'''

import numpy as np
import matplotlib.pyplot as plt
import argparse

def generate_waveform(f1, f2, A1, A2, t_start, t_end, sampling_rate):
    t = np.linspace(t_start, t_end, int(sampling_rate * (t_end - t_start)))
    signal1 = A1 * np.sin(2 * np.pi * f1 * t)
    signal2 = A2 * np.sin(2 * np.pi * f2 * t)
    interference = signal1 + signal2
    
    return t, signal1, signal2, interference

def plot_waveform(t, signal1, signal2, interference, f1, f2, A1, A2, filename_base):
    plt.figure(figsize=(10, 6))
    
    plt.subplot(3, 1, 1)
    plt.plot(t, signal1, label=f'Signal 1: {f1} Hz, {A1} Amplitude')
    plt.legend(loc='upper right')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    
    plt.subplot(3, 1, 2)
    plt.plot(t, signal2, label=f'Signal 2: {f2} Hz, {A2} Amplitude', color='orange')
    plt.legend(loc='upper right')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    
    plt.subplot(3, 1, 3)
    plt.plot(t, interference, label='Interference Signal', color='blue')
    plt.legend(loc='upper right')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(f'{filename_base}.png')
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Generate and plot TI waveforms.')
    parser.add_argument('-f1', type=float, required=True, help='Frequency of first signal in Hz')
    parser.add_argument('-f2', type=float, required=True, help='Frequency of second signal in Hz')
    parser.add_argument('-t_end', type=float, default=2, help='End time in seconds (default: 2)')
    parser.add_argument('-sr', type=float, help='Sampling rate in Hz (default: 10 * f1)')

    args = parser.parse_args()
    
    f1 = args.f1
    f2 = args.f2
    t_end = args.t_end
    sampling_rate = args.sr if args.sr else 10 * f1
    A1 = 1
    A2 = 1
    t_start = 0

    t, signal1, signal2, interference = generate_waveform(f1, f2, A1, A2, t_start, t_end, sampling_rate)
    plot_waveform(t, signal1, signal2, interference, f1, f2, A1, A2, 'interference_waveform')

if __name__ == '__main__':
    main()
