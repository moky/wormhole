package chat.dim.stargate;

import java.net.SocketAddress;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageDocker;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Docker;

public class UDPGate<H extends Hub> extends AutoGate<H> {

    public UDPGate(Docker.Delegate delegate, boolean isDaemon) {
        super(delegate, isDaemon);
    }

    public boolean sendMessage(byte[] body, SocketAddress remote, SocketAddress local) {
        Docker docker = getDocker(remote, local, null);
        if (docker instanceof PackageDocker) {
            return ((PackageDocker) docker).sendMessage(body);
        } else {
            return false;
        }
    }

    public boolean sendCommand(byte[] body, SocketAddress remote, SocketAddress local) {
        Docker docker = getDocker(remote, local, null);
        if (docker instanceof PackageDocker) {
            return ((PackageDocker) docker).sendCommand(body);
        } else {
            return false;
        }
    }

    public boolean sendPackage(Package pack, SocketAddress remote, SocketAddress local) {
        Docker docker = getDocker(remote, local, null);
        if (docker instanceof PackageDocker) {
            return ((PackageDocker) docker).sendPackage(pack);
        } else {
            return false;
        }
    }

    //
    //  Docker
    //

    @Override
    protected Docker createDocker(Connection conn, List<byte[]> data) {
        // TODO: check data format before creating docker
        PackageDocker docker = new PackageDocker(conn);
        docker.setDelegate(getDelegate());
        return docker;
    }

    //
    //  Connection Delegate
    //

    @Override
    public void onConnectionStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        super.onConnectionStateChanged(previous, current, connection);
        info("connection state changed: " + previous + " -> " + current + ", " + connection);
    }

    @Override
    public void onConnectionFailed(Throwable error, byte[] data, Connection connection) {
        super.onConnectionFailed(error, data, connection);
        error("connection failed: " + error + ", " + connection);
    }

    @Override
    public void onConnectionError(Throwable error, Connection connection) {
        super.onConnectionError(error, connection);
        error("connection error: " + error + ", " + connection);
    }

    public static void info(String msg) {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String now = formatter.format(new Date());
        System.out.printf("[%s] %s\n", now, msg);
    }
    public static void error(String msg) {
        System.out.printf("ERROR> %s\n", msg);
    }
}
