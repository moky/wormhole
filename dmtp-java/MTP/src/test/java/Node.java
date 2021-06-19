
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.List;

import chat.dim.dmtp.Hub;
import chat.dim.dmtp.Peer;
import chat.dim.mtp.PeerHandler;
import chat.dim.mtp.Pool;
import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.mtp.task.Departure;
import chat.dim.type.ByteArray;

public class Node implements PeerHandler {

    public final Peer peer;

    public Node(Peer peer) {
        super();
        this.peer = peer;
        peer.setHandler(this);
    }

    public Node(SocketAddress address, Hub hub, Pool pool) throws SocketException {
        super();
        this.peer = createPeer(address, hub, pool);
        this.peer.setHandler(this);
    }

    public Node(SocketAddress address, Hub hub) throws SocketException {
        super();
        this.peer = createPeer(address, hub, null);
        this.peer.setHandler(this);
    }

    public Node(SocketAddress address, Pool pool) throws SocketException {
        super();
        this.peer = createPeer(address, null, pool);
        this.peer.setHandler(this);
    }

    public Node(SocketAddress address) throws SocketException {
        super();
        this.peer = createPeer(address, null, null);
        this.peer.setHandler(this);
    }

    protected Peer createPeer(SocketAddress address, Hub hub, Pool pool) throws SocketException {
        if (hub == null) {
            if (pool == null) {
                return new Peer(address);
            } else {
                return new Peer(address, pool);
            }
        } else if (pool == null) {
            return new Peer(address, hub);
        } else {
            return new Peer(address, hub, pool);
        }
    }

    public void start() {
        // start peer
        peer.start();
    }

    public void stop() {
        close();
    }

    public void close() {
        // stop peer
        peer.close();
    }

    //
    //  Send
    //

    /**
     *  Send command data to destination address
     *
     * @param cmd         - command data
     * @param destination - remote IP and port
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendCommand(ByteArray cmd, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, cmd);
        return peer.sendCommand(pack, destination);
    }

    /**
     *  Send message data to destination address
     *
     * @param msg         - message data
     * @param destination - remote IP and port
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendMessage(ByteArray msg, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, msg);
        return peer.sendMessage(pack, destination);
    }

    //
    //  PeerHandler
    //

    @Override
    public void onSendCommandSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after success to send command
    }

    @Override
    public void onSendCommandTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after failed to send command
    }

    @Override
    public void onSendMessageSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after success to send message
    }

    @Override
    public void onSendMessageTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after failed to send message
    }

    @Override
    public boolean onReceivedCommand(ByteArray cmd, SocketAddress source, SocketAddress destination) {
        // TODO: process after received command data
        String text = cmd.toString();
        System.out.printf("received cmd (%d bytes) from %s to %s: %s\n", cmd.getLength(), source, destination, text);
        return true;
    }

    @Override
    public boolean onReceivedMessage(ByteArray msg, SocketAddress source, SocketAddress destination) {
        // TODO: process after received message data
        String text = msg.toString();
        System.out.printf("received msg (%d bytes) from %s to %s: %s\n", msg.getLength(), source, destination, text);
        return true;
    }

    @Override
    public void onReceivedError(ByteArray data, SocketAddress source, SocketAddress destination) {
        // TODO: process after received error data
        String text = data.toString();
        System.out.printf("received msg (%d bytes) from %s to %s: %s\n", data.getLength(), source, destination, text);
    }

    @Override
    public boolean checkFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        // TODO: process after received command fragment
        return true;
    }

    @Override
    public void recycleFragments(List<Package> fragments, SocketAddress source, SocketAddress destination) {
        // TODO: process after failed to send message as fragments
    }
}
