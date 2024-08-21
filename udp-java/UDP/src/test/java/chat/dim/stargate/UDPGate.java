package chat.dim.stargate;

import java.io.IOError;
import java.net.SocketAddress;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackagePorter;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Porter;
import chat.dim.utils.Log;

public class UDPGate<H extends Hub>
        extends AutoGate<H> {

    public UDPGate(Porter.Delegate keeper, boolean isDaemon) {
        super(keeper, isDaemon);
    }

    public boolean sendMessage(byte[] body, SocketAddress remote, SocketAddress local) {
        Porter docker = getPorter(remote, local);
        if (docker instanceof PackagePorter) {
            return ((PackagePorter) docker).sendMessage(body);
        } else {
            return false;
        }
    }

    public boolean sendCommand(byte[] body, SocketAddress remote, SocketAddress local) {
        Porter docker = getPorter(remote, local);
        if (docker instanceof PackagePorter) {
            return ((PackagePorter) docker).sendCommand(body);
        } else {
            return false;
        }
    }

    public boolean sendPackage(Package pack, SocketAddress remote, SocketAddress local) {
        Porter docker = getPorter(remote, local);
        if (docker instanceof PackagePorter) {
            return ((PackagePorter) docker).sendPackage(pack);
        } else {
            return false;
        }
    }

    //
    //  Docker
    //

    @Override
    protected Porter createPorter(SocketAddress remote, SocketAddress local) {
        // TODO: check data format before creating docker
        PackagePorter docker = new PackagePorter(remote, local);
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
