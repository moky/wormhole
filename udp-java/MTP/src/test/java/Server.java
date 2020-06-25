
import java.net.SocketException;

public class Server extends Node {

    static String HOST = "127.0.0.1";
    static int PORT = 9394;

    public Server(String host, int port) throws SocketException {
        super(host, port);
    }

    //
    //  Test
    //

    public static void main(String args[]) throws SocketException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        Server server = new Server(HOST, PORT);
        server.start();
    }
}
