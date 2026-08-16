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

> **Note:** One of the strengths of this project lies in the flexible audio input. It allows the user to input various formats like WAV, MP3, M4A and even MOV and MP4 if they contain an audio stream.

---
