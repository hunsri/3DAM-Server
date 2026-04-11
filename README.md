# 3DAM-Server

A simple **3D**-**A**sset-**M**anagement-**Server** designed to serve assets to a [Godot Client](https://github.com/hunsri/3DAM) or any custom frontend.

## Overview
<img width="1666" height="666" alt="3dam-server" src="https://github.com/user-attachments/assets/ac3d6e6c-fb7d-4b93-8636-71aa2682703a" />

## Getting Started

### Requirements
- Python 3.8+

### Installation
Download the project by cloning it (or as a .zip), then run the following commands.<br>
This creates a virtual environment to keep things clean and downloads everything needed.<br> *Simple as that!* <br>

<b>On Windows:</b>
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
<b>On Linux (Debian):</b>
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Customization (optional)
If you want to customize your asset server, copy `config.json.example` and rename it to `config.json`. <br>
You can then edit the values inside the newly created `config.json`!

### Startup Command
Run the server locally using the following command:
```bash
fastapi run main.py
```
Or alternatively, if you want to set a port:
```
uvicorn main:app --host 0.0.0.0 --port <portnumber>
```
