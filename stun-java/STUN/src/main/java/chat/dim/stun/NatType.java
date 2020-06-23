/* license: https://mit-license.org
 *
 *  STUN: Session Traversal Utilities for NAT
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ==============================================================================
 */
package chat.dim.stun;

/** [RFC] https://www.ietf.org/rfc/rfc3489.txt
 *
 *  Rosenberg, et al.           Standards Track                    [Page 21]
 *
 *  RFC 3489                          STUN                        March 2003
 *
 *
 *                         +--------+
 *                         |  Test  |
 *                         |   I    |
 *                         +--------+
 *                              |
 *                              |
 *                              V
 *                             /\              /\
 *                          N /  \ Y          /  \ Y             +--------+
 *           UDP     <-------/Resp\--------->/ IP \------------->|  Test  |
 *           Blocked         \ ?  /          \Same/              |   II   |
 *                            \  /            \? /               +--------+
 *                             \/              \/                    |
 *                                              | N                  |
 *                                              |                    V
 *                                              V                    /\
 *                                          +--------+  Sym.      N /  \
 *                                          |  Test  |  UDP    <---/Resp\
 *                                          |   II   |  Firewall   \ ?  /
 *                                          +--------+              \  /
 *                                              |                    \/
 *                                              V                     |Y
 *                   /\                         /\                    |
 *    Symmetric  N  /  \       +--------+   N  /  \                   V
 *       NAT  <--- / IP \<-----|  Test  |<--- /Resp\               Open
 *                 \Same/      |   I    |     \ ?  /               Internet
 *                  \? /       +--------+      \  /
 *                   \/                         \/
 *                   |                           |Y
 *                   |                           |
 *                   |                           V
 *                   |                           Full
 *                   |                           Cone
 *                   V              /\
 *               +--------+        /  \ Y
 *               |  Test  |------>/Resp\---->Restricted
 *               |   III  |       \ ?  /
 *               +--------+        \  /
 *                                  \/
 *                                   |N
 *                                   |       Port
 *                                   +------>Restricted
 *
 *                  Figure 2: Flow for type discovery process
 */

public class NatType {

    public static final String UDPBlocked = "UDP Blocked";
    public static final String OpenInternet = "Open Internet";
    public static final String SymmetricFirewall = "Symmetric UDP Firewall";
    public static final String SymmetricNAT = "Symmetric NAT";
    public static final String FullConeNAT = "Full Cone NAT";
    public static final String RestrictedNAT = "Restricted Cone NAT";
    public static final String PortRestrictedNAT = "Port Restricted Cone NAT";
}
