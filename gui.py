from lib_installer import *

ensure_pip()
install_requirements_in_directory("C:/Apps/Audio_analyzer")

import customtkinter
from tkinter import filedialog
import os
import csv
import subprocess
import soundfile as sf
import pyloudnorm as loud
from pathlib import Path
from prettytable import PrettyTable, from_csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime



def center_app(app_window, app_width: int, app_height: int):
    """Centers the window to the main display/monitor"""
    screen_width = app_window.winfo_screenwidth()
    screen_height = app_window.winfo_screenheight()
    x = int((screen_width / 2) - (app_width / 2))
    y = int((screen_height / 2) - (app_height / 2))
    app_window.geometry(f"{app_width}x{app_height}+{x}+{y}")

# BACK

def integrated_lufs_pyloudnorm_2(file):
    try:
        # Load audio file
        audio, rate = sf.read(file)
        # Block size configuration
        default_block_size = 0.4  # Example: 0.4 seconds
        min_block_size = len(audio) / rate
        # Determine block size to use
        block_size_to_use = min(default_block_size, min_block_size)
        if min_block_size < default_block_size:
            print(f"Warning: {file.name} is too short. Using smaller block size.")

        meter = loud.Meter(rate, block_size=block_size_to_use)
        return round(meter.integrated_loudness(audio))
    except Exception as e:
        print(f"Error processing {file.name}: {e}")
        return None


def true_peak_ffmpeg(file_path):
    """Analyzes True Peak for .wav / .flac / .mp3 files"""
    command = [
        'ffmpeg', '-i', file_path, '-af', 'volumedetect', '-vn', '-sn', '-dn', '-f', 'null', '/dev/null'
    ]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    for line in result.stderr.split('\n'):
        # print(result)
        if 'max_volume' in line:
            peak_db = float(line.split('max_volume:')[-1].split('dB')[0].strip())
            return peak_db
    return None


def sample_rate_pyloudnorm(file_path):
    """Analyzes Sample Rate for .wac / .flac / .mp3 files"""
    data, rate = sf.read(file_path)
    return rate


def bit_depth_soundfile(file_path):
    """Analyzes Bit-Depth for .wac / .flac / .mp3 files"""
    with sf.SoundFile(file_path) as f:
        bit_depth = f.subtype
    return bit_depth


def channel_count_ffprobe(file_path):
    try:
        # Run ffprobe to get audio file info
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels', '-of',
             'default=noprint_wrappers=1:nokey=1', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # Get channel count from stdout
        channel_count = int(result.stdout.strip()) if result.stdout.strip() else None

        # Return "Mono", "Stereo", or the channel number based on the channel count
        if channel_count == 1:
            return "Mono"
        elif channel_count == 2:
            return "Stereo"
        elif channel_count is not None:
            return f"{channel_count}"
        else:
            return None  # If no channel count is found
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def wav_lister(path):
    """Returns a list of .wav files contained in path (including parent and child directories)"""
    # Use Path.glob to find all files in the specified directory
    wav_files = list(path.glob('**/*.wav'))
    wav_lister_amount = len(wav_files)
    return wav_lister_amount


def flac_lister(path):
    """Returns a list of .flac files contained in path (including parent and child directories)"""
    # Use Path.glob to find all files in the specified directory
    flac_files = list(path.glob('**/*.flac'))
    flac_lister_amount = len(flac_files)
    # print(f'{flac_amount} FLAC files')
    return flac_lister_amount


def mp3_lister(path):
    """Returns a list of .mp3 files contained in path (including parent and child directories)"""
    # Use Path.glob to find all files in the specified directory
    mp3_files = list(path.glob('**/*.mp3'))
    mp3_lister_amount = len(mp3_files)
    # print(f'{mp3_amount} MP3 files')
    return mp3_lister_amount


