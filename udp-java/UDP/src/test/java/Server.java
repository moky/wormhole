import chat.dim.udp.*;

import java.net.SocketAddress;
import java.net.SocketException;

public class Server implements HubListener {

    static String HOST = "127.0.0.1";
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
        info(data);
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

    public static void main(String args[]) throws SocketException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        Hub hub = new Hub();
        hub.open(HOST, PORT);
        hub.start();

        hub.addListener(server);
    }
}
