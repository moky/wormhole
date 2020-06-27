
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.Charset;
import java.util.List;

import chat.dim.mtp.PeerHandler;
import chat.dim.mtp.Pool;
import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.mtp.task.Departure;

public class Node implements PeerHandler {

    public final Peer peer;

    public Node(Peer peer) {
        super();
        this.peer = peer;
        peer.setHandler(this);
    }

    public Node(SocketAddress address, Hub hub, Pool pool) throws SocketException {
        this(createPeer(address, hub, pool));
    }

    public Node(SocketAddress address, Hub hub) throws SocketException {
        this(address, hub, null);
    }

    public Node(SocketAddress address, Pool pool) throws SocketException {
        this(address, null, pool);
    }

    public Node(SocketAddress address) throws SocketException {
        this(address, null, null);
    }

    public Node(String host, int port) throws SocketException {
        this(new InetSocketAddress(host, port), null, null);
    }

    private static Peer createPeer(SocketAddress address, Hub hub, Pool pool) throws SocketException {
        Peer peer;
        if (hub == null) {
            if (pool == null) {
                peer = new Peer(address);
            } else {
                peer = new Peer(address, pool);
            }
        } else if (pool == null) {
            peer = new Peer(address, hub);
        } else {
            peer = new Peer(address, hub, pool);
        }
        //peer.start();
        return peer;
    }

    public void start() {
        // start peer
        peer.start();
    }

    public void stop() {
        // stop peer
        peer.close();
    }

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, Charset.forName("UTF-8")));
    }

    public Departure sendCommand(byte[] cmd, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, cmd);
        return peer.sendCommand(pack, destination);
    }

    public Departure sendMessage(byte[] msg, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, msg);
        return peer.sendMessage(pack, destination);
    }

    //
    //  PeerHandler
    //

    @Override
    public void onSendCommandSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public void onSendCommandTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public void onSendMessageSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public void onSendMessageTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public boolean onReceivedCommand(byte[] cmd, SocketAddress source, SocketAddress destination) {
        String text = new String(cmd, Charset.forName("UTF-8"));
        info("received cmd (" + cmd.length + " bytes) from " + source + " to " + destination + ": " + text);
        return false;
    }

    @Override
    public boolean onReceivedMessage(byte[] msg, SocketAddress source, SocketAddress destination) {
        String text = new String(msg, Charset.forName("UTF-8"));
        info("received msg (" + msg.length + " bytes) from " + source + " to " + destination + ": " + text);
        return false;
    }

    @Override
    public boolean checkFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        return true;
    }

    @Override
    public void recycleFragments(List<Package> fragments, SocketAddress source, SocketAddress destination) {

    }
}
