
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;

import chat.dim.udp.Cargo;

public class Server extends chat.dim.stun.Server {

    static final String SERVER_Test = "192.168.31.64"; // Test
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final SocketAddress CHANGED_ADDRESS = new InetSocketAddress(SERVER_HK2, 3478);
    static final SocketAddress NEIGHBOUR_SERVER = new InetSocketAddress(SERVER_HK2, 3478);

    static final String SERVER_IP = SERVER_Test;
    static final int SERVER_PORT = 3478;
    static final int CHANGE_PORT = 3479;

    public Server(String host, int port, int changePort) throws SocketException {
        super(host, port, changePort);
    }

    public void start() {
        info("STUN server started");
        info("source address: " + sourceAddress + ", another port: " + changePort + ", neighbour server: " + neighbour);
        info("changed address: " + changedAddress);

        run();  // run forever
    }

    public void run() {
        Cargo cargo;
        while (true) {
            try {
                cargo = receive();
                if (cargo == null) {
                    _sleep(0.1);
                    continue;
                }
                handle(cargo.data, cargo.source);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private void _sleep(double seconds) {
        try {
            Thread.sleep((long) (seconds * 1000));
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public static void main(String args[]) throws SocketException {

        Server server = new Server(SERVER_IP, SERVER_PORT, CHANGE_PORT);
        server.changedAddress = CHANGED_ADDRESS;
        server.neighbour = NEIGHBOUR_SERVER;
        server.start();

        System.exit(0);
    }
}
