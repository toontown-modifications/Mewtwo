OpenTTServer
============

_OpenTTServer_ is a free & open-source functional equivalent of _Disney's Toontown server_ as it existed in 2003.

A lot of credit for this goes towards _Astron_ and _Disney's VR studio_.

# Does this work as well as Disney's Toontown server?

Mostly. OpenTTServer can run with Toontown 2003 clients, however the DC file has to be modified since this uses Astron. This does not require client changes.
Aside from the DC file, this combined with the AI server can provide a suitable replacement to Disney's Toontown server.

# How does this work?

Using a modification to Astron, OpenTTServer serves as an extended ClientAgent of sorts, providing Toontown 2003 clients access to an Astron cluster.
Technically speaking, it's kind of like an UberDOG server without the DOGs.
OpenTTServer requires _Python_, _Panda3D (with Astron modifications)_, and _libpandadna_.

# What about the AI server?

Toontown 2003 had a pretty lackluster AI server (relative to later Toontown), and relied more on the Toontown server.
A base AI server is provided here, and it relies entirely upon Astron. It is only involved with OpenTTServer itself
as far as network messaging goes.

# Is the game client provided here?

No, a (de)compiled game client will never be provided here. This is entirely for server recreation.

# How do I use it?

You will need to clone the _Astron_ repository and apply the `astron.patch` file provided here. Compiled binaries will not be provided here.
You then need to create an Astron configuration file which uses OpenTTServer's extension ID _5536_. You can also use the simple one provided here.
You also need to put the NameMasterEnglish file, as well as the DNA files, into the _etc_ directory. These can be found in the original phase files.
You can then launch an Astron cluster, combined with OpenTTServer & an AI server, to be able to fully use the Toontown 2003 client.
OpenTTServer can be ran by importing `server.ServerStart`.

# Can I use this for a production game?

Not without modifications. OpenTTServer does not provide production functionality needed for things such as RPC, security, & moderation.
However, you may be able to use it for production with those added.
One thing you can certainly use this for by itself is to play Toontown 2003 with friends or by yourself.

# Can this support later Toontown versions such as 2005?

Not right now. Even in 2005, the Toontown networking protocol (by 2005 changed to OTP) significantly differs from the one this project is using.
It is possible for a 2005 mode to be added to the server later, although it is doubtful recreated AI files for 2005 would be provided here.