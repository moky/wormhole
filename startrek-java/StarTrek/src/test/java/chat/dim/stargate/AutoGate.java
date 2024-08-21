package chat.dim.stargate;

import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.skywalker.Runner;
import chat.dim.threading.Daemon;

public abstract class AutoGate<H extends Hub>
        extends BaseGate<H>
        implements Runnable {

    private final Daemon daemon;
    private boolean running;

    public AutoGate(Docker.Delegate delegate, boolean isDaemon) {
        super(delegate);
        daemon = new Daemon(this, isDaemon);
        running = false;
    }

    //
    //  Threading
    //

    public boolean isRunning() {
        return running;
    }

    public void start() {
        stop();
        running = true;
        daemon.start();
    }

    public void stop() {
        running = false;
        daemon.stop();
    }

    @Override
    public void run() {
        running = true;
        while (isRunning()) {
            if (!process()) {
                idle();
            }
        }
    }

    protected void idle() {
        Runner.sleep(128);
    }

    @Override
    public boolean process() {
        boolean incoming = getHub().process();
        boolean outgoing = super.process();
        return incoming || outgoing;
    }
}
