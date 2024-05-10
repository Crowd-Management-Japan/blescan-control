# Blescan control
This repository is an extention of the [blescan-backend](https://github.com/Crowd-Management-Japan/blescan-backend) repository aimed to visualize results from BLE scans on a map and on a graph. If the scanning devices using the blescan software (for details see here [blescan](https://github.com/Crowd-Management-Japan/blescan)) are positioned in an area to be surveilled, it is possible to identify crowded areas and keep track of the changes in total number of people (or a proportional value of it).

# Installation
This repository is thought to be installed as an addition to the [blescan-backend](https://github.com/Crowd-Management-Japan/blescan-backend) package. As such installation scripts are not provided and it is suggested to clone the repository and change settings file where required. In addition to the packages already installed by `blescan-backend`, for this repository `folium` and `pandas` are needed. Please change URLs, login credentials, etc. at your will.

# Running
The software can be simply run by executing `blemap.py`. However, it is suggested to control it through a service, first enabling it with `sudo systemctl enable blemap-backend.service` and later starting it by `sudo systemctl start blemap-backend.service`. A port may have to be opened to let the code work. Here, port `5555` is used, but it may be changed at will.
