
import java.net.InetSocketAddress;
import java.net.SocketException;

public class Server extends Node {

    static String HOST = "127.0.0.1";
    static int PORT = 9394;

    public Server(String host, int port) throws SocketException {
        super(new InetSocketAddress(host, port));
    }

    //
    //  Test
    //

    public static void main(String args[]) throws SocketException {

        System.out.printf("Starting server (%s:%d) ...\n", HOST, PORT);

        Server server = new Server(HOST, PORT);
        server.start();
    }
}
