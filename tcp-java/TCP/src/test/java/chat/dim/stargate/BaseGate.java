package chat.dim.stargate;

import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.startrek.StarGate;

public abstract class BaseGate<H extends Hub>
        extends StarGate {

    private H hub = null;

    protected BaseGate(Docker.Delegate delegate) {
        super(delegate);
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

    public Docker getDocker(SocketAddress remote, SocketAddress local, List<byte[]> data) {
        Docker docker = getDocker(remote, local);
        if (docker == null) {
            Connection conn = getHub().connect(remote, local);
            if (conn != null) {
                docker = getDocker(remote, local);
                if (docker == null) {
                    docker = createDocker(conn, data);
                    assert docker != null : "failed to create docker: " + remote + ", " + local;
                }
                setDocker(docker.getRemoteAddress(), docker.getLocalAddress(), docker);
            }
        }
        return docker;
    }

    @Override
    protected Docker getDocker(SocketAddress remote, SocketAddress local) {
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

    /*/
    @Override
    protected void heartbeat(Connection connection) {
        // let the client to do the job
        if (connection instanceof ActiveConnection) {
            super.heartbeat(connection);
        }
    }
    /*/

    @Override
    protected List<byte[]> cacheAdvanceParty(byte[] data, Connection connection) {
        // TODO: cache the advance party before decide which docker to use
        List<byte[]> array = new ArrayList<>();
        if (data != null) {
            array.add(data);
        }
        return array;
    }

    @Override
    protected void clearAdvanceParty(Connection connection) {
        // TODO: remove advance party for this connection
    }
}
