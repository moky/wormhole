/**
 * Star Trek: Interstellar Transport (v2.0.0)
 *
 * @author    moKy <albert.moky at gmail.com>
 * @date      Aug. 27, 2025
 * @copyright (c) 2020-2025 Albert Moky
 * @license   {@link https://mit-license.org | MIT License}
 */;
if (typeof StarTrek !== 'object') {
    StarTrek = {}
}
(function (st, fsm, mk) {
    if (typeof st.type !== 'object') {
        st.type = {}
    }
    if (typeof st.net !== 'object') {
        st.net = {}
    }
    if (typeof st.port !== 'object') {
        st.port = {}
    }
    if (typeof st.socket !== 'object') {
        st.socket = {}
    }
    var Interface = mk.type.Interface;
    var Class = mk.type.Class;
    var Implementation = mk.type.Implementation;
    var IObject = mk.type.Object;
    var BaseObject = mk.type.BaseObject;
    var HashSet = mk.type.HashSet;
    var Enum = mk.type.Enum;
    var Arrays = mk.type.Arrays;
    var Mapper = mk.type.Mapper;
    var Stringer = mk.type.Stringer;
    var ConstantString = mk.type.ConstantString;
    var Duration = fsm.type.Duration;
    var Processor = fsm.skywalker.Processor;
    var Runnable = fsm.skywalker.Runnable;
    var Thread = fsm.threading.Thread;
    var Ticker = fsm.threading.Ticker;
    var Context = fsm.Context;
    var BaseMachine = fsm.BaseMachine;
    var BaseState = fsm.BaseState;
    var BaseTransition = fsm.BaseTransition;
    st.type.SocketAddress = Interface(null, [Stringer]);
    var SocketAddress = st.type.SocketAddress;
    SocketAddress.prototype.getHost = function () {
    };
    SocketAddress.prototype.getPort = function () {
    };
    st.type.InetSocketAddress = function (host, port) {
        ConstantString.call(this, '(' + host + ':' + port + ')');
        this.__host = host;
        this.__port = port
    };
    var InetSocketAddress = st.type.InetSocketAddress
    Class(InetSocketAddress, ConstantString, [SocketAddress]);
    InetSocketAddress.prototype.getHost = function () {
        return this.__host
    };
    InetSocketAddress.prototype.getPort = function () {
        return this.__port
    };
    st.type.AnyAddress = new InetSocketAddress('0.0.0.0', 0);
    var AnyAddress = st.type.AnyAddress;
    st.type.PairMap = Interface(null, null);
    var PairMap = st.type.PairMap;
    PairMap.prototype.items = function () {
    };
    PairMap.prototype.get = function (remote, local) {
    };
    PairMap.prototype.set = function (remote, local, value) {
    };
    PairMap.prototype.remove = function (remote, local, value) {
    };
    st.type.AbstractPairMap = function (any) {
        BaseObject.call(this);
        this.__default = any;
        this.__map = {}
    };
    var AbstractPairMap = st.type.AbstractPairMap;
    Class(AbstractPairMap, BaseObject, [PairMap]);
    AbstractPairMap.prototype.get = function (remote, local) {
        var key_pair = get_pair_keys(remote, local, null);
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
        Mapper.forEach(table, function (address, conn) {
            if (conn) {
                value = conn;
                return true
            } else {
                return false
            }
        });
        return value
    };
    AbstractPairMap.prototype.set = function (remote, local, value) {
        var key_pair = get_pair_keys(remote, local, this.__default);
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
        var key_pair = get_pair_keys(remote, local, this.__default);
        var key1 = key_pair[0];
        var key2 = key_pair[1];
        var table = this.__map[key1];
        if (!table) {
            return null
        }
        var old = table[key2];
        if (old) {
            delete table[key2];
            if (Mapper.isEmpty(table)) {
                delete this.__map[key1]
            }
        }
        return old ? old : value
    };
    var get_pair_keys = function (remote, local, any) {
        if (!remote) {
            return [local, any]
        } else if (!local) {
            return [remote, any]
        } else {
            return [remote, local]
        }
    };
    st.type.HashPairMap = function (any) {
        AbstractPairMap.call(this, any);
        this.__items = new HashSet()
    };
    var HashPairMap = st.type.HashPairMap;
    Class(HashPairMap, AbstractPairMap, null);
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
    st.type.AddressPairMap = function () {
        HashPairMap.call(this, AnyAddress)
    };
    var AddressPairMap = st.type.AddressPairMap;
    Class(AddressPairMap, HashPairMap, null);
    st.type.AddressPairObject = function (remote, local) {
        BaseObject.call(this);
        this.remoteAddress = remote;
        this.localAddress = local
    };
    var AddressPairObject = st.type.AddressPairObject;
    Class(AddressPairObject, BaseObject, null);
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
        return this.toString()
    };
    AddressPairObject.prototype.toString = function () {
        var cname = this.getClassName();
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
    st.net.SocketHelper = {
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
    };
    var SocketHelper = st.net.SocketHelper;
    st.net.ChannelStateOrder = Enum('ChannelStatus', {INIT: 0, OPEN: 1, ALIVE: 2, CLOSED: 3});
    var ChannelStateOrder = st.net.ChannelStateOrder;
    st.net.Channel = Interface(null, null);
    var Channel = st.net.Channel;
    Channel.prototype.getStatus = function () {
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
    st.net.ConnectionStateOrder = Enum('ConnectionStatus', {
        DEFAULT: 0,
        PREPARING: 1,
        READY: 2,
        MAINTAINING: 3,
        EXPIRED: 4,
        ERROR: 5
    });
    var ConnectionStateOrder = st.net.ConnectionStateOrder;
    st.net.ConnectionState = function (order) {
        BaseState.call(this, Enum.getInt(order));
        this.__name = order.getName();
        this.__enterTime = null
    };
    var ConnectionState = st.net.ConnectionState;
    Class(ConnectionState, BaseState, null);
    Implementation(ConnectionState, {
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
            } else if (other instanceof ConnectionStateOrder) {
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
    st.net.ConnectionStateBuilder = function (transitionBuilder) {
        BaseObject.call(this);
        this.builder = transitionBuilder
    };
    var StateBuilder = st.net.ConnectionStateBuilder;
    Class(StateBuilder, BaseObject, null);
    Implementation(StateBuilder, {
        getDefaultState: function () {
            var state = new ConnectionState(ConnectionStateOrder.DEFAULT);
            state.addTransition(this.builder.getDefaultPreparingTransition());
            return state
        }, getPreparingState: function () {
            var state = new ConnectionState(ConnectionStateOrder.PREPARING);
            state.addTransition(this.builder.getPreparingReadyTransition());
            state.addTransition(this.builder.getPreparingDefaultTransition());
            return state
        }, getReadyState: function () {
            var state = new ConnectionState(ConnectionStateOrder.READY);
            state.addTransition(this.builder.getReadyExpiredTransition());
            state.addTransition(this.builder.getReadyErrorTransition());
            return state
        }, getExpiredState: function () {
            var state = new ConnectionState(ConnectionStateOrder.EXPIRED);
            state.addTransition(this.builder.getExpiredMaintainingTransition());
            state.addTransition(this.builder.getExpiredErrorTransition());
            return state
        }, getMaintainingState: function () {
            var state = new ConnectionState(ConnectionStateOrder.MAINTAINING);
            state.addTransition(this.builder.getMaintainingReadyTransition());
            state.addTransition(this.builder.getMaintainingExpiredTransition());
            state.addTransition(this.builder.getMaintainingErrorTransition());
            return state
        }, getErrorState: function () {
            var state = new ConnectionState(ConnectionStateOrder.ERROR);
            state.addTransition(this.builder.getErrorDefaultTransition());
            return state
        }
    });
    st.net.ConnectionStateTransition = function (order, evaluate) {
        BaseTransition.call(this, Enum.getInt(order));
        this.__evaluate = evaluate
    };
    var StateTransition = st.net.ConnectionStateTransition;
    Class(StateTransition, BaseTransition, null);
    StateTransition.prototype.evaluate = function (ctx, now) {
        return this.__evaluate.call(this, ctx, now)
    };
    st.net.ConnectionStateTransitionBuilder = function () {
        BaseObject.call(this)
    };
    var TransitionBuilder = st.net.ConnectionStateTransitionBuilder;
    Class(TransitionBuilder, BaseObject, null);
    Implementation(TransitionBuilder, {
        getDefaultPreparingTransition: function () {
            return new StateTransition(ConnectionStateOrder.PREPARING, function (ctx, now) {
                var conn = ctx.getConnection();
                return conn && conn.isOpen()
            })
        }, getPreparingReadyTransition: function () {
            return new StateTransition(ConnectionStateOrder.READY, function (ctx, now) {
                var conn = ctx.getConnection();
                return conn && conn.isAlive()
            })
        }, getPreparingDefaultTransition: function () {
            return new StateTransition(ConnectionStateOrder.DEFAULT, function (ctx, now) {
                var conn = ctx.getConnection();
                return !(conn && conn.isOpen())
            })
        }, getReadyExpiredTransition: function () {
            return new StateTransition(ConnectionStateOrder.EXPIRED, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return !conn.isReceivedRecently(now)
            })
        }, getReadyErrorTransition: function () {
            return new StateTransition(ConnectionStateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                return !(conn && conn.isAlive())
            })
        }, getExpiredMaintainingTransition: function () {
            return new StateTransition(ConnectionStateOrder.MAINTAINING, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return conn.isSentRecently(now)
            })
        }, getExpiredErrorTransition: function () {
            return new StateTransition(ConnectionStateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return true
                }
                return conn.isNotReceivedLongTimeAgo(now)
            })
        }, getMaintainingReadyTransition: function () {
            return new StateTransition(ConnectionStateOrder.READY, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return conn.isReceivedRecently(now)
            })
        }, getMaintainingExpiredTransition: function () {
            return new StateTransition(ConnectionStateOrder.EXPIRED, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return false
                }
                return !conn.isSentRecently(now)
            })
        }, getMaintainingErrorTransition: function () {
            return new StateTransition(ConnectionStateOrder.ERROR, function (ctx, now) {
                var conn = ctx.getConnection();
                if (!(conn && conn.isAlive())) {
                    return true
                }
                return conn.isNotReceivedLongTimeAgo(now)
            })
        }, getErrorDefaultTransition: function () {
            return new StateTransition(ConnectionStateOrder.DEFAULT, function (ctx, now) {
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
    st.net.ConnectionStateMachine = function (connection) {
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
    var StateMachine = st.net.ConnectionStateMachine;
    Class(StateMachine, BaseMachine, [Context]);
    StateMachine.prototype.createStateBuilder = function () {
        var stb = new TransitionBuilder();
        return new StateBuilder(stb)
    };
    StateMachine.prototype.getConnection = function () {
        return this.__connection
    };
    StateMachine.prototype.getContext = function () {
        return this
    };
    st.net.Connection = Interface(null, [Ticker]);
    var Connection = st.net.Connection;
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
    st.net.ConnectionDelegate = Interface(null, null);
    var ConnectionDelegate = st.net.ConnectionDelegate;
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
    st.net.TimedConnection = Interface(null, null);
    var TimedConnection = st.net.TimedConnection;
    TimedConnection.EXPIRES = Duration.ofSeconds(16);
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
    st.net.Hub = Interface(null, [Processor]);
    var Hub = st.net.Hub;
    Hub.prototype.open = function (remote, local) {
    };
    Hub.prototype.connect = function (remote, local) {
    };
    st.port.ShipStatus = Enum('ShipStatus', {
        NEW: (0x00),
        WAITING: (0x01),
        TIMEOUT: (0x02),
        DONE: (0x03),
        FAILED: (0x04),
        ASSEMBLING: (0x10),
        EXPIRED: (0x11)
    });
    var ShipStatus = st.port.ShipStatus;
    st.port.Ship = Interface(null, null);
    var Ship = st.port.Ship;
    Ship.prototype.getSN = function () {
    };
    Ship.prototype.touch = function (now) {
    };
    Ship.prototype.getStatus = function (now) {
    };
    st.port.Arrival = Interface(null, [Ship]);
    var Arrival = st.port.Arrival;
    Arrival.prototype.assemble = function (income) {
    };
    st.port.Departure = Interface(null, [Ship]);
    var Departure = st.port.Departure;
    Departure.prototype.getPriority = function () {
    };
    Departure.prototype.getFragments = function () {
    };
    Departure.prototype.checkResponse = function (response) {
    };
    Departure.prototype.isImportant = function () {
    };
    Departure.Priority = {URGENT: -1, NORMAL: 0, SLOWER: 1};
    var DeparturePriority = Departure.Priority;
    st.port.Porter = Interface(null, [Processor]);
    var Porter = st.port.Porter;
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
    st.port.PorterStatus = Enum('PorterStatus', {ERROR: -1, INIT: 0, PREPARING: 1, READY: 2});
    var PorterStatus = st.port.PorterStatus;
    PorterStatus.getStatus = function (state) {
        if (!state) {
            return PorterStatus.ERROR
        }
        var index = state.getIndex();
        if (ConnectionStateOrder.READY.equals(index) || ConnectionStateOrder.EXPIRED.equals(index) || ConnectionStateOrder.MAINTAINING.equals(index)) {
            return PorterStatus.READY
        } else if (ConnectionStateOrder.PREPARING.equals(index)) {
            return PorterStatus.PREPARING
        } else if (ConnectionStateOrder.ERROR.equals(index)) {
            return PorterStatus.ERROR
        } else {
            return PorterStatus.INIT
        }
    };
    st.port.PorterDelegate = Interface(null, null);
    var PorterDelegate = st.port.PorterDelegate;
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
    st.port.Gate = Interface(null, [Processor]);
    var Gate = st.port.Gate;
    Gate.prototype.sendData = function (payload, remote, local) {
    };
    Gate.prototype.sendShip = function (outgo, remote, local) {
    };
    st.socket.BaseChannel = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__reader = this.createReader();
        this.__writer = this.createWriter();
        this.__sock = null;
        this.__closed = -1
    };
    var BaseChannel = st.socket.BaseChannel;
    Class(BaseChannel, AddressPairObject, [Channel]);
    Implementation(BaseChannel, {
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
    st.socket.SocketReader = Interface(null, null);
    var SocketReader = st.socket.SocketReader;
    SocketReader.prototype.read = function (maxLen) {
    };
    SocketReader.prototype.receive = function (maxLen) {
    };
    st.socket.SocketWriter = Interface(null, null);
    var SocketWriter = st.socket.SocketWriter;
    SocketWriter.prototype.write = function (src) {
    };
    SocketWriter.prototype.send = function (src, target) {
    };
    st.socket.ChannelController = function (channel) {
        BaseObject.call(this);
        this.__channel = channel
    };
    var ChannelController = st.socket.ChannelController
    Class(ChannelController, BaseObject, null);
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
    st.socket.BaseConnection = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__channel = -1;
        this.__delegate = null;
        this.__lastSentTime = null;
        this.__lastReceivedTime = null;
        this.__fsm = null
    };
    var BaseConnection = st.socket.BaseConnection;
    Class(BaseConnection, AddressPairObject, [Connection, TimedConnection, ConnectionState.Delegate]);
    Implementation(BaseConnection, {
        toString: function () {
            var clazz = this.getClassName();
            var remote = this.getRemoteAddress();
            var local = this.getLocalAddress();
            var channel = this.getChannel();
            return '<' + clazz + ' remote="' + remote + '" local="' + local + '">\n\t' + channel + '\n</' + clazz + '>'
        }
    });
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
            try {
                old.close()
            } catch (e) {
            }
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
        var lastTime = this.__lastSentTime;
        if (!lastTime) {
            return false
        }
        var expired = TimedConnection.EXPIRES.addTo(lastTime);
        return expired.getTime() > now.getTime()
    };
    BaseConnection.prototype.isReceivedRecently = function (now) {
        var lastTime = this.__lastReceivedTime;
        if (!lastTime) {
            return false
        }
        var expired = TimedConnection.EXPIRES.addTo(lastTime);
        return expired.getTime() > now.getTime()
    };
    BaseConnection.prototype.isNotReceivedLongTimeAgo = function (now) {
        var lastTime = this.__lastReceivedTime;
        if (!lastTime) {
            return false
        }
        var expired = TimedConnection.EXPIRES.multiplies(8).addTo(lastTime);
        return expired.getTime() < now.getTime()
    };
    BaseConnection.prototype.enterState = function (next, ctx, now) {
    };
    BaseConnection.prototype.exitState = function (previous, ctx, now) {
        var current = ctx.getCurrentState();
        var currentIndex = !current ? -1 : current.getIndex();
        if (ConnectionStateOrder.READY.equals(currentIndex)) {
            var previousIndex = !previous ? -1 : previous.getIndex();
            if (ConnectionStateOrder.PREPARING.equals(previousIndex)) {
                var soon = TimedConnection.EXPIRES.divides(2).subtractFrom(now);
                var st = this.__lastSentTime;
                if (!st || st.getTime() < soon.getTime()) {
                    this.__lastSentTime = soon
                }
                var rt = this.__lastReceivedTime;
                if (!rt || rt.getTime() < soon.getTime()) {
                    this.__lastReceivedTime = soon
                }
            }
        }
        var delegate = this.getDelegate();
        if (delegate) {
            delegate.onConnectionStateChanged(previous, current, this)
        }
        if (ConnectionStateOrder.ERROR.equals(currentIndex)) {
            this.setChannel(null)
        }
    };
    BaseConnection.prototype.pauseState = function (current, ctx, now) {
    };
    BaseConnection.prototype.resumeState = function (current, ctx, now) {
    };
    st.socket.ActiveConnection = function (remote, local) {
        BaseConnection.call(this, remote, local);
        this.__hub = null;
        this.__thread = null;
        this.__bg_next_loop = 0;
        this.__bg_expired = 0;
        this.__bg_last_time = 0;
        this.__bg_interval = 8000
    };
    var ActiveConnection = st.socket.ActiveConnection;
    Class(ActiveConnection, BaseConnection, [Runnable]);
    Implementation(ActiveConnection, {
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
    st.socket.ConnectionPool = function () {
        AddressPairMap.call(this)
    };
    var ConnectionPool = st.socket.ConnectionPool;
    Class(ConnectionPool, AddressPairMap, null);
    Implementation(ConnectionPool, {
        set: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
            AddressPairMap.prototype.set.call(this, remote, local, value);
            return cached
        }
    });
    st.socket.BaseHub = function (gate) {
        BaseObject.call(this);
        this.__delegate = gate;
        this.__connPool = this.createConnectionPool();
        this.__last = new Date()
    };
    var BaseHub = st.socket.BaseHub;
    Class(BaseHub, BaseObject, [Hub]);
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
        var conn = this.getConnection(remote, local);
        if (conn) {
            if (!local) {
                return conn
            }
            var address = conn.getLocalAddress();
            if (!address || address.equals(local)) {
                return conn
            }
        }
        conn = this.createConnection(remote, local);
        if (!local) {
            local = conn.getLocalAddress()
        }
        var cached = this.setConnection(remote, local, conn);
        if (cached && cached !== conn) {
            cached.close()
        }
        if (conn instanceof BaseConnection) {
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
        if (ChannelStateOrder.INIT.equals(cs)) {
            return false
        } else if (ChannelStateOrder.CLOSED.equals(cs)) {
            return false
        }
        var conn;
        var remote;
        var local;
        var data;
        try {
            var pair = channel.receive(BaseHub.MSS);
            data = pair[0];
            remote = pair[1]
        } catch (e) {
            remote = channel.getRemoteAddress();
            local = channel.getLocalAddress();
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
        if (!remote || !data) {
            return false
        } else {
            local = channel.getLocalAddress()
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
        var elapsed = Duration.between(this.__last, now);
        for (var i = connections.length - 1; i >= 0; --i) {
            connections[i].tick(now, elapsed)
        }
        this.__last = now
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
    st.ArrivalShip = function (now) {
        BaseObject.call(this);
        if (!now) {
            now = new Date()
        }
        this.__expired = ArrivalShip.EXPIRES.addTo(now)
    };
    var ArrivalShip = st.ArrivalShip;
    Class(ArrivalShip, BaseObject, [Arrival]);
    ArrivalShip.EXPIRES = Duration.ofMinutes(5);
    ArrivalShip.prototype.touch = function (now) {
        this.__expired = ArrivalShip.EXPIRES.addTo(now)
    };
    ArrivalShip.prototype.getStatus = function (now) {
        if (now.getTime() > this.__expired.getTime()) {
            return ShipStatus.EXPIRED
        } else {
            return ShipStatus.ASSEMBLING
        }
    };
    st.ArrivalHall = function () {
        BaseObject.call(this);
        this.__arrivals = new HashSet();
        this.__arrival_map = {};
        this.__finished_times = {}
    };
    var ArrivalHall = st.ArrivalHall;
    Class(ArrivalHall, BaseObject, null);
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
        var ago = Duration.ofMinutes(60).subtractFrom(now);
        ago = ago.getTime();
        var finished_times = this.__finished_times;
        Mapper.forEach(finished_times, function (sn, when) {
            if (!when || when.getTime() < ago) {
                delete finished_times[sn]
            }
            return false
        });
        return count
    };
    st.DepartureShip = function (priority, maxTries) {
        BaseObject.call(this);
        if (priority === null) {
            priority = DeparturePriority.NORMAL
        }
        if (maxTries === null) {
            maxTries = 1 + DepartureShip.RETRIES
        }
        this.__priority = priority;
        this.__tries = maxTries;
        this.__expired = null
    };
    var DepartureShip = st.DepartureShip;
    Class(DepartureShip, BaseObject, [Departure]);
    DepartureShip.EXPIRES = Duration.ofMinutes(2);
    DepartureShip.RETRIES = 2;
    DepartureShip.prototype.getPriority = function () {
        return this.__priority
    };
    DepartureShip.prototype.touch = function (now) {
        this.__expired = DepartureShip.EXPIRES.addTo(now);
        this.__tries -= 1
    };
    DepartureShip.prototype.getStatus = function (now) {
        var expired = this.__expired;
        var fragments = this.getFragments();
        if (!fragments || fragments.length === 0) {
            return ShipStatus.DONE
        } else if (!expired) {
            return ShipStatus.NEW
        } else if (now.getTime() < expired.getTime()) {
            return ShipStatus.WAITING
        } else if (this.__tries > 0) {
            return ShipStatus.TIMEOUT
        } else {
            return ShipStatus.FAILED
        }
    };
    st.DepartureHall = function () {
        BaseObject.call(this);
        this.__all_departures = new HashSet();
        this.__new_departures = [];
        this.__fleets = {};
        this.__priorities = [];
        this.__departure_map = {};
        this.__departure_level = {};
        this.__finished_times = {}
    };
    var DepartureHall = st.DepartureHall;
    Class(DepartureHall, BaseObject, null);
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
            removeDeparture.call(this, ship, sn);
            this.__finished_times[sn] = new Date();
            return ship
        }
        return null
    };
    var removeDeparture = function (ship, sn) {
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
            insertDeparture.call(this, outgo, priority, sn);
            this.__departure_map[sn] = outgo
        } else {
            this.__all_departures.remove(outgo)
        }
        outgo.touch(now);
        return outgo
    };
    var insertDeparture = function (outgo, priority, sn) {
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
                    insertDeparture.call(this, ship, prior + 1, sn);
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
        var finished_times = this.__finished_times;
        var ago = Duration.ofMinutes(60).subtractFrom(now);
        ago = ago.getTime();
        Mapper.forEach(finished_times, function (sn, when) {
            if (!when || when.getTime() < ago) {
                delete finished_times[sn]
            }
            return false
        });
        return count
    };
    st.Dock = function () {
        BaseObject.call(this);
        this.__arrivalHall = this.createArrivalHall();
        this.__departureHall = this.createDepartureHall()
    };
    var Dock = st.Dock;
    Class(Dock, BaseObject, null);
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
    st.StarPorter = function (remote, local) {
        AddressPairObject.call(this, remote, local);
        this.__dock = this.createDock();
        this.__conn = -1;
        this.__delegate = null;
        this.__lastOutgo = null;
        this.__lastFragments = []
    };
    var StarPorter = st.StarPorter;
    Class(StarPorter, AddressPairObject, [Porter]);
    Implementation(StarPorter, {
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
        return this.__dock.purge(now)
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
    st.PorterPool = function () {
        AddressPairMap.call(this)
    };
    var PorterPool = st.PorterPool;
    Class(PorterPool, AddressPairMap, null);
    Implementation(PorterPool, {
        set: function (remote, local, value) {
            var cached = AddressPairMap.prototype.remove.call(this, remote, local, value);
            AddressPairMap.prototype.set.call(this, remote, local, value);
            return cached
        }
    });
    st.StarGate = function (keeper) {
        BaseObject.call(this);
        this.__delegate = keeper;
        this.__porterPool = this.createPorterPool()
    };
    var StarGate = st.StarGate;
    Class(StarGate, BaseObject, [Gate, ConnectionDelegate]);
    StarGate.prototype.createPorterPool = function () {
        return new PorterPool()
    };
    StarGate.prototype.getDelegate = function () {
        return this.__delegate
    };
    StarGate.prototype.sendData = function (payload, remote, local) {
        var worker = this.getPorter(remote, local);
        if (!worker) {
            return false
        } else if (!worker.isAlive()) {
            return false
        }
        return worker.sendData(payload)
    };
    StarGate.prototype.sendShip = function (outgo, remote, local) {
        var worker = this.getPorter(remote, local);
        if (!worker) {
            return false
        } else if (!worker.isAlive()) {
            return false
        }
        return worker.sendShip(outgo)
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
        var worker, cached;
        worker = this.getPorter(remote, local);
        if (worker) {
            return worker
        } else if (!shouldCreatePorter) {
            return null
        }
        worker = this.createPorter(remote, local);
        cached = this.setPorter(remote, local, worker);
        if (cached && cached !== worker) {
            cached.close()
        }
        if (worker instanceof StarPorter) {
            worker.setConnection(connection)
        }
        return worker
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
        var cached, worker;
        var remote, local;
        for (var i = porters.length - 1; i >= 0; --i) {
            worker = porters[i];
            if (worker.isOpen()) {
                worker.purge(now);
                continue
            }
            remote = worker.getRemoteAddress();
            local = worker.getLocalAddress();
            cached = this.removePorter(remote, local, worker);
            if (cached && cached !== worker) {
                cached.close()
            }
        }
    };
    StarGate.prototype.heartbeat = function (connection) {
        var remote = connection.getRemoteAddress();
        var local = connection.getLocalAddress();
        var worker = this.getPorter(remote, local);
        if (worker) {
            worker.heartbeat()
        }
    };
    StarGate.prototype.onConnectionStateChanged = function (previous, current, connection) {
        var s1 = PorterStatus.getStatus(previous);
        var s2 = PorterStatus.getStatus(current);
        if (s1 !== s2) {
            var notFinished = s2 !== PorterStatus.ERROR;
            var worker = this.dock(connection, notFinished);
            if (!worker) {
                return
            }
            var keeper = this.getDelegate();
            if (keeper) {
                keeper.onPorterStatusChanged(s1, s2, worker)
            }
        }
        var index = !current ? -1 : current.getIndex();
        if (ConnectionStateOrder.EXPIRED.equals(index)) {
            this.heartbeat(connection)
        }
    };
    StarGate.prototype.onConnectionReceived = function (data, connection) {
        var worker = this.dock(connection, true);
        if (worker) {
            worker.processReceived(data)
        }
    };
    StarGate.prototype.onConnectionSent = function (sent, data, connection) {
    };
    StarGate.prototype.onConnectionFailed = function (error, data, connection) {
    };
    StarGate.prototype.onConnectionError = function (error, connection) {
    }
})(StarTrek, FiniteStateMachine, MONKEY);
