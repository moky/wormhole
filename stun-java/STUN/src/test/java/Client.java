
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.Map;

public class Client extends chat.dim.stun.Client {

    public Client(String host, int port) throws SocketException {
        super(host, port);
    }

    public Client(int port) throws SocketException {
        super(port);
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

        String serverIP = "129.226.128.17"; // HK-2
        int serverPort = 3478;

        SocketAddress serverAddress = new InetSocketAddress(serverIP, serverPort);

        Client client = new Client(9527);
        client.detect(serverAddress);

        System.exit(0);
    }
}
