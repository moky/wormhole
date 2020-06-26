
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.Charset;
import java.util.List;

import chat.dim.mtp.PeerDelegate;
import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.mtp.task.Departure;
import chat.dim.udp.Hub;

public class Node implements PeerDelegate {

    public final Peer peer;
    public final Hub hub;

    public final SocketAddress localAddress;

    public Node(SocketAddress address) throws SocketException {
        super();
        localAddress = address;
        peer = createPeer();
        hub = createHub();
    }

    public Node(String host, int port) throws SocketException {
        this(new InetSocketAddress(host, port));
    }

    protected Peer createPeer() {
        Peer peer = new Peer();
        peer.setDelegate(this);
        //peer.start();
        return peer;
    }

    protected Hub createHub() throws SocketException {
        InetSocketAddress address = (InetSocketAddress) localAddress;
        Hub hub = new Hub();
        hub.open(address.getHostString(), address.getPort());
        hub.addListener(peer);
        //hub.start();
        return hub;
    }

    public void start() {
        // start peer
        if (!peer.isRunning()) {
            peer.start();
        }
        // start hub
        if (!hub.isRunning()) {
            hub.start();
        }
    }

    public void stop() {
        // stop hub
        hub.close();
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
        return peer.sendCommand(pack, destination, localAddress);
    }

    public Departure sendMessage(byte[] msg, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, msg);
        return peer.sendMessage(pack, destination, localAddress);
    }

    //
    //  PeerDelegate
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
    public int sendData(byte[] data, SocketAddress destination, SocketAddress source) {
        return hub.send(data, destination, source);
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
