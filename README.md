# Sonaris

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
python -m sonaris run --hardware-mock
```

The generated .env file will look as such:
```
WORKINGDIR='C:/source/sonaris'
CONFIG='C:/source/sonaris/etc'
DATA='C:/source/sonaris/data'
PYTHONPATH='C:\source\sonaris\frontend\src;C:\source\sonaris\src'
ASSETS='C:/source/sonaris/frontend/assets'
LOGS='C:/source/sonaris/logs'
```

## Installing and Running Sonaris

A stable distribution of the Sonaris
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
