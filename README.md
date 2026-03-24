# 3DAM-Server

This repository contains a simple model server designed to serve models to a [Godot Client](https://github.com/hunsri/3DAM).

## Getting Started

### Requirements
- Python 3.8+

### Installation
Download and run the following commands.<br>
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
