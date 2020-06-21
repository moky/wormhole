
import java.net.SocketException;

import chat.dim.udp.Hub;

public class Server extends Node {

    static String HOST = "127.0.0.1";
    static int PORT = 9394;

    public Server(String host, int port) {
        super(host, port);
    }

    //
    //  Test
    //

    private static Server server = new Server(HOST, PORT);

    public static void main(String args[]) throws SocketException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        Hub hub = new Hub();
        hub.open(HOST, PORT);
        hub.start();

        server.setHub(hub);
    }
}
