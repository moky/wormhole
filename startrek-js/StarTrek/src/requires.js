'use strict';

//-------- namespace --------
if (typeof st.type !== 'object') {
    st.type = {};
}
if (typeof st.net !== 'object') {
    st.net = {};
}
if (typeof st.port !== 'object') {
    st.port = {};
}
if (typeof st.socket !== 'object') {
    st.socket = {};
}

//-------- requires --------
var Interface      = mk.type.Interface;
var Class          = mk.type.Class;
var Implementation = mk.type.Implementation;
var IObject        = mk.type.Object;
var BaseObject     = mk.type.BaseObject;
var HashSet        = mk.type.HashSet;
var Enum           = mk.type.Enum;
var Arrays         = mk.type.Arrays;
var Mapper         = mk.type.Mapper;
var Stringer       = mk.type.Stringer;
var ConstantString = mk.type.ConstantString;

var Duration  = fsm.type.Duration;
var Processor = fsm.skywalker.Processor;
var Runnable  = fsm.skywalker.Runnable;
var Thread    = fsm.threading.Thread;
var Ticker    = fsm.threading.Ticker;
var Context        = fsm.Context;
var BaseMachine    = fsm.BaseMachine;
var BaseState      = fsm.BaseState;
var BaseTransition = fsm.BaseTransition;
