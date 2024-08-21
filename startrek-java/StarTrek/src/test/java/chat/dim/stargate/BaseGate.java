package chat.dim.stargate;

import java.net.SocketAddress;

import chat.dim.net.Hub;
import chat.dim.port.Porter;
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

    /*/
    @Override
    protected void heartbeat(Connection connection) {
        // let the client to do the job
        if (connection instanceof ActiveConnection) {
            super.heartbeat(connection);
        }
    }
    /*/

}
