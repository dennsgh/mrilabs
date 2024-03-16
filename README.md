<h1 align="center">
    <a href="//github.com/dennsgh/sonaris" target="_blank">
        <img alt="Sonaris" src="etc/sonaris.png" style="max-width:100%;">
    </a>
    <br>Sonaris Automation Framework
</h1>



Sonaris is a hardware device control platform developed to control lab devices and provide basic scheduling and monitoring utilities in a lab setting.

The device hardware written are at the moment quite limited and support only DG4202 Signal Generator and the EDUX1002A Oscilloscope, written to facilitate a thesis project.

## Dependencies

To setup the environment for env variables used in the app

On Linux you might need to install a few packages:
```bash
sudo apt-get update
sudo apt-get install libgl1 libegl1 ffmpeg libsm6 libxext6
```

On development environments or running from source:

```bash
python etc/env.py
```

To setup dependencies on the terminal:
```
poetry install --no-root
poetry shell
# Running the app
python -m sonaris run --hardware-mock --grafana
```

The generated .env file will look as such:
```
WORKINGDIR='C:/source/sonaris'
DATA='C:/source/sonaris/data'
PYTHONPATH='C:\source\sonaris\frontend\src;C:\source\sonaris\src'
ASSETS='C:/source/sonaris/frontend/assets'
```

## Run Flags

```bash
Usage: python -m sonaris run [OPTIONS]

  Run the Sonaris application.

Options:
  -hm, --hardware-mock  Run the app in hardware mock mode.
  --grafana             Start Grafana container alongside the application.
                        Requires Docker.
  --help                Show this message and exit.
```

## Installing and Running Sonaris

A stable distribution of Sonaris
```
pip install sonaris
```

When not utilizing a ```.env``` file it will attempt to use $HOME/.sonaris

Running the app
```
python -m sonaris run
```

Running the app from source
```
poetry install --no-root
poetry run python -m sonaris run
```

Running the app for hardware-mock
```
poetry run python -m sonaris run --hardware-mock
```
