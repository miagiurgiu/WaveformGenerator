import numpy as np
import subprocess
from PIL import Image,ImageDraw
from pathlib import Path

STRAND_COUNT = 11
STRAND_SHIFT = 14
STRAND_SEPARATION = 0.013

SAMPLE_RATE = 24_000
FPS=30
WIDTH = 1_920
HEIGHT = 1_080
SUPERSAMPLE = 3
WAVEFORM_COLOR = "#C8A96A"

def decode_audio(file_path):
    command=["ffmpeg",
             "-v","error",
             "-i",str(file_path),
             "-vn",
             "-ac", "1",
             "-ar", str(SAMPLE_RATE),
             "-f", "f32le",
             "pipe:1",
    ]
    result = subprocess.run(command, check=True, capture_output=True)
    audio_samples=np.frombuffer(result.stdout,dtype="<f4")
    return audio_samples

def analyse_basic_audio(samples):
    duration_seconds = len(samples) / SAMPLE_RATE
    peak_amplitude = np.max(np.abs(samples))
    rms_amplitude = np.sqrt(
        np.mean(samples ** 2)
    )
    peak_dbfs = 20 * np.log10(peak_amplitude)
    rms_dbfs = 20 * np.log10(rms_amplitude)
    return (
        duration_seconds,
        peak_amplitude,
        rms_amplitude,
        peak_dbfs,
        rms_dbfs,
    )

def calculate_frame_loudness(samples):
    samples_per_frame = SAMPLE_RATE // FPS

    number_of_frames = int(
        np.ceil(len(samples) / samples_per_frame)
    )

    frame_loudness = np.zeros(
        number_of_frames,
        dtype=np.float32
    )

    for frame_index in range(number_of_frames):
        start = frame_index * samples_per_frame
        end = min(
            start + samples_per_frame,
            len(samples)
        )

        frame_samples = samples[start:end]

        rms = np.sqrt(
            np.mean(frame_samples ** 2)
        )

        frame_loudness[frame_index] = rms

    return frame_loudness

def smooth_loudness(frame_loudness):
    attack_factor = 0.38
    release_factor = 0.075

    smoothed_loudness = np.zeros_like(frame_loudness)

    current_value = 0.0

    for frame_index in range(len(frame_loudness)):
        target_value = frame_loudness[frame_index]

        if target_value > current_value:
            smoothing_factor = attack_factor
        else:
            smoothing_factor = release_factor

        difference = target_value - current_value

        current_value = (
            current_value
            + difference * smoothing_factor
        )

        smoothed_loudness[frame_index] = current_value

    return smoothed_loudness

def normalize_loudness(smoothed_loudness):
    reference_level = np.percentile(
        smoothed_loudness,
        95
    )

    normalized_loudness = (
        smoothed_loudness / reference_level
    )

    normalized_loudness = np.clip(
        normalized_loudness,
        0.0,
        1.0
    )

    silence_threshold = 0.02

    activity = (
        normalized_loudness - silence_threshold
    ) / (
        1.0 - silence_threshold
    )

    activity = np.clip(
        activity,
        0.0,
        1.0
    )

    activity = activity ** 0.68

    return activity, reference_level

def hex_to_rgba(hex_color, alpha=185):
    clean_color = hex_color.lstrip("#")

    red = int(clean_color[0:2], 16)
    green = int(clean_color[2:4], 16)
    blue = int(clean_color[4:6], 16)

    return red, green, blue, alpha

def create_waveform_frame(activity_value,frame_index):
    strand_color = hex_to_rgba(
        WAVEFORM_COLOR
    )
    large_width = WIDTH * SUPERSAMPLE
    large_height = HEIGHT * SUPERSAMPLE

    image = Image.new(
        "RGBA",
        (large_width, large_height),
        (0, 0, 0, 0)
    )

    drawing = ImageDraw.Draw(image)

    number_of_points = 600

    horizontal_positions = np.linspace(
        -1.0,
        1.0,
        number_of_points
    )

    pixel_positions = np.linspace(
        100,
        WIDTH - 100,
        number_of_points
    )

    time_seconds = frame_index / FPS
    phase = time_seconds * 0.34

    sine_wave = np.sin(
        2 * np.pi * (2.15 * horizontal_positions + phase)
    )

    taper = np.sin(
        np.linspace(
            0.0,
            np.pi,
            number_of_points
        )
    ) ** 2.5

    wave_shape = sine_wave * taper

    maximum_height = HEIGHT * 0.25

    strand_offsets = np.linspace(
        -1.0,
        1.0,
        STRAND_COUNT
    )

    for strand_offset in strand_offsets:
        horizontal_shift = int(
            strand_offset
            * STRAND_SHIFT
            * activity_value
        )

        shifted_wave = np.roll(
            wave_shape,
            horizontal_shift
        )

        strand_separation = (
            strand_offset
            * HEIGHT
            * STRAND_SEPARATION
            * activity_value
            * taper
        )

        vertical_positions = (
            HEIGHT / 2
            + shifted_wave
            * maximum_height
            * activity_value
            + strand_separation
        )

        points = []

        for point_index in range(number_of_points):
            x = int(
                pixel_positions[point_index]
                * SUPERSAMPLE
            )

            y = int(
                vertical_positions[point_index]
                * SUPERSAMPLE
            )

            points.append((x, y))

        drawing.line(
            points,
            fill=strand_color,
            width=2
        )

    image = image.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    return image


