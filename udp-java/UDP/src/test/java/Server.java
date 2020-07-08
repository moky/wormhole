
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.Charset;

import chat.dim.udp.*;

public class Server implements HubListener {

//    static String HOST = "127.0.0.1";
    static String HOST = "192.168.31.64";
    static int PORT = 9394;

    //
    //  HubListener
    //

    @Override
    public HubFilter getFilter() {
        return null;
    }

    @Override
    public byte[] onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, Charset.forName("UTF-8"));
        info("received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
        return null;
    }

    @Override
    public void onStatusChanged(Connection connection, ConnectionStatus oldStatus, ConnectionStatus newStatus) {
        // do nothing
    }

    //
    //  Test
    //

    private static void info(String msg) {
        Client.info(msg);
    }
    private static void info(byte[] data) {
        Client.info(data);
    }

    private static Server server = new Server();
    private static Hub hub = new Hub();

    public static void main(String args[]) throws SocketException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        hub.open(HOST, PORT);
        hub.start();
        hub.addListener(server);
    }
}
