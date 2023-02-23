/**
 * Star Trek: Interstellar Transport (v0.2.2)
 *
 * @author    moKy <albert.moky at gmail.com>
 * @date      Feb. 12, 2023
 * @copyright (c) 2023 Albert Moky
 * @license   {@link https://mit-license.org | MIT License}
 */;
if (typeof StarTrek !== "object") {
    StarTrek = {};
}
(function (ns) {
    if (typeof ns.type !== "object") {
        ns.type = {};
    }
    if (typeof ns.net !== "object") {
        ns.net = {};
    }
    if (typeof ns.port !== "object") {
        ns.port = {};
    }
    if (typeof ns.socket !== "object") {
        ns.socket = {};
    }
})(StarTrek);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var Class = sys.type.Class;
    var Stringer = sys.type.Stringer;
    var ConstantString = sys.type.ConstantString;
    var SocketAddress = Interface(null, [Stringer]);
    SocketAddress.prototype.getHost = function () {
        throw new Error("NotImplemented");
    };
    SocketAddress.prototype.getPort = function () {
        throw new Error("NotImplemented");
    };
    var InetSocketAddress = function (host, port) {
        ConstantString.call(this, "(" + host + ":" + port + ")");
        this.__host = host;
        this.__port = port;
    };
    Class(InetSocketAddress, ConstantString, [SocketAddress], null);
    InetSocketAddress.prototype.getHost = function () {
        return this.__host;
    };
    InetSocketAddress.prototype.getPort = function () {
        return this.__port;
    };
    ns.type.SocketAddress = SocketAddress;
    ns.type.InetSocketAddress = InetSocketAddress;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var KeyPairMap = Interface(null, null);
    KeyPairMap.prototype.values = function () {
        throw new Error("NotImplemented");
    };
    KeyPairMap.prototype.get = function (remote, local) {
        throw new Error("NotImplemented");
    };
    KeyPairMap.prototype.set = function (remote, local, value) {
        throw new Error("NotImplemented");
    };
    KeyPairMap.prototype.remove = function (remote, local, value) {
        throw new Error("NotImplemented");
    };
    ns.type.KeyPairMap = KeyPairMap;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var KeyPairMap = ns.type.KeyPairMap;
    var HashKeyPairMap = function (any) {
        Object.call(this);
        this.__default = any;
        this.__map = {};
        this.__values = [];
    };
    Class(HashKeyPairMap, Object, [KeyPairMap], null);
    HashKeyPairMap.prototype.values = function () {
        return this.__values;
    };
    HashKeyPairMap.prototype.get = function (remote, local) {
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map[keys[0]];
        if (!table) {
            return null;
        }
        var value;
        if (keys[1]) {
            value = table[keys[1]];
            if (value) {
                return value;
            }
            return table[this.__default];
        }
        value = table[this.__default];
        if (value) {
            return value;
        }
        var allKeys = Object.keys(table);
        for (var i = 0; i < allKeys.length; ++i) {
            value = table[allKeys[i]];
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
        var table = this.__map[keys[0]];
        if (table) {
            if (!value) {
                delete table[keys[1]];
            } else {
                table[keys[1]] = value;
            }
        } else {
            if (value) {
                table = {};
                table[keys[1]] = value;
                this.__map[keys[0]] = table;
            }
        }
    };
    HashKeyPairMap.prototype.remove = function (remote, local, value) {
        var keys = get_keys(remote, local, this.__default);
        var table = this.__map[keys[0]];
        var old = null;
        if (table) {
            old = table[keys[1]];
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
            return [localAddress, defaultAddress];
        } else {
            if (!localAddress) {
                return [remoteAddress, defaultAddress];
            } else {
                return [remoteAddress, localAddress];
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var InetSocketAddress = ns.type.InetSocketAddress;
    var HashKeyPairMap = ns.type.HashKeyPairMap;
    var AnyAddress = new InetSocketAddress("0.0.0.0", 0);
    var AddressPairMap = function () {
        HashKeyPairMap.call(this, AnyAddress);
    };
    Class(AddressPairMap, HashKeyPairMap, null, null);
    AddressPairMap.AnyAddress = AnyAddress;
    ns.type.AddressPairMap = AddressPairMap;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var BaseObject = sys.type.BaseObject;
    var AddressPairObject = function (remote, local) {
        BaseObject.call(this);
        this.remoteAddress = remote;
        this.localAddress = local;
    };
    Class(AddressPairObject, BaseObject, null, null);
    AddressPairObject.prototype.getRemoteAddress = function () {
        return this.remoteAddress;
    };
    AddressPairObject.prototype.getLocalAddress = function () {
        return this.localAddress;
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
        return desc.call(this);
    };
    AddressPairObject.prototype.toString = function () {
        return desc.call(this);
    };
    var address_equals = function (address1, address2) {
        if (address1) {
            return address1.equals(address2);
        } else {
            return !address2;
        }
    };
    var desc = function () {
        var cname = this.constructor.name;
        var remote = this.getRemoteAddress();
        var local = this.getLocalAddress();
        if (remote) {
            remote = remote.toString();
        }
        if (local) {
            local = local.toString();
        }
        return "<" + cname + ' remote="' + remote + '" local="' + local + '" />';
    };
    ns.type.AddressPairObject = AddressPairObject;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var Channel = Interface(null, null);
    Channel.prototype.isOpen = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.isBound = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.isAlive = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.close = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.read = function (maxLen) {
        throw new Error("NotImplemented");
    };
    Channel.prototype.write = function (src) {
        throw new Error("NotImplemented");
    };
    Channel.prototype.configureBlocking = function (block) {
        throw new Error("NotImplemented");
    };
    Channel.prototype.isBlocking = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.bind = function (local) {
        throw new Error("NotImplemented");
    };
    Channel.prototype.getLocalAddress = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.isConnected = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.connect = function (remote) {
        throw new Error("NotImplemented");
    };
    Channel.prototype.getRemoteAddress = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.disconnect = function () {
        throw new Error("NotImplemented");
    };
    Channel.prototype.receive = function (maxLen) {
        throw new Error("NotImplemented");
    };
    Channel.prototype.send = function (src, target) {
        throw new Error("NotImplemented");
    };
    ns.net.Channel = Channel;
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    var Class = sys.type.Class;
    var BaseState = fsm.BaseState;
    var ConnectionState = function (name) {
        BaseState.call(this);
        this.__name = name;
        this.__enterTime = 0;
    };
    Class(ConnectionState, BaseState, null, null);
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
            if (!other) {
                return false;
            } else {
                if (other instanceof ConnectionState) {
                    return this.__name === other.toString();
                } else {
                    return this.__name === other;
                }
            }
        }
    };
    ConnectionState.prototype.valueOf = function () {
        return this.__name;
    };
    ConnectionState.prototype.toString = function () {
        return this.__name;
    };
    ConnectionState.prototype.getName = function () {
        return this.__name;
    };
    ConnectionState.prototype.getEnterTime = function () {
        return this.__enterTime;
    };
    ConnectionState.prototype.onEnter = function (previous, machine, now) {
        this.__enterTime = now;
    };
    ConnectionState.prototype.onExit = function (next, machine, now) {
        this.__enterTime = 0;
    };
    ConnectionState.prototype.onPause = function (machine) {};
    ConnectionState.prototype.onResume = function (machine) {};
    ConnectionState.Delegate = fsm.Delegate;
    var StateBuilder = function (transitionBuilder) {
        Object.call(this);
        this.builder = transitionBuilder;
    };
    Class(StateBuilder, Object, null, {
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
    ns.net.ConnectionState = ConnectionState;
    ns.net.StateBuilder = StateBuilder;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    var Class = sys.type.Class;
    var BaseTransition = fsm.BaseTransition;
    var ConnectionState = ns.net.ConnectionState;
    var StateTransition = function (targetStateName, evaluate) {
        BaseTransition.call(this, targetStateName);
        this.__evaluate = evaluate;
    };
    Class(StateTransition, BaseTransition, null, null);
    StateTransition.prototype.evaluate = function (machine, now) {
        return this.__evaluate.call(this, machine, now);
    };
    var TransitionBuilder = function () {
        Object.call(this);
    };
    Class(TransitionBuilder, Object, null, {
        getDefaultPreparingTransition: function () {
            return new StateTransition(ConnectionState.PREPARING, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                return conn && conn.isOpen();
            });
        },
        getPreparingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                return conn && conn.isAlive();
            });
        },
        getPreparingDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                return !conn || !conn.isOpen();
            });
        },
        getReadyExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return !conn.isReceivedRecently(now);
            });
        },
        getReadyErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                return !conn || !conn.isAlive();
            });
        },
        getExpiredMaintainingTransition: function () {
            return new StateTransition(ConnectionState.MAINTAINING, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return conn.isSentRecently(now);
            });
        },
        getExpiredErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                return conn.isNotReceivedLongTimeAgo(now);
            });
        },
        getMaintainingReadyTransition: function () {
            return new StateTransition(ConnectionState.READY, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return conn.isReceivedRecently(now);
            });
        },
        getMaintainingExpiredTransition: function () {
            return new StateTransition(ConnectionState.EXPIRED, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return false;
                }
                return !conn.isSentRecently(now);
            });
        },
        getMaintainingErrorTransition: function () {
            return new StateTransition(ConnectionState.ERROR, function (
                machine,
                now
            ) {
                var conn = machine.getConnection();
                if (!conn || !conn.isAlive()) {
                    return true;
                }
                return conn.isNotReceivedLongTimeAgo(now);
            });
        },
        getErrorDefaultTransition: function () {
            return new StateTransition(ConnectionState.DEFAULT, function (
                machine,
                now
            ) {
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
    ns.net.StateTransition = StateTransition;
    ns.net.TransitionBuilder = TransitionBuilder;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    var Class = sys.type.Class;
    var Context = fsm.Context;
    var BaseMachine = fsm.BaseMachine;
    var ConnectionState = ns.net.ConnectionState;
    var StateBuilder = ns.net.StateBuilder;
    var TransitionBuilder = ns.net.TransitionBuilder;
    var StateMachine = function (connection) {
        BaseMachine.call(this, ConnectionState.DEFAULT);
        this.__connection = connection;
        var builder = this.createStateBuilder();
        add_state(this, builder.getDefaultState());
        add_state(this, builder.getPreparingState());
        add_state(this, builder.getReadyState());
        add_state(this, builder.getExpiredState());
        add_state(this, builder.getMaintainingState());
        add_state(this, builder.getErrorState());
    };
    Class(StateMachine, BaseMachine, [Context], null);
    StateMachine.prototype.createStateBuilder = function () {
        return new StateBuilder(new TransitionBuilder());
    };
    StateMachine.prototype.getConnection = function () {
        return this.__connection;
    };
    StateMachine.prototype.getContext = function () {
        return this;
    };
    var add_state = function (machine, state) {
        machine.setState(state.getName(), state);
    };
    ns.net.StateMachine = StateMachine;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    var Interface = sys.type.Interface;
    var Ticker = fsm.threading.Ticker;
    var Connection = Interface(null, [Ticker]);
    Connection.prototype.isOpen = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.isBound = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.isConnected = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.isAlive = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.getLocalAddress = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.getRemoteAddress = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.getState = function () {
        throw new Error("NotImplemented");
    };
    Connection.prototype.send = function (data) {
        throw new Error("NotImplemented");
    };
    Connection.prototype.onReceived = function (data) {
        throw new Error("NotImplemented");
    };
    Connection.prototype.close = function () {
        throw new Error("NotImplemented");
    };
    ns.net.Connection = Connection;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var ConnectionDelegate = Interface(null, null);
    ConnectionDelegate.prototype.onConnectionStateChanged = function (
        previous,
        current,
        connection
    ) {
        throw new Error("NotImplemented");
    };
    ConnectionDelegate.prototype.onConnectionReceived = function (
        data,
        connection
    ) {
        throw new Error("NotImplemented");
    };
    ConnectionDelegate.prototype.onConnectionSent = function (
        sent,
        data,
        connection
    ) {
        throw new Error("NotImplemented");
    };
    ConnectionDelegate.prototype.onConnectionFailed = function (
        error,
        data,
        connection
    ) {
        throw new Error("NotImplemented");
    };
    ConnectionDelegate.prototype.onConnectionError = function (
        error,
        connection
    ) {
        throw new Error("NotImplemented");
    };
    ns.net.ConnectionDelegate = ConnectionDelegate;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var TimedConnection = Interface(null, null);
    TimedConnection.prototype.getLastSentTime = function () {
        throw new Error("NotImplemented");
    };
    TimedConnection.prototype.getLastReceivedTime = function () {
        throw new Error("NotImplemented");
    };
    TimedConnection.prototype.isSentRecently = function () {
        throw new Error("NotImplemented");
    };
    TimedConnection.prototype.isReceivedRecently = function () {
        throw new Error("NotImplemented");
    };
    TimedConnection.prototype.isNotReceivedLongTimeAgo = function () {
        throw new Error("NotImplemented");
    };
    ns.net.TimedConnection = TimedConnection;
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;
    var Hub = Interface(null, [Processor]);
    Hub.prototype.open = function (remote, local) {
        throw new Error("NotImplemented");
    };
    Hub.prototype.connect = function (remote, local) {
        throw new Error("NotImplemented");
    };
    ns.net.Hub = Hub;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var Enum = sys.type.Enum;
    var ShipStatus = Enum(null, {
        ASSEMBLING: 0,
        EXPIRED: 1,
        NEW: 16,
        WAITING: 17,
        TIMEOUT: 18,
        DONE: 19,
        FAILED: 20
    });
    var Ship = Interface(null, null);
    Ship.prototype.getSN = function () {
        throw new Error("NotImplemented");
    };
    Ship.prototype.touch = function (now) {
        throw new Error("NotImplemented");
    };
    Ship.prototype.getStatus = function (now) {
        throw new Error("NotImplemented");
    };
    ns.port.Ship = Ship;
    ns.port.ShipStatus = ShipStatus;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var Ship = ns.port.Ship;
    var Arrival = Interface(null, [Ship]);
    Arrival.prototype.assemble = function (income) {
        throw new Error("NotImplemented");
    };
    ns.port.Arrival = Arrival;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var Enum = sys.type.Enum;
    var Ship = ns.port.Ship;
    var DeparturePriority = Enum(null, { URGENT: -1, NORMAL: 0, SLOWER: 1 });
    var Departure = Interface(null, [Ship]);
    Departure.prototype.getPriority = function () {
        throw new Error("NotImplemented");
    };
    Departure.prototype.getFragments = function () {
        throw new Error("NotImplemented");
    };
    Departure.prototype.checkResponse = function (response) {
        throw new Error("NotImplemented");
    };
    Departure.prototype.isImportant = function () {
        throw new Error("NotImplemented");
    };
    Departure.Priority = DeparturePriority;
    ns.port.Departure = Departure;
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;
    var Docker = Interface(null, [Processor]);
    Docker.prototype.isOpen = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.isAlive = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.getStatus = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.getRemoteAddress = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.getLocalAddress = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.sendData = function (payload) {
        throw new Error("NotImplemented");
    };
    Docker.prototype.sendShip = function (ship) {
        throw new Error("NotImplemented");
    };
    Docker.prototype.processReceived = function (data) {
        throw new Error("NotImplemented");
    };
    Docker.prototype.heartbeat = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.purge = function () {
        throw new Error("NotImplemented");
    };
    Docker.prototype.close = function () {
        throw new Error("NotImplemented");
    };
    ns.port.Docker = Docker;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    var Enum = sys.type.Enum;
    var DockerStatus = Enum(null, { ERROR: -1, INIT: 0, PREPARING: 1, READY: 2 });
    DockerStatus.getStatus = function (state) {
        var ConnectionState = ns.net.ConnectionState;
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var DockerDelegate = Interface(null, null);
    DockerDelegate.prototype.onDockerReceived = function (arrival, docker) {
        throw new Error("NotImplemented");
    };
    DockerDelegate.prototype.onDockerSent = function (departure, docker) {
        throw new Error("NotImplemented");
    };
    DockerDelegate.prototype.onDockerFailed = function (
        error,
        departure,
        docker
    ) {
        throw new Error("NotImplemented");
    };
    DockerDelegate.prototype.onDockerError = function (error, departure, docker) {
        throw new Error("NotImplemented");
    };
    DockerDelegate.prototype.onDockerStatusChanged = function (
        previous,
        current,
        docker
    ) {
        throw new Error("NotImplemented");
    };
    ns.port.DockerDelegate = DockerDelegate;
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;
    var Gate = Interface(null, [Processor]);
    Gate.prototype.sendData = function (payload, remote, local) {
        throw new Error("NotImplemented");
    };
    Gate.prototype.sendShip = function (outgo, remote, local) {
        throw new Error("NotImplemented");
    };
    ns.port.Gate = Gate;
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var SocketReader = Interface(null, null);
    SocketReader.prototype.read = function (maxLen) {
        throw new Error("NotImplemented");
    };
    SocketReader.prototype.receive = function (maxLen) {
        throw new Error("NotImplemented");
    };
    var SocketWriter = Interface(null, null);
    SocketWriter.prototype.write = function (src) {
        throw new Error("NotImplemented");
    };
    SocketWriter.prototype.send = function (src, target) {
        throw new Error("NotImplemented");
    };
    ns.socket.SocketReader = SocketReader;
    ns.socket.SocketWriter = SocketWriter;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
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
    Class(BaseChannel, AddressPairObject, [Channel], null);
    BaseChannel.prototype.finalize = function () {
        removeSocketChannel.call(this);
    };
    BaseChannel.prototype.createReader = function () {
        throw new Error("NotImplemented");
    };
    BaseChannel.prototype.createWriter = function () {
        throw new Error("NotImplemented");
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
        var sock = this.__sock;
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Interface = sys.type.Interface;
    var Class = sys.type.Class;
    var ChannelChecker = Interface(null, null);
    ChannelChecker.prototype.checkError = function (error, sock) {
        throw new Error("NotImplemented");
    };
    ChannelChecker.prototype.checkData = function (data, sock) {
        throw new Error("NotImplemented");
    };
    var DefaultChecker = function () {
        Object.call(this);
    };
    Class(DefaultChecker, Object, [ChannelChecker], {
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
    Class(ChannelController, Object, [ChannelChecker], null);
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var SocketReader = ns.socket.SocketReader;
    var SocketWriter = ns.socket.SocketWriter;
    var ChannelController = ns.socket.ChannelController;
    var ChannelReader = function (channel) {
        ChannelController.call(this, channel);
    };
    Class(ChannelReader, ChannelController, [SocketReader], {
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
    Class(ChannelWriter, ChannelController, [SocketWriter], {
        write: function (data) {
            var sock = this.getSocket();
            var sent = 0;
            var rest = data.length;
            var cnt;
            while (sock.isOpen()) {
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
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
    Class(
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
    BaseConnection.prototype.tick = function (now, elapsed) {
        var machine = this.getStateMachine();
        if (machine) {
            machine.tick(now, elapsed);
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var BaseConnection = ns.socket.BaseConnection;
    var ActiveConnection = function (remote, local, channel, hub) {
        BaseConnection.call(this, remote, local, channel);
        this.__hub = hub;
    };
    Class(ActiveConnection, BaseConnection, null, {
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var AddressPairMap = ns.type.AddressPairMap;
    var Hub = ns.net.Hub;
    var ConnectionPool = function () {
        AddressPairMap.call(this);
    };
    Class(ConnectionPool, AddressPairMap, null, {
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
    var BaseHub = function (delegate) {
        Object.call(this);
        this.__delegate = delegate;
        this.__connPool = this.createConnectionPool();
        this.__last = new Date().getTime();
    };
    Class(BaseHub, Object, [Hub], null);
    BaseHub.prototype.createConnectionPool = function () {
        return new ConnectionPool();
    };
    BaseHub.prototype.getDelegate = function () {
        return this.__delegate;
    };
    BaseHub.MSS = 1472;
    BaseHub.prototype.allChannels = function () {
        throw new Error("NotImplemented");
    };
    BaseHub.prototype.removeChannel = function (remote, local, channel) {
        throw new Error("NotImplemented");
    };
    BaseHub.prototype.createConnection = function (remote, local, channel) {
        throw new Error("NotImplemented");
    };
    BaseHub.prototype.allConnections = function () {
        return this.__connPool.values();
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
        for (var i = channels.length - 1; i >= 0; --i) {
            if (this.driveChannel(channels[i])) {
                ++count;
            }
        }
        return count;
    };
    BaseHub.prototype.cleanupChannels = function (channels) {
        var sock;
        for (var i = channels.length - 1; i >= 0; --i) {
            sock = channels[i];
            if (!sock.isAlive()) {
                this.removeChannel(
                    sock.getRemoteAddress(),
                    sock.getLocalAddress(),
                    sock
                );
            }
        }
    };
    BaseHub.prototype.driveConnections = function (connections) {
        var now = new Date().getTime();
        var elapsed = now - this.__last;
        for (var i = connections.length - 1; i >= 0; --i) {
            connections[i].tick(now, elapsed);
        }
        this.__last = now;
    };
    BaseHub.prototype.cleanupConnections = function (connections) {
        var conn;
        for (var i = connections.length - 1; i >= 0; --i) {
            conn = connections[i];
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
        var channels = this.allChannels();
        var count = this.driveChannels(channels);
        var connections = this.allConnections();
        this.driveConnections(connections);
        this.cleanupChannels(channels);
        this.cleanupConnections(connections);
        return count > 0;
    };
    ns.socket.BaseHub = BaseHub;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var Arrival = ns.port.Arrival;
    var ShipStatus = ns.port.ShipStatus;
    var ArrivalShip = function (now) {
        Object.call(this);
        if (!now) {
            now = new Date().getTime();
        }
        this.__expired = now + ArrivalShip.EXPIRED;
    };
    Class(ArrivalShip, Object, [Arrival], null);
    ArrivalShip.EXPIRES = 300 * 1000;
    ArrivalShip.prototype.touch = function (now) {
        this.__expired = now + ArrivalShip.EXPIRES;
    };
    ArrivalShip.prototype.getStatus = function (now) {
        if (now > this.__expired) {
            return ShipStatus.EXPIRED;
        } else {
            return ShipStatus.ASSEMBLING;
        }
    };
    ns.ArrivalShip = ArrivalShip;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var Arrays = sys.type.Arrays;
    var ShipStatus = ns.port.ShipStatus;
    var ArrivalHall = function () {
        Object.call(this);
        this.__arrivals = [];
        this.__arrival_map = {};
        this.__finished_times = {};
    };
    Class(ArrivalHall, Object, null, null);
    ArrivalHall.prototype.assembleArrival = function (income) {
        var sn = income.getSN();
        if (!sn) {
            return income;
        }
        var completed;
        var cached = this.__arrival_map[sn];
        if (cached) {
            completed = cached.assemble(income);
            if (completed) {
                Arrays.remove(this.__arrivals, cached);
                delete this.__arrival_map[sn];
                this.__finished_times[sn] = new Date().getTime();
            } else {
                cached.touch(new Date().getTime());
            }
        } else {
            var time = this.__finished_times[sn];
            if (time && time > 0) {
                return null;
            }
            completed = income.assemble(income);
            if (!completed) {
                this.__arrivals.push(income);
                this.__arrival_map[sn] = income;
            }
        }
        return completed;
    };
    ArrivalHall.prototype.purge = function () {
        var now = new Date().getTime();
        var ship;
        var sn;
        for (var i = this.__arrivals.length - 1; i >= 0; --i) {
            ship = this.__arrivals[i];
            if (ship.getStatus(now).equals(ShipStatus.EXPIRED)) {
                this.__arrivals.splice(i, 1);
                sn = ship.getSN();
                if (sn) {
                    delete this.__arrival_map[sn];
                }
            }
        }
        var ago = now - 3600 * 1000;
        var when;
        var keys = Object.keys(this.__finished_times);
        for (var j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__finished_times[sn];
            if (!when || when < ago) {
                delete this.__finished_times[sn];
            }
        }
    };
    ns.ArrivalHall = ArrivalHall;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var Enum = sys.type.Enum;
    var Departure = ns.port.Departure;
    var ShipStatus = ns.port.ShipStatus;
    var DepartureShip = function (priority, maxTries) {
        Object.call(this);
        if (priority === null) {
            priority = 0;
        } else {
            if (Enum.isEnum(priority)) {
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
    Class(DepartureShip, Object, [Departure], {
        getPriority: function () {
            return this.__priority;
        },
        touch: function (now) {
            this.__expired = now + DepartureShip.EXPIRES;
            this.__tries -= 1;
        },
        getStatus: function (now) {
            var fragments = this.getFragments();
            if (!fragments || fragments.length === 0) {
                return ShipStatus.DONE;
            } else {
                if (this.__expired === 0) {
                    return ShipStatus.NEW;
                } else {
                    if (now < this.__expired) {
                        return ShipStatus.WAITING;
                    } else {
                        if (this.__tries > 0) {
                            return ShipStatus.TIMEOUT;
                        } else {
                            return ShipStatus.FAILED;
                        }
                    }
                }
            }
        }
    });
    DepartureShip.EXPIRES = 120 * 1000;
    DepartureShip.RETRIES = 2;
    ns.DepartureShip = DepartureShip;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var Arrays = sys.type.Arrays;
    var ShipStatus = ns.port.ShipStatus;
    var DepartureHall = function () {
        Object.call(this);
        this.__all_departures = [];
        this.__new_departures = [];
        this.__fleets = {};
        this.__priorities = [];
        this.__departure_map = {};
        this.__departure_level = {};
        this.__finished_times = {};
    };
    Class(DepartureHall, Object, null, null);
    DepartureHall.prototype.addDeparture = function (outgo) {
        if (this.__all_departures.indexOf(outgo) >= 0) {
            return false;
        } else {
            this.__all_departures.push(outgo);
        }
        var priority = outgo.getPriority();
        var index;
        for (index = 0; index < this.__new_departures.length; ++index) {
            if (this.__new_departures[index].getPriority() > priority) {
                break;
            }
        }
        Arrays.insert(this.__new_departures, index, outgo);
        return true;
    };
    DepartureHall.prototype.checkResponse = function (response) {
        var sn = response.getSN();
        var time = this.__finished_times[sn];
        if (time && time > 0) {
            return null;
        }
        var ship = this.__departure_map[sn];
        if (ship && ship.checkResponse(response)) {
            removeShip.call(this, ship, sn);
            this.__finished_times[sn] = new Date().getTime();
            return ship;
        }
        return null;
    };
    var removeShip = function (ship, sn) {
        var priority = this.__departure_level[sn];
        var fleet = this.__fleets[priority];
        if (fleet) {
            Arrays.remove(fleet, ship);
            if (fleet.length === 0) {
                delete this.__fleets[priority];
            }
        }
        delete this.__departure_map[sn];
        delete this.__departure_level[sn];
        Arrays.remove(this.__all_departures, ship);
    };
    DepartureHall.prototype.getNextDeparture = function (now) {
        var next = getNextNewDeparture.call(this, now);
        if (!next) {
            next = getNextTimeoutDeparture.call(this, now);
        }
        return next;
    };
    var getNextNewDeparture = function (now) {
        if (this.__new_departures.length === 0) {
            return null;
        }
        var outgo = this.__new_departures.shift();
        var sn = outgo.getSN();
        if (outgo.isImportant() && sn) {
            var priority = outgo.getPriority();
            insertShip.call(this, outgo, priority, sn);
            this.__departure_map[sn] = outgo;
        } else {
            Arrays.remove(this.__all_departures, outgo);
        }
        outgo.touch(now);
        return outgo;
    };
    var insertShip = function (outgo, priority, sn) {
        var fleet = this.__fleets[priority];
        if (!fleet) {
            fleet = [];
            this.__fleets[priority] = fleet;
            insertPriority.call(this, priority);
        }
        fleet.push(outgo);
        this.__departure_level[sn] = priority;
    };
    var insertPriority = function (priority) {
        var index, value;
        for (index = 0; index < this.__priorities.length; ++index) {
            value = this.__priorities[index];
            if (value === priority) {
                return;
            } else {
                if (value > priority) {
                    break;
                }
            }
        }
        Arrays.insert(this.__priorities, index, priority);
    };
    var getNextTimeoutDeparture = function (now) {
        var priorityList = this.__priorities.slice();
        var prior;
        var fleet, ship, sn, status;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            prior = priorityList[i];
            fleet = this.__fleets[prior];
            if (!fleet) {
                continue;
            }
            for (j = 0; j < fleet.length; ++j) {
                ship = fleet[j];
                sn = ship.getSN();
                status = ship.getStatus(now);
                if (status.equals(ShipStatus.TIMEOUT)) {
                    fleet.splice(j, 1);
                    insertShip.call(this, ship, prior + 1, sn);
                    ship.touch(now);
                    return ship;
                } else {
                    if (status.equals(ShipStatus.FAILED)) {
                        fleet.splice(j, 1);
                        delete this.__departure_map[sn];
                        delete this.__departure_level[sn];
                        Arrays.remove(this.__all_departures, ship);
                        return ship;
                    }
                }
            }
        }
        return null;
    };
    DepartureHall.prototype.purge = function () {
        var now = new Date().getTime();
        var prior;
        var fleet, ship, sn;
        var i, j;
        for (i = this.__priorities.length - 1; i >= 0; --i) {
            prior = this.__priorities[i];
            fleet = this.__fleets[prior];
            if (!fleet) {
                this.__priorities.splice(i, 1);
                continue;
            }
            for (j = fleet.length - 1; j >= 0; --j) {
                ship = fleet[j];
                if (ship.getStatus(now).equals(ShipStatus.DONE)) {
                    fleet.splice(j, 1);
                    sn = ship.getSN();
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    this.__finished_times[sn] = now;
                }
            }
            if (fleet.length === 0) {
                delete this.__fleets[prior];
                this.__priorities.splice(i, 1);
            }
        }
        var ago = now - 3600 * 1000;
        var keys = Object.keys(this.__finished_times);
        var when;
        for (j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__finished_times[sn];
            if (!when || when < ago) {
                delete this.__finished_times[sn];
            }
        }
    };
    ns.DepartureHall = DepartureHall;
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var ArrivalHall = ns.ArrivalHall;
    var DepartureHall = ns.DepartureHall;
    var Dock = function () {
        Object.call(this);
        this.__arrivalHall = this.createArrivalHall();
        this.__departureHall = this.createDepartureHall();
    };
    Class(Dock, Object, null, null);
    Dock.prototype.createArrivalHall = function () {
        return new ArrivalHall();
    };
    Dock.prototype.createDepartureHall = function () {
        return new DepartureHall();
    };
    Dock.prototype.assembleArrival = function (income) {
        return this.__arrivalHall.assembleArrival(income);
    };
    Dock.prototype.addDeparture = function (outgo) {
        return this.__departureHall.addDeparture(outgo);
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var AddressPairObject = ns.type.AddressPairObject;
    var ShipStatus = ns.port.ShipStatus;
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
    Class(StarDocker, AddressPairObject, [Docker], null);
    StarDocker.prototype.finalize = function () {
        removeConnection.call(this);
        this.__dock = null;
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
        return this.__dock.addDeparture(ship);
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
        throw new Error("NotImplemented");
    };
    StarDocker.prototype.checkArrival = function (income) {
        throw new Error("NotImplemented");
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
                if (outgo.getStatus(now).equals(ShipStatus.FAILED)) {
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
})(StarTrek, MONKEY);
(function (ns, sys) {
    var Class = sys.type.Class;
    var AddressPairMap = ns.type.AddressPairMap;
    var ConnectionDelegate = ns.net.ConnectionDelegate;
    var ConnectionState = ns.net.ConnectionState;
    var DockerStatus = ns.port.DockerStatus;
    var Gate = ns.port.Gate;
    var DockerPool = function () {
        AddressPairMap.call(this);
    };
    Class(DockerPool, AddressPairMap, null, {
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
    var StarGate = function (delegate) {
        Object.call(this);
        this.__delegate = delegate;
        this.__dockerPool = this.createDockerPool();
    };
    Class(StarGate, Object, [Gate, ConnectionDelegate], null);
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
        throw new Error("NotImplemented");
    };
    StarGate.prototype.allDockers = function () {
        return this.__dockerPool.values();
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
        var dockers = this.allDockers();
        var count = this.driveDockers(dockers);
        this.cleanupDockers(dockers);
        return count > 0;
    };
    StarGate.prototype.driveDockers = function (dockers) {
        var count = 0;
        for (var i = dockers.length - 1; i >= 0; --i) {
            if (dockers[i].process()) {
                ++count;
            }
        }
        return count;
    };
    StarGate.prototype.cleanupDockers = function (dockers) {
        var worker;
        for (var i = dockers.length - 1; i >= 0; --i) {
            worker = dockers[i];
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
                changed = !!s2;
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
        if (worker) {
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
        throw new Error("NotImplemented");
    };
    StarGate.prototype.clearAdvanceParty = function (connection) {
        throw new Error("NotImplemented");
    };
    ns.StarGate = StarGate;
})(StarTrek, MONKEY);
