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

    public boolean sendCommand(byte[] body, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.COMMAND, null, 1, 0, -1, new Data(body));
        return send(pack/*, Departure.Priority.SLOWER.value*/, source, destination);
    }

    public boolean sendMessage(byte[] body, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.MESSAGE, null, 1, 0, -1, new Data(body));
        return send(pack, source, destination);
    }

    public boolean send(Package pack, SocketAddress source, SocketAddress destination) {
        Docker worker = getDocker(destination, source, null);
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
    public Docker getDocker(SocketAddress remote, SocketAddress local) {
        return super.getDocker(remote, null);
    }

    @Override
    protected void setDocker(SocketAddress remote, SocketAddress local, Docker docker) {
        super.setDocker(remote, null, docker);
    }

    @Override
    protected void removeDocker(SocketAddress remote, SocketAddress local, Docker docker) {
        super.removeDocker(remote, null, docker);
    }

    @Override
    protected Docker createDocker(Connection conn, List<byte[]> data) {
        // TODO: check data format before creating docker
        PackageDocker docker = new PackageDocker(conn);
        docker.setDelegate(getDelegate());
        return docker;
    }
}
