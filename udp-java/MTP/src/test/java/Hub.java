
import chat.dim.mtp.PeerDelegate;

import java.net.SocketAddress;

public class Hub extends chat.dim.udp.Hub implements PeerDelegate {

    @Override
    public int sendData(byte[] data, SocketAddress destination, SocketAddress source) {
        return send(data, destination, source);
    }
}
