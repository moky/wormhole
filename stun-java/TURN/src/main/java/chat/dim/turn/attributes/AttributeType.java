package chat.dim.turn.attributes;

import chat.dim.stun.attributes.AttributeValue;
import chat.dim.tlv.Data;
import chat.dim.turn.values.XorPeerAddressValue;
import chat.dim.turn.values.XorRelayedAddressValue;

/*  Mahy, et al.                 Standards Track                    [Page 5]
 *
 *  RFC 5766                          TURN                        April 2010
 *
 *
 *                                             Peer A
 *                                             Server-Reflexive    +---------+
 *                                             Transport Address   |         |
 *                                             192.0.2.150:32102   |         |
 *                                                 |              /|         |
 *                               TURN              |            / ^|  Peer A |
 *         Client's              Server            |           /  ||         |
 *         Host Transport        Transport         |         //   ||         |
 *         Address               Address           |       //     |+---------+
 *        10.1.1.2:49721       192.0.2.15:3478     |+-+  //     Peer A
 *                 |               |               ||N| /       Host Transport
 *                 |   +-+         |               ||A|/        Address
 *                 |   | |         |               v|T|     192.168.100.2:49582
 *                 |   | |         |               /+-+
 *      +---------+|   | |         |+---------+   /              +---------+
 *      |         ||   |N|         ||         | //               |         |
 *      | TURN    |v   | |         v| TURN    |/                 |         |
 *      | Client  |----|A|----------| Server  |------------------|  Peer B |
 *      |         |    | |^         |         |^                ^|         |
 *      |         |    |T||         |         ||                ||         |
 *      +---------+    | ||         +---------+|                |+---------+
 *                     | ||                    |                |
 *                     | ||                    |                |
 *                     +-+|                    |                |
 *                        |                    |                |
 *                        |                    |                |
 *                  Client's                   |            Peer B
 *                  Server-Reflexive    Relayed             Transport
 *                  Transport Address   Transport Address   Address
 *                  192.0.2.1:7000      192.0.2.15:50000    192.0.2.210:49191
 */

public class AttributeType extends chat.dim.stun.attributes.AttributeType {

    public AttributeType(chat.dim.stun.attributes.AttributeType type) {
        super(type);
    }

    public AttributeType(Data data, int value, String name) {
        super(data, value, name);
    }

    public AttributeType(Data data, int value) {
        super(data, value);
    }

    public AttributeType(int value, String name) {
        super(value, name);
    }

    public AttributeType(int value) {
        super(value);
    }

    // [RFC-3489] New STUN Attributes
    public static final AttributeType ChannelNumber      = new AttributeType(0x000C, "CHANNEL-NUMBER");
    public static final AttributeType Lifetime           = new AttributeType(0x000D, "LIFETIME");
    //public static final AttributeType Bandwidth          = new AttributeType(0x0010, "BANDWIDTH");  // Reserved
    public static final AttributeType XorPeerAddress     = new AttributeType(0x0012, "XOR-PEER-ADDRESS");
    public static final AttributeType Data               = new AttributeType(0x0013, "DATA");
    public static final AttributeType XorRelayedAddress  = new AttributeType(0x0016, "XOR-RELAYED-ADDRESS");
    public static final AttributeType EvenPort           = new AttributeType(0x0018, "EVEN-PORT");
    public static final AttributeType RequestedTransport = new AttributeType(0x0019, "REQUESTED-TRANSPORT");
    public static final AttributeType DoNotFragment      = new AttributeType(0x001A, "DONT-FRAGMENT");
    //public static final AttributeType TimerVal           = new AttributeType(0x0021, "TIMER-VAL");  // Reserved
    public static final AttributeType ReservationToken   = new AttributeType(0x0022, "RESERVATION-TOKEN");

    static {
        //
        //  Register attribute parsers
        //
        AttributeValue.register(XorPeerAddress,    XorPeerAddressValue.class);
        AttributeValue.register(XorRelayedAddress, XorRelayedAddressValue.class);
    }
}
