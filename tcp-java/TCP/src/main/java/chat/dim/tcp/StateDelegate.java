/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ==============================================================================
 */
package chat.dim.tcp;

import java.lang.ref.WeakReference;

import chat.dim.fsm.BaseMachine;
import chat.dim.fsm.BaseTransition;
import chat.dim.fsm.Context;
import chat.dim.fsm.Delegate;

public interface StateDelegate extends Delegate<StateMachine, StateTransition, ConnectionState> {

}

abstract class StateTransition extends BaseTransition<StateMachine> {

    protected StateTransition(String target) {
        super(target);
    }
}

class StateMachine extends BaseMachine<StateMachine, StateTransition, ConnectionState, Delegate<StateMachine, StateTransition, ConnectionState>>
        implements Context {

    private WeakReference<BaseConnection> connectionRef = null;

    public StateMachine() {
        super(ConnectionState.DEFAULT);

        // init states
        setState(ConnectionState.getDefaultState());
        setState(ConnectionState.getConnectingState());
        setState(ConnectionState.getConnectedState());
        setState(ConnectionState.getExpiredState());
        setState(ConnectionState.getMaintainingState());
        setState(ConnectionState.getErrorState());
    }

    @Override
    public StateMachine getContext() {
        return this;
    }

    private void setState(ConnectionState state) {
        addState(state.name, state);
    }

    BaseConnection getConnection() {
        return connectionRef == null ? null : connectionRef.get();
    }
    void setConnection(BaseConnection connection) {
        connectionRef = new WeakReference<>(connection);
    }
}
