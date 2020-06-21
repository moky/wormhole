
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.Charset;
import java.util.Arrays;
import java.util.List;

import chat.dim.mtp.PeerDelegate;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.mtp.task.Departure;
import chat.dim.udp.Hub;

public class Node implements PeerDelegate {

    private final Peer peer;
    private Hub hub = null;

    public final SocketAddress localAddress;

    public Node(SocketAddress address) {
        super();
        localAddress = address;
        peer = new Peer();
        peer.setDelegate(this);
        peer.start();
    }

    public Node(String host, int port) {
        this(new InetSocketAddress(host, port));
    }

    public Node(int port) {
        this("127.0.0.1", port);
    }

    public void setHub(Hub hub) {
        hub.addListener(peer);
        this.hub = hub;
    }

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, Charset.forName("UTF-8")));
    }

    public Departure sendCommand(byte[] cmd, SocketAddress destination) {
        return peer.sendCommand(cmd, destination, localAddress);
    }

    public Departure sendMessage(byte[] msg, SocketAddress destination) {
        return peer.sendMessage(msg, destination, localAddress);
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
        String string = new String(cmd, Charset.forName("UTF-8"));
        info("received cmd: " + string);
        return false;
    }

    @Override
    public boolean onReceivedMessage(byte[] msg, SocketAddress source, SocketAddress destination) {
        String string = new String(msg, Charset.forName("UTF-8"));
        info("received msg: " + string);
        return false;
    }

    @Override
    public boolean checkFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        return false;
    }

    @Override
    public void recycleFragments(List<Package> fragments, SocketAddress source, SocketAddress destination) {

    }
}
