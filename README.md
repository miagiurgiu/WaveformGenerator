<div align="center">

<h1>Waveform Generator 〰️</h1>

<p>
  <strong>An audio-reactive waveform renderer for high-quality video overlays.</strong>
</p>

<br>

<p>
  <img
    src="https://img.shields.io/badge/ENGINE-PYTHON-blue?style=for-the-badge&logo=python&logoColor=blue"
  >
  <img
    src="https://img.shields.io/badge/AUDIO-FFMPEG-green?style=for-the-badge&logo=ffmpeg&logoColor=green"
  >
  <img
    src="https://img.shields.io/badge/SIGNAL-NUMPY-4D77CF?style=for-the-badge&logo=numpy&logoColor=white&labelColor=484848"
    alt="NumPy"
  >
  <img
    src="https://img.shields.io/badge/DRAWING-PILLOW-pink?style=for-the-badge&logo=pillow&logoColor=pink"
  >
</p>

<p>
  <img
    src="https://img.shields.io/badge/DESKTOP-PYSIDE6-41CD52?style=for-the-badge&logo=qt&logoColor=white&labelColor=484848"
    alt="PySide6"
  >
  <img
    src="https://img.shields.io/badge/WEB-FASTAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=484848"
    alt="FastAPI"
  >
</p>

</div>

---

## 📖 Project Overview

**Waveform Generator** is a Python application that transforms audio files into animated, audio-reactive waveform videos. The waveform responds to changes in loudness and can be customized using a hexadecimal colour value.

The project provides both a **PySide6 desktop interface** and a **FastAPI web interface**. Both interfaces use the same waveform-processing engine, keeping the audio analysis and rendering logic in one place.

The application supports **transparent ProRes 4444 exports** in landscape and vertical formats, with the option to include or exclude the original audio. These videos can be later imported into video editors and placed over other footage.

> **Note:** One of the strengths of this project lies in the flexible audio input. It allows the user to input various formats like WAV, MP3, M4A and even MOV/MP4 if they contain an audio stream.

---

## Demo

> These previews...

---

## Project Structure

This repository is a monorepo containing two interfaces and one shared waveform-processing engine.
```text
WaveformGenerator/
├── desktop_app/
│   └── gui.py                  # desktop interface
│
├── web_app/
│   ├── static/
│   │   └── style.css           # Web interface
│   ├── templates/
│   │   └── index.html          # Upload and export form
│   └── app.py                  # FastAPI routes / file handling
│
├── waveform_engine.py          # Audio analysis and video rendering
├── requirements.txt            # Python dependencies
├── .gitignore                  # Files excluded from Git
└── README.md                   # Project documentation
```

### 1. Shared waveform engine (waveform_engine.py)
The technical core of the project. Used by both desktop and web interfaces.
- Roles:
  - Decodes input media through FFmpeg
  - Converts the audio into mono PCM samples
  - Measures RMS loudness for every video frame
  - Draws the animated waveform using Pillow and NumPy
- Highlights:
  - Normalizes the loudness values
  - Streams frames directly to FFmpeg
  - Exports transparent ProRes 4444 video

### 2. Desktop interface (/desktop_app)
A local graphical interface built with PySide6. It allows the user to:
- select an audio/video file
- choose the waveform color in hex
- select an export format (vertical/horizontal, with/without sound)
- choose output location

### 3. Web interface(/web_app)
A local web interface built with FastAPI, HTML, and CSS.
- Roles:
  - Receives the uploaded file and some export settings
  - Calls the waveform engine
  - Returns the video as a download
- Highlights:
  - Temporarily stores the uploaded file
  - Removes temporary files after response is complete

> **Architecture note**: The desktop and web interfaces do not duplicate the signal-processing logic. Both call the same Python waveform engine, which keeps rendering behaviour consistent across the application.

## Key features
- 
-
-
-
-

## Audio Engineering
The waveform animation is driven by the changing loudness of the given audio. The engine does not display the original audio signal directly. Instead, it measures the audio's energy over time and uses that information to control a multi-strand waveform.

### 1. Audio decoding
FFmpeg receives the uploaded file and decodes its audio stream into raw numerical samples. During decoding, the audio is:
- converted to mono
- resampled to 24,000 samples/second
- converted to 32-bit floating-point PCM
- returned to Python as raw binary data

( - render video: create every frame and send to FFmpeg - instead of storing all frames, ffmpeg allows us to send one frame only, process it, then delete it, and so on without ?system/memory overuse?)


NumPy interprets the binary data as an array of floating-point numbers.
> Format note: FFmpeg allows the engine to accept common formats such as WAV, MP3, M4A, AAC, and FLAC, as well as MOV and MP4 files containing an audio stream. Compatibility depends on the codecs available in the installed FFmpeg build.

### 2. Connecting audio samples to video frames
The exported video runs at 30 frames per second, while the decoded audio contains 24,000 samples per second.
 => each video frame has 800 audio samples and for each of these frames, RMS is calculated to find out the amplitude:
    ```python
    rms = np.sqrt(np.mean(frame_samples ** 2))
    ```
- RMS describes signal's overall energy rather than the peaks
> Important: The current engine performs amplitude analysis, not frequency analysis. It does not currently use a Fourier transform or separate the audio into bass, midrange, and treble frequencies.

### 3. Smoothing and normalizing the movement
Smoothing loudness is needed to prevent sudden movements in the waveform. The engine smooths these changes using separate attack and release factors.
- Attack controls how quickly the waveform grows when the audio becomes louder (like the time-complexity concept in CS:))
- Release controls how slowly it becomes smaller when the audio becomes quieter
  
Normalising loudness is needed since audio files may have different recording levels. Their raw RMS values therefore can't be used directly as visual heights. Therefore, the engine makes use of the smoothed loudness value and selects the 95th percentile of it as its reference level.
- normalize loudness: make quiet sounds more visible and set a border for loud ones

## Visuals
The visual waveform is based on a sine wave.
- each waveform is composed of 11 individual strands for a dynamic design (VEED-inspired) 
- the horizontal movement is produced by the phase that changes with time
- the vertical movement is controlled by the calculated audio activity
- a taper reduces the waveform height at the edges (taper is strongest at the centre, weaker at the edges)
- the final shape is created by combining the sine wave and the taper


> for more details regarding the implementation of the engine please check the specifications inside the waveform_engine.py module.

## Technology stack
**Backend infrastructure**
- Language: Python 3.13
- Framework:
- Storage:
- Security: -

**Frontend client**
- Core:
- Build tool:
- Styling: CSS


## Running Locally


## Project Intentions/Storytime/Background
This app was mainly designed as an alternative to the VEED Waveform Generator Tool. I enjoy making music-related YouTube videos and the dynamic waveform 
---
**For professional inquiries, networking, or architectural discussions, feel free to reach out via GitHub or LinkedIn.*
  
