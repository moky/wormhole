package chat.dim.utils;

import java.text.SimpleDateFormat;
import java.util.Date;


public final class Log {

    private static String now() {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        return formatter.format(new Date());
    }

    public static void info(String msg) {
        System.out.printf("[%s] %s\n", now(), msg);
    }

    public static void error(String msg) {
        System.out.printf("[%s] ERROR> %s\n", now(), msg);
    }

}
