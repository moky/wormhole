package chat.dim.mtp;

import java.net.InetSocketAddress;
import java.net.SocketException;

import chat.dim.type.Data;
import chat.dim.type.MutableData;

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

        Data fixed = new Data(text.toString().getBytes());
        MutableData data;

        for (int index = 0; index < 16; ++index) {
            data = new MutableData(1024);
            data.append((index + " sheep:").getBytes());
            data.append(fixed);
            System.out.printf("sending (%d bytes): %s\n", data.getSize(), data);
            client.sendCommand(data, destination);
            client.sendMessage(data, destination);
            Thread.sleep(2000);
        }

        client.stop();
    }
}
