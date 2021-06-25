
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;

import chat.dim.udp.Cargo;
import chat.dim.udp.Hub;

public class Client extends chat.dim.stun.Client {

    static final SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_IP, Server.SERVER_PORT);
//    static final SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_GZ1, Server.SERVER_PORT);
//    static final SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_HK2, Server.SERVER_PORT);

    static final String CLIENT_IP = "192.168.31.91"; // Test
    static final int CLIENT_PORT = 9527;

    public final Hub hub;

    public Client(String host, int port) throws SocketException {
        super(host, port);
        hub = new Hub();
        hub.open(sourceAddress);
        //hub.start();
    }

    @Override
    public int send(byte[] data, SocketAddress destination, SocketAddress source) {
        return hub.send(data, destination, source);
    }

    @Override
    public byte[] receive() {
        Cargo cargo = hub.receive(2.0f);
        if (cargo == null) {
            return null;
        } else {
            info("received " + cargo.data.length + " bytes from " + cargo.source);
            return cargo.data;
        }
    }

    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    public void detect(SocketAddress serverAddress) {
        info("----------------------------------------------------------------");
        info("-- Detection starts from : " + serverAddress);
        Map<String, Object> res = getNatType(serverAddress);
        info("-- Detection Result: " + res.get("NAT"));
        info("-- External Address: " + res.get("MAPPED-ADDRESS"));
        info("----------------------------------------------------------------");
    }

    public static void main(String args[]) throws SocketException {

        Client client = new Client(CLIENT_IP, CLIENT_PORT);
        client.detect(SERVER_ADDRESS);

        System.exit(0);
    }
}
