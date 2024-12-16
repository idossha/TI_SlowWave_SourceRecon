
import numpy as np
import matplotlib.pyplot as plt

def get_wave_parameters(wave_number):
    """
    Prompt the user to input amplitude, frequency, and phase for a sine wave.

    Args:
        wave_number (int): The current wave number for reference.

    Returns:
        tuple: A tuple containing amplitude (float), frequency (float), phase (float in radians).
    """
    print(f"\nEnter parameters for Wave {wave_number}:")
    while True:
        try:
            amplitude = float(input("  Amplitude: "))
            frequency = float(input("  Frequency (Hz): "))
            phase_deg = float(input("  Phase (degrees): "))
            phase_rad = np.deg2rad(phase_deg)  # Convert degrees to radians
            return amplitude, frequency, phase_rad
        except ValueError:
            print("  Invalid input. Please enter numerical values.")

def main():
    print("=== Multiple Sine Waves Mixer ===")
    
    # Get number of waves
    while True:
        try:
            num_waves = int(input("Enter the number of sine waves to mix: "))
            if num_waves < 1:
                print("Please enter at least one wave.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    # Get parameters for each wave
    waves = []
    for i in range(1, num_waves + 1):
        amplitude, frequency, phase = get_wave_parameters(i)
        waves.append({'amplitude': amplitude, 'frequency': frequency, 'phase': phase})

    # Define time parameters
    duration = 1.0  # seconds
    sampling_rate = 1000  # Hz
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

    # Initialize mixed signal
    mixed_signal = np.zeros_like(t)

    # Plot setup
    plt.figure(figsize=(12, 6))
    
    # Generate and plot each wave
    for idx, wave in enumerate(waves, start=1):
        signal = wave['amplitude'] * np.sin(2 * np.pi * wave['frequency'] * t + wave['phase'])
        mixed_signal += signal
        plt.plot(t, signal, label=f"Wave {idx}: A={wave['amplitude']}, f={wave['frequency']}Hz, φ={np.rad2deg(wave['phase'])}°", alpha=0.5)

    # Plot mixed signal
    plt.plot(t, mixed_signal, label="Mixed Signal", color='black', linewidth=2)

    # Customize plot
    plt.title("Mixed Sine Waves")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
