# Star Trek: Interstellar Transport

[![License](https://img.shields.io/github/license/moky/wormhole)](https://github.com/moky/wormhole/blob/master/LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/moky/wormhole/pulls)
[![Platform](https://img.shields.io/badge/Platform-Dart%203-brightgreen.svg)](https://github.com/moky/wormhole/wiki)
[![Issues](https://img.shields.io/github/issues/moky/wormhole)](https://github.com/moky/wormhole/issues)
[![Repo Size](https://img.shields.io/github/repo-size/moky/wormhole)](https://github.com/moky/wormhole/archive/refs/heads/main.zip)
[![Tags](https://img.shields.io/github/tag/moky/wormhole)](https://github.com/moky/wormhole/tags)
[![Version](https://img.shields.io/pypi/v/startrek)](https://pypi.org/project/startrek)

[![Watchers](https://img.shields.io/github/watchers/moky/wormhole)](https://github.com/moky/wormhole/watchers)
[![Forks](https://img.shields.io/github/forks/moky/wormhole)](https://github.com/moky/wormhole/forks)
[![Stars](https://img.shields.io/github/stars/moky/wormhole)](https://github.com/moky/wormhole/stargazers)
[![Followers](https://img.shields.io/github/followers/moky)](https://github.com/orgs/moky/followers)

## Network Module

* Channel
	* Socket
* Connection
	* TimedConnection
	* ConnectionState
	* ConnectionDelegate
* Hub
	* ConnectionPool

```
    Architecture
    ~~~~~~~~~~~~

                   Connection        Connection      Connection
                   Delegate          Delegate        Delegate
                       ^                 ^               ^
                       :                 :               :
          ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
                       :                 :               :
            +===+------V-----+====+------V-----+===+-----V------+===+
            ||  | connection |    | connection |   | connection |  ||
            ||  +------------+    +------------+   +------------+  ||
            ||          :                :               :         ||
            ||          :      HUB       :...............:         ||
            ||          :                        :                 ||
            ||     +-----------+           +-----------+           ||
            ||     |  channel  |           |  channel  |           ||
            +======+-----------+===========+-----------+============+
                   |  socket   |           |  socket   |
                   +-----^-----+           +-----^-----+
                         : (TCP)                 : (UDP)
                         :               ........:........
                         :               :               :
          ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
                         :               :               :
                         V               V               V
                    Remote Peer     Remote Peer     Remote Peer
```

* Ship
	* Arrival
	* Departure
* Dock
	* ArrivalHall
	* DepartureHall
* Porter
	* PorterDelegate
* Gate
	* PorterPool

```
    Architecture
    ~~~~~~~~~~~~

                Porter Delegate   Porter Delegate   Porter Delegate
                       ^                 ^               ^
                       :                 :               :
          ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
                       :                 :               :
            +==========V=================V===============V==========+
            ||         :                 :               :         ||
            ||         :      Gate       :               :         ||
            ||         :                 :               :         ||
            ||  +------------+    +------------+   +------------+  ||
            ||  |   porter   |    |   porter   |   |   porter   |  ||
            +===+------------+====+------------+===+------------+===+
            ||  | connection |    | connection |   | connection |  ||
            ||  +------------+    +------------+   +------------+  ||
            ||          :                :               :         ||
            ||          :      HUB       :...............:         ||
            ||          :                        :                 ||
            ||     +-----------+           +-----------+           ||
            ||     |  channel  |           |  channel  |           ||
            +======+-----------+===========+-----------+============+
                   |  socket   |           |  socket   |
                   +-----^-----+           +-----^-----+
                         : (TCP)                 : (UDP)
                         :               ........:........
                         :               :               :
          ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
                         :               :               :
                         V               V               V
                    Remote Peer     Remote Peer     Remote Peer
```

## Finite State Machine

* State
	* Transition
* Machine
	* BaseMachine
	* AutoMachine
* MachineDelegate

## Others

* Runner
* Ticker
* Metronome

Copyright &copy; 2021 Albert Moky
