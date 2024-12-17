/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.socket;

import java.io.IOError;
import java.lang.ref.WeakReference;
import java.net.SocketAddress;

import chat.dim.net.Channel;
import chat.dim.net.Hub;
import chat.dim.skywalker.Runner;
import chat.dim.threading.Daemon;

/**
 * Active connection for client
 */
public final class ActiveConnection extends BaseConnection implements Runnable {

    private final Daemon daemon;

    private WeakReference<Hub> hubRef;

    public ActiveConnection(SocketAddress remote, SocketAddress local) {
        super(remote, local);
        daemon = new Daemon(this);
        hubRef = null;
    }

    private Hub getHub() {
        WeakReference<Hub> ref = hubRef;
        return ref == null ? null : ref.get();
    }

    @Override
    public boolean isOpen() {
        return getStateMachine() != null;
    }

    @Override
    public void start(Hub hub) {
        assert hub != null : "start hub can not be empty";
        hubRef = new WeakReference<>(hub);
        // 1. start state machine
        startMachine();
        // 2. start a background thread to check channel
        daemon.start();
    }

    @Override
    public void run() {
        long expired = 0;
        long lastTime = 0;
        long interval = 8000;
        long now;
        Channel sock;
        while (true) {
            Runner.sleep(1000);
            if (!isOpen()) {
                break;
            }
            now = System.currentTimeMillis();
            try {
                sock = getChannel();
                if (sock == null || !sock.isOpen()) {
                    // first time to try connecting (lastTime == 0)?
                    // or connection lost, then try to reconnect again.
                    // check time interval for the trying here
                    if (now < lastTime + interval) {
                        continue;
                    } else {
                        // update last connect time
                        lastTime = now;
                    }
                    // get new socket channel via hub
                    Hub hub = getHub();
                    if (hub == null) {
                        assert false : "hub not found: " + getLocalAddress() + " -> " + getRemoteAddress();
                        break;
                    }
                    // try to open a new socket channel from the hub.
                    // the returned socket channel is opened for connecting,
                    // but maybe failed,
                    // so set an expired time to close it after timeout;
                    // if failed to open a new socket channel,
                    // then extend the time interval for next trying.
                    sock = openChannel(hub);
                    if (sock != null) {
                        // connect timeout after 2 minutes
                        expired = now + 128000;
                    } else if (interval < 128000) {
                        interval <<= 1;
                    }
                } else if (sock.isAlive()) {
                    // socket channel is normal, reset the time interval here.
                    // this will work when the current connection lost
                    interval = 8000;
                } else if (0 < expired && expired < now) {
                    // connect timeout
                    sock.close();
                }
            } catch (Exception ex) {
                //ex.printStackTrace();
                Delegate delegate = getDelegate();
                if (delegate != null) {
                    delegate.onConnectionError(new IOError(ex), this);
                }
            }
        }
        // connection exists
        System.out.println("[Socket] active connection exits: " + remoteAddress);
    }

}
