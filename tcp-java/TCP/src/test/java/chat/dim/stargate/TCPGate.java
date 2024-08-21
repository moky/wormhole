package chat.dim.stargate;

import java.io.IOError;
import java.net.SocketAddress;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Porter;
import chat.dim.startrek.PlainPorter;
import chat.dim.utils.Log;

public class TCPGate<H extends Hub>
        extends AutoGate<H> {

    public TCPGate(Porter.Delegate keeper, boolean isDaemon) {
        super(keeper, isDaemon);
    }

    public boolean sendMessage(byte[] payload, SocketAddress remote, SocketAddress local) {
        Porter docker = fetchPorter(remote, local);
        if (docker == null) {
            return false;
        }
        return docker.sendData(payload);
    }

    //
    //  Docker
    //

    @Override
    protected Porter createPorter(SocketAddress remote, SocketAddress local) {
        // TODO: check data format before creating docker
        PlainPorter docker = new PlainPorter(remote, local);
        docker.setDelegate(getDelegate());
        return docker;
    }

    //
    //  Connection Delegate
    //

    @Override
    public void onConnectionStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        super.onConnectionStateChanged(previous, current, connection);
        Log.info("connection state changed: " + previous + " -> " + current + ", " + connection);
    }

    @Override
    public void onConnectionFailed(IOError error, byte[] data, Connection connection) {
        super.onConnectionFailed(error, data, connection);
        Log.error("connection failed: " + error + ", " + connection);
    }

    @Override
    public void onConnectionError(IOError error, Connection connection) {
        super.onConnectionError(error, connection);
        Log.error("connection error: " + error + ", " + connection);
    }

}
