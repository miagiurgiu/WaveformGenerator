import numpy as np # numpy performs numerical and audio calculations (handles arrays, RMS calculations, sine waves, interpolation)
import subprocess # allows python to run ffmpeg
from PIL import Image,ImageDraw # allows access to pillow (image - creates, resizes images; imagedraw - draws lines onto images)
from pathlib import Path # access to filesystem paths

# configuration constants
STRAND_COUNT = 11 # waveform composed of 11 individual strands
STRAND_SHIFT = 14 # horizontal distance between strands
STRAND_SEPARATION = 0.018 # vertical distance between strands

SAMPLE_RATE = 24_000 # ffmpeg converts audio to 24000 samples/second
FPS=30 # output video has 30 frames/second

# full hd dimensions (pillow draws at 5760 × 3240 -> reduce to 1920 × 1080)
WIDTH = 1_920
HEIGHT = 1_080

# shorts dimensions
SHORTS_WIDTH = 1_080
SHORTS_HEIGHT = 1_920

SUPERSAMPLE = 3 # waveform drawn 3x final resolution
WAVEFORM_COLOR = "#C8A96A" # default waveform color (C8=RED,A9=green,6A=blue)

def decode_audio(file_path):
    '''
    asks FFmpeg to convert input audio into raw numbers
    :param file_path: audio file's location
    :return: NumPy array containing audio samples for the whole song
    '''
    command=["ffmpeg", # external program
             "-v","error", # print only errors
             "-i",str(file_path), # introduce input file, convert Path object to String
             "-vn", # no video (if you select video, only audio will be selected)
             "-ac", "1", # convert audio to mono (does it reduce quality if recording is stereo?)
             "-ar", str(SAMPLE_RATE), # set audio sample to the given one (24000)
             "-f", "f32le", # f32=32-bit floating point numbers; le=little endian byte order
             "pipe:1", # send raw audio through stdout pipe instead of creating an audio file
    ]
    result = subprocess.run(command, check=True, capture_output=True) # run ffmpeg
    audio_samples=np.frombuffer(result.stdout,dtype="<f4") # convert ffmpeg binary output to numpy array
    return audio_samples # ex: [0.00001,-0.00015,...] = pcm audio samples

def analyse_basic_audio(samples):
    '''
    calculates general info about the whole audio file
    rms describes signal's overall energy better than one peak
    :param samples:
    :return: tuple (5 values)
    '''
    duration_seconds = len(samples) / SAMPLE_RATE # samples/samples_per_second=seconds
    peak_amplitude = np.max(np.abs(samples)) # remove negative signs -> find largest magnitude
    rms_amplitude = np.sqrt(np.mean(samples ** 2)) # root mean square (square every sample -> calculate average -> sqrt)
    # convert linear amplitudes into dbfs (decibels relative to full scale, 0 dBFS is max)
    peak_dbfs = 20 * np.log10(peak_amplitude)
    rms_dbfs = 20 * np.log10(rms_amplitude)
    return duration_seconds,peak_amplitude,rms_amplitude,peak_dbfs,rms_dbfs

def calculate_frame_loudness(samples):
    '''
    calculates how loud should each video frame be
    divides the audio according to frames
    calculates one RMS per frame
    each video frame corresponds to 800 audio samples
    :param samples: numpy array
    :return: an array of rms
    '''

    samples_per_frame = SAMPLE_RATE // FPS # 24000//30=800 samples (integer division)
    number_of_frames = int(np.ceil(len(samples) / samples_per_frame)) # how many frames are needed (np.ceil() so that the last segment is not discarded)
    frame_loudness = np.zeros(number_of_frames,dtype=np.float32) # create array filled with 0 (one position for every frame)

    for frame_index in range(number_of_frames): # traverse the frames (0...)
        start = frame_index * samples_per_frame # where the current audio segment starts (ex: frame 2 => 2*800 = sample 1600)
        end = min(start + samples_per_frame,len(samples)) # where the segment ends (min prevents from surpassing the audio array)
        frame_samples = samples[start:end] # extracts part of the numpy array (ex: samples[800:1600] => frame 2)
        rms = np.sqrt(np.mean(frame_samples ** 2)) # calculates rms for this frame
        frame_loudness[frame_index] = rms # store rms in correct position

    return frame_loudness # array

def smooth_loudness(frame_loudness):
    '''
    prevent sudden movement
    :param frame_loudness:
    :return: smoothed value
    '''

    attack_factor = 0.38 # how quickly it grows when sound becomes louder
    release_factor = 0.075 # how slowly it falls after sound becomes quieter
    smoothed_loudness = np.zeros_like(frame_loudness) # array filled with zeroes (with the same shape and data type as frame_loudness array)
    current_value = 0.0 # begin at silence

    for frame_index in range(len(frame_loudness)): # traverse every loudness measurement
        target_value = frame_loudness[frame_index] # get raw loudness the waveform is tryna reach
        if target_value > current_value: # if audio becomes louder, use faster attack
            smoothing_factor = attack_factor
        else: # if quieter, use slower release
            smoothing_factor = release_factor
        difference = target_value - current_value # distance between current value and desired value
        current_value = current_value+ difference * smoothing_factor # move towards target
        smoothed_loudness[frame_index] = current_value # store smoothed value

    return smoothed_loudness

