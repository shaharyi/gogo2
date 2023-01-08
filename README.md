# Gogo2

## Installation
* Download Gogo2 zip and extract  
  or  
  Clone Gogo2 git repository  
  `$ git clone https://github.com/shaharyi/gogo2.git`  
  `$ cd gogo2`
  

* Install python 3  
  `$ apt get install python3`
  

* Install Pip  
  `$ apt get install pip3`     
  

* Optional: create Python virtual-env   
`$ python3 -m venv myenv`  
`$ source myenv/bin/activate`  


* Install dependencies:  
  `$ pip install pygame multimethod`
  
## Run locally in demo mode
* `python main.py`

## Run in client/server Mode
* Copy `config_template.py` to `config.py` and edit as follows.

  
* Set `MODE_INDEX`:  
  0 - Unicast, 1 - Broadcast, 2 - Multicast
  

* Set `LOCAL_IP` to your local ip.  
  Find what is your local ip using `ifconfig` on Linux or
  `ipconfig` on Windows.
  

* `python server.py`
  

* `python client.py [server ip]`
  

* Use __arrows__ to move around, __space__ to shoot, __m__ to lay mines.

## Known issues
* On multiple machins, sometimes hangs
*

## For further guide, see 
`gogo2/pypyvenv/site-packages/pygame/examples`