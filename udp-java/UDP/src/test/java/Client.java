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

        StringBuilder text = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            text.append(" Hello!");
        }

        byte[] data;

        for (int index = 0; index < 16; ++index) {
            data = (index + " sheep:" + text).getBytes();
            info("sending (" + data.length + " bytes): " + new String(data, Charset.forName("UTF-8")));
            hub.send(data, destination);
            Thread.sleep(2000);
        }

        hub.close();
    }
}
