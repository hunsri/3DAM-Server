# 3DAM-Server

This repository contains a simple model server designed to serve models to a [Godot Client](https://github.com/hunsri/3DAM).

## Getting Started

### Requirements
- Python 3.8+
- FastAPI
- Uvicorn

### Installation
Creation of a virtual environment is recommended!
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

You can make sure that activation of the virtual environment was successful.
The result should point to the installation path of this project.

```
python -c "import sys; print(sys.executable)"
```


### Startup Command
Run the server locally using the following command:
```bash
fastapi dev main.py
```