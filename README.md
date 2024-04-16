Mewtwo
============

Mewtwo is a implementation of Disney's OTP server.

## Panda3D
[Windows SDK (x86_64)](https://rocketprogrammer.me/binaries/Panda3D-1.11.0-py3.9-x64.exe)

[Linux SDK (x86_64)](https://rocketprogrammer.me/linux/py3.deb)

## Getting Started
* `git clone https://gitlab.com/sunrisemmos/Mewtwo`
* `python -m pip install -r requirements.txt`
* `cd startup/win32`
* `run_otpd.bat`
* `run_server_ext.bat`
* `run_ai.bat`

## Components
* [OTP Server](https://gitlab.com/sunrisemmos/OTP-Server)
* [Panda3D](https://github.com/rocketprogrammer/panda3d)
* [Anesidora](https://github.com/satire6/Anesidora)
* [DNA Parser](https://github.com/rocketprogrammer/panda3d/tree/master/panda/src/dna)

## MySQL
Create a database called ``toontownTopDb``
User: ``ttDb_user``
Pass: ``toontastic2008``
```
CREATE TABLE IF NOT EXISTS ttParty (
    partyId       BIGINT      NOT NULL AUTO_INCREMENT,
    hostId        BIGINT      NOT NULL,
    startTime     DATETIME    NOT NULL DEFAULT '1970-01-01 00:00:00',
    endTime       DATETIME    NOT NULL DEFAULT '1970-01-01 00:00:00',
    isPrivate     TINYINT(1)  DEFAULT 0,
    inviteTheme   TINYINT,
    activities    VARBINARY(252),
    decorations   VARBINARY(252),
    statusId      TINYINT     DEFAULT 0,
    creationTime  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lastupdate    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (partyId),
    INDEX idx_hostId (hostId),
    INDEX idx_statusId (statusId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```
