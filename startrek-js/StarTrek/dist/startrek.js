/**
 * Star Trek: Interstellar Transport (v1.0.0)
 *
 * @author    moKy <albert.moky at gmail.com>
 * @date      Nov. 22, 2024
 * @copyright (c) 2024 Albert Moky
 * @license   {@link https://mit-license.org | MIT License}
 */;
if (typeof StarTrek !== 'object') {
    StarTrek = {}
}
(function (ns) {
    'use strict';
    if (typeof ns.type !== 'object') {
        ns.type = {}
    }
    if (typeof ns.net !== 'object') {
        ns.net = {}
    }
    if (typeof ns.port !== 'object') {
        ns.port = {}
    }
    if (typeof ns.socket !== 'object') {
        ns.socket = {}
    }
})(StarTrek);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Class = sys.type.Class;
    var Stringer = sys.type.Stringer;
    var ConstantString = sys.type.ConstantString;
    var SocketAddress = Interface(null, [Stringer]);
    SocketAddress.prototype.getHost = function () {
    };
    SocketAddress.prototype.getPort = function () {
    };
    var InetSocketAddress = function (host, port) {
        ConstantString.call(this, '(' + host + ':' + port + ')');
        this.__host = host;
        this.__port = port
    };
    Class(InetSocketAddress, ConstantString, [SocketAddress], null);
    InetSocketAddress.prototype.getHost = function () {
        return this.__host
    };
    InetSocketAddress.prototype.getPort = function () {
        return this.__port
    };
    ns.type.SocketAddress = SocketAddress;
    ns.type.InetSocketAddress = InetSocketAddress
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var PairMap = Interface(null, null);
    PairMap.prototype.items = function () {
    };
    PairMap.prototype.get = function (remote, local) {
    };
    PairMap.prototype.set = function (remote, local, value) {
    };
    PairMap.prototype.remove = function (remote, local, value) {
    };
    ns.type.PairMap = PairMap
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var PairMap = ns.type.PairMap;
    var AbstractPairMap = function (any) {
        Object.call(this);
        this.__default = any;
        this.__map = {}
    };
    Class(AbstractPairMap, Object, [PairMap], null);
    AbstractPairMap.prototype.get = function (remote, local) {
        var key_pair = get_keys(remote, local, null);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        if (!table) {
            return null
        }
        var value;
        if (key2) {
            value = table[key2];
            if (value) {
                return value
            }
            return table[this.__default]
        }
        value = table[this.__default];
        if (value) {
            return value
        }
        var addresses = Object.keys(table);
        for (var i = 0; i < addresses.length; ++i) {
            value = table[addresses[i]];
            if (value) {
                return value
            }
        }
        return null
    };
    AbstractPairMap.prototype.set = function (remote, local, value) {
        var key_pair = get_keys(remote, local, this.__default);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        var old = null;
        if (table) {
            old = table[key2];
            if (value) {
                table[key2] = value
            } else if (old) {
                delete table[key2]
            }
        } else if (value) {
            table = {};
            table[key2] = value;
            this.__map[key1] = table
        }
        return old
    };
    AbstractPairMap.prototype.remove = function (remote, local, value) {
        var key_pair = get_keys(remote, local, this.__default);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        if (!table) {
            return null
        }
        var old = table[key2];
        if (old) {
            delete table[key2];
            if (Object.keys(table).length === 0) {
                delete this.__map[key1]
            }
        }
        return old ? old : value
    };
    var get_keys = function (remote, local, any) {
        if (!remote) {
            return [local, any]
        } else if (!local) {
            return [remote, any]
        } else {
            return [remote, local]
        }
    };
    ns.type.AbstractPairMap = AbstractPairMap
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Class = sys.type.Class;
    var IObject = sys.type.Object;
    var HashSet = sys.type.HashSet;
    var AbstractPairMap = ns.type.AbstractPairMap;
    var HashPairMap = function (any) {
        AbstractPairMap.call(this, any);
        this.__items = new HashSet()
    };
    Class(HashPairMap, AbstractPairMap, null, null);
    HashPairMap.prototype.items = function () {
        return this.__items.toArray()
    };
    HashPairMap.prototype.set = function (remote, local, value) {
        if (value) {
            this.__items.remove(value);
            this.__items.add(value)
        }
        var old = AbstractPairMap.prototype.set.call(this, remote, local, value);
        if (old && !object_equals(old, value)) {
            this.__items.remove(old)
        }
        return old
    };
    HashPairMap.prototype.remove = function (remote, local, value) {
        var old = AbstractPairMap.prototype.remove.call(this, remote, local, value);
        if (old) {
            this.__items.remove(old)
        }
        if (value && !object_equals(value, old)) {
            this.__items.remove(value)
        }
        return old ? old : value
    };
    var object_equals = function (a, b) {
        if (!a) {
            return !b
        } else if (!b) {
            return false
        } else if (a === b) {
            return true
        } else if (Interface.conforms(a, IObject)) {
            return a.equals(b)
        } else if (Interface.conforms(b, IObject)) {
            return b.equals(a)
        } else {
            return false
        }
    };
    ns.type.HashPairMap = HashPairMap
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var InetSocketAddress = ns.type.InetSocketAddress;
    var HashPairMap = ns.type.HashPairMap;
    var AnyAddress = new InetSocketAddress('0.0.0.0', 0);
    var AddressPairMap = function () {
        HashPairMap.call(this, AnyAddress)
    };
    Class(AddressPairMap, HashPairMap, null, null);
    AddressPairMap.AnyAddress = AnyAddress;
    ns.type.AddressPairMap = AddressPairMap
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var BaseObject = sys.type.BaseObject;
    var AddressPairObject = function (remote, local) {
        BaseObject.call(this);
        this.remoteAddress = remote;
        this.localAddress = local
    };
    Class(AddressPairObject, BaseObject, null, null);
    AddressPairObject.prototype.getRemoteAddress = function () {
        return this.remoteAddress
    };
    AddressPairObject.prototype.getLocalAddress = function () {
        return this.localAddress
    };
    AddressPairObject.prototype.equals = function (other) {
        if (!other) {
            return this.isEmpty()
        } else if (other === this) {
            return true
        } else if (other instanceof AddressPairObject) {
            return address_equals(other.getRemoteAddress(), this.remoteAddress) && address_equals(other.getLocalAddress(), this.localAddress)
        } else {
            return false
        }
    };
    AddressPairObject.prototype.isEmpty = function () {
        return !(this.remoteAddress || this.localAddress)
    };
    AddressPairObject.prototype.valueOf = function () {
        return desc.call(this)
    };
    AddressPairObject.prototype.toString = function () {
        return desc.call(this)
    };
    var address_equals = function (a, b) {
        if (!a) {
            return !b
        } else if (!b) {
            return false
        } else if (a === b) {
            return true
        } else {
            return a.equals(b)
        }
    };
    var desc = function () {
        var cname = this.constructor.name;
        var remote = this.getRemoteAddress();
        var local = this.getLocalAddress();
        if (remote) {
            remote = remote.toString()
        }
        if (local) {
            local = local.toString()
        }
        return '<' + cname + ' remote="' + remote + '" local="' + local + '" />'
    };
    ns.type.AddressPairObject = AddressPairObject
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Enum = sys.type.Enum;
    var ChannelStateOrder = Enum('ChannelState', {INIT: 0, OPEN: 1, ALIVE: 2, CLOSED: 3});
    var Channel = Interface(null, null);
    Channel.prototype.getState = function () {
    };
    Channel.prototype.isOpen = function () {
    };
    Channel.prototype.isBound = function () {
    };
    Channel.prototype.isAlive = function () {
    };
    Channel.prototype.isAvailable = function () {
    };
    Channel.prototype.isVacant = function () {
    };
    Channel.prototype.close = function () {
    };
    Channel.prototype.read = function (maxLen) {
    };
    Channel.prototype.write = function (src) {
    };
    Channel.prototype.configureBlocking = function (block) {
    };
    Channel.prototype.isBlocking = function () {
    };
    Channel.prototype.bind = function (local) {
    };
    Channel.prototype.getLocalAddress = function () {
    };
    Channel.prototype.isConnected = function () {
    };
    Channel.prototype.connect = function (remote) {
    };
    Channel.prototype.getRemoteAddress = function () {
    };
    Channel.prototype.disconnect = function () {
    };
    Channel.prototype.receive = function (maxLen) {
    };
    Channel.prototype.send = function (src, target) {
    };
    ns.net.Channel = Channel;
    ns.net.ChannelStateOrder = ChannelStateOrder
})(StarTrek, MONKEY);
(function (ns) {
    'use strict';
    ns.net.SocketHelper = {
        socketGetLocalAddress: function (sock) {
            return sock.getRemoteAddress()
        }, socketGetRemoteAddress: function (sock) {
            return sock.getLocalAddress()
        }, socketIsBlocking: function (sock) {
            return sock.isBlocking()
        }, socketIsConnected: function (sock) {
            return sock.isConnected()
        }, socketIsBound: function (sock) {
            return sock.isBound()
        }, socketIsClosed: function (sock) {
            return !sock.isOpen()
        }, socketIsAvailable: function (sock) {
            return sock.isAlive()
        }, socketIsVacant: function (sock) {
            return sock.isAlive()
        }, socketSend: function (sock, data) {
            return sock.write(data)
        }, socketReceive: function (sock, maxLen) {
            return sock.read(maxLen)
        }, socketBind: function (sock, local) {
            return sock.bind(local)
        }, socketConnect: function (sock, remote) {
            return sock.connect(remote)
        }, socketDisconnect: function (sock) {
            return sock.close()
        }
    }
})(StarTrek);
(function (ns, fsm, sys) {
    'use strict';
    var Class = sys.type.Class;
    var Enum = sys.type.Enum;
    var BaseState = fsm.BaseState;
    var StateOrder = Enum('ConnectionState', {
        DEFAULT: 0,
        PREPARING: 1,
        READY: 2,
        MAINTAINING: 3,
        EXPIRED: 4,
        ERROR: 5
    });
    var ConnectionState = function (order) {
        BaseState.call(this, Enum.getInt(order));
        this.__name = order.getName();
        this.__enterTime = null
    };
    Class(ConnectionState, BaseState, null, {
        getName: function () {
            return this.__name
        }, getEnterTime: function () {
            return this.__enterTime
        }, toString: function () {
            return this.__name
        }, valueOf: function () {
            return this.__name
        }, equals: function (other) {
            if (other instanceof ConnectionState) {
                if (other === this) {
                    return true
                }
                other = other.getIndex()
            } else if (other instanceof StateOrder) {
                other = other.getValue()
            }
            return this.getIndex() === other
        }
    });
    ConnectionState.prototype.onEnter = function (previous, ctx, now) {
        this.__enterTime = now
    };
    ConnectionState.prototype.onExit = function (next, ctx, now) {
        this.__enterTime = null
    };
    ConnectionState.prototype.onPause = function (ctx, now) {
    };
    ConnectionState.prototype.onResume = function (ctx, now) {
    };
    ConnectionState.Delegate = fsm.Delegate;
    var StateBuilder = function (transitionBuilder) {
        Object.call(this);
        this.builder = transitionBuilder
    };
    Class(StateBuilder, Object, null, {
        getDefaultState: function () {
            var state = new ConnectionState(StateOrder.DEFAULT);
            state.addTransition(this.builder.getDefaultPreparingTransition());
            return state
        }, getPreparingState: function () {
            var state = new ConnectionState(StateOrder.PREPARING);
            state.addTransition(this.builder.getPreparingReadyTransition());
            state.addTransition(this.builder.getPreparingDefaultTransition());
            return state
        }, getReadyState: function () {
            var state = new ConnectionState(StateOrder.READY);
            state.addTransition(this.builder.getReadyExpiredTransition());
            state.addTransition(this.builder.getReadyErrorTransition());
            return state
        }, getExpiredState: function () {
            var state = new ConnectionState(StateOrder.EXPIRED);
            state.addTransition(this.builder.getExpiredMaintainingTransition());
            state.addTransition(this.builder.getExpiredErrorTransition());
            return state
        }, getMaintainingState: function () {
            var state = new ConnectionState(StateOrder.MAINTAINING);
            state.addTransition(this.builder.getMaintainingReadyTransition());
            state.addTransition(this.builder.getMaintainingExpiredTransition());
            state.addTransition(this.builder.getMaintainingErrorTransition());
            return state
        }, getErrorState: function () {
            var state = new ConnectionState(StateOrder.ERROR);
            state.addTransition(this.builder.getErrorDefaultTransition());
            return state
        }
    });
    ns.net.ConnectionState = ConnectionState;
    ns.net.ConnectionStateBuilder = StateBuilder;
    ns.net.ConnectionStateOrder = StateOrder
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Class = sys.type.Class;
    var Enum = sys.type.Enum;
    var BaseTransition = fsm.BaseTransition;
    var StateOrder = ns.net.ConnectionStateOrder;
    var StateTransition = function (order, evaluate) {
        BaseTransition.call(this, Enum.getInt(order));
        this.__evaluate = evaluate
    };
    Class(StateTransition, BaseTransition, null, null);
    StateTransition.prototype.evaluate = function (ctx, now) {
        return this.__evaluate.call(this, ctx, now)
    };
    var TransitionBuilder = function () {
        Object.call(this)
    };
    Class(TransitionBuilder, Object, null, {
        getDefaultPreparingTransition: function () {
            return new StateTransition(StateOrder.PREPARING, function (ctx, now) {
                var conn = ctx.getConnection();
                return conn && conn.isOpen()
            })
        }, getPreparingReadyTransition: function () {
            return new StateTransition(StateOrder.READY, function (ctx, now) {
                var conn = ctx.getConnection();
                return conn && conn.isAlive()
            })
        }, getPreparingDefaultTransition: function () {
            return new StateTransition(StateOrder.DEFAULT, function (ctx, now) {
                var conn = ctx.getConnection();
                return !(conn && conn.isOpen())
            })
        }, getReadyExpiredTransition: function () {
            return new StateTransition(StateOrder.EXPIRED, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return !conn.isReceivedRecently(now)
            })
        }, getReadyErrorTransition: function () {
            return new StateTransition(StateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                return !(conn && conn.isAlive())
            })
        }, getExpiredMaintainingTransition: function () {
            return new StateTransition(StateOrder.MAINTAINING, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return conn.isSentRecently(now)
            })
        }, getExpiredErrorTransition: function () {
            return new StateTransition(StateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return true
                }
                return conn.isNotReceivedLongTimeAgo(now)
            })
        }, getMaintainingReadyTransition: function () {
            return new StateTransition(StateOrder.READY, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return conn.isReceivedRecently(now)
            })
        }, getMaintainingExpiredTransition: function () {
            return new StateTransition(StateOrder.EXPIRED, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return !conn.isSentRecently(now)
            })
        }, getMaintainingErrorTransition: function () {
            return new StateTransition(StateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return true
                }
                return conn.isNotReceivedLongTimeAgo(now)
            })
        }, getErrorDefaultTransition: function () {
            return new StateTransition(StateOrder.DEFAULT, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                var current = ctx.getCurrentState();
                var enter = current.getEnterTime();
                if (!enter) {
                    return true
                }
                var last = conn.getLastReceivedTime();
                return last && enter.getTime() < last.getTime()
            })
        }
    });
    ns.net.ConnectionStateTransition = StateTransition;
    ns.net.ConnectionStateTransitionBuilder = TransitionBuilder
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Class = sys.type.Class;
    var Context = fsm.Context;
    var BaseMachine = fsm.BaseMachine;
    var StateMachine = function (connection) {
        BaseMachine.call(this);
        this.__connection = connection;
        var builder = this.createStateBuilder();
        this.addState(builder.getDefaultState());
        this.addState(builder.getPreparingState());
        this.addState(builder.getReadyState());
        this.addState(builder.getExpiredState());
        this.addState(builder.getMaintainingState());
        this.addState(builder.getErrorState())
    };
    Class(StateMachine, BaseMachine, [Context], null);
    StateMachine.prototype.createStateBuilder = function () {
        var stb = new ns.net.ConnectionStateTransitionBuilder();
        return new ns.net.ConnectionStateBuilder(stb)
    };
    StateMachine.prototype.getConnection = function () {
        return this.__connection
    };
    StateMachine.prototype.getContext = function () {
        return this
    };
    ns.net.ConnectionStateMachine = StateMachine
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Ticker = fsm.threading.Ticker;
    var Connection = Interface(null, [Ticker]);
    Connection.prototype.isOpen = function () {
    };
    Connection.prototype.isBound = function () {
    };
    Connection.prototype.isConnected = function () {
    };
    Connection.prototype.isAlive = function () {
    };
    Connection.prototype.isAvailable = function () {
    };
    Connection.prototype.isVacant = function () {
    };
    Connection.prototype.getLocalAddress = function () {
    };
    Connection.prototype.getRemoteAddress = function () {
    };
    Connection.prototype.getState = function () {
    };
    Connection.prototype.sendData = function (data) {
    };
    Connection.prototype.onReceivedData = function (data) {
    };
    Connection.prototype.close = function () {
    };
    ns.net.Connection = Connection
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var ConnectionDelegate = Interface(null, null);
    ConnectionDelegate.prototype.onConnectionStateChanged = function (previous, current, connection) {
    };
    ConnectionDelegate.prototype.onConnectionReceived = function (data, connection) {
    };
    ConnectionDelegate.prototype.onConnectionSent = function (sent, data, connection) {
    };
    ConnectionDelegate.prototype.onConnectionFailed = function (error, data, connection) {
    };
    ConnectionDelegate.prototype.onConnectionError = function (error, connection) {
    };
    ns.net.ConnectionDelegate = ConnectionDelegate
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var TimedConnection = Interface(null, null);
    TimedConnection.prototype.getLastSentTime = function () {
    };
    TimedConnection.prototype.getLastReceivedTime = function () {
    };
    TimedConnection.prototype.isSentRecently = function (now) {
    };
    TimedConnection.prototype.isReceivedRecently = function (now) {
    };
    TimedConnection.prototype.isNotReceivedLongTimeAgo = function (now) {
    };
    ns.net.TimedConnection = TimedConnection
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;
    var Hub = Interface(null, [Processor]);
    Hub.prototype.open = function (remote, local) {
    };
    Hub.prototype.connect = function (remote, local) {
    };
    ns.net.Hub = Hub
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Enum = sys.type.Enum;
    var ShipStatus = Enum('ShipStatus', {
        ASSEMBLING: (0x00),
        EXPIRED: (0x01),
        NEW: (0x10),
        WAITING: (0x11),
        TIMEOUT: (0x12),
        DONE: (0x13),
        FAILED: (0x14)
    });
    var Ship = Interface(null, null);
    Ship.prototype.getSN = function () {
    };
    Ship.prototype.touch = function (now) {
    };
    Ship.prototype.getStatus = function (now) {
    };
    ns.port.Ship = Ship;
    ns.port.ShipStatus = ShipStatus
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Ship = ns.port.Ship;
    var Arrival = Interface(null, [Ship]);
    Arrival.prototype.assemble = function (income) {
    };
    ns.port.Arrival = Arrival
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Enum = sys.type.Enum;
    var Ship = ns.port.Ship;
    var DeparturePriority = Enum('Priority', {URGENT: -1, NORMAL: 0, SLOWER: 1});
    var Departure = Interface(null, [Ship]);
    Departure.prototype.getPriority = function () {
    };
    Departure.prototype.getFragments = function () {
    };
    Departure.prototype.checkResponse = function (response) {
    };
    Departure.prototype.isImportant = function () {
    };
    Departure.Priority = DeparturePriority;
    ns.port.Departure = Departure
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;
    var Porter = Interface(null, [Processor]);
    Porter.prototype.isOpen = function () {
    };
    Porter.prototype.isAlive = function () {
    };
    Porter.prototype.getStatus = function () {
    };
    Porter.prototype.getRemoteAddress = function () {
    };
    Porter.prototype.getLocalAddress = function () {
    };
    Porter.prototype.sendData = function (payload) {
    };
    Porter.prototype.sendShip = function (ship) {
    };
    Porter.prototype.processReceived = function (data) {
    };
    Porter.prototype.heartbeat = function () {
    };
    Porter.prototype.purge = function (now) {
    };
    Porter.prototype.close = function () {
    };
    ns.port.Porter = Porter
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    'use strict';
    var Enum = sys.type.Enum;
    var StateOrder = ns.net.ConnectionStateOrder;
    var PorterStatus = Enum('PorterStatus', {ERROR: -1, INIT: 0, PREPARING: 1, READY: 2});
    PorterStatus.getStatus = function (state) {
        if (!state) {
            return PorterStatus.ERROR
        }
        var index = state.getIndex();
        if (StateOrder.READY.equals(index) || StateOrder.EXPIRED.equals(index) || StateOrder.MAINTAINING.equals(index)) {
            return PorterStatus.READY
        } else if (StateOrder.PREPARING.equals(index)) {
            return PorterStatus.PREPARING
        } else if (StateOrder.ERROR.equals(index)) {
            return PorterStatus.ERROR
        } else {
            return PorterStatus.INIT
        }
    };
    ns.port.PorterStatus = PorterStatus
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var PorterDelegate = Interface(null, null);
    PorterDelegate.prototype.onPorterReceived = function (arrival, porter) {
    };
    PorterDelegate.prototype.onPorterSent = function (departure, porter) {
    };
    PorterDelegate.prototype.onPorterFailed = function (error, departure, porter) {
    };
    PorterDelegate.prototype.onPorterError = function (error, departure, porter) {
    };
    PorterDelegate.prototype.onPorterStatusChanged = function (previous, current, porter) {
    };
    ns.port.PorterDelegate = PorterDelegate
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var Processor = fsm.skywalker.Processor;
    var Gate = Interface(null, [Processor]);
    Gate.prototype.sendData = function (payload, remote, local) {
    };
    Gate.prototype.sendShip = function (outgo, remote, local) {
    };
    ns.port.Gate = Gate
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var AddressPairObject = ns.type.AddressPairObject;
    var Channel = ns.net.Channel;
    var ChannelStateOrder = ns.net.ChannelStateOrder;
    var SocketHelper = ns.net.SocketHelper;
    var BaseChannel = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__reader = this.createReader();
        this.__writer = this.createWriter();
        this.__sock = null;
        this.__closed = -1
    };
    Class(BaseChannel, AddressPairObject, [Channel], {
        toString: function () {
            var clazz = this.getClassName();
            var remote = this.getRemoteAddress();
            var local = this.getLocalAddress();
            var closed = !this.isOpen();
            var bound = this.isBound();
            var connected = this.isConnected();
            var sock = this.getSocket();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '"' + ' closed=' + closed + ' bound=' + bound + ' connected=' + connected + '>\n\t' + sock + '\n</' + clazz + '>'
        }
    });
    BaseChannel.prototype.createReader = function () {
    };
    BaseChannel.prototype.createWriter = function () {
    };
    BaseChannel.prototype.getReader = function () {
        return this.__reader
    };
    BaseChannel.prototype.getWriter = function () {
        return this.__writer
    };
    BaseChannel.prototype.getSocket = function () {
        return this.__sock
    };
    BaseChannel.prototype.setSocket = function (sock) {
        var old = this.__sock;
        if (sock) {
            this.__sock = sock;
            this.__closed = 0
        } else {
            this.__sock = null;
            this.__closed = 1
        }
        if (old && old !== sock) {
            SocketHelper.socketDisconnect(old)
        }
    };
    BaseChannel.prototype.getState = function () {
        if (this.__closed < 0) {
            return ChannelStateOrder.INIT
        }
        var sock = this.getSocket();
        if (!sock || SocketHelper.socketIsClosed(sock)) {
            return ChannelStateOrder.CLOSED
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            return ChannelStateOrder.ALIVE
        } else {
            return ChannelStateOrder.OPEN
        }
    };
    BaseChannel.prototype.isOpen = function () {
        if (this.__closed < 0) {
            return true
        }
        var sock = this.getSocket();
        return sock && !SocketHelper.socketIsClosed(sock)
    };
    BaseChannel.prototype.isBound = function () {
        var sock = this.getSocket();
        return sock && SocketHelper.socketIsBound(sock)
    };
    BaseChannel.prototype.isConnected = function () {
        var sock = this.getSocket();
        return sock && SocketHelper.socketIsConnected(sock)
    };
    BaseChannel.prototype.isAlive = function () {
        return this.isOpen() && (this.isConnected() || this.isBound())
    };
    BaseChannel.prototype.isAvailable = function () {
        var sock = this.getSocket();
        if (!sock || SocketHelper.socketIsClosed(sock)) {
            return false
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            return this.checkAvailable(sock)
        } else {
            return false
        }
    };
    BaseChannel.prototype.checkAvailable = function (sock) {
        return SocketHelper.socketIsAvailable(sock)
    };
    BaseChannel.prototype.isVacant = function () {
        var sock = this.getSocket();
        if (!sock || SocketHelper.socketIsClosed(sock)) {
            return false
        } else if (SocketHelper.socketIsConnected(sock) || SocketHelper.socketIsBound(sock)) {
            return this.checkVacant(sock)
        } else {
            return false
        }
    };
    BaseChannel.prototype.checkVacant = function (sock) {
        return SocketHelper.socketIsVacant(sock)
    };
    BaseChannel.prototype.isBlocking = function () {
        var sock = this.getSocket();
        return sock && SocketHelper.socketIsBlocking(sock)
    };
    BaseChannel.prototype.configureBlocking = function (block) {
        var sock = this.getSocket();
        sock.configureBlocking(block);
        return sock
    };
    BaseChannel.prototype.doBind = function (sock, local) {
        return SocketHelper.socketBind(sock, local)
    };
    BaseChannel.prototype.doConnect = function (sock, remote) {
        return SocketHelper.socketConnect(sock, remote)
    };
    BaseChannel.prototype.doDisconnect = function (sock) {
        return SocketHelper.socketDisconnect(sock)
    };
    BaseChannel.prototype.bind = function (local) {
        var sock = this.getSocket();
        if (sock) {
            this.doBind(sock, local)
        }
        this.localAddress = local;
        return sock
    };
    BaseChannel.prototype.connect = function (remote) {
        var sock = this.getSocket();
        if (sock) {
            this.doConnect(sock, remote)
        }
        this.remoteAddress = remote;
        return sock
    };
    BaseChannel.prototype.disconnect = function () {
        var sock = this.getSocket();
        if (sock) {
            this.doDisconnect(sock)
        }
        return sock
    };
    BaseChannel.prototype.close = function () {
        this.setSocket(null)
    };
    BaseChannel.prototype.read = function (maxLen) {
        try {
            return this.getReader().read(maxLen)
        } catch (e) {
            this.close();
            throw e;
        }
    };
    BaseChannel.prototype.write = function (src) {
        try {
            return this.getWriter().write(src)
        } catch (e) {
            this.close();
            throw e;
        }
    };
    BaseChannel.prototype.receive = function (maxLen) {
        try {
            return this.getReader().receive(maxLen)
        } catch (e) {
            this.close();
            throw e;
        }
    };
    BaseChannel.prototype.send = function (src, target) {
        try {
            return this.getWriter().send(src, target)
        } catch (e) {
            this.close();
            throw e;
        }
    };
    ns.socket.BaseChannel = BaseChannel
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Interface = sys.type.Interface;
    var SocketReader = Interface(null, null);
    SocketReader.prototype.read = function (maxLen) {
    };
    SocketReader.prototype.receive = function (maxLen) {
    };
    var SocketWriter = Interface(null, null);
    SocketWriter.prototype.write = function (src) {
    };
    SocketWriter.prototype.send = function (src, target) {
    };
    ns.socket.SocketReader = SocketReader;
    ns.socket.SocketWriter = SocketWriter
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var SocketHelper = ns.net.SocketHelper;
    var ChannelController = function (channel) {
        Object.call(this);
        this.__channel = channel
    };
    Class(ChannelController, Object, null, null);
    ChannelController.prototype.getChannel = function () {
        return this.__channel
    };
    ChannelController.prototype.getRemoteAddress = function () {
        var channel = this.getChannel();
        return !channel ? null : channel.getRemoteAddress()
    };
    ChannelController.prototype.getLocalAddress = function () {
        var channel = this.getChannel();
        return !channel ? null : channel.getLocalAddress()
    };
    ChannelController.prototype.getSocket = function () {
        var channel = this.getChannel();
        return !channel ? null : channel.getSocket()
    };
    ChannelController.prototype.receivePackage = function (sock, maxLen) {
        return SocketHelper.socketReceive(sock, maxLen)
    };
    ChannelController.prototype.sendAll = function (sock, data) {
        return SocketHelper.socketSend(sock, data)
    };
    ns.socket.ChannelController = ChannelController
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var SocketReader = ns.socket.SocketReader;
    var SocketWriter = ns.socket.SocketWriter;
    var ChannelController = ns.socket.ChannelController;
    var ChannelReader = function (channel) {
        ChannelController.call(this, channel)
    };
    Class(ChannelReader, ChannelController, [SocketReader], {
        read: function (maxLen) {
            var sock = this.getSocket();
            if (sock && sock.isOpen()) {
                return this.receivePackage(sock, maxLen)
            } else {
                throw new Error('channel closed');
            }
        }
    });
    var ChannelWriter = function (channel) {
        ChannelController.call(this, channel)
    };
    Class(ChannelWriter, ChannelController, [SocketWriter], {
        write: function (data) {
            var sock = this.getSocket();
            if (sock && sock.isOpen()) {
                return this.sendAll(sock, data)
            } else {
                throw new Error('channel closed');
            }
        }
    });
    ns.socket.ChannelReader = ChannelReader;
    ns.socket.ChannelWriter = ChannelWriter
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var AddressPairObject = ns.type.AddressPairObject;
    var Connection = ns.net.Connection;
    var TimedConnection = ns.net.TimedConnection;
    var ConnectionState = ns.net.ConnectionState;
    var StateMachine = ns.net.ConnectionStateMachine;
    var StateOrder = ns.net.ConnectionStateOrder;
    var BaseConnection = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__channel = -1;
        this.__delegate = null;
        this.__lastSentTime = null;
        this.__lastReceivedTime = null;
        this.__fsm = null
    };
    Class(BaseConnection, AddressPairObject, [Connection, TimedConnection, ConnectionState.Delegate], {
        toString: function () {
            var clazz = this.getClassName();
            var remote = this.getRemoteAddress();
            var local = this.getLocalAddress();
            var channel = this.getChannel();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '">\n\t' + channel + '\n</' + clazz + '>'
        }
    });
    BaseConnection.EXPIRES = 16 * 1000;
    BaseConnection.prototype.getDelegate = function () {
        return this.__delegate
    };
    BaseConnection.prototype.setDelegate = function (delegate) {
        this.__delegate = delegate
    };
    BaseConnection.prototype.getStateMachine = function () {
        return this.__fsm
    };
    BaseConnection.prototype.setStateMachine = function (machine) {
        var old = this.__fsm;
        this.__fsm = machine;
        if (old && old !== machine) {
            old.stop()
        }
    };
    BaseConnection.prototype.createStateMachine = function () {
        var machine = new StateMachine(this);
        machine.setDelegate(this);
        return machine
    };
    BaseConnection.prototype.getChannel = function () {
        var channel = this.__channel;
        return channel === -1 ? null : channel
    };
    BaseConnection.prototype.setChannel = function (channel) {
        var old = this.__channel;
        this.__channel = channel;
        if (old && old !== -1 && old !== channel) {
            old.close()
        }
    };
    BaseConnection.prototype.isOpen = function () {
        var channel = this.__channel;
        if (channel === -1) {
            return true
        }
        return channel && channel.isOpen()
    };
    BaseConnection.prototype.isBound = function () {
        var channel = this.getChannel();
        return channel && channel.isBound()
    };
    BaseConnection.prototype.isConnected = function () {
        var channel = this.getChannel();
        return channel && channel.isConnected()
    };
    BaseConnection.prototype.isAlive = function () {
        return this.isOpen() && (this.isConnected() || this.isBound())
    };
    BaseConnection.prototype.isAvailable = function () {
        var channel = this.getChannel();
        return channel && channel.isAvailable()
    };
    BaseConnection.prototype.isVacant = function () {
        var channel = this.getChannel();
        return channel && channel.isVacant()
    };
    BaseConnection.prototype.close = function () {
        this.setStateMachine(null);
        this.setChannel(null)
    };
    BaseConnection.prototype.start = function (hub) {
        this.openChannel(hub);
        this.startMachine()
    };
    BaseConnection.prototype.startMachine = function () {
        var machine = this.createStateMachine();
        this.setStateMachine(machine);
        machine.start()
    };
    BaseConnection.prototype.openChannel = function (hub) {
        var remote = this.getRemoteAddress();
        var local = this.getLocalAddress();
        var channel = hub.open(remote, local);
        if (channel) {
            this.setChannel(channel)
        }
        return channel
    };
    BaseConnection.prototype.onReceivedData = function (data) {
        this.__lastReceivedTime = new Date();
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionReceived(data, this)
        }
    };
    BaseConnection.prototype.doSend = function (data, destination) {
        var channel = this.getChannel();
        if (!(channel && channel.isAlive())) {
            return -1
        } else if (!destination) {
            throw new ReferenceError('remote address should not empty')
        }
        var sent = channel.send(data, destination);
        if (sent > 0) {
            this.__lastSentTime = new Date()
        }
        return sent
    };
    BaseConnection.prototype.sendData = function (pack) {
        var error = null
        var sent = -1;
        try {
            var destination = this.getRemoteAddress();
            sent = this.doSend(pack, destination);
            if (sent < 0) {
                error = new Error('failed to send data: ' + pack.length + ' byte(s) to ' + destination)
            }
        } catch (e) {
            error = e;
            this.setChannel(null)
        }
        var delegate = this.getDelegate();
        if (delegate) {
            if (error) {
                delegate.onConnectionFailed(error, pack, this)
            } else {
                delegate.onConnectionSent(sent, pack, this)
            }
        }
        return sent
    };
    BaseConnection.prototype.getState = function () {
        var machine = this.getStateMachine();
        return !machine ? null : machine.getCurrentState()
    };
    BaseConnection.prototype.tick = function (now, elapsed) {
        if (this.__channel === -1) {
            return
        }
        var machine = this.getStateMachine();
        if (machine) {
            machine.tick(now, elapsed)
        }
    };
    BaseConnection.prototype.getLastSentTime = function () {
        return this.__lastSentTime
    };
    BaseConnection.prototype.getLastReceivedTime = function () {
        return this.__lastReceivedTime
    };
    BaseConnection.prototype.isSentRecently = function (now) {
        var last = this.__lastSentTime;
        last = !last ? 0 : last.getTime();
        return now.getTime() <= last + BaseConnection.EXPIRES
    };
    BaseConnection.prototype.isReceivedRecently = function (now) {
        var last = this.__lastReceivedTime;
        last = !last ? 0 : last.getTime();
        return now.getTime() <= last + BaseConnection.EXPIRES
    };
    BaseConnection.prototype.isNotReceivedLongTimeAgo = function (now) {
        var last = this.__lastReceivedTime;
        last = !last ? 0 : last.getTime();
        return now.getTime() > last + (BaseConnection.EXPIRES << 3)
    };
    BaseConnection.prototype.enterState = function (next, ctx, now) {
    };
    BaseConnection.prototype.exitState = function (previous, ctx, now) {
        var current = ctx.getCurrentState();
        var currentIndex = !current ? -1 : current.getIndex();
        if (StateOrder.READY.equals(currentIndex)) {
            var previousIndex = !previous ? -1 : previous.getIndex();
            if (StateOrder.PREPARING.equals(previousIndex)) {
                var soon = (new Date()).getTime() - (BaseConnection.EXPIRES >> 1);
                var st = this.__lastSentTime;
                st = !st ? 0 : st.getTime();
                if (st < soon) {
                    this.__lastSentTime = new Date(soon)
                }
                var rt = this.__lastReceivedTime;
                rt = !rt ? 0 : rt.getTime();
                if (rt < soon) {
                    this.__lastReceivedTime = new Date(soon)
                }
            }
        }
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionStateChanged(previous, current, this)
        }
        if (StateOrder.ERROR.equals(currentIndex)) {
            this.setChannel(null)
        }
    };
    BaseConnection.prototype.pauseState = function (current, ctx, now) {
    };
    BaseConnection.prototype.resumeState = function (current, ctx, now) {
    };
    ns.socket.BaseConnection = BaseConnection
})(StarTrek, MONKEY);
(function (ns, fsm, sys) {
    'use strict';
    var Class = sys.type.Class;
    var Runnable = fsm.skywalker.Runnable;
    var Thread = fsm.threading.Thread;
    var BaseConnection = ns.socket.BaseConnection;
    var ActiveConnection = function (remote, local) {
        BaseConnection.call(this, remote, local);
        this.__hub = null;
        this.__thread = null;
        this.__bg_next_loop = 0;
        this.__bg_expired = 0;
        this.__bg_last_time = 0;
        this.__bg_interval = 8000
    };
    Class(ActiveConnection, BaseConnection, [Runnable], {
        isOpen: function () {
            return this.getStateMachine() !== null
        }, start: function (hub) {
            this.__hub = hub;
            this.startMachine();
            var thread = this.__thread;
            if (thread) {
                this.__thread = null;
                thread.stop()
            }
            thread = new Thread(this);
            thread.start();
            this.__thread = thread
        }, run: function () {
            var now = (new Date()).getTime();
            if (this.__bg_next_loop === 0) {
                this.__bg_next_loop = now + 1000;
                return true
            } else if (this.__bg_next_loop > now) {
                return true
            } else {
                this.__bg_next_loop = now + 1000
            }
            if (!this.isOpen()) {
                return false
            }
            try {
                var channel = this.getChannel();
                if (!(channel && channel.isOpen())) {
                    if (now < this.__bg_last_time + this.__bg_interval) {
                        return true
                    } else {
                        this.__bg_last_time = now
                    }
                    var hub = this.__hub;
                    if (!hub) {
                        return false
                    }
                    channel = this.openChannel(hub);
                    if (channel) {
                        this.__bg_expired = now + 128000
                    } else if (this.__bg_interval < 128000) {
                        this.__bg_interval <<= 1
                    }
                } else if (channel.isAlive()) {
                    this.__bg_interval = 8000
                } else if (0 < this.__bg_expired && this.__bg_expired < now) {
                    channel.close()
                }
            } catch (e) {
                var delegate = this.getDelegate();
                if (delegate) {
                    delegate.onConnectionError(e, this)
                }
            }
            return true
        }
    });
    ns.socket.ActiveConnection = ActiveConnection
})(StarTrek, FiniteStateMachine, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var AddressPairMap = ns.type.AddressPairMap;
    var StateOrder = ns.net.ChannelStateOrder;
    var Hub = ns.net.Hub;
    var ConnectionPool = function () {
        AddressPairMap.call(this)
    };
    Class(ConnectionPool, AddressPairMap, null, {
        set: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
            AddressPairMap.prototype.set.call(this, remote, local, value);
            return cached
        }
    });
    var BaseHub = function (gate) {
        Object.call(this);
        this.__delegate = gate;
        this.__connPool = this.createConnectionPool();
        this.__last = (new Date()).getTime()
    };
    Class(BaseHub, Object, [Hub], null);
    BaseHub.prototype.createConnectionPool = function () {
        return new ConnectionPool()
    };
    BaseHub.prototype.getDelegate = function () {
        return this.__delegate
    };
    BaseHub.MSS = 1472;
    BaseHub.prototype.allChannels = function () {
    };
    BaseHub.prototype.removeChannel = function (remote, local, channel) {
    };
    BaseHub.prototype.createConnection = function (remote, local) {
    };
    BaseHub.prototype.allConnections = function () {
        return this.__connPool.items()
    };
    BaseHub.prototype.getConnection = function (remote, local) {
        return this.__connPool.get(remote, local)
    };
    BaseHub.prototype.setConnection = function (remote, local, connection) {
        return this.__connPool.set(remote, local, connection)
    };
    BaseHub.prototype.removeConnection = function (remote, local, connection) {
        return this.__connPool.remove(remote, local, connection)
    };
    BaseHub.prototype.connect = function (remote, local) {
        var conn;
        var old = this.getConnection(remote, local);
        if (!old) {
            conn = this.createConnection(remote, local);
            var cached = this.setConnection(remote, local, conn);
            if (cached && cached !== conn) {
                cached.close()
            }
        } else {
            conn = old
        }
        if (!old) {
            conn.start(this)
        }
        return conn
    };
    BaseHub.prototype.closeChannel = function (channel) {
        try {
            if (channel.isOpen()) {
                channel.close()
            }
        } catch (e) {
        }
    };
    BaseHub.prototype.driveChannel = function (channel) {
        var cs = channel.getState();
        if (StateOrder.INIT.equals(cs)) {
            return false
        } else if (StateOrder.CLOSED.equals(cs)) {
            return false
        }
        var conn;
        var remote = channel.getRemoteAddress();
        var local = channel.getLocalAddress();
        var data;
        try {
            data = channel.receive(BaseHub.MSS)
        } catch (e) {
            var gate = this.getDelegate();
            var cached;
            if (!gate || !remote) {
                cached = this.removeChannel(remote, local, channel)
            } else {
                conn = this.getConnection(remote, local);
                cached = this.removeChannel(remote, local, channel);
                if (conn) {
                    gate.onConnectionError(e, conn)
                }
            }
            if (cached && cached !== channel) {
                this.closeChannel(cached)
            }
            this.closeChannel(channel);
            return false
        }
        if (!data) {
            return false
        }
        conn = this.connect(remote, local);
        if (conn) {
            conn.onReceivedData(data)
        }
        return true
    };
    BaseHub.prototype.driveChannels = function (channels) {
        var count = 0;
        for (var i = channels.length - 1; i >= 0; --i) {
            if (this.driveChannel(channels[i])) {
                ++count
            }
        }
        return count
    };
    BaseHub.prototype.cleanupChannels = function (channels) {
        var cached, sock;
        var remote, local;
        for (var i = channels.length - 1; i >= 0; --i) {
            sock = channels[i];
            if (!sock.isOpen()) {
                remote = sock.getRemoteAddress();
                local = sock.getLocalAddress();
                cached = this.removeChannel(remote, local, sock);
                if (cached && cached !== sock) {
                    this.closeChannel(cached)
                }
            }
        }
    };
    BaseHub.prototype.driveConnections = function (connections) {
        var now = new Date();
        var elapsed = now.getTime() - this.__last;
        for (var i = connections.length - 1; i >= 0; --i) {
            connections[i].tick(now, elapsed)
        }
        this.__last = now.getTime()
    };
    BaseHub.prototype.cleanupConnections = function (connections) {
        var cached, conn;
        var remote, local;
        for (var i = connections.length - 1; i >= 0; --i) {
            conn = connections[i];
            if (!conn.isOpen()) {
                remote = conn.getRemoteAddress();
                local = conn.getLocalAddress();
                cached = this.removeConnection(remote, local, conn);
                if (cached && cached !== conn) {
                    cached.close()
                }
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
        return count > 0
    };
    ns.socket.BaseHub = BaseHub
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var BaseObject = sys.type.BaseObject;
    var Arrival = ns.port.Arrival;
    var ShipStatus = ns.port.ShipStatus;
    var ArrivalShip = function (now) {
        BaseObject.call(this);
        if (!now) {
            now = new Date()
        }
        this.__expired = now.getTime() + ArrivalShip.EXPIRED
    };
    Class(ArrivalShip, BaseObject, [Arrival], null);
    ArrivalShip.EXPIRES = 300 * 1000;
    ArrivalShip.prototype.touch = function (now) {
        this.__expired = now.getTime() + ArrivalShip.EXPIRES
    };
    ArrivalShip.prototype.getStatus = function (now) {
        if (now.getTime() > this.__expired) {
            return ShipStatus.EXPIRED
        } else {
            return ShipStatus.ASSEMBLING
        }
    };
    ns.ArrivalShip = ArrivalShip
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var HashSet = sys.type.HashSet;
    var ShipStatus = ns.port.ShipStatus;
    var ArrivalHall = function () {
        Object.call(this);
        this.__arrivals = new HashSet();
        this.__arrival_map = {};
        this.__finished_times = {}
    };
    Class(ArrivalHall, Object, null, null);
    ArrivalHall.prototype.assembleArrival = function (income) {
        var sn = income.getSN();
        if (!sn) {
            return income
        }
        var completed;
        var cached = this.__arrival_map[sn];
        if (cached) {
            completed = cached.assemble(income);
            if (completed) {
                this.__arrivals.remove(cached);
                delete this.__arrival_map[sn];
                this.__finished_times[sn] = new Date()
            } else {
                cached.touch(new Date())
            }
        } else {
            var time = this.__finished_times[sn];
            if (time) {
                return null
            }
            completed = income.assemble(income);
            if (!completed) {
                this.__arrivals.add(income);
                this.__arrival_map[sn] = income
            }
        }
        return completed
    };
    ArrivalHall.prototype.purge = function (now) {
        if (!now) {
            now = new Date()
        }
        var count = 0;
        var ship;
        var sn;
        var arrivals = this.__arrivals.toArray();
        for (var i = arrivals.length - 1; i >= 0; --i) {
            ship = arrivals[i];
            if (ship.getStatus(now) === ShipStatus.EXPIRED) {
                sn = ship.getSN();
                if (sn) {
                    delete this.__arrival_map[sn]
                }
                ++count;
                this.__arrivals.remove(ship)
            }
        }
        var ago = now.getTime() - 3600 * 1000;
        var when;
        var keys = Object.keys(this.__finished_times);
        for (var j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__finished_times[sn];
            if (!when || when.getTime() < ago) {
                delete this.__finished_times[sn]
            }
        }
        return count
    };
    ns.ArrivalHall = ArrivalHall
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var Enum = sys.type.Enum;
    var BaseObject = sys.type.BaseObject;
    var Departure = ns.port.Departure;
    var ShipStatus = ns.port.ShipStatus;
    var DepartureShip = function (priority, maxTries) {
        BaseObject.call(this);
        if (priority === null) {
            priority = 0
        } else {
            priority = Enum.getInt(priority)
        }
        if (maxTries === null) {
            maxTries = 1 + DepartureShip.RETRIES
        }
        this.__priority = priority;
        this.__tries = maxTries;
        this.__expired = 0
    };
    Class(DepartureShip, BaseObject, [Departure], {
        getPriority: function () {
            return this.__priority
        }, touch: function (now) {
            this.__expired = now.getTime() + DepartureShip.EXPIRES;
            this.__tries -= 1
        }, getStatus: function (now) {
            var expired = this.__expired;
            var fragments = this.getFragments();
            if (!fragments || fragments.length === 0) {
                return ShipStatus.DONE
            } else if (expired === 0) {
                return ShipStatus.NEW
            } else if (now.getTime() < expired) {
                return ShipStatus.WAITING
            } else if (this.__tries > 0) {
                return ShipStatus.TIMEOUT
            } else {
                return ShipStatus.FAILED
            }
        }
    });
    DepartureShip.EXPIRES = 120 * 1000;
    DepartureShip.RETRIES = 2;
    ns.DepartureShip = DepartureShip
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var Arrays = sys.type.Arrays;
    var HashSet = sys.type.HashSet;
    var ShipStatus = ns.port.ShipStatus;
    var DepartureHall = function () {
        Object.call(this);
        this.__all_departures = new HashSet();
        this.__new_departures = [];
        this.__fleets = {};
        this.__priorities = [];
        this.__departure_map = {};
        this.__departure_level = {};
        this.__finished_times = {}
    };
    Class(DepartureHall, Object, null, null);
    DepartureHall.prototype.addDeparture = function (outgo) {
        if (this.__all_departures.contains(outgo)) {
            return false
        } else {
            this.__all_departures.add(outgo)
        }
        var priority = outgo.getPriority();
        var index = this.__new_departures.length;
        while (index > 0) {
            --index;
            if (this.__new_departures[index].getPriority() <= priority) {
                ++index;
                break
            }
        }
        Arrays.insert(this.__new_departures, index, outgo);
        return true
    };
    DepartureHall.prototype.checkResponse = function (response) {
        var sn = response.getSN();
        var time = this.__finished_times[sn];
        if (time) {
            return null
        }
        var ship = this.__departure_map[sn];
        if (ship && ship.checkResponse(response)) {
            removeShip.call(this, ship, sn);
            this.__finished_times[sn] = new Date();
            return ship
        }
        return null
    };
    var removeShip = function (ship, sn) {
        var priority = this.__departure_level[sn];
        if (!priority) {
            priority = 0
        }
        var fleet = this.__fleets[priority];
        if (fleet) {
            Arrays.remove(fleet, ship);
            if (fleet.length === 0) {
                delete this.__fleets[priority]
            }
        }
        delete this.__departure_map[sn];
        delete this.__departure_level[sn];
        this.__all_departures.remove(ship)
    };
    DepartureHall.prototype.getNextDeparture = function (now) {
        var next = getNextNewDeparture.call(this, now);
        if (!next) {
            next = getNextTimeoutDeparture.call(this, now)
        }
        return next
    };
    var getNextNewDeparture = function (now) {
        if (this.__new_departures.length === 0) {
            return null
        }
        var outgo = this.__new_departures.shift();
        var sn = outgo.getSN();
        if (outgo.isImportant() && sn) {
            var priority = outgo.getPriority();
            insertShip.call(this, outgo, priority, sn);
            this.__departure_map[sn] = outgo
        } else {
            this.__all_departures.remove(outgo)
        }
        outgo.touch(now);
        return outgo
    };
    var insertShip = function (outgo, priority, sn) {
        var fleet = this.__fleets[priority];
        if (!fleet) {
            fleet = [];
            this.__fleets[priority] = fleet;
            insertPriority.call(this, priority)
        }
        fleet.push(outgo);
        this.__departure_level[sn] = priority
    };
    var insertPriority = function (priority) {
        var index, value;
        for (index = 0; index < this.__priorities.length; ++index) {
            value = this.__priorities[index];
            if (value === priority) {
                return
            } else if (value > priority) {
                break
            }
        }
        Arrays.insert(this.__priorities, index, priority)
    };
    var getNextTimeoutDeparture = function (now) {
        var priorityList = this.__priorities.slice();
        var departures;
        var fleet;
        var ship;
        var status;
        var sn;
        var prior;
        var i, j;
        for (i = 0; i < priorityList.length; ++i) {
            prior = priorityList[i];
            fleet = this.__fleets[prior];
            if (!fleet) {
                continue
            }
            departures = fleet.slice();
            for (j = 0; j < departures.length; ++j) {
                ship = departures[j];
                sn = ship.getSN();
                status = ship.getStatus(now);
                if (status === ShipStatus.TIMEOUT) {
                    fleet.splice(j, 1);
                    insertShip.call(this, ship, prior + 1, sn);
                    ship.touch(now);
                    return ship
                } else if (status === ShipStatus.FAILED) {
                    fleet.splice(j, 1);
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    this.__all_departures.remove(ship);
                    return ship
                }
            }
        }
        return null
    };
    DepartureHall.prototype.purge = function (now) {
        if (!now) {
            now = new Date()
        }
        var count = 0;
        var priorityList = this.__priorities.slice();
        var departures;
        var fleet;
        var ship;
        var sn;
        var prior;
        var i, j;
        for (i = priorityList.length - 1; i >= 0; --i) {
            prior = priorityList[i];
            fleet = this.__fleets[prior];
            if (!fleet) {
                this.__priorities.splice(i, 1);
                continue
            }
            departures = fleet.slice();
            for (j = departures.length - 1; j >= 0; --j) {
                ship = departures[j];
                if (ship.getStatus(now) === ShipStatus.DONE) {
                    fleet.splice(j, 1);
                    sn = ship.getSN();
                    delete this.__departure_map[sn];
                    delete this.__departure_level[sn];
                    this.__finished_times[sn] = now;
                    ++count
                }
            }
            if (fleet.length === 0) {
                delete this.__fleets[prior];
                this.__priorities.splice(i, 1)
            }
        }
        var ago = now.getTime() - 3600 * 1000;
        var keys = Object.keys(this.__finished_times);
        var when;
        for (j = keys.length - 1; j >= 0; --j) {
            sn = keys[j];
            when = this.__finished_times[sn];
            if (!when || when.getTime() < ago) {
                delete this.__finished_times[sn]
            }
        }
        return count
    };
    ns.DepartureHall = DepartureHall
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var ArrivalHall = ns.ArrivalHall;
    var DepartureHall = ns.DepartureHall;
    var Dock = function () {
        Object.call(this);
        this.__arrivalHall = this.createArrivalHall();
        this.__departureHall = this.createDepartureHall()
    };
    Class(Dock, Object, null, null);
    Dock.prototype.createArrivalHall = function () {
        return new ArrivalHall()
    };
    Dock.prototype.createDepartureHall = function () {
        return new DepartureHall()
    };
    Dock.prototype.assembleArrival = function (income) {
        return this.__arrivalHall.assembleArrival(income)
    };
    Dock.prototype.addDeparture = function (outgo) {
        return this.__departureHall.addDeparture(outgo)
    };
    Dock.prototype.checkResponse = function (response) {
        return this.__departureHall.checkResponse(response)
    };
    Dock.prototype.getNextDeparture = function (now) {
        return this.__departureHall.getNextDeparture(now)
    };
    Dock.prototype.purge = function (now) {
        var count = 0;
        count += this.__arrivalHall.purge(now);
        count += this.__departureHall.purge(now);
        return count
    };
    ns.Dock = Dock
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var AddressPairObject = ns.type.AddressPairObject;
    var ShipStatus = ns.port.ShipStatus;
    var Porter = ns.port.Porter;
    var PorterStatus = ns.port.PorterStatus;
    var Dock = ns.Dock;
    var StarPorter = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__dock = this.createDock();
        this.__conn = -1;
        this.__lastOutgo = null;
        this.__lastFragments = [];
        this.__delegate = null
    };
    Class(StarPorter, AddressPairObject, [Porter], {
        toString: function () {
            var clazz = this.getClassName();
            var remote = this.getRemoteAddress();
            var local = this.getLocalAddress();
            var conn = this.getConnection();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '">\n\t' + conn + '\n</' + clazz + '>'
        }
    });
    StarPorter.prototype.createDock = function () {
        return new Dock()
    };
    StarPorter.prototype.getDelegate = function () {
        return this.__delegate
    };
    StarPorter.prototype.setDelegate = function (keeper) {
        this.__delegate = keeper
    };
    StarPorter.prototype.getConnection = function () {
        var conn = this.__conn;
        return conn === -1 ? null : conn
    };
    StarPorter.prototype.setConnection = function (conn) {
        var old = this.__conn;
        this.__conn = conn;
        if (old && old !== -1 && old !== conn) {
            old.close()
        }
    };
    StarPorter.prototype.isOpen = function () {
        var conn = this.__conn;
        if (conn === -1) {
            return false
        }
        return conn && conn.isOpen()
    };
    StarPorter.prototype.isAlive = function () {
        var conn = this.getConnection();
        return conn && conn.isAlive()
    };
    StarPorter.prototype.getStatus = function () {
        var conn = this.getConnection();
        if (conn) {
            return PorterStatus.getStatus(conn.getState())
        } else {
            return PorterStatus.ERROR
        }
    };
    StarPorter.prototype.sendShip = function (ship) {
        return this.__dock.addDeparture(ship)
    };
    StarPorter.prototype.processReceived = function (data) {
        var incomeShips = this.getArrivals(data);
        if (!incomeShips || incomeShips.length === 0) {
            return
        }
        var keeper = this.getDelegate();
        var income, ship;
        for (var i = 0; i < incomeShips.length; ++i) {
            ship = incomeShips[i];
            income = this.checkArrival(ship);
            if (!income) {
                continue
            }
            if (keeper) {
                keeper.onPorterReceived(income, this)
            }
        }
    };
    StarPorter.prototype.getArrivals = function (data) {
    };
    StarPorter.prototype.checkArrival = function (income) {
    };
    StarPorter.prototype.checkResponse = function (income) {
        var linked = this.__dock.checkResponse(income);
        if (!linked) {
            return null
        }
        var keeper = this.getDelegate();
        if (keeper) {
            keeper.onPorterSent(linked, this)
        }
        return linked
    };
    StarPorter.prototype.assembleArrival = function (income) {
        return this.__dock.assembleArrival(income)
    };
    StarPorter.prototype.getNextDeparture = function (now) {
        return this.__dock.getNextDeparture(now)
    };
    StarPorter.prototype.purge = function (now) {
        this.__dock.purge(now)
    };
    StarPorter.prototype.close = function () {
        this.setConnection(null)
    };
    StarPorter.prototype.process = function () {
        var conn = this.getConnection();
        if (!conn) {
            return false
        } else if (!conn.isVacant()) {
            return false
        }
        var keeper = this.getDelegate();
        var error;
        var outgo = this.__lastOutgo;
        var fragments = this.__lastFragments;
        if (outgo && fragments.length > 0) {
            this.__lastOutgo = null;
            this.__lastFragments = []
        } else {
            var now = new Date();
            outgo = this.getNextDeparture(now);
            if (!outgo) {
                return false
            } else if (outgo.getStatus(now) === ShipStatus.FAILED) {
                if (keeper) {
                    error = new Error('Request timeout');
                    keeper.onPorterFailed(error, outgo, this)
                }
                return true
            } else {
                fragments = outgo.getFragments();
                if (fragments.length === 0) {
                    return true
                }
            }
        }
        var index = 0;
        var sent = 0;
        try {
            var fra;
            for (var i = 0; i < fragments.length; ++i) {
                fra = fragments[i];
                sent = conn.sendData(fra);
                if (sent < fra.length) {
                    break
                } else {
                    index += 1;
                    sent = 0
                }
            }
            if (index < fragments.length) {
                error = new Error('only ' + index + '/' + fragments.length + ' fragments sent.')
            } else {
                if (outgo.isImportant()) {
                } else if (keeper) {
                    keeper.onPorterSent(outgo, this)
                }
                return true
            }
        } catch (e) {
            error = e
        }
        for (; index > 0; --index) {
            fragments.shift()
        }
        if (sent > 0) {
            var last = fragments.shift();
            var part = last.subarray(sent);
            fragments.unshift(part)
        }
        this.__lastOutgo = outgo;
        this.__lastFragments = fragments;
        if (keeper) {
            keeper.onPorterError(error, outgo, this)
        }
        return false
    };
    ns.StarPorter = StarPorter
})(StarTrek, MONKEY);
(function (ns, sys) {
    'use strict';
    var Class = sys.type.Class;
    var AddressPairMap = ns.type.AddressPairMap;
    var ConnectionDelegate = ns.net.ConnectionDelegate;
    var ConnectionStateOrder = ns.net.ConnectionStateOrder;
    var PorterStatus = ns.port.PorterStatus;
    var Gate = ns.port.Gate;
    var StarPorter = ns.StarPorter;
    var PorterPool = function () {
        AddressPairMap.call(this)
    };
    Class(PorterPool, AddressPairMap, null, {
        set: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
            AddressPairMap.prototype.set.call(this, remote, local, value);
            return cached
        }
    });
    var StarGate = function (keeper) {
        Object.call(this);
        this.__delegate = keeper;
        this.__porterPool = this.createPorterPool()
    };
    Class(StarGate, Object, [Gate, ConnectionDelegate], null);
    StarGate.prototype.createPorterPool = function () {
        return new PorterPool()
    };
    StarGate.prototype.getDelegate = function () {
        return this.__delegate
    };
    StarGate.prototype.sendData = function (payload, remote, local) {
        var docker = this.getPorter(remote, local);
        if (!docker) {
            return false
        } else if (!docker.isAlive()) {
            return false
        }
        return docker.sendData(payload)
    };
    StarGate.prototype.sendShip = function (outgo, remote, local) {
        var docker = this.getPorter(remote, local);
        if (!docker) {
            return false
        } else if (!docker.isAlive()) {
            return false
        }
        return docker.sendShip(outgo)
    };
    StarGate.prototype.createPorter = function (remote, local) {
    };
    StarGate.prototype.allPorters = function () {
        return this.__porterPool.items()
    };
    StarGate.prototype.getPorter = function (remote, local) {
        return this.__porterPool.get(remote, local)
    };
    StarGate.prototype.setPorter = function (remote, local, porter) {
        return this.__porterPool.set(remote, local, porter)
    };
    StarGate.prototype.removePorter = function (remote, local, porter) {
        return this.__porterPool.remove(remote, local, porter)
    };
    StarGate.prototype.dock = function (connection, shouldCreatePorter) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        if (!remote) {
            return null
        }
        var docker;
        var old = this.getPorter(remote, local);
        if (!old && shouldCreatePorter) {
            docker = this.createPorter(remote, local);
            var cached = this.setPorter(remote, local, docker);
            if (cached && cached !== docker) {
                cached.close()
            }
        } else {
            docker = old
        }
        if (!old && docker instanceof StarPorter) {
            docker.setConnection(connection)
        }
        return docker
    };
    StarGate.prototype.process = function () {
        var dockers = this.allPorters();
        var count = this.drivePorters(dockers);
        this.cleanupPorters(dockers);
        return count > 0
    };
    StarGate.prototype.drivePorters = function (porters) {
        var count = 0;
        for (var i = porters.length - 1; i >= 0; --i) {
            if (porters[i].process()) {
                ++count
            }
        }
        return count
    };
    StarGate.prototype.cleanupPorters = function (porters) {
        var now = new Date();
        var cached, docker;
        var remote, local;
        for (var i = porters.length - 1; i >= 0; --i) {
            docker = porters[i];
            if (docker.isOpen()) {
                docker.purge(now)
            } else {
                remote = docker.getRemoteAddress();
                local = docker.getLocalAddress();
                cached = this.removePorter(remote, local, docker);
                if (cached && cached !== docker) {
                    cached.close()
                }
            }
        }
    };
    StarGate.prototype.heartbeat = function (connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        var docker = this.getPorter(remote, local);
        if (docker) {
            docker.heartbeat()
        }
    };
    StarGate.prototype.onConnectionStateChanged = function (previous, current, connection) {
        var s1 = PorterStatus.getStatus(previous);
        var s2 = PorterStatus.getStatus(current);
        if (s1 !== s2) {
            var notFinished = s2 !== PorterStatus.ERROR;
            var docker = this.dock(connection, notFinished);
            if (!docker) {
                return
            }
            var keeper = this.getDelegate();
            if (keeper) {
                keeper.onPorterStatusChanged(s1, s2, docker)
            }
        }
        var index = !current ? -1 : current.getIndex();
        if (ConnectionStateOrder.EXPIRED.equals(index)) {
            this.heartbeat(connection)
        }
    };
    StarGate.prototype.onConnectionReceived = function (data, connection) {
        var docker = this.dock(connection, true);
        if (docker) {
            docker.processReceived(data)
        }
    };
    StarGate.prototype.onConnectionSent = function (sent, data, connection) {
    };
    StarGate.prototype.onConnectionFailed = function (error, data, connection) {
    };
    StarGate.prototype.onConnectionError = function (error, connection) {
    };
    ns.StarGate = StarGate
})(StarTrek, MONKEY);
