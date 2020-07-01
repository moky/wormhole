
import java.net.InetSocketAddress;
import java.net.SocketException;
import java.nio.charset.Charset;

public class Client extends Node {

    static String HOST = "127.0.0.1";
    static int PORT = 9999;

    public Client(String host, int port) throws SocketException {
        super(new InetSocketAddress(host, port));
    }

    //
    //  Test
    //

    public static void main(String args[]) throws SocketException, InterruptedException {

        System.out.printf("Connecting server (%s:%d) ...\n", Server.HOST, Server.PORT);

        InetSocketAddress destination = new InetSocketAddress(Server.HOST, Server.PORT);

        Client client = new Client(HOST, PORT);

        StringBuilder text = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            text.append(" Hello!");
        }

        byte[] data;

        for (int index = 0; index < 16; ++index) {
            data = (index + " sheep:" + text).getBytes();
            System.out.printf("sending (%d bytes): %s\n", data.length, new String(data, Charset.forName("UTF-8")));
            client.sendCommand(data, destination);
            client.sendMessage(data, destination);
            Thread.sleep(2000);
        }

        client.stop();
    }
}
