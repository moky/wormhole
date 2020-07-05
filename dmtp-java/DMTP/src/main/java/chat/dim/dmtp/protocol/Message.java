/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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
package chat.dim.dmtp.protocol;

import java.util.ArrayList;
import java.util.List;

import chat.dim.dmtp.fields.Field;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;
import chat.dim.dmtp.fields.FieldsValue;
import chat.dim.dmtp.values.*;
import chat.dim.tlv.Data;

/*     Message
 *     ~~~~~~~
 *
 *         Fields:
 *
 *             <Envelope>
 *             S - Sender
 *             R - Receiver
 *             W - Time (OPTIONAL)
 *
 *             T - msg Type (OPTIONAL)
 *             G - Group ID (OPTIONAL)
 *
 *             <Body>
 *             D - content Data
 *             V - signature, Verify it with content data and sender's meta.key
 *             K - symmetric Key for en/decrypt content data (OPTIONAL)
 *
 *             <Attachments>
 *             M - sender's Meta info (OPTIONAL)
 *             P - sender's Profile info (OPTIONAL)
 *
 *     File
 *     ~~~~
 *
 *         Fields:
 *
 *             F - Filename
 *             D - file content Data
 *
 *             S - Sender (OPTIONAL)
 *             R - Receiver (OPTIONAL)
 *             V - signature (OPTIONAL)
 *             K - symmetric key (OPTIONAL)
 */

public class Message extends FieldsValue {

    // envelope
    private String sender = null;
    private String receiver = null;
    private long timestamp = 0; // message time (in seconds)
    private int type = 0;
    private String group = null;

    // body
    private Data content = null;
    private Data signature = null;
    private Data key = null;

    // attachments
    private Data meta = null;
    private Data profile = null;

    // file in message
    private String filename = null;

    public Message(Data data, List<Field> fields) {
        super(data, fields);
    }

    public Message(List<Field> fields) {
        super(fields);
    }

    //
    //  envelope
    //
    public String getSender() {
        if (sender == null) {
            sender = (String) get(SENDER);
        }
        return sender;
    }
    public String getReceiver() {
        if (receiver == null) {
            receiver = (String) get(RECEIVER);
        }
        return receiver;
    }
    public long getTimestamp() {
        if (timestamp == 0) {
            timestamp = (long) get(TIME);
        }
        return timestamp;
    }
    public int getType() {
        if (type == 0) {
            type = (int) get(TYPE);
        }
        return type;
    }
    public String getGroup() {
        if (group == null) {
            group = (String) get(GROUP);
        }
        return group;
    }

    //
    //  body
    //
    public Data getContent() {
        if (content == null) {
            content = (Data) get(CONTENT);
        }
        return content;
    }
    public Data getSignature() {
        if (signature == null) {
            signature = (Data) get(CONTENT);
        }
        return signature;
    }
    public Data getKey() {
        if (key == null) {
            key = (Data) get(CONTENT);
        }
        return key;
    }

    //
    //  attachments
    //
    public Data getMeta() {
        if (meta == null) {
            meta = (Data) get(CONTENT);
        }
        return meta;
    }
    public Data getProfile() {
        if (profile == null) {
            profile = (Data) get(CONTENT);
        }
        return profile;
    }

    //
    //  file in message
    //
    public String getFilename() {
        if (filename == null) {
            filename = (String) get(FILENAME);
        }
        return filename;
    }

    //
    //  Factories
    //

    private static void addField(List<Field> fields, FieldName name, FieldValue value) {
        if (value != null) {
            fields.add(new Field(name, value));
        }
    }

    public static Message create(StringValue sender, StringValue receiver, TimestampValue time,
                                 ByteValue type, StringValue group,
                                 BinaryValue content, BinaryValue signature, BinaryValue key,
                                 BinaryValue meta, BinaryValue profile,
                                 StringValue filename) {
        List<Field> fields = new ArrayList<>();
        //
        //  envelope
        //
        addField(fields, SENDER, sender);
        addField(fields, RECEIVER, receiver);
        addField(fields, TIME, time);
        addField(fields, TYPE, type);
        addField(fields, GROUP, group);
        //
        //  body
        //
        addField(fields, CONTENT, content);
        addField(fields, SIGNATURE, signature);
        addField(fields, KEY, key);
        //
        //  attachments
        //
        addField(fields, META, meta);
        addField(fields, PROFILE, profile);
        //
        //  file in message
        //
        addField(fields, FILENAME, filename);
        //
        //  OK
        //
        return new Message(fields);
    }

