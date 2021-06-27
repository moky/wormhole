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
package chat.dim.net;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.channels.AlreadyBoundException;
import java.nio.channels.AlreadyConnectedException;
import java.nio.channels.AsynchronousCloseException;
import java.nio.channels.ByteChannel;
import java.nio.channels.ClosedByInterruptException;
import java.nio.channels.ClosedChannelException;
import java.nio.channels.ConnectionPendingException;
import java.nio.channels.IllegalBlockingModeException;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;
import java.nio.channels.UnresolvedAddressException;
import java.nio.channels.UnsupportedAddressTypeException;

public interface Channel extends ByteChannel {

    //boolean isOpen();
    boolean isBound();

    //void close() throws IOException;


    /*================================================*\
    |*          Readable Byte Channel                 *|
    \*================================================*/

    //int read(ByteBuffer dst) throws IOException;


    /*================================================*\
    |*          Writable Byte Channel                 *|
    \*================================================*/

    //int write(ByteBuffer src) throws IOException;


    /*================================================*\
    |*          Selectable Channel                    *|
    \*================================================*/

    /**
     * Adjusts this channel's blocking mode.
     *
     * <p> If this channel is registered with one or more selectors then an
     * attempt to place it into blocking mode will cause an {@link
     * IllegalBlockingModeException} to be thrown.
     *
     * <p> This method may be invoked at any time.  The new blocking mode will
     * only affect I/O operations that are initiated after this method returns.
     * For some implementations this may require blocking until all pending I/O
     * operations are complete.
     *
     * <p> If this method is invoked while another invocation of this method or
     * of the {link #register(Selector, int) register} method is in progress
     * then it will first block until the other operation is complete. </p>
     *
     * @param  block  If <tt>true</tt> then this channel will be placed in
     *                blocking mode; if <tt>false</tt> then it will be placed
     *                non-blocking mode
     *
     * @return  This selectable channel
     *
     * @throws  ClosedChannelException
     *          If this channel is closed
     *
     * @throws  IllegalBlockingModeException
     *          If <tt>block</tt> is <tt>true</tt> and this channel is
     *          registered with one or more selectors
     *
     * @throws IOException
     *         If an I/O error occurs
     */
    SelectableChannel configureBlocking(boolean block) throws IOException;

    /**
     * Tells whether or not every I/O operation on this channel will block
     * until it completes.  A newly-created channel is always in blocking mode.
     *
     * <p> If this channel is closed then the value returned by this method is
     * not specified. </p>
     *
     * @return <tt>true</tt> if, and only if, this channel is in blocking mode
     */
    boolean isBlocking();


    /*================================================*\
    |*          Network Channel                       *|
    \*================================================*/

    /**
     * Binds the channel's socket to a local address.
     *
     * <p> This method is used to establish an association between the socket and
     * a local address. Once an association is established then the socket remains
     * bound until the channel is closed. If the {@code local} parameter has the
     * value {@code null} then the socket will be bound to an address that is
     * assigned automatically.
     *
     * @param   local
     *          The address to bind the socket, or {@code null} to bind the socket
     *          to an automatically assigned socket address
     *
     * @return  This channel
     *
     * @throws  AlreadyBoundException
     *          If the socket is already bound
     * @throws  UnsupportedAddressTypeException
     *          If the type of the given address is not supported
     * @throws  ClosedChannelException
     *          If the channel is closed
     * @throws  IOException
     *          If some other I/O error occurs
     * @throws  SecurityException
     *          If a security manager is installed and it denies an unspecified
     *          permission. An implementation of this interface should specify
     *          any required permissions.
     *
     * @see #getLocalAddress
     */
    NetworkChannel bind(SocketAddress local) throws IOException;

    /**
     * Returns the socket address that this channel's socket is bound to.
     *
     * <p> Where the channel is {@link #bind bound} to an Internet Protocol
     * socket address then the return value from this method is of type {@link
     * java.net.InetSocketAddress}.
     *
     * @return  The socket address that the socket is bound to, or {@code null}
     *          if the channel's socket is not bound
     *
     * @throws  ClosedChannelException
     *          If the channel is closed
     * @throws  IOException
     *          If an I/O error occurs
     */
    SocketAddress getLocalAddress() throws IOException;


