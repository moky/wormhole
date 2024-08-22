package chat.dim.stargate;

import java.net.SocketAddress;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Porter;
import chat.dim.socket.ActiveConnection;
import chat.dim.startrek.StarGate;

public abstract class BaseGate<H extends Hub>
        extends StarGate {

    private H hub = null;

    protected BaseGate(Porter.Delegate keeper) {
        super(keeper);
    }

    public H getHub() {
        return hub;
    }
    public void setHub(H h) {
        hub = h;
    }

    //
    //  Docker
    //

    @Override
    protected Porter getPorter(SocketAddress remote, SocketAddress local) {
        return super.getPorter(remote, null);
    }

    @Override
    protected Porter setPorter(SocketAddress remote, SocketAddress local, Porter porter) {
        return super.setPorter(remote, null, porter);
    }

    @Override
    protected Porter removePorter(SocketAddress remote, SocketAddress local, Porter porter) {
        return super.removePorter(remote, null, porter);
    }

    public Porter fetchPorter(SocketAddress remote, SocketAddress local) {
        // get connection from hub
        Connection conn = getHub().connect(remote, local);
        if (conn == null) {
            assert false : "failed to get connection: " + local + " -> " + remote;
            return null;
        }
        // connected, get docker with this connection
        return dock(conn, true);
    }

    public boolean sendResponse(byte[] payload, Arrival ship, SocketAddress remote, SocketAddress local) {
        Porter docker = getPorter(remote, local);
        if (docker == null) {
            return false;
        } else if (!docker.isAlive()) {
            return false;
        }
        return docker.sendData(payload);
    }

    @Override
    protected void heartbeat(Connection connection) {
        // let the client to do the job
        if (connection instanceof ActiveConnection) {
            super.heartbeat(connection);
        }
    }

}
