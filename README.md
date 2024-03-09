# mrilabs

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
python -m mrilabs run --hardware-mock
```

The generated .env file will look as such:
```
WORKINGDIR='C:/source/mrilabs'
CONFIG='C:/source/mrilabs/etc'
DATA='C:/source/mrilabs/data'
PYTHONPATH='C:\source\mrilabs\frontend\src;C:\source\mrilabs\src'
ASSETS='C:/source/mrilabs/frontend/assets'
LOGS='C:/source/mrilabs/logs'
```

## Installing and Running MRILabs

A stable distribution of the MRILabs
```
pip install mrilabs
```

When not utilizing a ```.env``` file it will attempt to use $HOME/.mrilabs

Running the app
```
python -m mrilabs run
```

Running the app from source
```
poetry install --no-root
poetry run python -m mrilabs run
```

Running the app for hardware-mock
```
poetry run python -m mrilabs run --hardware-mock
```
