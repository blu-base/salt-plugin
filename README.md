# Salt Stack Plugin Rundeck Plugin

This repository provides integration between [Rundeck]() and 
[SaltStack](https://www.saltproject.io). It aims to provide a number of
providers which only require minimal changes to the rundeck server and salt-api
and it's master.

Use cases:
  * Run Adhoc commands

## Requirements

### Rundeck instance
Python 3.6+ is required. For communication with the salt-api, the python
library `salt-pepper>=0.76` is required on the rundeck server.
Use `pip install salt-pepper` to install it.

Further instructions can be found here: https://github.com/saltstack/pepper

### Salt-API
The library `salt-pepper` in the current state is focussing on the `cherry_py`
backend for the Salt-API. Follow salt's documentation configuring its API
[here](https://docs.saltproject.io/en/latest/ref/netapi/all/salt.netapi.rest_cherrypy.html).
You'll also have to [specify credentials](https://docs.saltproject.io/en/latest/topics/eauth/index.html)
and its ACL to be used by rundeck.

## Build

* Using gradle
```
gradle clean build
```

* Using make

```
make clean build
```

## Install

```
cp build/libs/salt-plugin.zip $RDECK_BASE/libext
```



## Attribution

This repository contains derivate work from the following projects:

* [salt-gen-source](https://github.com/amendlik/salt-gen-resource)
* [pepper](https://github.com/saltstack/pepper)