def analyze_audio_files(path, wav_switch_state, flac_switch_state, mp3_switch_state, include_lufs,
                        include_peak, include_samplerate, include_channels, include_bit_depth, include_path):
    """Analyze selected audio files in the given path and return their filename, integrated loudness (LUFS-I),
    true peak, sample rate, and channel count, based on checkbox states."""
    # Find all audio files in the specified directory
    wav_files = list(path.glob('*/*.wav')) if wav_switch_state else []
    mp3_files = list(path.glob('*/*.mp3')) if mp3_switch_state else []
    flac_files = list(path.glob('*/*.flac')) if flac_switch_state else []
    if wav_files:
        global wav_amount
        wav_amount = wav_lister(path)
    if mp3_files:
        global mp3_amount
        mp3_amount = mp3_lister(path)
    if flac_files:
        global flac_amount
        flac_amount = flac_lister(path)
    audio_files = wav_files + mp3_files + flac_files
    results = []

    # Total number of files to process
    total_files = len(audio_files)
    label_results.configure(text="In progress. Please wait...")
    update_interval = max(1, total_files // 100)

    for i, file in enumerate(audio_files):
        # Update the progress bar based on the current index and total number of files
        if i % update_interval == 0:
            progress_bar.set(i / total_files)
            window.update()  # Refresh the UI

        # Prepare the result row starting with the file name
        result_row = [file.name]

        # Add LUFS-I if the checkbox is checked
        if include_lufs:
            result_row.append(integrated_lufs_pyloudnorm_2(file))

        # Add True Peak if the checkbox is checked
        if include_peak:
            result_row.append(true_peak_ffmpeg(file))

        # Add Sample Rate if the checkbox is checked
        if include_samplerate:
            result_row.append(sample_rate_pyloudnorm(file))

        # Add Channel Count if the checkbox is checked
        if include_channels:
            result_row.append(channel_count_ffprobe(file))

        # Add bit_depth to results
        if include_bit_depth:
            result_row.append(bit_depth_soundfile(file))

        # Add Path if checked
        if include_path:
            result_row.append(path / file)

        # Append the result row to the final results
        results.append(tuple(result_row))

    # Set progress bar to complete when done
    progress_bar.set(1.0)
    window.update()  # Final UI refresh

    return results



def analyze_audio_files_2(path, wav_switch_state, flac_switch_state, mp3_switch_state, include_lufs,
                          include_peak, include_samplerate, include_channels, include_bit_depth, include_path):
    wav_files = list(path.glob('**/*.wav')) if wav_switch_state else []
    mp3_files = list(path.glob('**/*.mp3')) if mp3_switch_state else []
    flac_files = list(path.glob('**/*.flac')) if flac_switch_state else []

    audio_files = wav_files + mp3_files + flac_files
    results = []

    total_files = len(audio_files)
    label_results.configure(text="In progress. Please wait...")

    def update_progress(it):
        progress_bar.set(it / total_files)
        window.update()

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_file, file, include_lufs, include_peak, include_samplerate,
                                   include_channels, include_bit_depth, include_path, path): file for file in audio_files}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result is not None:
                results.append(result)

            if i % max(1, total_files // 100) == 0:
                update_progress(i)

    progress_bar.set(1.0)
    window.update()

    return results


def process_file(file, include_lufs, include_peak, include_samplerate,
                 include_channels, include_bit_depth, include_path, path):
    result_row = [file.name]

    if include_lufs:
        result_row.append(integrated_lufs_pyloudnorm_2(file))

    if include_peak:
        result_row.append(true_peak_ffmpeg(file))

    if include_samplerate:
        result_row.append(sample_rate_pyloudnorm(file))

    if include_channels:
        result_row.append(channel_count_ffprobe(file))

    if include_bit_depth:
        result_row.append(bit_depth_soundfile(file))

    if include_path:
        result_row.append(path / file)

    return tuple(result_row)


# FRONT
def uncheck_boxes_if_switches():
    if switch_wav.get() == 0 and switch_flac.get() == 0 and switch_mp3.get() == 0:
        checkbox_LUFS.configure(state="disabled")
        checkbox_LUFS.deselect()
        checkbox_peak.configure(state="disabled")
        checkbox_peak.deselect()
        checkbox_sampleR.configure(state="disabled")
        checkbox_sampleR.deselect()
        checkbox_channels.configure(state="disabled")
        checkbox_channels.deselect()
        checkbox_bit_depth.configure(state="disabled")
        checkbox_bit_depth.deselect()
        checkbox_path.configure(state="disabled")
        checkbox_path.deselect()
    else:
        checkbox_LUFS.configure(state="normal")
        checkbox_LUFS.select()
        checkbox_peak.configure(state="normal")
        checkbox_peak.select()
        checkbox_sampleR.configure(state="normal")
        checkbox_sampleR.select()
        checkbox_channels.configure(state="normal")
        checkbox_channels.select()
        checkbox_bit_depth.configure(state="normal")
        checkbox_bit_depth.select()
        checkbox_path.configure(state="normal")
        checkbox_path.select()


def check_entry(*args):
    if entry_path.get().strip():
        if switch_wav.get() == 0 and switch_mp3.get() == 0:
            button_start.configure(state="disable", )
        else:
            button_start.configure(state="normal", text_color=enabled_text_color)


def button_export_csv_file_to_entry_path():
    export_dir = Path(entry_path.get().strip('"'))
    analysis_results = scroll_results.get("1.0", "end")
    convert_prettytable_to_csv_2(analysis_results, os.path.basename(export_dir), export_dir)


def button_browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        var_directory_path.set(directory)
        entry_path.configure(textvariable=var_directory_path)  # Set text variable
        button_start.configure(state="normal")
        label_results.configure(text='Directory selected, click "Start" to begin...')
    else:
        label_results.configure(text="No directory selected, previous path retained.")


def display_analysis_results(textbox, audio_file_analysis, include_lufs, include_peak,
                             include_samplerate, include_channels, include_bit_depth, include_path):
    """Format the analysis results and display them in a CustomTkinter textbox."""

    # Clear the textbox first if needed
    textbox.delete("1.0", "end")  # Clears previous content

    # Loop over the results and format each one
    formatted_results = []

    # Create the header before processing file_data
    header = ["Filename"]
    if include_lufs:
        header.append("LUFS-I")
    if include_peak:
        header.append("T-Peak")
    if include_samplerate:
        header.append("Rate")
    if include_channels:
        header.append("CH")
    if include_bit_depth:
        header.append("Depth")
    if include_path:
        header.append("Path")

    headers = ",".join(str(header_name) for header_name in header)
    formatted_results.append(headers)

    for file_data in audio_file_analysis:
        # Extract filename and join the rest of the values into a comma-separated string
        filename = file_data[0]
        values = ",".join(str(value) for value in file_data[1:])  # Convert the values to string
        formatted_result = f"{filename},{values}"
        formatted_results.append(formatted_result)

    # Join all the formatted lines into a single string with newline separators
    results_string = "\n".join(formatted_results)

    global results_to_export
    results_to_export = results_string

    # Raw data as a single string
    data = results_string
    # Split the data into rows
    rows = data.split('\n')

    # Extract headers
    headers = rows[0].split(',')

    # Initialize PrettyTable with headers
    table = PrettyTable(headers)
    # table.set_style(PLAIN_COLUMNS)
    table.preserve_internal_border = True

    # table.padding_width = 1  # Set padding width to 2 spaces

    # Add the rest of the rows to the table
    for row in rows[1:]:
        table.add_row(row.split(','))
    # table.max_width["Path"] = 100  # You can adjust this value

    # Align other columns if needed (e.g., right-align numbers)

    table.align["Filename"] = "l"
    table.align["LUFS-I"] = "c"
    table.align["T-Peak"] = "c"
    table.align["Rate"] = "c"
    table.align["CH"] = "c"
    table.align["Depth"] = "c"
    table.align["Path"] = "l"
    table.padding_width = 1
    # print(table)

    # Insert the results into the textbox
    textbox.insert("0.0", table)
    button_export_data.configure(state="normal")


def convert_prettytable_to_csv_2(table_str, dir_name, output_directory):
    """Converts a PrettyTable string to a CSV file with a custom filename."""

    # Process the string
    lines = table_str.strip().split('\n')
    headers = [h.strip() for h in lines[1].split('|')[1:-1]]
    rows = []

    for line in lines[3:-1]:
        row = [field.strip() for field in line.split('|')[1:-1]]
        rows.append(row)

    # Get current date and time
    date_time = datetime.now().strftime("%Y_%h%m_%H_%M")

    # Get the OS user
    user = os.getlogin()

    # Create the output filename
    output_filename = f"{user}_results__{dir_name}_{date_time}.csv"
    output_path = os.path.join(output_directory, output_filename)

    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        print("CSV file exported successfully")
    except Exception as e:
        print(f"Error writing to file: {e}")


def button_start_analysis(event=None):
    global wav_amount, flac_amount, mp3_amount
    wav_amount = 0
    flac_amount = 0
    mp3_amount = 0

    # Get the directory path from the entry field
    directory_path = entry_path.get().strip()
    # Handle cases where the path might be quoted
    if directory_path.startswith('"') and directory_path.endswith('"'):
        directory_path = directory_path[1:-1]
    # Create a Path object
    path = Path(directory_path)

    # Ensure a file type is selected
    if switch_wav.get() == 0 and switch_mp3.get() == 0 and switch_flac.get() == 0:
        button_start.configure(state="disable", text_color=enabled_text_color)
        label_results.configure(text="You must select a file type first!", corner_radius=10)
        return
    else:
        button_start.configure(state="normal", text_color=enabled_text_color)

    # Check if the path is a valid directory
    if path.is_dir():
        # Get the state of the switches
        include_wav = switch_wav.get() == 1
        include_mp3 = switch_mp3.get() == 1
        include_flac = switch_flac.get() == 1

        # Get the state of the checkboxes (Lufs, True Peak, Sample Rate, Channels)
        lufs_state = checkbox_LUFS.get()
        peak_state = checkbox_peak.get()
        samplerate_state = checkbox_sampleR.get()
        channels_state = checkbox_channels.get()
        bit_depth_state = checkbox_bit_depth.get()
        path_state = checkbox_path.get()

        # Run the analysis function with the provided states
        final_analysis = analyze_audio_files_2(
            path,
            wav_switch_state=include_wav,
            flac_switch_state=include_flac,
            mp3_switch_state=include_mp3,
            include_lufs=lufs_state,
            include_peak=peak_state,
            include_samplerate=samplerate_state,
            include_channels=channels_state,
            include_bit_depth=bit_depth_state,
            include_path=path_state,

        )

        # Extract filename and results for further processing or saving
        filename_list = [file_data[0] for file_data in final_analysis]

        if not filename_list:  # Efficiently check if the list is empty
            scroll_results.configure(state="normal", wrap="none")
            scroll_results.delete("1.0", "end")
            scroll_results.configure(state="disable")
            label_results.configure(text="No such files to analyze")
            return

        # Handling dynamic columns depending on the checkbox states
        results_columns = []
        # Collect results for each file
        for file_data in final_analysis:
            result_row = [file_data[0]]  # Start with the filename
            column_index = 1  # Start at index 1 because index 0 is the filename

            if lufs_state:
                result_row.append(file_data[column_index])
                column_index += 1
            if peak_state and (file_data[0].endswith('.wav') or file_data[0].endswith('.flac')):
                result_row.append(file_data[column_index])
                column_index += 1
            if samplerate_state:
                result_row.append(file_data[column_index])
                column_index += 1
            if channels_state:
                result_row.append(file_data[column_index])
                column_index += 1
            if bit_depth_state:
                result_row.append(file_data[column_index])
            if path_state:
                result_row.append(file_data[column_index])

            results_columns.append(result_row)
        # Update the GUI: show success message and hide the progress bar
        label_results.configure(text="Analysis Completed.")
        scroll_results.configure(state="normal", wrap="none")
        display_analysis_results(scroll_results, final_analysis,
                                 include_lufs=lufs_state,
                                 include_peak=peak_state,
                                 include_samplerate=samplerate_state,
                                 include_channels=channels_state,
                                 include_bit_depth=bit_depth_state,
                                 include_path=path_state, )
        scroll_results.configure(state="disable")

    else:
        # Update the GUI with an error message if the directory is invalid
        entry_path.delete(0, customtkinter.END)
        entry_path.insert(0, var_directory_path.get())
        entry_path.configure(textvariable=var_directory_path)
        label_results.configure(text="Invalid directory. Please try again.")


# GLOBAL

results_to_export = ""
wav_amount = 0
flac_amount = 0
mp3_amount = 0

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("dark-blue")
customtkinter.deactivate_automatic_dpi_awareness()
window = customtkinter.CTk()
window.resizable(width=False, height=False)
window.geometry("1300x390")  # "797x390"
window.title("Audio Data Analyzer - by @roldyaudio")

enabled_text_color = "white"  # Example: blue color when enabled
disabled_text_color = "#a3a3a3"  # Example: gray color when disabled
var_entry = customtkinter.StringVar()
var_entry.trace("w", check_entry)
var_directory_path = customtkinter.StringVar()

colors = ["#011f4b", "#03396c", "#005b96", "#6497b1", "#b3cde0", "#001f24"]

frame_main = customtkinter.CTkFrame(master=window, fg_color="black", corner_radius=10)  # Color transversal
frame_main.pack(expand=True, fill="both", padx=5, pady=5)
frame_main.columnconfigure((0, 1), weight=0)
frame_main.rowconfigure((0, 4), weight=0)

# Top left frame ------------------------------------------------------------------------------------------------------

frame_switches = customtkinter.CTkFrame(master=frame_main, corner_radius=10)
frame_switches.grid(row=0, column=0, padx=5, pady=5, rowspan=2)
frame_switches.columnconfigure((0, 1), weight=0)
frame_switches.rowconfigure((0, 3), weight=0)

# Label
label_filetype = customtkinter.CTkLabel(master=frame_switches, text="Select file type to analyse:", )
label_filetype.grid(row=0, column=0, columnspan=2, ipadx=10)

# Switch theme
progress_color = colors[1]
switch_color = colors[0]
switch_hover = "#03396c"

# Switches
switch_wav = customtkinter.CTkSwitch(master=frame_switches, text=".wav", progress_color=progress_color,
                                     button_color=switch_color, button_hover_color=switch_hover,
                                     command=uncheck_boxes_if_switches)
switch_wav.grid(row=1, column=0, columnspan=2, ipady=3)
switch_wav.select()
switch_mp3 = customtkinter.CTkSwitch(master=frame_switches, text=".mp3", corner_radius=10, progress_color=progress_color,
                                     button_color=switch_color, button_hover_color=switch_hover,
                                     command=uncheck_boxes_if_switches)
switch_mp3.grid(row=3, column=0, columnspan=2, ipady=3)
switch_flac = customtkinter.CTkSwitch(master=frame_switches, text=".flac", corner_radius=10,
                                      progress_color=progress_color,
                                      button_color=switch_color, button_hover_color=switch_hover,
                                      command=uncheck_boxes_if_switches)
switch_flac.grid(row=2, column=0, columnspan=2, ipady=3)

# Bottom left frame --------------------------------------------------------------------------------------------------

frame_checkbox = customtkinter.CTkFrame(master=frame_main, corner_radius=10)
frame_checkbox.grid(row=2, column=0, rowspan=4, padx=5, ipady=5)
frame_checkbox.columnconfigure((0, 0), weight=0)
frame_checkbox.rowconfigure((0, 6), weight=0)
# Label
label_info = customtkinter.CTkLabel(master=frame_checkbox, text="Check data to include:")
label_info.grid(row=0, column=0, padx=22, pady=1, ipady=1, )
label_fill = customtkinter.CTkLabel(master=frame_checkbox, text="")

# Checkboxes theme
checkmark_color = "white"
checkbox_fg_color = colors[1]
checkbox_hover_color = colors[5]
checkbox_border_width = 2
checkbox_border_color = "black"

# Checkboxes
separation = 5
x_pos = 1
checkbox_LUFS = customtkinter.CTkCheckBox(master=frame_checkbox, text="LUFS-I", fg_color=checkbox_fg_color,
                                          hover_color=checkbox_hover_color, checkmark_color=checkmark_color,
                                          border_width=checkbox_border_width,
                                          border_color=checkbox_border_color, state="normal", )
checkbox_LUFS.grid(row=1, column=0, pady=separation, ipadx=x_pos)
checkbox_LUFS.select()
checkbox_peak = customtkinter.CTkCheckBox(master=frame_checkbox, text="True Peak", fg_color=checkbox_fg_color,
                                          hover_color=checkbox_hover_color, checkmark_color=checkmark_color,
                                          border_width=checkbox_border_width,
                                          border_color=checkbox_border_color, state="normal", )
checkbox_peak.grid(row=2, column=0, pady=separation, ipadx=x_pos)
checkbox_peak.select()

checkbox_sampleR = customtkinter.CTkCheckBox(master=frame_checkbox, text="Sample rate", fg_color=checkbox_fg_color,
                                             hover_color=checkbox_hover_color, checkmark_color=checkmark_color,
                                             border_width=checkbox_border_width,
                                             border_color=checkbox_border_color, state="normal", )
checkbox_sampleR.grid(row=3, column=0, pady=separation, ipadx=x_pos)
checkbox_sampleR.select()
checkbox_channels = customtkinter.CTkCheckBox(master=frame_checkbox, text="Channels", fg_color=checkbox_fg_color,
                                              hover_color=checkbox_hover_color, checkmark_color=checkmark_color,
                                              border_width=checkbox_border_width,
                                              border_color=checkbox_border_color, state="normal", )
checkbox_channels.grid(row=5, column=0, pady=separation, ipadx=x_pos)
checkbox_channels.select()
checkbox_bit_depth = customtkinter.CTkCheckBox(master=frame_checkbox, text="Bit Depth", fg_color=checkbox_fg_color,
                                               hover_color=checkbox_hover_color, checkmark_color=checkmark_color,
                                               border_width=checkbox_border_width,
                                               border_color=checkbox_border_color, state="normal", )
checkbox_bit_depth.grid(row=4, column=0, pady=separation, ipadx=x_pos)
checkbox_bit_depth.select()
checkbox_path = customtkinter.CTkCheckBox(master=frame_checkbox, text="Path", fg_color=checkbox_fg_color,
                                          hover_color=checkbox_hover_color, checkmark_color=checkmark_color,
                                          border_width=checkbox_border_width,
                                          border_color=checkbox_border_color, state="normal", )
checkbox_path.grid(row=6, column=0, pady=separation, ipadx=x_pos)
checkbox_path.select()

# Top right frame -----------------------------------------------------------------------------------------------------

frame_results = customtkinter.CTkFrame(master=frame_main, corner_radius=10)
frame_results.grid(row=0, column=1, rowspan=4, padx=1, pady=5, sticky="nsew", )
frame_results.columnconfigure((0, 0), weight=0)
frame_results.rowconfigure((0, 0), weight=0)
scroll_results = customtkinter.CTkTextbox(master=frame_results, state="normal", wrap="none", width=1105, height=240,
                                          font=("Lucida Console", 13), )
scroll_results.grid(row=0, column=1, rowspan=4)
scroll_results.configure(state="normal", wrap="word")
scroll_results.insert("0.0", """
Measures in accordance with the ITU-R BS.1770 recommendation.

- Enter path or browse for directory containing audio files.
- Select the desire file type to analyse.
- Check the data you want to include in the analysis.
- Visualize the data.
- Export to input path if needed.

Enjoy ^^ """)
scroll_results.configure(state="disable", )

# Buttons theme
width = 120
height = 25
corner_radius = 10
border_width = 1
border_color = "gray"
hover_color = colors[1]
fg_color = colors[0]
text_color = "black"

# Bottom right frame --------------------------------------------------------------------------------------------------
frame_buttons = customtkinter.CTkFrame(master=frame_main, corner_radius=10)
frame_buttons.grid(row=4, column=1, rowspan=2, padx=1, sticky="nsew")
frame_buttons.rowconfigure((0, 2), weight=1)
frame_buttons.columnconfigure((0, 2), weight=1)

# Buttons
button_start = customtkinter.CTkButton(master=frame_buttons, text="Start", width=width, height=height,
                                       corner_radius=corner_radius, border_width=border_width,
                                       border_color=border_color, hover_color=hover_color, fg_color=fg_color,
                                       state="disabled", command=button_start_analysis)
button_start.grid(row=0, column=4, )
button_export_data = customtkinter.CTkButton(master=frame_buttons, text="Export to file", width=width, height=height,
                                             corner_radius=corner_radius, border_width=border_width,
                                             border_color=border_color, hover_color=hover_color, fg_color=fg_color,
                                             state="disabled", command=button_export_csv_file_to_entry_path)
button_export_data.grid(row=2, column=4, padx=15)
button_browse = customtkinter.CTkButton(master=frame_buttons, text="Browse", width=width, height=height,
                                        corner_radius=corner_radius, border_width=border_width,
                                        border_color=border_color, hover_color=hover_color, fg_color=fg_color,
                                        command=button_browse_directory)
button_browse.grid(row=0, column=0, sticky="w", padx=15)

# Entry
entry_path = customtkinter.CTkEntry(master=frame_buttons, width=800,
                                    placeholder_text="Enter directory with files here...", textvariable=var_entry)
entry_path.grid(row=0, column=1, ipadx=1)
entry_path.bind("<Return>", button_start_analysis)

# Label results
label_results = customtkinter.CTkLabel(master=frame_buttons, text="", wraplength=750, )
label_results.grid(row=1, column=0, sticky="w", ipadx=30, columnspan=3,)

# Progress bar
progress_bar = customtkinter.CTkProgressBar(master=frame_buttons, progress_color=colors[1], border_width=1,
                                            fg_color="black", width=800)
progress_bar.grid(row=2, column=0, columnspan=2, padx=10)
progress_bar.set(0)

center_app(window, 1300, 390)
window.mainloop()