def render_transparent_video(
    audio_file,
    activity,
    output_file,
    duration_seconds
):
    requested_frame_count = int(
        duration_seconds * FPS
    )

    frame_count = min(
        requested_frame_count,
        len(activity)
    )

    actual_duration = frame_count / FPS

    command = [
        "ffmpeg",
        "-y",

        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-framerate", str(FPS),
        "-i", "pipe:0",

        "-i", str(audio_file),

        "-t", str(actual_duration),

        "-map", "0:v:0",
        "-map", "1:a:0",

        "-c:v", "prores_ks",
        "-profile:v", "4",
        "-pix_fmt", "yuva444p10le",
        "-alpha_bits", "16",

        "-c:a", "pcm_s24le",

        str(output_file),
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE
    )

    for frame_index in range(frame_count):
        frame = create_waveform_frame(
            activity[frame_index],
            frame_index
        )

        process.stdin.write(
            frame.tobytes()
        )

        if frame_index % FPS == 0:
            seconds_completed = (
                frame_index / FPS
            )

            print(
                f"Rendered "
                f"{seconds_completed:.0f}/"
                f"{actual_duration:.0f} seconds"
            )

    process.stdin.close()

    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(
            "FFmpeg could not create the video."
        )

    print("Transparent video completed.")

def generate_video(
    audio_file,
    output_file,
    color,
    duration_seconds=None
):
    global WAVEFORM_COLOR
    WAVEFORM_COLOR = color

    samples = decode_audio(audio_file)

    frame_loudness = calculate_frame_loudness(samples)
    smoothed_loudness = smooth_loudness(
        frame_loudness
    )

    activity, _ = normalize_loudness(
        smoothed_loudness
    )

    audio_duration = len(samples) / SAMPLE_RATE

    if duration_seconds is None:
        duration_seconds = audio_duration
    else:
        duration_seconds = min(
            duration_seconds,
            audio_duration
        )

    render_transparent_video(
        audio_file,
        activity,
        output_file,
        duration_seconds
    )

def main():
    # # audio_file=Path(__file__).parent / "Diabelli Sonatina.wav"
    # audio_file = Path(__file__).parent / "Imagine1.mp3"
    # samples=decode_audio(audio_file)
    # print("Number of samples:",len(samples))
    # print("First 10 samples:",samples[:10])
    # print("Smallest value:",samples.min())
    # print("Largest value:",samples.max())
    #
    # # print("Python version:", sys.version)
    # # print("NumPy version:", np.__version__)
    # # print("Audio waveform project is ready.")
    #
    # analysis = analyse_basic_audio(samples)
    # duration, peak, rms, peak_dbfs, rms_dbfs = analysis
    # print("Duration:", duration, "seconds")
    # print("Peak amplitude:", peak)
    # print("RMS amplitude:", rms)
    # print("Peak level:", peak_dbfs, "dBFS")
    # print("RMS level:", rms_dbfs, "dBFS")
    #
    # frame_loudness = calculate_frame_loudness(samples)
    #
    # print("Number of video frames:", len(frame_loudness))
    # print("Samples per video frame:", SAMPLE_RATE // FPS)
    # print("First 20 frame loudness values:")
    # print(frame_loudness[:20])
    # print("Quietest frame:", frame_loudness.min())
    # print("Loudest frame:", frame_loudness.max())
    #
    # smoothed_loudness = smooth_loudness(frame_loudness)
    #
    # print("\nRaw versus smoothed loudness:")
    #
    # for frame_index in range(20):
    #     print(
    #         f"Frame {frame_index:02d}: "
    #         f"raw={frame_loudness[frame_index]:.6f}, "
    #         f"smoothed={smoothed_loudness[frame_index]:.6f}"
    #     )
    #
    # activity, reference_level = normalize_loudness(
    #     smoothed_loudness
    # )
    #
    # print("\nReference loudness:", reference_level)
    # print("First 20 activity values:")
    # print(activity[:20])
    #
    # active_frames = np.where(activity > 0.0)[0]
    #
    # if len(active_frames) > 0:
    #     first_active_frame = active_frames[0]
    #     first_active_time = first_active_frame / FPS
    #
    #     print("First active frame:", first_active_frame)
    #     print("First active time:", first_active_time, "seconds")
    #
    #
    # preview_seconds = 3
    #
    # transparent_output = (
    #         Path(__file__).parent
    #         / "waveform_transparent.mov"
    # )
    #
    # render_transparent_video(
    #     audio_file,
    #     activity,
    #     transparent_output,
    #     preview_seconds
    # )
    #
    # print(
    #     "Created transparent video:",
    #     transparent_output
    # )
    project_folder = Path(__file__).parent

    generate_video(
        audio_file=project_folder / "Imagine1.mp3",
        output_file=project_folder / "waveform_transparent.mov",
        color="#C8A96A",
        duration_seconds=3
    )

if __name__ == "__main__":
    main()