    /*================================================*\
    |*          Socket/Datagram Channel               *|
    \*================================================*/

    /**
     * Tells whether or not this channel's network socket is connected.
     *
     * @return  <tt>true</tt> if, and only if, this channel's network socket
     *          is {@link #isOpen open} and connected
     */
    boolean isConnected();

    /**
     * Connects this channel's socket.
     *
     * <p> If this channel is in non-blocking mode then an invocation of this
     * method initiates a non-blocking connection operation.  If the connection
     * is established immediately, as can happen with a local connection, then
     * this method returns <tt>true</tt>.  Otherwise this method returns
     * <tt>false</tt> and the connection operation must later be completed by
     * invoking the {link #finishConnect finishConnect} method.
     *
     * <p> If this channel is in blocking mode then an invocation of this
     * method will block until the connection is established or an I/O error
     * occurs.
     *
     * <p> This method performs exactly the same security checks as the {@link
     * java.net.Socket} class.  That is, if a security manager has been
     * installed then this method verifies that its {@link
     * java.lang.SecurityManager#checkConnect checkConnect} method permits
     * connecting to the address and port number of the given remote endpoint.
     *
     * <p> This method may be invoked at any time.  If a read or write
     * operation upon this channel is invoked while an invocation of this
     * method is in progress then that operation will first block until this
     * invocation is complete.  If a connection attempt is initiated but fails,
     * that is, if an invocation of this method throws a checked exception,
     * then the channel will be closed.  </p>
     *
     * @param  remote
     *         The remote address to which this channel is to be connected
     *
     * @return  <tt>true</tt> if a connection was established,
     *          <tt>false</tt> if this channel is in non-blocking mode
     *          and the connection operation is in progress
     *
     * @throws AlreadyConnectedException
     *          If this channel is already connected
     *
     * @throws ConnectionPendingException
     *          If a non-blocking connection operation is already in progress
     *          on this channel
     *
     * @throws ClosedChannelException
     *          If this channel is closed
     *
     * @throws AsynchronousCloseException
     *          If another thread closes this channel
     *          while the connect operation is in progress
     *
     * @throws ClosedByInterruptException
     *          If another thread interrupts the current thread
     *          while the connect operation is in progress, thereby
     *          closing the channel and setting the current thread's
     *          interrupt status
     *
     * @throws  UnresolvedAddressException
     *          If the given remote address is not fully resolved
     *
     * @throws  UnsupportedAddressTypeException
     *          If the type of the given remote address is not supported
     *
     * @throws  SecurityException
     *          If a security manager has been installed
     *          and it does not permit access to the given remote endpoint
     *
     * @throws  IOException
     *          If some other I/O error occurs
     */
    NetworkChannel connect(SocketAddress remote) throws IOException;

    /**
     * Returns the remote address to which this channel's socket is connected.
     *
     * <p> Where the channel is bound and connected to an Internet Protocol
     * socket address then the return value from this method is of type {@link
     * java.net.InetSocketAddress}.
     *
     * @return  The remote address; {@code null} if the channel's socket is not
     *          connected
     *
     * @throws  ClosedChannelException
     *          If the channel is closed
     * @throws  IOException
     *          If an I/O error occurs
     *
     * @since 1.7
     */
    SocketAddress getRemoteAddress() throws IOException;


    /*================================================*\
    |*          Datagram Channel                      *|
    \*================================================*/

    /**
     * Disconnects this channel's socket.
     *
     * <p> The channel's socket is configured so that it can receive datagrams
     * from, and sends datagrams to, any remote address so long as the security
     * manager, if installed, permits it.
     *
     * <p> This method may be invoked at any time.  It will not have any effect
     * on read or write operations that are already in progress at the moment
     * that it is invoked.
     *
     * <p> If this channel's socket is not connected, or if the channel is
     * closed, then invoking this method has no effect.  </p>
     *
     * @return  This datagram channel
     *
     * @throws  IOException
     *          If some other I/O error occurs
     */
    ByteChannel disconnect() throws IOException;
}
