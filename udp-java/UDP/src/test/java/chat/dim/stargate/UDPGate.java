package chat.dim.stargate;

import java.net.SocketAddress;
import java.util.List;

import chat.dim.mtp.DataType;
import chat.dim.mtp.Package;
import chat.dim.mtp.PackageDocker;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.type.Data;

public class UDPGate<H extends Hub> extends AutoGate<H> {

    public UDPGate(Docker.Delegate delegate, boolean isDaemon) {
        super(delegate, isDaemon);
    }

    public boolean sendCommand(byte[] body, SocketAddress remote, SocketAddress local) {
        Package pack = Package.create(DataType.COMMAND, null, 1, 0, -1, new Data(body));
        return send(pack, remote, local);
    }

    public boolean sendMessage(byte[] body, SocketAddress remote, SocketAddress local) {
        Package pack = Package.create(DataType.MESSAGE, null, 1, 0, -1, new Data(body));
        return send(pack, remote, local);
    }

    public boolean send(Package pack, SocketAddress remote, SocketAddress local) {
        Docker worker = getDocker(remote, local, null);
        if (worker instanceof PackageDocker) {
            return ((PackageDocker) worker).send(pack);
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
}
