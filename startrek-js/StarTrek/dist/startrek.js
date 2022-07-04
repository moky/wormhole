/**
 * Star Trek: Interstellar Transport (v0.2.0)
 *
 * @author    moKy <albert.moky at gmail.com>
 * @date      Jul. 5, 2022
 * @copyright (c) 2022 Albert Moky
 * @license   {@link https://mit-license.org | MIT License}
 */;
if (typeof StarTrek !== "object") {
    StarTrek = new MONKEY.Namespace();
}
(function (ns, sys) {
    if (typeof ns.assert !== "function") {
        ns.assert = console.assert;
    }
    if (typeof ns.type !== "object") {
        ns.type = new sys.Namespace();
    }
    if (typeof ns.net !== "object") {
        ns.net = new sys.Namespace();
    }
    if (typeof ns.port !== "object") {
        ns.port = new sys.Namespace();
    }
    if (typeof ns.socket !== "object") {
        ns.socket = new sys.Namespace();
    }
    ns.registers("type");
    ns.registers("net");
    ns.registers("port");
    ns.registers("socket");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Stringer = sys.type.Stringer;
    var ConstantString = sys.type.ConstantString;
    var SocketAddress = function () {};
    sys.Interface(SocketAddress, [Stringer]);
    SocketAddress.prototype.getHost = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    SocketAddress.prototype.getPort = function () {
        ns.assert(false, "implement me!");
        return 0;
    };
    var InetSocketAddress = function (host, port) {
        ConstantString.call(this, "(" + host + ":" + port + ")");
        this.__host = host;
        this.__port = port;
    };
    sys.Class(InetSocketAddress, ConstantString, [SocketAddress], null);
    InetSocketAddress.prototype.getHost = function () {
        return this.__host;
    };
    InetSocketAddress.prototype.getPort = function () {
        return this.__port;
    };
    ns.type.SocketAddress = SocketAddress;
    ns.type.InetSocketAddress = InetSocketAddress;
    ns.type.registers("SocketAddress");
    ns.type.registers("InetSocketAddress");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var KeyPairMap = function () {};
    sys.Interface(KeyPairMap, null);
    KeyPairMap.prototype.allValues = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    KeyPairMap.prototype.get = function (remote, local) {
        ns.assert(false, "implement me!");
        return null;
    };
    KeyPairMap.prototype.set = function (remote, local, value) {
        ns.assert(false, "implement me!");
        return null;
    };
    KeyPairMap.prototype.remove = function (remote, local, value) {
        ns.assert(false, "implement me!");
        return null;
    };
    ns.type.KeyPairMap = KeyPairMap;
    ns.type.registers("KeyPairMap");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Dictionary = sys.type.Dictionary;
    var KeyPairMap = ns.type.KeyPairMap;
    var HashKeyPairMap = function (any) {
        Object.call(this);
        this.__default = any;
        this.__map = new Dictionary();
        this.__values = [];
    };
    sys.Class(HashKeyPairMap, Object, [KeyPairMap], null);
    HashKeyPairMap.prototype.allValues = function () {
        return this.__values;
    };
    HashKeyPairMap.prototype.get = function (remote, local) {
        var key1, key2;
        if (remote) {
            key1 = remote;
            key2 = local;
        } else {
            key1 = local;
            key2 = null;
        }
        var table = this.__map.getValue(key1);
        if (!table) {
            return null;
        }
        var value;
        if (key2) {
            value = table.getValue(key2);
            if (value) {
                return value;
            }
            return table.getValue(this.__default);
        }
        value = table.getValue(this.__default);
        if (value) {
            return value;
        }
        var allKeys = table.allKeys();
        for (var i = 0; i < allKeys.length; ++i) {
            value = table.getValue(allKeys[i]);
            if (value) {
                return value;
            }
        }
        return null;
    };
    HashKeyPairMap.prototype.set = function (remote, local, value) {
        if (value) {
            remove_item(this.__values, value);
            this.__values.push(value);
        }
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map.getValue(keys.key1);
        if (table) {
            table.setValue(keys.key2, value);
        } else {
            if (value) {
                table = new Dictionary();
                table.setValue(keys.key2, value);
                this.__map.setValue(keys.key1, table);
            }
        }
    };
    HashKeyPairMap.prototype.remove = function (remote, local, value) {
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map.getValue(keys.key1);
        var old = null;
        if (table) {
            old = table.removeValue(keys.key2);
            if (old) {
                remove_item(this.__values, old);
            }
        }
        if (value && value !== old) {
            remove_item(this.__values, value);
        }
        return old ? old : value;
    };
    var get_keys = function (remoteAddress, localAddress, defaultAddress) {
        if (!remoteAddress) {
            return { key1: localAddress, key2: defaultAddress };
        } else {
            if (!localAddress) {
                return { key1: remoteAddress, key2: defaultAddress };
            } else {
                return { key1: remoteAddress, key2: localAddress };
            }
        }
    };
    var remove_item = function (array, item) {
        var remote = item.getRemoteAddress();
        var local = item.getLocalAddress();
        var old;
        for (var index = array.length - 1; index >= 0; --index) {
            old = array[index];
            if (old === item) {
                array.splice(index, 1);
                continue;
            }
            if (
                address_equals(old.getRemoteAddress(), remote) &&
                address_equals(old.getLocalAddress(), local)
            ) {
                array.splice(index, 1);
            }
        }
    };
    var address_equals = function (address1, address2) {
        if (address1) {
            return address1.equals(address2);
        } else {
            return !address2;
        }
    };
    ns.type.HashKeyPairMap = HashKeyPairMap;
    ns.type.registers("HashKeyPairMap");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var InetSocketAddress = ns.type.InetSocketAddress;
    var HashKeyPairMap = ns.type.HashKeyPairMap;
    var AnyAddress = new InetSocketAddress("0.0.0.0", 0);
    var AddressPairMap = function () {
        HashKeyPairMap.call(this, AnyAddress);
    };
    sys.Class(AddressPairMap, HashKeyPairMap, null, null);
    AddressPairMap.AnyAddress = AnyAddress;
    ns.type.AddressPairMap = AddressPairMap;
    ns.type.registers("AddressPairMap");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var BaseObject = sys.type.BaseObject;
    var AddressPairObject = function (remote, local) {
        BaseObject.call(this);
        this.remoteAddress = remote;
        this.localAddress = local;
    };
    sys.Class(AddressPairObject, BaseObject, null, null);
    AddressPairObject.prototype.getRemoteAddress = function () {
        return this.remoteAddress;
    };
    AddressPairObject.prototype.getLocalAddress = function () {
        return this.localAddress;
    };
    var address_equals = function (address1, address2) {
        if (address1) {
            return address1.equals(address2);
        } else {
            return !address2;
        }
    };
    AddressPairObject.prototype.equals = function (other) {
        if (!other) {
            return !this.remoteAddress && !this.localAddress;
        } else {
            if (other === this) {
                return true;
            } else {
                if (other instanceof AddressPairObject) {
                    return (
                        address_equals(other.getRemoteAddress(), this.remoteAddress) &&
                        address_equals(other.getLocalAddress(), this.localAddress)
                    );
                } else {
                    return false;
                }
            }
        }
    };
    AddressPairObject.prototype.valueOf = function () {
        var cname = this.constructor.name;
        var remote = this.getRemoteAddress();
        var local = this.getLocalAddress();
        if (remote) {
            remote = remote.toString();
        }
        if (local) {
            local = local.toString();
        }
        return "<" + cname + ": remote=" + remote + ", local=" + local + " />";
    };
    ns.type.AddressPairObject = AddressPairObject;
    ns.type.registers("AddressPairObject");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Channel = function () {};
    sys.Interface(Channel, null);
    Channel.prototype.isOpen = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Channel.prototype.isBound = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Channel.prototype.isAlive = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Channel.prototype.close = function () {
        ns.assert(false, "implement me!");
    };
    Channel.prototype.read = function (maxLen) {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.write = function (src) {
        ns.assert(false, "implement me!");
        return 0;
    };
    Channel.prototype.configureBlocking = function (block) {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.isBlocking = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Channel.prototype.bind = function (local) {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.getLocalAddress = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.isConnected = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Channel.prototype.connect = function (remote) {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.getRemoteAddress = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.disconnect = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.receive = function (maxLen) {
        ns.assert(false, "implement me!");
        return null;
    };
    Channel.prototype.send = function (src, target) {
        ns.assert(false, "implement me!");
        return 0;
    };
    ns.net.Channel = Channel;
    ns.net.registers("Channel");
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    var Stringer = sys.type.Stringer;
    var BaseState = fsm.BaseState;
    var ConnectionState = function (name) {
        BaseState.call(this);
        this.__name = name;
        this.__enterTime = 0;
    };
    sys.Class(ConnectionState, BaseState, null, null);
    ConnectionState.DEFAULT = "default";
    ConnectionState.PREPARING = "preparing";
    ConnectionState.READY = "ready";
    ConnectionState.MAINTAINING = "maintaining";
    ConnectionState.EXPIRED = "expired";
    ConnectionState.ERROR = "error";
    ConnectionState.prototype.equals = function (other) {
        if (this === other) {
            return true;
        } else {
            if (other instanceof ConnectionState) {
                return this.__name === other.toString();
            } else {
                if (sys.Interface.conforms(other, Stringer)) {
                    return this.__name === other.toString();
                } else {
                    return this.__name === other;
                }
            }
        }
    };
    ConnectionState.prototype.toString = function () {
        return this.__name;
    };
    ConnectionState.prototype.getEnterTime = function () {
        return this.__enterTime;
    };
    ConnectionState.prototype.onEnter = function (previous, machine) {
        this.__enterTime = new Date().getTime();
    };
    ConnectionState.prototype.onExit = function (next, machine) {
        this.__enterTime = 0;
    };
    ConnectionState.prototype.onPause = function (machine) {};
    ConnectionState.prototype.onResume = function (machine) {};
    ConnectionState.Delegate = fsm.Delegate;
    ns.net.ConnectionState = ConnectionState;
    ns.net.registers("ConnectionState");
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    var BaseTransition = fsm.BaseTransition;
    var StateTransition = function (targetStateName, evaluate) {
        BaseTransition.call(this, targetStateName);
        this.__evaluate = evaluate;
    };
    sys.Class(StateTransition, BaseTransition, null, null);
    StateTransition.prototype.evaluate = function (machine) {
        return this.__evaluate.call(this, machine);
    };
    ns.net.StateTransition = StateTransition;
    ns.net.registers("StateTransition");
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    var Context = fsm.Context;
    var BaseMachine = fsm.BaseMachine;
    var ConnectionState = ns.net.ConnectionState;
    var StateTransition = ns.net.StateTransition;
    var StateMachine = function (connection) {
        BaseMachine.call(this);
        this.__connection = connection;
        var builder = this.getStateBuilder();
        init_states(this, builder);
    };
    sys.Class(StateMachine, BaseMachine, [Context], null);
    StateMachine.prototype.getStateBuilder = function () {
        return new StateBuilder(new TransitionBuilder());
    };
    StateMachine.prototype.getConnection = function () {
        return this.__connection;
    };
    StateMachine.prototype.getContext = function () {
        return this;
    };
    var add_state = function (machine, state) {
        machine.setState(state.toString(), state);
    };
    var init_states = function (machine, builder) {
        add_state(machine, builder.getDefaultState());
        add_state(machine, builder.getPreparingState());
        add_state(machine, builder.getReadyState());
        add_state(machine, builder.getExpiredState());
        add_state(machine, builder.getMaintainingState());
        add_state(machine, builder.getErrorState());
    };
    var StateBuilder = function (transitionBuilder) {
        Object.call(this);
        this.builder = transitionBuilder;
    };
    sys.Class(StateBuilder, Object, null, {
        getDefaultState: function () {
            var state = getNamedState(ConnectionState.DEFAULT);
            state.addTransition(this.builder.getDefaultPreparingTransition());
            return state;
        },
        getPreparingState: function () {
            var state = getNamedState(ConnectionState.PREPARING);
            state.addTransition(this.builder.getPreparingReadyTransition());
            state.addTransition(this.builder.getPreparingDefaultTransition());
            return state;
        },
        getReadyState: function () {
            var state = getNamedState(ConnectionState.READY);
            state.addTransition(this.builder.getReadyExpiredTransition());
            state.addTransition(this.builder.getReadyErrorTransition());
            return state;
        },
        getExpiredState: function () {
            var state = getNamedState(ConnectionState.EXPIRED);
            state.addTransition(this.builder.getExpiredMaintainingTransition());
            state.addTransition(this.builder.getExpiredErrorTransition());
            return state;
        },
        getMaintainingState: function () {
            var state = getNamedState(ConnectionState.MAINTAINING);
            state.addTransition(this.builder.getMaintainingReadyTransition());
            state.addTransition(this.builder.getMaintainingExpiredTransition());
            state.addTransition(this.builder.getMaintainingErrorTransition());
            return state;
        },
        getErrorState: function () {
            var state = getNamedState(ConnectionState.ERROR);
            state.addTransition(this.builder.getErrorDefaultTransition());
            return state;
        }
    });
    var getNamedState = function (name) {
        return new ConnectionState(name);
    };
    var TransitionBuilder = function () {
        Object.call(this);
    };
    sys.Class(TransitionBuilder, Object, null, {
        getDefaultPreparingTransition: function () {
            return new StateTransition(ConnectionState.PREPARING, function (machine) {
                var conn = machine.getConnection();
                return conn && conn.isOpen();
            });
        },
        getPreparingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (machine) {
                var conn = machine.getConnection();
                return conn && conn.isAlive();
            });
        },
        getPreparingDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (machine) {
                var conn = machine.getConnection();
                return !conn || !conn.isOpen();
            });
        },
        getReadyExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return !conn.isReceivedRecently(new Date().getTime());
            });
        },
        getReadyErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine) {
                var conn = machine.getConnection();
                return !conn || !conn.isAlive();
            });
        },
        getExpiredMaintainingTransition: function () {
            return new StateTransition(ConnectionState.MAINTAINING, function (
                machine
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return conn.isSentRecently(new Date().getTime());
            });
        },
        getExpiredErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                return conn.isNotReceivedLongTimeAgo(new Date().getTime());
            });
        },
        getMaintainingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return conn.isReceivedRecently(new Date().getTime());
            });
        },
        getMaintainingExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return !conn.isSentRecently(new Date().getTime());
            });
        },
        getMaintainingErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                return conn.isNotReceivedLongTimeAgo(new Date().getTime());
            });
        },
        getErrorDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (machine) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                var current = machine.getCurrentState();
                var enter = current.getEnterTime();
                return 0 < enter && enter < conn.getLastReceivedTime();
            });
        }
    });
    ns.net.StateMachine = StateMachine;
    ns.net.registers("StateMachine");
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    var Ticker = sys.threading.Ticker;
    var Connection = function () {};
    sys.Interface(Connection, [Ticker]);
    Connection.prototype.isOpen = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Connection.prototype.isBound = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Connection.prototype.isConnected = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Connection.prototype.isAlive = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Connection.prototype.getLocalAddress = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Connection.prototype.getRemoteAddress = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Connection.prototype.getState = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Connection.prototype.send = function (data) {
        ns.assert(false, "implement me!");
        return 0;
    };
    Connection.prototype.onReceived = function (data) {
        ns.assert(false, "implement me!");
    };
    Connection.prototype.close = function () {
        ns.assert(false, "implement me!");
    };
    ns.net.Connection = Connection;
    ns.net.registers("Connection");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var ConnectionDelegate = function () {};
    sys.Interface(ConnectionDelegate, null);
    ConnectionDelegate.prototype.onConnectionStateChanged = function (
        previous,
        current,
        connection
    ) {
        ns.assert(false, "implement me!");
    };
    ConnectionDelegate.prototype.onConnectionReceived = function (
        data,
        connection
    ) {
        ns.assert(false, "implement me!");
    };
    ConnectionDelegate.prototype.onConnectionSent = function (
        sent,
        data,
        connection
    ) {
        ns.assert(false, "implement me!");
    };
    ConnectionDelegate.prototype.onConnectionFailed = function (
        error,
        data,
        connection
    ) {
        ns.assert(false, "implement me!");
    };
    ConnectionDelegate.prototype.onConnectionError = function (
        error,
        connection
    ) {
        ns.assert(false, "implement me!");
    };
    ns.net.ConnectionDelegate = ConnectionDelegate;
    ns.net.registers("ConnectionDelegate");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var TimedConnection = function () {};
    sys.Interface(TimedConnection, null);
    TimedConnection.prototype.getLastSentTime = function () {
        ns.assert(false, "implement me!");
        return 0;
    };
    TimedConnection.prototype.getLastReceivedTime = function () {
        ns.assert(false, "implement me!");
        return 0;
    };
    TimedConnection.prototype.isSentRecently = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    TimedConnection.prototype.isReceivedRecently = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    TimedConnection.prototype.isNotReceivedLongTimeAgo = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    ns.net.TimedConnection = TimedConnection;
    ns.net.registers("TimedConnection");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Processor = sys.skywalker.Processor;
    var Hub = function () {};
    sys.Interface(Hub, [Processor]);
    Hub.prototype.open = function (remote, local) {
        ns.assert(false, "implement me!");
        return null;
    };
    Hub.prototype.connect = function (remote, local) {
        ns.assert(false, "implement me!");
        return null;
    };
    ns.net.Hub = Hub;
    ns.net.registers("Hub");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Ship = function () {};
    sys.Interface(Ship, null);
    Ship.prototype.getSN = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    ns.port.Ship = Ship;
    ns.port.registers("Ship");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Ship = ns.port.Ship;
    var Arrival = function () {};
    sys.Interface(Arrival, [Ship]);
    Arrival.prototype.assemble = function (income) {
        ns.assert(false, "implement me!");
        return null;
    };
    Arrival.prototype.isTimeout = function (now) {
        ns.assert(false, "implement me!");
        return false;
    };
    Arrival.prototype.touch = function (now) {
        ns.assert(false, "implement me!");
    };
    ns.port.Arrival = Arrival;
    ns.port.registers("Arrival");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Ship = ns.port.Ship;
    var Departure = function () {};
    sys.Interface(Departure, [Ship]);
    var DeparturePriority = sys.type.Enum(null, {
        URGENT: -1,
        NORMAL: 0,
        SLOWER: 1
    });
    Departure.prototype.getPriority = function () {
        ns.assert(false, "implement me!");
        return 0;
    };
    Departure.prototype.getFragments = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Departure.prototype.checkResponse = function (response) {
        ns.assert(false, "implement me!");
        return false;
    };
    Departure.prototype.isNew = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Departure.prototype.isDisposable = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Departure.prototype.isTimeout = function (now) {
        ns.assert(false, "implement me!");
        return false;
    };
    Departure.prototype.isFailed = function (now) {
        ns.assert(false, "implement me!");
        return false;
    };
    Departure.prototype.touch = function (now) {
        ns.assert(false, "implement me!");
    };
    Departure.Priority = DeparturePriority;
    ns.port.Departure = Departure;
    ns.port.registers("Departure");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Processor = sys.skywalker.Processor;
    var Docker = function () {};
    sys.Interface(Docker, [Processor]);
    Docker.prototype.isOpen = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Docker.prototype.isAlive = function () {
        ns.assert(false, "implement me!");
        return false;
    };
    Docker.prototype.getStatus = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Docker.prototype.getRemoteAddress = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Docker.prototype.getLocalAddress = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    Docker.prototype.sendData = function (payload) {
        ns.assert(false, "implement me!");
        return false;
    };
    Docker.prototype.sendShip = function (ship) {
        ns.assert(false, "implement me!");
        return false;
    };
    Docker.prototype.processReceived = function (data) {
        ns.assert(false, "implement me!");
    };
    Docker.prototype.heartbeat = function () {
        ns.assert(false, "implement me!");
    };
    Docker.prototype.purge = function () {
        ns.assert(false, "implement me!");
    };
    Docker.prototype.close = function () {
        ns.assert(false, "implement me!");
    };
    ns.port.Docker = Docker;
    ns.port.registers("Docker");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var ConnectionState = ns.net.ConnectionState;
    var DockerStatus = sys.type.Enum(null, {
        ERROR: -1,
        INIT: 0,
        PREPARING: 1,
        READY: 2
    });
    DockerStatus.getStatus = function (state) {
        if (!state) {
            return DockerStatus.ERROR;
        } else {
            if (
                state.equals(ConnectionState.READY) ||
                state.equals(ConnectionState.EXPIRED) ||
                state.equals(ConnectionState.MAINTAINING)
            ) {
                return DockerStatus.READY;
            } else {
                if (state.equals(ConnectionState.PREPARING)) {
                    return DockerStatus.PREPARING;
                } else {
                    if (state.equals(ConnectionState.ERROR)) {
                        return DockerStatus.ERROR;
                    } else {
                        return DockerStatus.INIT;
                    }
                }
            }
        }
    };
    ns.port.DockerStatus = DockerStatus;
    ns.port.registers("DockerStatus");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var DockerDelegate = function () {};
    sys.Interface(DockerDelegate, null);
    DockerDelegate.prototype.onDockerReceived = function (arrival, docker) {
        ns.assert(false, "implement me!");
    };
    DockerDelegate.prototype.onDockerSent = function (departure, docker) {
        ns.assert(false, "implement me!");
    };
    DockerDelegate.prototype.onDockerFailed = function (
        error,
        departure,
        docker
    ) {
        ns.assert(false, "implement me!");
    };
    DockerDelegate.prototype.onDockerError = function (error, departure, docker) {
        ns.assert(false, "implement me!");
    };
    DockerDelegate.prototype.onDockerStatusChanged = function (
        previous,
        current,
        docker
    ) {
        ns.assert(false, "implement me!");
    };
    ns.port.DockerDelegate = DockerDelegate;
    ns.port.registers("DockerDelegate");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Processor = sys.skywalker.Processor;
    var Gate = function () {};
    sys.Interface(Gate, [Processor]);
    Gate.prototype.sendData = function (payload, remote, local) {
        ns.assert(false, "implement me!");
        return false;
    };
    Gate.prototype.sendShip = function (outgo, remote, local) {
        ns.assert(false, "implement me!");
        return false;
    };
    ns.port.Gate = Gate;
    ns.port.registers("Gate");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var SocketReader = function () {};
    sys.Interface(SocketReader, null);
    SocketReader.prototype.read = function (maxLen) {
        ns.assert(false, "implement me!");
        return null;
    };
    SocketReader.prototype.receive = function (maxLen) {
        ns.assert(false, "implement me!");
        return null;
    };
    var SocketWriter = function () {};
    sys.Interface(SocketWriter, null);
    SocketWriter.prototype.write = function (src) {
        ns.assert(false, "implement me!");
        return 0;
    };
    SocketWriter.prototype.send = function (src, target) {
        ns.assert(false, "implement me!");
        return 0;
    };
    ns.socket.SocketReader = SocketReader;
    ns.socket.SocketWriter = SocketWriter;
    ns.socket.registers("SocketReader");
    ns.socket.registers("SocketWriter");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var AddressPairObject = ns.type.AddressPairObject;
    var Channel = ns.net.Channel;
    var BaseChannel = function (remote, local, sock) {
        AddressPairObject.call(this, remote, local);
        this.__sock = sock;
        this.__reader = this.createReader();
        this.__writer = this.createWriter();
        this.__blocking = false;
        this.__opened = false;
        this.__connected = false;
        this.__bound = false;
        this.refreshFlags();
    };
    sys.Class(BaseChannel, AddressPairObject, [Channel], null);
    BaseChannel.prototype.finalize = function () {
        removeSocketChannel.call(this);
    };
    BaseChannel.prototype.createReader = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    BaseChannel.prototype.createWriter = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    BaseChannel.prototype.refreshFlags = function () {
        var sock = this.__sock;
        if (sock) {
            this.__blocking = sock.isBlocking();
            this.__opened = sock.isOpen();
            this.__connected = sock.isConnected();
            this.__bound = sock.isBound();
        } else {
            this.__blocking = false;
            this.__opened = false;
            this.__connected = false;
            this.__bound = false;
        }
    };
    BaseChannel.prototype.getSocket = function () {
        return this.__sock;
    };
    var removeSocketChannel = function () {
        var old = this.__sock;
        this.__sock = null;
        this.refreshFlags();
        if (old && old.isOpen()) {
            old.clone();
        }
    };
    BaseChannel.prototype.configureBlocking = function (block) {
        var sock = this.getSocket();
        sock.configureBlocking(block);
        this.__blocking = block;
        return sock;
    };
    BaseChannel.prototype.isBlocking = function () {
        return this.__blocking;
    };
    BaseChannel.prototype.isOpen = function () {
        return this.__opened;
    };
    BaseChannel.prototype.isConnected = function () {
        return this.__connected;
    };
    BaseChannel.prototype.isBound = function () {
        return this.__bound;
    };
    BaseChannel.prototype.isAlive = function () {
        return this.isOpen() && (this.isConnected() || this.isBound());
    };
    BaseChannel.prototype.bind = function (local) {
        if (!local) {
            local = this.localAddress;
        }
        var sock = this.getSocket();
        var nc = sock.bind(local);
        console.info("BaseChannel::bind()", local, sock);
        this.localAddress = local;
        this.__bound = true;
        this.__opened = true;
        this.__blocking = sock.isBlocking();
        return nc;
    };
    BaseChannel.prototype.connect = function (remote) {
        if (!remote) {
            remote = this.remoteAddress;
        }
        var sock = this.getSocket();
        sock.connect(remote);
        this.remoteAddress = remote;
        this.__connected = true;
        this.__opened = true;
        this.__blocking = sock.isBlocking();
        return sock;
    };
    BaseChannel.prototype.disconnect = function () {
        var sock = this.getSocket();
        removeSocketChannel.call(this);
        return sock;
    };
    BaseChannel.prototype.close = function () {
        removeSocketChannel.call(this);
    };
    BaseChannel.prototype.read = function (maxLen) {
        try {
            return this.__reader.read(maxLen);
        } catch (e) {
            this.close();
            throw e;
        }
    };
    BaseChannel.prototype.write = function (src) {
        try {
            return this.__writer.write(src);
        } catch (e) {
            this.close();
            throw e;
        }
    };
    BaseChannel.prototype.receive = function (maxLen) {
        try {
            return this.__reader.receive(maxLen);
        } catch (e) {
            this.close();
            throw e;
        }
    };
    BaseChannel.prototype.send = function (src, target) {
        try {
            return this.__writer.send(src, target);
        } catch (e) {
            this.close();
            throw e;
        }
    };
    ns.socket.BaseChannel = BaseChannel;
    ns.socket.registers("BaseChannel");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var ChannelChecker = function () {};
    sys.Interface(ChannelChecker, null);
    ChannelChecker.prototype.checkError = function (error, sock) {
        ns.assert(false, "implement me!");
        return null;
    };
    ChannelChecker.prototype.checkData = function (data, sock) {
        ns.assert(false, "implement me!");
        return null;
    };
    ns.socket.ChannelChecker = ChannelChecker;
    ns.socket.registers("ChannelChecker");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var ChannelChecker = ns.socket.ChannelChecker;
    var DefaultChecker = function () {
        Object.call(this);
    };
    sys.Class(DefaultChecker, Object, [ChannelChecker], {
        checkError: function (error, sock) {
            return error;
        },
        checkData: function (data, sock) {
            return null;
        }
    });
    var ChannelController = function (channel) {
        Object.call(this);
        this.__channel = channel;
        this.__checker = this.createChecker();
    };
    sys.Class(ChannelController, Object, [ChannelChecker], null);
    ChannelController.prototype.getChannel = function () {
        return this.__channel;
    };
    ChannelController.prototype.getRemoteAddress = function () {
        var channel = this.getChannel();
        return channel.getRemoteAddress();
    };
    ChannelController.prototype.getLocalAddress = function () {
        var channel = this.getChannel();
        return channel.getLocalAddress();
    };
    ChannelController.prototype.getSocket = function () {
        var channel = this.getChannel();
        return channel.getSocket();
    };
    ChannelController.prototype.createChecker = function () {
        return new DefaultChecker();
    };
    ChannelController.prototype.checkError = function (error, sock) {
        return this.__checker.checkError(error, sock);
    };
    ChannelController.prototype.checkData = function (data, sock) {
        return this.__checker.checkData(data, sock);
    };
    ns.socket.ChannelController = ChannelController;
    ns.socket.registers("ChannelController");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var SocketReader = ns.socket.SocketReader;
    var SocketWriter = ns.socket.SocketWriter;
    var ChannelController = ns.socket.ChannelController;
    var ChannelReader = function (channel) {
        ChannelController.call(this, channel);
    };
    sys.Class(ChannelReader, ChannelController, [SocketReader], {
        read: function (maxLen) {
            var sock = this.getSocket();
            var data = this.tryRead(maxLen, sock);
            var error = this.checkData(data, sock);
            if (error) {
                throw error;
            }
            return data;
        },
        tryRead: function (maxLen, sock) {
            try {
                return sock.read(maxLen);
            } catch (e) {
                e = this.checkError(e, sock);
                if (e) {
                    throw e;
                }
                return null;
            }
        }
    });
    var ChannelWriter = function (channel) {
        ChannelController.call(this, channel);
    };
    sys.Class(ChannelWriter, ChannelController, [SocketWriter], {
        write: function (data) {
            var sock = this.getSocket();
            var sent = 0;
            var rest = data.length;
            var cnt;
            while (true) {
                cnt = this.tryWrite(data, sock);
                if (cnt <= 0) {
                    break;
                }
                sent += cnt;
                rest -= cnt;
                if (rest <= 0) {
                    break;
                } else {
                    data = data.subarray(cnt);
                }
            }
        },
        tryWrite: function (data, sock) {
            try {
                return sock.write(data);
            } catch (e) {
                e = this.checkError(e, sock);
                if (e) {
                    throw e;
                }
                return 0;
            }
        }
    });
    ns.socket.ChannelReader = ChannelReader;
    ns.socket.ChannelWriter = ChannelWriter;
    ns.socket.registers("ChannelReader");
    ns.socket.registers("ChannelWriter");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var AddressPairObject = ns.type.AddressPairObject;
    var Connection = ns.net.Connection;
    var TimedConnection = ns.net.TimedConnection;
    var ConnectionState = ns.net.ConnectionState;
    var StateMachine = ns.net.StateMachine;
    var BaseConnection = function (remote, local, channel) {
        AddressPairObject.call(this, remote, local);
        this.__channel = channel;
        this.__delegate = null;
        this.__lastSentTime = 0;
        this.__lastReceivedTime = 0;
        this.__fsm = null;
    };
    sys.Class(
        BaseConnection,
        AddressPairObject,
        [Connection, TimedConnection, ConnectionState.Delegate],
        null
    );
    BaseConnection.EXPIRES = 16 * 1000;
    BaseConnection.prototype.finalize = function () {
        this.setChannel(null);
        this.setStateMachine(null);
    };
    BaseConnection.prototype.getStateMachine = function () {
        return this.__fsm;
    };
    BaseConnection.prototype.setStateMachine = function (machine) {
        var old = this.__fsm;
        this.__fsm = machine;
        if (old && old !== machine) {
            old.stop();
        }
    };
    BaseConnection.prototype.createStateMachine = function () {
        var machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine;
    };
    BaseConnection.prototype.getDelegate = function () {
        return this.__delegate;
    };
    BaseConnection.prototype.setDelegate = function (delegate) {
        this.__delegate = delegate;
    };
    BaseConnection.prototype.getChannel = function () {
        return this.__channel;
    };
    BaseConnection.prototype.setChannel = function (channel) {
        var old = this.__channel;
        this.__channel = channel;
        if (old && old !== channel) {
            if (old.isConnected()) {
                try {
                    old.disconnect();
                } catch (e) {
                    console.error("BaseConnection::setChannel()", e, old);
                }
            }
        }
    };
    BaseConnection.prototype.isOpen = function () {
        var channel = this.getChannel();
        return channel && channel.isOpen();
    };
    BaseConnection.prototype.isBound = function () {
        var channel = this.getChannel();
        return channel && channel.isBound();
    };
    BaseConnection.prototype.isConnected = function () {
        var channel = this.getChannel();
        return channel && channel.isConnected();
    };
    BaseConnection.prototype.isAlive = function () {
        return this.isOpen() && (this.isConnected() || this.isBound());
    };
    BaseConnection.prototype.clone = function () {
        this.setChannel(null);
        this.setStateMachine(null);
    };
    BaseConnection.prototype.start = function () {
        var machine = this.createStateMachine();
        machine.start();
        this.setStateMachine(machine);
    };
    BaseConnection.prototype.stop = function () {
        this.setChannel(null);
        this.setStateMachine(null);
    };
    BaseConnection.prototype.onReceived = function (data) {
        this.__lastReceivedTime = new Date().getTime();
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionReceived(data, this);
        }
    };
    BaseConnection.prototype.sendTo = function (data, destination) {
        var sent = -1;
        var channel = this.getChannel();
        if (channel && channel.isAlive()) {
            sent = channel.send(data, destination);
            if (sent > 0) {
                this.__lastSentTime = new Date().getTime();
            }
        }
        return sent;
    };
    BaseConnection.prototype.send = function (pack) {
        var error = null;
        var sent = -1;
        try {
            var destination = this.getRemoteAddress();
            sent = this.sendTo(pack, destination);
            if (sent < 0) {
                error = new Error(
                    "failed to send data: " + pack.length + " byte(s) to " + destination
                );
            }
        } catch (e) {
            error = e;
            this.setChannel(null);
        }
        var delegate = this.getDelegate();
        if (delegate) {
            if (error) {
                delegate.onConnectionFailed(error, pack, this);
            } else {
                delegate.onConnectionSent(sent, pack, this);
            }
        }
        return sent;
    };
    BaseConnection.prototype.getState = function () {
        var machine = this.getStateMachine();
        return machine ? machine.getCurrentState() : null;
    };
    BaseConnection.prototype.tick = function (now, delta) {
        var machine = this.getStateMachine();
        if (machine) {
            machine.tick(now, delta);
        }
    };
    BaseConnection.prototype.getLastSentTime = function () {
        return this.__lastSentTime;
    };
    BaseConnection.prototype.getLastReceivedTime = function () {
        return this.__lastReceivedTime;
    };
    BaseConnection.prototype.isSentRecently = function (now) {
        return now <= this.__lastSentTime + BaseConnection.EXPIRES;
    };
    BaseConnection.prototype.isReceivedRecently = function (now) {
        return now <= this.__lastReceivedTime + BaseConnection.EXPIRES;
    };
    BaseConnection.prototype.isNotReceivedLongTimeAgo = function (now) {
        return now > this.__lastSentTime + (BaseConnection.EXPIRES << 3);
    };
    BaseConnection.prototype.enterState = function (next, machine) {};
    BaseConnection.prototype.exitState = function (previous, machine) {
        var current = machine.getCurrentState();
        if (current && current.equals(ConnectionState.READY)) {
            if (previous && previous.equals(ConnectionState.PREPARING)) {
                var timestamp = new Date().getTime() - (BaseConnection.EXPIRES >> 1);
                if (this.__lastSentTime < timestamp) {
                    this.__lastSentTime = timestamp;
                }
                if (this.__lastReceivedTime < timestamp) {
                    this.__lastReceivedTime = timestamp;
                }
            }
        }
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionStateChanged(previous, current, this);
        }
    };
    BaseConnection.prototype.pauseState = function (current, machine) {};
    BaseConnection.prototype.resumeState = function (current, machine) {};
    ns.socket.BaseConnection = BaseConnection;
    ns.socket.registers("BaseConnection");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var BaseConnection = ns.socket.BaseConnection;
    var ActiveConnection = function (remote, local, channel, hub) {
        BaseConnection.call(this, remote, local, channel);
        this.__hub = hub;
    };
    sys.Class(ActiveConnection, BaseConnection, null, {
        isOpen: function () {
            return this.getStateMachine() !== null;
        },
        getChannel: function () {
            var channel = BaseConnection.prototype.getChannel.call(this);
            if (!channel || !channel.isOpen()) {
                if (this.getStateMachine() === null) {
                    return null;
                }
                this.__hub.open(this.remoteAddress, this.localAddress);
                this.setChannel(channel);
            }
            return channel;
        }
    });
    ns.socket.ActiveConnection = ActiveConnection;
    ns.socket.registers("ActiveConnection");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var AddressPairMap = ns.type.AddressPairMap;
    var ConnectionPool = function () {
        AddressPairMap.call(this);
    };
    sys.Class(ConnectionPool, AddressPairMap, null, {
        set: function (remote, local, value) {
            var old = this.get(remote, local);
            if (old && old !== value) {
                this.remove(remote, local, old);
            }
            AddressPairMap.prototype.set.call(this, remote, local, value);
        },
        remove: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(
                this,
                remote,
                local,
                value
            );
            if (cached && cached.isOpen()) {
                cached.close();
            }
            return cached;
        }
    });
    ns.socket.ConnectionPool = ConnectionPool;
    ns.socket.registers("ConnectionPool");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Hub = ns.net.Hub;
    var ConnectionPool = ns.socket.ConnectionPool;
    var BaseHub = function (delegate) {
        Object.call(this);
        this.__delegate = delegate;
        this.__connPool = this.createConnectionPool();
        this.__last = new Date().getTime();
    };
    sys.Class(BaseHub, Object, [Hub], null);
    BaseHub.prototype.createConnectionPool = function () {
        return new ConnectionPool();
    };
    BaseHub.prototype.getDelegate = function () {
        return this.__delegate;
    };
    BaseHub.MSS = 1472;
    BaseHub.prototype.allChannels = function () {
        ns.assert(false, "implement me!");
        return null;
    };
    BaseHub.prototype.removeChannel = function (remote, local, channel) {
        ns.assert(false, "implement me!");
    };
    BaseHub.prototype.createConnection = function (remote, local, channel) {
        ns.assert(false, "implement me!");
        return null;
    };
    BaseHub.prototype.allConnections = function () {
        return this.__connPool.allValues();
    };
    BaseHub.prototype.getConnection = function (remote, local) {
        return this.__connPool.get(remote, local);
    };
    BaseHub.prototype.setConnection = function (remote, local, connection) {
        this.__connPool.set(remote, local, connection);
    };
    BaseHub.prototype.removeConnection = function (remote, local, connection) {
        this.__connPool.remove(remote, local, connection);
    };
    BaseHub.prototype.connect = function (remote, local) {
        var conn = this.getConnection(remote, local);
        if (conn) {
            if (!local) {
                return conn;
            }
            var address = conn.getLocalAddress();
            if (!address || address.equals(local)) {
                return conn;
            }
        }
        var channel = this.open(remote, local);
        if (!channel || !channel.isOpen()) {
            return null;
        }
        conn = this.createConnection(remote, local, channel);
        if (conn) {
            this.setConnection(conn.getRemoteAddress(), conn.getLocalAddress(), conn);
        }
        return conn;
    };
    BaseHub.prototype.driveChannel = function (channel) {
        if (!channel.isAlive()) {
            return false;
        }
        var remote = channel.getRemoteAddress();
        var local = channel.getLocalAddress();
        var conn;
        var data;
        try {
            data = channel.receive(BaseHub.MSS);
        } catch (e) {
            var delegate = this.getDelegate();
            if (!delegate || !remote) {
                this.removeChannel(remote, local, channel);
            } else {
                conn = this.getConnection(remote, local);
                this.removeChannel(remote, local, channel);
                if (conn) {
                    delegate.onConnectionError(e, conn);
                }
            }
            return false;
        }
        if (!data) {
            return false;
        }
        conn = this.connect(remote, local);
        if (conn) {
            conn.onReceived(data);
        }
        return true;
    };
    BaseHub.prototype.driveChannels = function (channels) {
        var count = 0;
        for (var index = channels.length - 1; index >= 0; --index) {
            try {
                if (this.driveChannel(channels[index])) {
                    ++count;
                }
            } catch (e) {
                console.error("BaseHub::driveChannel()", e, channels[index]);
            }
        }
        return count;
    };
    BaseHub.prototype.cleanupChannels = function (channels) {
        var channel;
        for (var index = channels.length - 1; index >= 0; --index) {
            channel = channels[index];
            if (!channel.isAlive()) {
                this.removeChannel(
                    channel.getRemoteAddress(),
                    channel.getLocalAddress(),
                    channel
                );
            }
        }
    };
    BaseHub.prototype.driveConnections = function (connections) {
        var now = new Date().getTime();
        var delta = now - this.__last;
        for (var index = connections.length - 1; index >= 0; --index) {
            try {
                connections[index].tick(now, delta);
            } catch (e) {
                console.error("BaseHub::driveConnections()", e, connections[index]);
            }
        }
        this.__last = now;
    };
    BaseHub.prototype.cleanupConnections = function (connections) {
        var conn;
        for (var index = connections.length - 1; index >= 0; --index) {
            conn = connections[index];
            if (!conn.isOpen()) {
                this.removeConnection(
                    conn.getRemoteAddress(),
                    conn.getLocalAddress(),
                    conn
                );
            }
        }
    };
    BaseHub.prototype.process = function () {
        try {
            var channels = this.allChannels();
            var count = this.driveChannels(channels);
            var connections = this.allConnections();
            this.driveConnections(connections);
            this.cleanupChannels(channels);
            this.cleanupConnections(connections);
            return count > 0;
        } catch (e) {
            console.error("BaseHub::process()", e);
            return false;
        }
    };
    ns.socket.BaseHub = BaseHub;
    ns.socket.registers("BaseHub");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Arrival = ns.port.Arrival;
    var ArrivalShip = function (now) {
        Object.call(this);
        if (!now) {
            now = new Date().getTime();
        }
        this.__expired = now + ArrivalShip.EXPIRED;
    };
    sys.Class(ArrivalShip, Object, [Arrival], null);
    ArrivalShip.EXPIRES = 600 * 1000;
    ArrivalShip.prototype.isTimeout = function (now) {
        return now > this.__expired;
    };
    ArrivalShip.prototype.touch = function (now) {
        this.__expired = now + ArrivalShip.EXPIRES;
    };
    ns.ArrivalShip = ArrivalShip;
    ns.registers("ArrivalShip");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Arrays = sys.type.Arrays;
    var Dictionary = sys.type.Dictionary;
    var ArrivalHall = function () {
        Object.call(this);
        this.__arrivals = [];
        this.__amap = new Dictionary();
        this.__aft = new Dictionary();
    };
    sys.Class(ArrivalHall, Object, null, null);
    ArrivalHall.prototype.assembleArrival = function (income) {
        var sn = income.getSN();
        if (!sn) {
            return income;
        }
        var time = this.__aft.getValue(sn);
        if (time && time > 0) {
            return null;
        }
        var task = this.__amap.getValue(sn);
        if (!task) {
            task = income.assemble(income);
            if (!task) {
                this.__arrivals.push(income);
                this.__amap.setValue(sn, income);
                return null;
            } else {
                return task;
            }
        }
        var completed = task.assemble(income);
        if (!completed) {
            task.touch(new Date().getTime());
            return null;
        }
        Arrays.remove(this.__arrivals, task);
        this.__amap.removeValue(sn);
        this.__aft.setValue(sn, new Date().getTime());
        return completed;
    };
    ArrivalHall.prototype.purge = function () {
        var now = new Date().getTime();
        var ship;
        for (var i = this.__arrivals.length - 1; i >= 0; --i) {
            ship = this.__arrivals[i];
            if (ship.isTimeout(now)) {
                this.__arrivals.splice(i, 1);
                this.__amap.removeValue(ship.getSN());
            }
        }
        var ago = now - 3600;
        var keys = this.__aft.allKeys();
        var sn, when;
        for (var j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__aft.getValue(sn);
            if (!when || when < ago) {
                this.__aft.removeValue(sn);
                this.__amap.removeValue(sn);
            }
        }
    };
    ns.ArrivalHall = ArrivalHall;
    ns.registers("ArrivalHall");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Departure = ns.port.Departure;
    var DepartureShip = function (priority, maxTries) {
        Object.call(this);
        if (priority === null) {
            priority = 0;
        } else {
            if (priority instanceof sys.type.Enum) {
                priority = priority.valueOf();
            }
        }
        if (maxTries === null) {
            maxTries = 1 + DepartureShip.RETRIES;
        }
        this.__priority = priority;
        this.__tries = maxTries;
        this.__expired = 0;
    };
    sys.Class(DepartureShip, Object, [Departure], null);
    DepartureShip.EXPIRES = 120 * 1000;
    DepartureShip.RETRIES = 2;
    DepartureShip.DISPOSABLE = -1;
    DepartureShip.prototype.getPriority = function () {
        return this.__priority;
    };
    DepartureShip.prototype.isNew = function () {
        return this.__expired === 0;
    };
    DepartureShip.prototype.isDisposable = function () {
        return this.__tries <= 0;
    };
    DepartureShip.prototype.isTimeout = function (now) {
        return this.__tries > 0 && now > this.__expired;
    };
    DepartureShip.prototype.isFailed = function (now) {
        return this.__tries === 0 && now > this.__expired;
    };
    DepartureShip.prototype.touch = function (now) {
        this.__expired = now + DepartureShip.EXPIRES;
        this.__tries -= 1;
    };
    ns.DepartureShip = DepartureShip;
    ns.registers("DepartureShip");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Arrays = sys.type.Arrays;
    var Dictionary = sys.type.Dictionary;
    var DepartureHall = function () {
        Object.call(this);
        this.__priorities = [];
        this.__fleets = new Dictionary();
        this.__dmap = new Dictionary();
        this.__dft = new Dictionary();
    };
    sys.Class(DepartureHall, Object, null, null);
    DepartureHall.prototype.appendDeparture = function (outgo) {
        var priority = outgo.getPriority();
        var fleet = this.__fleets.getValue(priority);
        if (!fleet) {
            fleet = [];
            this.__fleets.setValue(priority, fleet);
            insertPriority(priority, this.__priorities);
        } else {
            if (fleet.indexOf(outgo) >= 0) {
                return false;
            }
        }
        fleet.push(outgo);
        var sn = outgo.getSN();
        if (sn && !outgo.isDisposable()) {
            this.__dmap.setValue(sn, outgo);
        }
        return true;
    };
    var insertPriority = function (prior, priorities) {
        var index, value;
        for (index = 0; index < priorities.length; ++index) {
            value = priorities[index];
            if (value === prior) {
                return;
            } else {
                if (value > prior) {
                    break;
                }
            }
        }
        Arrays.insert(priorities, index, prior);
    };
    DepartureHall.prototype.checkResponse = function (response) {
        var sn = response.getSN();
        var time = this.__dft.getValue(sn);
        if (!time || time === 0) {
            var ship = this.__dmap.getValue(sn);
            if (ship && ship.checkResponse(response)) {
                removeShip(ship, sn, this.__fleets, this.__dmap);
                this.__dft.setValue(sn, new Date().getTime());
                return ship;
            }
        }
        return null;
    };
    var removeShip = function (ship, sn, departureFleets, departureMap) {
        var prior = ship.getPriority();
        var fleet = departureFleets.getValue(prior);
        if (fleet) {
            Arrays.remove(fleet, ship);
            if (fleet.length === 0) {
                departureFleets.removeValue(prior);
            }
        }
        departureMap.removeValue(sn);
    };
    DepartureHall.prototype.getNextDeparture = function (now) {
        var next = getNextNewDeparture.call(this, now);
        if (!next) {
            next = getNextTimeoutDeparture.call(this, now);
        }
        return next;
    };
    var getNextNewDeparture = function (now) {
        var priorityList = new Array(this.__priorities);
        var prior, sn;
        var fleet, ship;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            prior = priorityList[i];
            fleet = this.__fleets.getValue(prior);
            if (!fleet) {
                continue;
            }
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                if (ship.isNew()) {
                    if (ship.isDisposable()) {
                        fleet.splice(j, 1);
                        sn = ship.getSN();
                        if (sn) {
                            this.__dmap.removeValue(sn);
                        }
                    } else {
                        ship.touch(now);
                    }
                    return ship;
                }
            }
        }
        return null;
    };
    var getNextTimeoutDeparture = function (now) {
        var priorityList = new Array(this.__priorities);
        var prior, sn;
        var fleet, ship;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            prior = priorityList[i];
            fleet = this.__fleets.getValue(prior);
            if (!fleet) {
                continue;
            }
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                if (ship.isTimeout(now)) {
                    ship.touch(now);
                    if (fleet.length > 1) {
                        fleet.splice(j, 1);
                        fleet.push(ship);
                    }
                    return ship;
                } else {
                    if (ship.isFailed(now)) {
                        fleet.splice(j, 1);
                        sn = ship.getSN();
                        if (sn) {
                            this.__dmap.removeValue(sn);
                        }
                        return ship;
                    }
                }
            }
        }
        return null;
    };
    DepartureHall.prototype.purge = function () {
        var failedTasks = [];
        var now = new Date().getTime();
        var priorityList = new Array(this.__priorities);
        var prior;
        var fleet, ship;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            prior = priorityList[i];
            fleet = this.__fleets.getValue(prior);
            if (!fleet) {
                continue;
            }
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                if (ship.isFailed(now)) {
                    failedTasks.push(ship);
                }
            }
            clear.call(this, fleet, failedTasks, prior);
            failedTasks = [];
        }
        var ago = now - 3600;
        var keys = this.__dft.allKeys();
        var sn, when;
        for (j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__dft.getValue(sn);
            if (!when || when < ago) {
                this.__dft.removeValue(sn);
                this.__dmap.removeValue(sn);
            }
        }
    };
    var clear = function (fleet, failedTasks, prior) {
        var sn, ship;
        for (var index = failedTasks.length - 1; index >= 0; --index) {
            ship = fleet[index];
            fleet.splice(index, 1);
            sn = ship.getSN();
            if (sn) {
                this.__dmap.removeValue(sn);
            }
        }
        if (fleet.length === 0) {
            this.__fleets.removeValue(prior);
        }
    };
    ns.DepartureHall = DepartureHall;
    ns.registers("DepartureHall");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var ArrivalHall = ns.ArrivalHall;
    var DepartureHall = ns.DepartureHall;
    var Dock = function () {
        Object.call(this);
        this.__arrivalHall = this.createArrivalHall();
        this.__departureHall = this.createDepartureHall();
    };
    sys.Class(Dock, Object, null, null);
    Dock.prototype.createArrivalHall = function () {
        return new ArrivalHall();
    };
    Dock.prototype.createDepartureHall = function () {
        return new DepartureHall();
    };
    Dock.prototype.assembleArrival = function (income) {
        return this.__arrivalHall.assembleArrival(income);
    };
    Dock.prototype.appendDeparture = function (outgo) {
        return this.__departureHall.appendDeparture(outgo);
    };
    Dock.prototype.checkResponse = function (response) {
        return this.__departureHall.checkResponse(response);
    };
    Dock.prototype.getNextDeparture = function (now) {
        return this.__departureHall.getNextDeparture(now);
    };
    Dock.prototype.purge = function () {
        this.__arrivalHall.purge();
        this.__departureHall.purge();
    };
    ns.Dock = Dock;
    ns.registers("Dock");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var AddressPairObject = ns.type.AddressPairObject;
    var Docker = ns.port.Docker;
    var DockerStatus = ns.port.DockerStatus;
    var Dock = ns.Dock;
    var StarDocker = function (connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        AddressPairObject.call(this, remote, local);
        this.__conn = connection;
        this.__delegate = null;
        this.__dock = this.createDock();
        this.__lastOutgo = null;
        this.__lastFragments = [];
    };
    sys.Class(StarDocker, AddressPairObject, [Docker], null);
    StarDocker.prototype.finalize = function () {
        removeConnection.call(this);
    };
    StarDocker.prototype.createDock = function () {
        return new Dock();
    };
    StarDocker.prototype.getDelegate = function () {
        return this.__delegate;
    };
    StarDocker.prototype.setDelegate = function (delegate) {
        this.__delegate = delegate;
    };
    StarDocker.prototype.getConnection = function () {
        return this.__conn;
    };
    var removeConnection = function () {
        var old = this.__conn;
        this.__conn = null;
        if (old && old.isOpen()) {
            old.close();
        }
    };
    StarDocker.prototype.isOpen = function () {
        var conn = this.getConnection();
        return conn && conn.isOpen();
    };
    StarDocker.prototype.isAlive = function () {
        var conn = this.getConnection();
        return conn && conn.isAlive();
    };
    StarDocker.prototype.getStatus = function () {
        var conn = this.getConnection();
        if (conn) {
            return DockerStatus.getStatus(conn.getState());
        } else {
            return DockerStatus.ERROR;
        }
    };
    StarDocker.prototype.sendShip = function (ship) {
        return this.__dock.appendDeparture(ship);
    };
    StarDocker.prototype.processReceived = function (data) {
        var income = this.getArrival(data);
        if (!income) {
            return;
        }
        income = this.checkArrival(income);
        if (!income) {
            return;
        }
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onDockerReceived(income, this);
        }
    };
    StarDocker.prototype.getArrival = function (data) {
        ns.assert("implement me!");
        return null;
    };
    StarDocker.prototype.checkArrival = function (income) {
        ns.assert("implement me!");
        return null;
    };
    StarDocker.prototype.checkResponse = function (income) {
        var linked = this.__dock.checkResponse(income);
        if (!linked) {
            return null;
        }
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onDockerSent(linked, this);
        }
        return linked;
    };
    StarDocker.prototype.assembleArrival = function (income) {
        return this.__dock.assembleArrival(income);
    };
    StarDocker.prototype.getNextDeparture = function (now) {
        return this.__dock.getNextDeparture(now);
    };
    StarDocker.prototype.purge = function () {
        this.__dock.purge();
    };
    StarDocker.prototype.close = function () {
        removeConnection.call(this);
        this.__dock = null;
    };
    StarDocker.prototype.process = function () {
        var conn = this.getConnection();
        if (!conn || !conn.isAlive()) {
            return false;
        }
        var delegate;
        var error;
        var outgo;
        var fragments;
        if (this.__lastFragments.length > 0) {
            outgo = this.__lastOutgo;
            fragments = this.__lastFragments;
            this.__lastOutgo = null;
            this.__lastFragments = [];
        } else {
            var now = new Date().getTime();
            outgo = this.getNextDeparture(now);
            if (!outgo) {
                return false;
            } else {
                if (outgo.isFailed(now)) {
                    delegate = this.getDelegate();
                    if (delegate) {
                        error = new Error("Request timeout");
                        delegate.onDockerFailed(error, outgo, this);
                    }
                    return true;
                } else {
                    fragments = outgo.getFragments();
                    if (fragments.length === 0) {
                        return true;
                    }
                }
            }
        }
        var index = 0;
        var sent = 0;
        try {
            var fra;
            for (var i = 0; i < fragments.length; ++i) {
                fra = fragments[i];
                sent = conn.send(fra);
                if (sent < fra.length) {
                    break;
                } else {
                    index += 1;
                    sent = 0;
                }
            }
            if (index < fragments.length) {
                error = new Error(
                    "only " + index + "/" + fragments.length + " fragments sent."
                );
            } else {
                return true;
            }
        } catch (e) {
            error = e;
        }
        for (; index > 0; --index) {
            fragments.shift();
        }
        if (sent > 0) {
            var last = fragments.shift();
            var part = last.subarray(sent);
            fragments.unshift(part);
        }
        this.__lastOutgo = outgo;
        this.__lastFragments = fragments;
        delegate = this.getDelegate();
        if (delegate) {
            delegate.onDockerError(error, outgo, this);
        }
        return false;
    };
    ns.StarDocker = StarDocker;
    ns.registers("StarDocker");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var AddressPairMap = ns.type.AddressPairMap;
    var DockerPool = function () {
        AddressPairMap.call(this);
    };
    sys.Class(DockerPool, AddressPairMap, null, {
        set: function (remote, local, value) {
            var old = this.get(remote, local);
            if (old && old !== value) {
                this.remove(remote, local, old);
            }
            AddressPairMap.prototype.set.call(this, remote, local, value);
        },
        remove: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(
                this,
                remote,
                local,
                value
            );
            if (cached && cached.isOpen()) {
                cached.close();
            }
            return cached;
        }
    });
    ns.DockerPool = DockerPool;
    ns.registers("DockerPool");
})(StarTrek, MONKEY);
(function (ns, sys) {
    var ConnectionDelegate = ns.net.ConnectionDelegate;
    var ConnectionState = ns.net.ConnectionState;
    var Gate = ns.port.Gate;
    var DockerStatus = ns.port.DockerStatus;
    var DockerPool = ns.DockerPool;
    var StarGate = function (delegate) {
        Object.call(this);
        this.__delegate = delegate;
        this.__dockerPool = this.createDockerPool();
    };
    sys.Class(StarGate, Object, [Gate, ConnectionDelegate], null);
    StarGate.prototype.createDockerPool = function () {
        return new DockerPool();
    };
    StarGate.prototype.getDelegate = function () {
        return this.__delegate;
    };
    StarGate.prototype.sendData = function (payload, remote, local) {
        var docker = this.getDocker(remote, local);
        if (!docker || !docker.isOpen()) {
            return false;
        }
        return docker.sendData(payload);
    };
    StarGate.prototype.sendShip = function (outgo, remote, local) {
        var docker = this.getDocker(remote, local);
        if (!docker || !docker.isOpen()) {
            return false;
        }
        return docker.sendShip(outgo);
    };
    StarGate.prototype.createDocker = function (connection, advanceParties) {
        ns.assert(false, "implement me!");
        return null;
    };
    StarGate.prototype.allDockers = function () {
        return this.__dockerPool.allValues();
    };
    StarGate.prototype.getDocker = function (remote, local) {
        return this.__dockerPool.get(remote, local);
    };
    StarGate.prototype.setDocker = function (remote, local, docker) {
        this.__dockerPool.set(remote, local, docker);
    };
    StarGate.prototype.removeDocker = function (remote, local, docker) {
        this.__dockerPool.remove(remote, local, docker);
    };
    StarGate.prototype.process = function () {
        try {
            var dockers = this.allDockers();
            var count = this.driveDockers(dockers);
            this.cleanupDockers(dockers);
            return count > 0;
        } catch (e) {
            console.error("StarGate::process()", e);
        }
    };
    StarGate.prototype.driveDockers = function (dockers) {
        var count = 0;
        for (var index = dockers.length - 1; index >= 0; --index) {
            try {
                if (dockers[index].process()) {
                    ++count;
                }
            } catch (e) {
                console.error("StarGate::driveDockers()", e, dockers[index]);
            }
        }
        return count;
    };
    StarGate.prototype.cleanupDockers = function (dockers) {
        var worker;
        for (var index = dockers.length - 1; index >= 0; --index) {
            worker = dockers[index];
            if (worker.isOpen()) {
                worker.purge();
            } else {
                this.removeDocker(
                    worker.getRemoteAddress(),
                    worker.getLocalAddress(),
                    worker
                );
            }
        }
    };
    StarGate.prototype.heartbeat = function (connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        var worker = this.getDocker(remote, local);
        if (worker) {
            worker.heartbeat();
        }
    };
    StarGate.prototype.onConnectionStateChanged = function (
        previous,
        current,
        connection
    ) {
        var delegate = this.getDelegate();
        if (delegate) {
            var s1 = DockerStatus.getStatus(previous);
            var s2 = DockerStatus.getStatus(current);
            var changed;
            if (!s1) {
                changed = !s2;
            } else {
                if (!s2) {
                    changed = true;
                } else {
                    changed = !s1.equals(s2);
                }
            }
            if (changed) {
                var remote = connection.getRemoteAddress();
                var local = connection.getLocalAddress();
                var docker = this.getDocker(remote, local);
                if (docker != null) {
                    delegate.onDockerStatusChanged(s1, s2, docker);
                }
            }
        }
        if (current && current.equals(ConnectionState.EXPIRED)) {
            this.heartbeat(connection);
        }
    };
    StarGate.prototype.onConnectionReceived = function (data, connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        var worker = this.getDocker(remote, local);
        if (worker) {
            worker.processReceived(data);
            return;
        }
        var advanceParties = this.cacheAdvanceParty(data, connection);
        worker = this.createDocker(connection, advanceParties);
        if (worker != null) {
            this.setDocker(
                worker.getRemoteAddress(),
                worker.getLocalAddress(),
                worker
            );
            for (var i = 0; i < advanceParties.length; ++i) {
                worker.processReceived(advanceParties[i]);
            }
            this.clearAdvanceParty(connection);
        }
    };
    StarGate.prototype.onConnectionSent = function (sent, data, connection) {};
    StarGate.prototype.onConnectionFailed = function (error, data, connection) {};
    StarGate.prototype.onConnectionError = function (error, connection) {};
    StarGate.prototype.cacheAdvanceParty = function (data, connection) {
        ns.assert("implement me!");
        return null;
    };
    StarGate.prototype.clearAdvanceParty = function (connection) {
        ns.assert("implement me!");
    };
    ns.StarGate = StarGate;
    ns.registers("StarGate");
})(StarTrek, MONKEY);
