# Gogo2
### Installation
* Install python 3
* Install dependencies: `pip install pygame multimethod`
### Run locally in demo mode
* `python main.py`

### Run in client/server Mode
####Review `config.py`:
  
* Set `MODE_INDEX`:  
  0 - Unicast, 1 - Broadcast, 2 - Multicast

* Set `LOCAL_IP` to your local ip.  
  Find it using `ifconfig` on Linux or `ipconfig` on Windows.

* `python server.py`
* `python client.py [server ip]`
* Use __arrows__ to move around, __space__ to shoot, __m__ to lay mines.

### Known issues
* On multiple machins, sometimes hangs
* 