def normalize_loudness(smoothed_loudness):
    '''
    - step 1: compare with a representative loud level
    - step 2: limit values to 0-1
    - step 3: remove background noise from visuals
    - step 4: make quiet sounds more visible
    - step 5: return animation activity
    convert loudness into activity values between 0 and 1
    :param smoothed_loudness: array containing one smoothed loudness value for every frame
    :return: activity=waveform intensity for every frame; reference level=the 95th percentile loudness used for normalisation
    '''
    reference_level = np.percentile(smoothed_loudness,95) # about 95% of the frames ar quieter than this value (prevents one loud peak from controlling the animation)
    normalized_loudness = smoothed_loudness / reference_level # loudness value / reference level
    normalized_loudness = np.clip(normalized_loudness,0.0,1.0) # restrict every value to the interval 0.0-1.0
    silence_threshold = 0.02 # activity below 2% is treated as silence/background noise
    activity = (normalized_loudness - silence_threshold) / (1.0 - silence_threshold) # 0.02 is 0.0 and 1.00 is 1.0
    activity = np.clip(activity,0.0,1.0) # remove negative values and keep activity within 0.0-1.0
    activity = activity ** 0.68 # make quiet sounds more visually noticeable (0.25->0.39)
    return activity, reference_level

def hex_to_rgba(hex_color, alpha=185):
    '''

    :param hex_color: such as #C8A96A
    :param alpha: transparency: default 185 (range: 0-255)
    :return:  RGBA tuple
    '''
    clean_color = hex_color.lstrip("#") # remove '#' from the beginning
    red = int(clean_color[0:2], 16) # take first 2 characters at indexes 0 and 1 (C8) -> convert from base 16 to base 10
    green = int(clean_color[2:4], 16) # take characters at indexes 2 and 3 (A9) -> convert ...
    blue = int(clean_color[4:6], 16)
    return red, green, blue, alpha # (alpha=transparency)

def create_waveform_frame(activity_value,frame_index,canvas_width=WIDTH,canvas_height=HEIGHT):
    '''
    # draw one transparent image (0.0 activity =flat, 1.0 activity =full height)
    :param activity_value: audio intensity between 0.0 and 1.0
    :param frame_index: current frame index
    :param canvas_width: output width
    :param canvas_height: output height
    :return:
    '''
    strand_color = hex_to_rgba(WAVEFORM_COLOR) # convert hex into rgba tuple for Pillow
    large_width = canvas_width * SUPERSAMPLE # larger temporary canvas (for smoother lines)
    large_height = canvas_height * SUPERSAMPLE
    image = Image.new("RGBA",(large_width, large_height),(0, 0, 0, 0)) # create empty pillow image

    drawing = ImageDraw.Draw(image) # create object used to draw lines onto image
    scale = canvas_width / WIDTH # calculate size ratio between selected canvas and normal landscape
    number_of_points = 600 # each strand will contain 600 connected points (more points => smoother curve, but more processing)

    horizontal_positions = np.linspace( -1.0,1.0,number_of_points) # create 600 evenly spaced mathematical positions between -1.0 and 1.0
    horizontal_margin = 100 * scale # calculate empty space at left and right edges
    pixel_positions = np.linspace(horizontal_margin,canvas_width - horizontal_margin,number_of_points) # create 600 horizontal pixel positions

    time_seconds = frame_index / FPS # convert current frame number into seconds
    phase = time_seconds * 0.34 # control wave's movement over time (0.34 speed)

    sine_wave = np.sin(2 * np.pi * (2.15 * horizontal_positions + phase)) # creates main curved shape

    taper = np.sin( np.linspace( 0.0, np.pi, number_of_points)) ** 2.5 # make waveform flat at both edges; 2.5 makes waveform more concentrated around the centre (higher exponent => narrower middle section)

    wave_shape = sine_wave * taper # combine sine with taper

    maximum_height = HEIGHT * 0.25 * scale # largest possible height the waveform can reach (h*0.25 means 25% of the normal video height)

    strand_offsets = np.linspace(-1.0, 1.0,STRAND_COUNT) # create offset value for each strand

    for strand_offset in strand_offsets: # draw every strand separately
        # calculate horizontal displacement of the current strand
        horizontal_shift = int(
            strand_offset
            * STRAND_SHIFT
            * scale
            * activity_value
        )

        # move wave values horizontally
        shifted_wave = np.roll(
            wave_shape,
            horizontal_shift
        )

        # calculate vertical distance between strands
        strand_separation = (
                strand_offset
                * HEIGHT
                * STRAND_SEPARATION
                * scale
                * activity_value
                * taper
        )

        # start every strand at the vertical centre of the canvas
        vertical_positions = (
            canvas_height / 2
            + shifted_wave
            * maximum_height
            * activity_value
            + strand_separation
        )

        points = [] # empty list for the strand's coordinates

        for point_index in range(number_of_points): # loops through all 600 points (0-599)
            x = int(pixel_positions[point_index]* SUPERSAMPLE) # get current horizontal pixel coordinate
            y = int(vertical_positions[point_index]* SUPERSAMPLE) # get corresponding vertical pixel coordinate
            points.append((x, y)) # add the pair to the list of tuples

        drawing.line(points,fill=strand_color,width=2*SUPERSAMPLE) # draw one complete strand connecting all 600 points

    image = image.resize((canvas_width, canvas_height),Image.Resampling.LANCZOS) # reduce supersampled image to final size (lanczos = high-quality resizing method)
    return image #


