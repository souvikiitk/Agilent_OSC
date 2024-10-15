import serial

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

import csv

port = 'COM4'
baudrate = 9600
timeout = 10

def connect_serial_port():
    try:
        # TODO Try a timeout here
        ser = serial.Serial(port, baudrate, xonxoff=True, timeout = timeout)
        #ser.write(b':AUT\n')
        #ser.flush()
        print(f"Connected to {ser.port}.")
        return ser
    
    except serial.SerialException as e:
        print(f"Error opening Port: {e}")
        return None

def calculate_and_plot_fft(data_points, scope_x_increment):
    
    # Calculate FFT
    N = len(data_points)
    fft_result = np.fft.fft(data_points)
    fft_freq = np.fft.fftfreq(N, d=scope_x_increment)  # Frequency axis
    fft_magnitude = np.abs(fft_result)  # Magnitude of the FFT

    # Plot the frequency-domain representation
    plt.figure(figsize=(14.43, 9.84))  # Width, Height in inches
    plt.plot(fft_freq[:N // 2], fft_magnitude[:N // 2])  # Plot positive frequencies
    plt.title("FFT of the Waveform")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.grid()
    plt.tight_layout()
    plt.show()

    # TODO 1. Make the plot better, 2. Mark the frequency peaks

def export_data_to_csv(data_points, filename):

    # Export the data points to a CSV file.
    # TODO Make the exported data take the seconds and the Voltage instead of index
    with open(filename, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Index', 'Voltage (V)'])  # Header row
        for index, voltage in enumerate(data_points):
            writer.writerow([index, voltage])  # Write each data point

def main():
    ser = None
    try:
        # Attempt to connect to the serial port
        ser = connect_serial_port()
        if ser is None:
            return

        # Write *IDN? command to identify the device
        ser.write(b'*IDN?\n')
        ser.flush()
        print(ser.readline().decode(errors="ignore").strip())  # Ignore decoding errors

        # Set data to be formatted as signed WORDs (16 bits, so -32,768 through 32,767)
        ser.write(b':WAVEform:FORMat \n')
        ser.write(b':WAVeform:BYTeorder MSBFirst\n')
        ser.write(b':WAVeform:UNSigned 0\n')
        
        
        # Set channel 1 for waveform examination
        ser.write(b':WAVeform:SOURce CHANnel1\n')
        #ser.write(b'WAV:SOUR CHAN2\n')

        ser.write(b':WAVeform:TYPE?\n')
        ser.flush()
        scope_read_type = ser.readline().decode().strip()

        # TODO write comments for all of these basic commands
        ser.write(b':WAVeform:XINCrement?\n')
        ser.flush()
        scope_x_increment = float(ser.readline())

        ser.write(b':WAVeform:XORigin?\n')
        ser.flush()
        scope_x_origin = float(ser.readline())

        ser.write(b':WAVeform:XREFerence?\n')
        ser.flush()
        scope_x_reference = float(ser.readline())

        ser.write(b':WAVeform:YINCrement?\n')
        ser.flush()
        scope_y_increment = float(ser.readline())

        ser.write(b':WAVeform:YORigin?\n')
        ser.flush()
        scope_y_origin = float(ser.readline())

        ser.write(b':WAVeform:YREFerence?\n')
        ser.flush()
        scope_y_reference = float(ser.readline())
        
        ser.write(b':WAV:POIN 2000\n')
        ser.flush()
        ser.write(b':WAV:POIN?\n')
        ser.flush()
        print(ser.readline())

        print("Oscilloscope mode:", scope_read_type)
        print("X increment (S):", scope_x_increment)
        print("X reference (S):", scope_x_reference)
        print("X origin (S):", scope_x_origin)
        print("Y increment (V):", scope_y_increment)
        print("Y reference (V):", scope_y_reference)
        print("Y origin (V):", scope_y_origin)
        
        # Request waveform data
        ser.write(b':WAVeform:DATA?\n')
        ser.flush()
        scope_data_bytes = ser.readline() # TODO Check if readlines works better than readline
        # Preamble length is found in the 2nd character and actual data follows
        scope_data_preamble_len = int(scope_data_bytes[1] - 48)
        print(scope_data_preamble_len)
        scope_data_len = int(scope_data_bytes[2:2 + scope_data_preamble_len])

        data_points = []
        for i in range(0, scope_data_len, 2):
            data_offset = i + scope_data_preamble_len + 2
            data_point = int.from_bytes(scope_data_bytes[data_offset:data_offset + 2], byteorder='big', signed=True)

            # Voltage calculation formula
            data_point_voltage = ((data_point - scope_y_reference) * scope_y_increment) + scope_y_origin
            data_points.append(data_point_voltage)

        print("Min (V):", min(data_points))
        print("Max (V):", max(data_points))

        # Calculate time axis (X-axis)
        data_points_times = []
        for i in range(len(data_points)):
            # Formula for time: [(data point number - xreference) * xincrement] + xorigin
            data_point_time = ((i - scope_x_reference) * scope_x_increment) + scope_x_origin
            data_points_times.append(data_point_time)

        # Plot the time-domain waveform
        # TODO Make the plot better, mark one of the maximums with its datapoint
        
        plt.figure(figsize=(14, 7))  # Width, Height in inches
        plt.subplot(2, 1, 1)  # Create a subplot for the time-domain signal
        plt.plot(data_points_times, data_points)
        plt.title(f"Oscilloscope capture (mode: {scope_read_type})")
        plt.xlabel("Time (S)")
        plt.ylabel("Voltage (V)")
        plt.grid()
        plt.tight_layout()

        # Call the FFT function to calculate and plot the FFT
        calculate_and_plot_fft(data_points, scope_x_increment)
        print(len(data_points))
        # Export data points to a CSV file
        
        export_data_to_csv(data_points, 'oscilloscope_data.csv')
        print("Data points exported to 'oscilloscope_data.csv'.")
        
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure the serial port is closed after use
        if ser is not None and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
