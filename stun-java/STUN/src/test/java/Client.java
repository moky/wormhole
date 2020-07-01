
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.Map;

public class Client extends chat.dim.stun.Client {

//    static final SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_IP, Server.SERVER_PORT);
    static final SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_HK2, Server.SERVER_PORT);

    static final String CLIENT_IP = "192.168.31.64"; // Test
    static final int CLIENT_PORT = 9527;

    public Client(String host, int port) throws SocketException {
        super(host, port);
    }

    public void detect(SocketAddress serverAddress) {
        info("----------------------------------------------------------------");
        info("-- Detection starts from : " + serverAddress);
        Map<String, Object> res = getNatType(serverAddress);
        info("-- Detection Result: " + res.get("NAT"));
        info("-- External Address: " + res.get("MAPPED-ADDRESS"));
        info("----------------------------------------------------------------");
    }

    public static void main(String args[]) throws SocketException {

        Client client = new Client(CLIENT_IP, CLIENT_PORT);
        client.detect(SERVER_ADDRESS);

        System.exit(0);
    }
}
