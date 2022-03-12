package chat.dim.stargate;

import java.net.SocketAddress;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.startrek.PlainDocker;

public class TCPGate<H extends Hub> extends AutoGate<H> {

    public TCPGate(Docker.Delegate delegate, boolean isDaemon) {
        super(delegate, isDaemon);
    }

    public boolean send(byte[] payload, SocketAddress source, SocketAddress destination) {
        Docker worker = getDocker(destination, source, null);
        if (worker instanceof PlainDocker) {
            return ((PlainDocker) worker).send(payload);
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
        PlainDocker docker = new PlainDocker(conn);
        docker.setDelegate(getDelegate());
        return docker;
    }
}
