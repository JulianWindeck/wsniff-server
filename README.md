<p align="center">
  
  <p align="center">
    <img alt="version" src="https://img.shields.io/badge/version-1.4-brightgreen?style=for-the-badge&labelColor=6d6157" />
    <img src="https://img.shields.io/badge/uses-python3-brightgreen?style=for-the-badge&logo=python&logoColor=white&labelColor=6d6157" />
  </p>
  <div align="center">Built with ❤️&nbsp; by <a href="https://github.com/JulianWindeck">julian</a></div>
</p>

# wsniff-server 
You don't know wsniff yet? Then [check it out](https://github.com/JulianWindeck/wsniff) before continuing here. 🌱

With this software, you can use the combined power of multiple wsniff-sniffers and create wardriving maps even faster ... it's over 9000! 🔥
 
## 📝 Requirements
You will need:
- multiple Raspberry Pis running [wsniff](https://github.com/JulianWindeck/wsniff)
- a separate server that can be reached online 

## Setup 
Execute the following commands on the server:

1. Clone the project from Github
```sh
cd <path_to_install_to>
git clone https://github.com/JulianWindeck/wsniff-server
```
2. Install the software 
```
cd wsniff-server
python -m venv venv
source ./venv/bin/activate
pip install -r ./requirements.txt
python create_db.py
```

4. In theory, you are now ready to go and [can start the software](#start-wsniff).
However, the default Flask webserver is very slow. If you want to use it in production and not just for a first test, 
please use Nginx+gunicorn with this program. 
Moreover, it is highly recommended to switch to a MySQL database instead of using the SQLite server which is just intended for
you to test the server easily. The server can work with MySQL without any problems, you just need to provide the corresponding tables.

## Start the server
Be sure you are in the wsniff-server directory which you cloned from Github.

Then, you can start wsniff with:
```sh
source ./venv/bin/activate
python main.py
```
After you have executed that command, you can enter the IP/URL of your server in the settings of your wsniff sniffers.
Then, click on 'Connect'. The Raspberry should show a login interface. Enter the default password 'feedmepackets' here.
Important: after you are logged in, you should immediately change the password!

Now you should be able to add a new sniffer to the server. After that, your sniffer should be completely configured.

## 📖 Licence
[GNU General Public License v3.0](https://github.com/JulianWindeck/wsniff/blob/main/LICENSE.md)
