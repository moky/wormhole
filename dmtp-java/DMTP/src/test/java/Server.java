
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;

public class Server extends chat.dim.dmtp.Server {

    public Server(String host, int port) throws SocketException {
        super(new InetSocketAddress(host, port));
    }

    @Override
    public boolean processCommand(Command cmd, SocketAddress source) {
        System.out.printf("received cmd from %s: %s\n", source, cmd);
        return super.processCommand(cmd, source);
    }

    @Override
    public boolean processMessage(Message msg, SocketAddress source) {
        System.out.printf("received msg from %s: %s\n", source, msg);
        return true;
    }

    static final String SERVER_Test = "192.168.31.64"; // Test
    static final String SERVER_GZ1 = "134.175.87.98"; // GZ-1
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final String SERVER_IP = SERVER_Test;
    static final int SERVER_PORT = 9395;

    public static void main(String args[]) throws SocketException {

        System.out.printf("UDP server (%s:%d) starting ...\n", SERVER_IP, SERVER_PORT);

        Server server = new Server(SERVER_IP, SERVER_PORT);

        ContactManager database = new ContactManager(server.peer);

        server.setDelegate(database);
        server.start();
    }
}