def render_video(audio_file,activity,output_file,duration_seconds,export_type):
    '''
    create every frame and send to FFmpeg
    :param audio_file: selected source audio
    :param activity: array containing waveform intensity for every frame
    :param output_file: destination video path
    :param duration_seconds: requested video length
    :param export_type: selected video format
    :return:
    '''
    if export_type in (
            "prores_shorts_audio",
            "prores_shorts_silent"
    ):
        video_width = SHORTS_WIDTH
        video_height = SHORTS_HEIGHT
    else:
        video_width = WIDTH
        video_height = HEIGHT
    has_audio = export_type in (
        "youtube",
        "prores_audio",
        "prores_shorts_audio"
    )
    requested_frames = int(duration_seconds * FPS) # calculate requested number of frames
    frame_count = min(requested_frames,len(activity)) # take min in order to prevent from reading beyond audio
    actual_duration = frame_count / FPS # convert frame count back into seconds
    # list containing the ffmpeg command
    command = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{video_width}x{video_height}",
        "-framerate", str(FPS),
        "-i", "pipe:0",
    ]

    if has_audio:
        command.extend([
            "-i", str(audio_file)
        ])

    command.extend([
        "-t", str(actual_duration),
        "-map", "0:v:0",
    ])

    if has_audio:
        command.extend([
            "-map", "1:a:0"
        ])

    if export_type == "youtube":
        command.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "17",
            "-pix_fmt", "yuv420p",

            "-c:a", "aac",
            "-b:a", "320k",

            "-movflags", "+faststart",
        ])

    else:
        command.extend([
            "-c:v", "prores_ks",
            "-profile:v", "4",
            "-pix_fmt", "yuva444p10le",
            "-alpha_bits", "16",
        ])

        if export_type == "prores_audio":
            command.extend([
                "-c:a", "pcm_s24le"
            ])

    command.append(str(output_file))

    process = subprocess.Popen(command,stdin=subprocess.PIPE)

    if process.stdin is None:
        raise RuntimeError(
            "Could not open the FFmpeg input pipe."
        )

    try:
        for frame_index in range(frame_count):
            image = create_waveform_frame(
                activity_value=activity[frame_index],
                frame_index=frame_index,
                canvas_width=video_width,
                canvas_height=video_height
            )

            process.stdin.write(
                image.tobytes()
            )

            if (
                frame_index % FPS == 0
                or frame_index == frame_count - 1
            ):
                rendered_seconds = (
                    frame_index + 1
                ) / FPS

                print(
                    f"Rendered "
                    f"{rendered_seconds:.0f}/"
                    f"{actual_duration:.0f} seconds"
                )

    except Exception:
        process.stdin.close()
        process.wait()
        raise

    process.stdin.close()
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError("FFmpeg could not create the video.")

    print("Video export completed.")

def generate_video(audio_file,output_file,color,duration_seconds=None,export_type="prores_audio"):
    '''

    :param audio_file: source audio
    :param output_file: destination video
    :param color: selected hex colour
    :param duration_seconds: use full audio by default
    :param export_type: ProRes with audio by default
    :return:
    '''
    global WAVEFORM_COLOR
    WAVEFORM_COLOR = color
    samples = decode_audio(audio_file) # use ffmpeg to decode audio into numpy array of pcm samples
    frame_loudness = calculate_frame_loudness(samples) # calculates one rms loudness value for every video frame
    smoothed_loudness = smooth_loudness(frame_loudness) # apply attack and release smoothing

    activity, _ = normalize_loudness(smoothed_loudness) # converts loudness into values between 0.0 and 1.0 (_ means ref level is ignored)

    audio_duration = len(samples) / SAMPLE_RATE # audio duration in seconds

    if duration_seconds is None: # if no duration specified, export complete audio
        duration_seconds = audio_duration
    else:
        duration_seconds = min(duration_seconds,audio_duration)
    # the function that draws and encodes the video
    render_video(
        audio_file=audio_file,
        activity=activity,
        output_file=output_file,
        duration_seconds=duration_seconds,
        export_type=export_type
    )
'''
def main():
    project_folder = Path(__file__).parent
    generate_video(
        audio_file=project_folder / "Imagine1.mp3",
        output_file=project_folder / "waveform_transparent.mov",
        color="#C8A96A",
        duration_seconds=3
    )

if __name__ == "__main__":
    main()
    #..
'''