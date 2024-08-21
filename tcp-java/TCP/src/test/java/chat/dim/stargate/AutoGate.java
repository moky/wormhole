package chat.dim.stargate;

import chat.dim.net.Hub;
import chat.dim.port.Porter;
import chat.dim.skywalker.Runner;
import chat.dim.threading.Daemon;

public abstract class AutoGate<H extends Hub>
        extends BaseGate<H>
        implements Runnable {

    private final Daemon daemon;
    private boolean running;

    public AutoGate(Porter.Delegate keeper, boolean isDaemon) {
        super(keeper);
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
        if (isRunning()) {
            stop();
            idle();
        }
        // 1. mark this gate to running
        running = true;
        // 2. start a background thread for this gate
        daemon.start();
    }

    public void stop() {
        // 1. mark this gate to stopped
        running = false;
        // 2. waiting for the gate to stop
        Runner.sleep(256);
        // 3. cancel the background thread
        daemon.stop();
    }

    @Override
    public void run() {
        while (isRunning()) {
            if (process()) {
                // process() return true,
                // means this thread is busy,
                // so process next task immediately
                continue;
            }
            // nothing to do now,
            // have a rest ^_^
            idle();
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