    public static Message create(String sender, String receiver, long timestamp,
                                 int type, String group,
                                 Data content, Data signature, Data key,
                                 Data meta, Data profile,
                                 String filename) {
        StringValue senderValue = null;
        StringValue receiverValue = null;
        TimestampValue timestampValue = null;
        ByteValue typeValue = null;
        StringValue groupValue = null;
        BinaryValue contentValue = null;
        BinaryValue signatureValue = null;
        BinaryValue keyValue = null;
        BinaryValue metaValue = null;
        BinaryValue profileValue = null;
        StringValue filenameValue = null;
        //
        //  envelope
        //
        if (sender != null) {
            senderValue = new StringValue(sender);
        }
        if (receiver != null) {
            receiverValue = new StringValue(receiver);
        }
        if (timestamp > 0) {
            timestampValue = new TimestampValue(timestamp);
        }
        if (type > 0) {
            typeValue = new ByteValue(type);
        }
        if (group != null) {
            groupValue = new StringValue(group);
        }
        //
        //  body
        //
        if (content != null) {
            contentValue = new BinaryValue(content);
        }
        if (signature != null) {
            signatureValue = new BinaryValue(signature);
        }
        if (key != null) {
            keyValue = new BinaryValue(key);
        }
        //
        //  attachments
        //
        if (meta != null) {
            metaValue = new BinaryValue(meta);
        }
        if (profile != null) {
            profileValue = new BinaryValue(profile);
        }
        //
        //  file in message
        //
        if (filename != null) {
            filenameValue = new StringValue(filename);
        }
        //
        //  OK
        //
        return create(senderValue, receiverValue, timestampValue, typeValue, groupValue,
                contentValue, signatureValue, keyValue,
                metaValue, profileValue, filenameValue);
    }

    //
    //  instant message
    //

    public static Message create(String sender, String receiver, long timestamp,
                                 int type, String group,
                                 Data content, Data signature, Data key,
                                 Data meta, Data profile) {
        return create(sender, receiver, timestamp, type, group,
                content, signature, key, meta, profile, null);
    }

    public static Message create(String sender, String receiver, long timestamp,
                                 Data content, Data signature, Data key) {
        return create(sender, receiver, timestamp, 0, null,
                content, signature, key, null, null, null);
    }

    //
    //  file in message
    //

    public static Message create(String filename, Data content,
                                 String sender, String receiver,
                                 Data signature, Data key) {
        return create(sender, receiver, 0, 0, null,
                content, signature, key, null, null, filename);
    }

    public static Message create(String filename, Data content) {
        return create(null, null, 0, 0, null,
                content, null, null, null, null, filename);
    }

    //
    //  Message field names
    //

    public static final FieldName SENDER    = new FieldName("S");
    public static final FieldName RECEIVER  = new FieldName("R");
    public static final FieldName TIME      = new FieldName("W");
    public static final FieldName TYPE      = new FieldName("T");
    public static final FieldName GROUP     = new FieldName("G");

    public static final FieldName CONTENT   = new FieldName("D");  // message content Data; or file content Data
    public static final FieldName SIGNATURE = new FieldName("V");  // signature for Verify content data with sender's meta.key
    public static final FieldName KEY       = new FieldName("K");

    public static final FieldName META      = new FieldName("M");
    public static final FieldName PROFILE   = new FieldName("P");

    public static final FieldName FILENAME  = new FieldName("F");  // file in message

    static {
        //
        //  classes for parsing message fields
        //

        register(SENDER,    StringValue.class);
        register(RECEIVER,  StringValue.class);
        register(TIME,      TimestampValue.class);
        register(TYPE,      ByteValue.class);
        register(GROUP,     StringValue.class);

        register(CONTENT,   BinaryValue.class);
        register(SIGNATURE, BinaryValue.class);
        register(KEY,       BinaryValue.class);

        register(META,      BinaryValue.class);
        register(PROFILE,   BinaryValue.class);

        register(FILENAME,  StringValue.class);
    }
}
