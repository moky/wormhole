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

    public AutoGate(Porter.Delegate delegate, boolean isDaemon) {
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
        if (isRunning()) {
            stop();
            idle();
        }
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
            if (process()) {
                // process() return true,
                // means this thread is busy,
                // so process next task immediately
            } else {
                // nothing to do now,
                // have a rest ^_^
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
