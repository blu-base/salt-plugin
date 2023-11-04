# Salt Stack Plugin Rundeck Plugin

This repository provides integration between [Rundeck](https://www.rundeck.com)
and [SaltStack](https://www.saltproject.io). It aims to provide a number of
providers which only require minimal changes to the rundeck server and salt-api
and it's master.

Currently the following plugins are included:
  * NodeExecutor

Use cases:
  * Run Adhoc commands
  * Command Node Step

## Requirements

### Rundeck instance
Python 3.6+ is required. For communication with the salt-api, the python
library `salt-pepper>=0.76` is required on the rundeck server.
Use `pip install salt-pepper` to install it.
Further instructions on pepper can be found here: https://github.com/saltstack/pepper

Moreover, the command `python` must exist within Rundeck's `PATH` environment.
Usually it can be set systemwide by `updates-alternatives`.


### Salt-API
The library `salt-pepper` in the current state is focussing on the `cherry_py`
backend for the Salt-API. Follow salt's documentation configuring its API
[here](https://docs.saltproject.io/en/latest/ref/netapi/all/salt.netapi.rest_cherrypy.html).
You'll also have to [specify credentials](https://docs.saltproject.io/en/latest/topics/eauth/index.html)
and its ACL to be used by rundeck.

## Components

### NodeExecutor
This plugin forwards the specified command to the `cmd.run` execution module via
the Salt API. It uses the `local` client of salt's `netapi`.

Plugin Configuration:
* `Run As` sets the user in who's context the comand is run
* `Additional Arguments` can be used to set further keyword arguments for
  salt's `cmd.run` module. See its documentation for further details:
  [here](https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.cmdmod.html#salt.modules.cmdmod.run)


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
