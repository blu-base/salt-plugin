# Salt Stack Plugin Rundeck Plugin

This repository provides integration between [Rundeck](https://www.rundeck.com)
and [SaltStack](https://www.saltproject.io). It aims to provide a number of
providers which only require minimal changes to the rundeck server and salt-api
and it's master.

Currently the following plugins are included:
  * NodeExecutor
  * FileCopier

Use cases:
  * Run Adhoc commands
  * Embed Scripts in a Workflow
  * Command Node Step
  * Upload files

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

A Node's `hostname` in Rundeck must match the respective minion id in salt.
The nodes file in yaml format would contain entries such as:
```yaml
minion.example.org:
  description: A server with salt-minion
  hostname: minion.example.org
  nodename: minion.example.org
  username:
  osArch: x86_64
  osFamily: unix
  osName: Linux
  tags: 'salt-minion,server'
  node-executor: salt-node-executor
```
If you set up the Salt-NodeExecutor as default NodeExecutor, the attribute
`node-executor` is not required. For further Details on the nodes file can be
found in the [respective
documentation](https://docs.rundeck.com/docs/manual/document-format-reference/).


Plugin Configuration:
* `Run As` sets the user in who's context the comand is run. Optional.
* `Additional Arguments` can be used to set further keyword arguments for
  salt's `cmd.run` module. Optional. See its documentation for further details:
  [here](https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.cmdmod.html#salt.modules.cmdmod.run)
* The node attribute `salt-cmd-run-args` can also be used to provide additional
  arguments to salt's `cmd.run` module, individually per node.

  E.g.:
  ```yaml
  minion.example.org:
    hostname: minion.example.org
    nodename: foobar_minion
    username:
    node-executor: salt-node-executor
    salt-cmd-run-args: "env='{\"FOO\": \"bar\"}'"
  ```

### FileCopier
This plugin forwards files to a Node via the Salt API. In combination with the
Salt NodeExecutor, the inline script plugin can be used as well.

This FileCopier is intended for small files only, since it's sending files via
Salt's bus.

A Node's `hostname` in Rundeck must match the respective minion id in salt.
The nodes file in yaml format would contain entries such as:
```yaml
minion.example.org:
  description: A server with salt-minion
  hostname: minion.example.org
  nodename: minion.example.org
  username:
  osArch: x86_64
  osFamily: unix
  osName: Linux
  tags: 'salt-minion,server'
  node-executor: salt-node-executor
  file-copier: salt-file-copier
```

Configuration:
* `Chunksize` can modify the chunk size send via the Salt Event bus.

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
