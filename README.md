# Instalation:

``` bash

# get the code:
mkdir -p /srv/laser_db
git clone https://github.com/Stackpole-International-Stratford/laser_db.git /srv/laser_db

# install the servie file
ln -s /srv/laser_db/laserdb.service /etc/systemd/system/laserdb.service
systemctl daemon-reload
systemctl enable laserdb.service
systemctl start laserdb.service

# monitor
journalctl -f -u laserdb.service
```


# Notes:

Running Python via systemd:
 - source: https://trstringer.com/systemd-logging-in-python/
 - logging requires the following ubuntu packages be installed:
     build-essential, libsystemd-dev


``` bash
ln -s /srv/laser_db/laserdb.service /etc/systemd/system/laserdb.service
systemctl daemon-reload
systemctl start pysystemdlogging.service
```

# Changelog:

1/11/2023 - Updated to use config file.  Added detailed README

# TODO:

- Survive PUNS db offline
    - Save PUNS to file after retrieving from DB
    - use last saved PUNS when db unavailable
    - if using file, recheck periodically for network connection and load puns from server.

- Survive Laser db offline
    - Load today's marks on startup from db to file
    - save each mark to file and db
    - use saved marks to check against if db is unavailable
    - if using saved marks, check for connectivity periodically and upload all marks saved in the file to db
    
