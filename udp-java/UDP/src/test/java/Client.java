import chat.dim.udp.Hub;

import java.net.InetSocketAddress;
import java.net.SocketException;
import java.nio.charset.Charset;

public class Client {

    //
    //  Test
    //

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, Charset.forName("UTF-8")));
    }

    public static void main(String args[]) throws SocketException, InterruptedException {

        info("Connecting server (" + Server.HOST + ":" + Server.PORT + ") ...");

        InetSocketAddress destination = new InetSocketAddress(Server.HOST, Server.PORT);

        Hub hub = new Hub();
        hub.open(9999);

        byte[] data;
        int index = 0;

        while (true) {
            data = ("PING " + ++index).getBytes();
            info(data);
            hub.send(data, destination);
            Thread.sleep(2000);
        }
    }
}
