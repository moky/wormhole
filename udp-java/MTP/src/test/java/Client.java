
import java.net.InetSocketAddress;
import java.net.SocketException;

import chat.dim.udp.Hub;

public class Client extends Node {

    static String HOST = "127.0.0.1";
    static int PORT = 9999;

    public Client(String host, int port) {
        super(host, port);
    }

    //
    //  Test
    //

    public static void main(String args[]) throws SocketException, InterruptedException {

        info("Connecting server (" + Server.HOST + ":" + Server.PORT + ") ...");

        InetSocketAddress destination = new InetSocketAddress(Server.HOST, Server.PORT);

        Hub hub = new Hub();
        hub.open(PORT);
        hub.start();

        Client client = new Client(HOST, PORT);
        client.setHub(hub);

        byte[] data;
        int index = 0;

        while (true) {
            data = ("PING " + ++index).getBytes();
            info(data);
            client.sendCommand(data, destination);
            Thread.sleep(2000);
        }
    }
}
