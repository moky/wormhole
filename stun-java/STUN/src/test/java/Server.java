
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.text.SimpleDateFormat;
import java.util.Date;

import chat.dim.type.Data;
import chat.dim.udp.Cargo;
import chat.dim.udp.Hub;

public class Server extends chat.dim.stun.Server {

    static final String SERVER_Test = "192.168.31.91"; // Test
    static final String SERVER_GZ1 = "134.175.87.98"; // GZ-1
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final InetSocketAddress CHANGED_ADDRESS = new InetSocketAddress(SERVER_HK2, 3478);
    static final InetSocketAddress NEIGHBOUR_SERVER = new InetSocketAddress(SERVER_HK2, 3478);

    static final String SERVER_IP = SERVER_Test;
    static final int SERVER_PORT = 3478;
    static final int CHANGE_PORT = 3479;

    public final Hub hub;

    public Server(String host, int port, int changePort) throws SocketException {
        super(host, port, changePort);
        hub = new Hub();
        hub.open(sourceAddress);
        hub.open(new InetSocketAddress(host, changePort));
        //hub.start();
    }

    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    /**
     *  Received data from any socket
     *
     * @param timeout - in seconds
     * @return data and remote address
     */
    public Cargo receive(float timeout) {
        return hub.receive(timeout);
    }

    public Cargo receive() {
        return receive(2.0f);
    }

    @Override
    public int send(byte[] data, SocketAddress destination, SocketAddress source) {
        return hub.send(data, destination, source);
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
                handle(new Data(cargo.data), cargo.source);
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
