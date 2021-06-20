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

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import chat.dim.dmtp.fields.Field;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;
import chat.dim.dmtp.fields.FieldsValue;
import chat.dim.dmtp.values.BinaryValue;
import chat.dim.dmtp.values.StringValue;
import chat.dim.dmtp.values.TimestampValue;
import chat.dim.dmtp.values.TypeValue;
import chat.dim.type.ByteArray;

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
    private ByteArray content = null;
    private ByteArray signature = null;
    private ByteArray key = null;

    // attachments
    private ByteArray meta = null;
    private ByteArray profile = null;

    // file in message
    private String filename = null;

    public Message(ByteArray data, List<Field> fields) {
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
            sender = getStringValue(SENDER);
        }
        return sender;
    }
    public String getReceiver() {
        if (receiver == null) {
            receiver = getStringValue(RECEIVER);
        }
        return receiver;
    }
    public long getTimestamp() {
        if (timestamp == 0) {
            timestamp = getTimestampValue(TIME);
        }
        return timestamp;
    }
    public int getType() {
        if (type == 0) {
            type = getTypeValue(TYPE);
        }
        return type;
    }
    public String getGroup() {
        if (group == null) {
            group = getStringValue(GROUP);
        }
        return group;
    }

    //
    //  body
    //
    public ByteArray getContent() {
        if (content == null) {
            content = getBinaryValue(CONTENT);
        }
        return content;
    }
    public ByteArray getSignature() {
        if (signature == null) {
            signature = getBinaryValue(SIGNATURE);
        }
        return signature;
    }
    public ByteArray getKey() {
        if (key == null) {
            key = getBinaryValue(KEY);
        }
        return key;
    }

    //
    //  attachments
    //
    public ByteArray getMeta() {
        if (meta == null) {
            meta = getBinaryValue(META);
        }
        return meta;
    }
    public ByteArray getProfile() {
        if (profile == null) {
            profile = getBinaryValue(PROFILE);
        }
        return profile;
    }

    //
    //  file in message
    //
    public String getFilename() {
        if (filename == null) {
            filename = getStringValue(FILENAME);
        }
        return filename;
    }

    //
    //  Factories
    //

    public static Message parse(ByteArray data) {
        // parse fields
        List<Field> fields = Field.parseAll(data);
        if (fields.size() == 0) {
            return null;
        }
        return new Message(fields);
    }

    @SuppressWarnings("unchecked")
    private static void fetchMsgField(List<Field> fields, Map info,
                                      String s, String name, FieldName tag, Class valueClass) {
        Object object = info.get(name);
        if (object == null) {
            object = info.get(s);
            if (object == null) {
                // no this field
                return;
            }
        }
        FieldValue value;
        if (object instanceof FieldValue) {
            value = (FieldValue) object;
        } else {
            // try 'new Clazz(dict)'
            try {
                Constructor constructor = valueClass.getConstructor(object.getClass());
                value = (FieldValue) constructor.newInstance(object);
            } catch (NoSuchMethodException | IllegalAccessException | InstantiationException | InvocationTargetException e) {
                e.printStackTrace();
                value = null;
            }
        }
        if (value == null) {
            // value error
            return;
        }
        fields.add(new Field(tag, value));
    }

    public static Message create(Map info) {
        List<Field> fields = new ArrayList<>();
        // envelope
        fetchMsgField(fields, info, "S", "sender",    SENDER,    StringValue.class);
        fetchMsgField(fields, info, "R", "receiver",  RECEIVER,  StringValue.class);
        fetchMsgField(fields, info, "W", "time",      TIME,      TimestampValue.class);
        fetchMsgField(fields, info, "T", "type",      TYPE,      TypeValue.class);
        fetchMsgField(fields, info, "G", "group",     GROUP,     StringValue.class);
        // body
        fetchMsgField(fields, info, "D", "data",      CONTENT,   BinaryValue.class);
        fetchMsgField(fields, info, "V", "signature", SIGNATURE, BinaryValue.class);
        fetchMsgField(fields, info, "K", "key",       KEY,       BinaryValue.class);
        // attachments
        fetchMsgField(fields, info, "M", "meta",      META,      BinaryValue.class);
        fetchMsgField(fields, info, "P", "profile",   PROFILE,   BinaryValue.class);
        // file
        fetchMsgField(fields, info, "F", "filename",  FILENAME,  StringValue.class);
        // create message with fields
        return new Message(fields);
    }

    private static Message create(Object sender, Object receiver, Object timestamp,
                                  Object type, Object group,
                                  Object content, Object signature, Object key,
                                  Object meta, Object profile,
                                  Object filename) {
        Map<Object, Object> info = new HashMap<>();
        info.put("sender", sender);
        info.put("receiver", receiver);
        info.put("timestamp", timestamp);

        if (type != null) {
            info.put("type", type);
        }
        if (group != null) {
            info.put("group", group);
        }

        info.put("data", content);
        info.put("signature", signature);

        if (key != null) {
            info.put("key", key);
        }

        if (meta != null) {
            info.put("meta", meta);
        }
        if (profile != null) {
            info.put("profile", profile);
        }

        if (filename != null) {
            info.put("filename", filename);
        }
        return create(info);
    }

    //
    //  instant message
    //

    public static Message create(String sender, String receiver, long timestamp,
                                 int type, String group,
                                 ByteArray content, ByteArray signature, ByteArray key,
                                 ByteArray meta, ByteArray profile) {
        return create(sender, receiver, timestamp, type, group,
                content, signature, key, meta, profile,
                null);
    }

    public static Message create(String sender, String receiver, long timestamp,
                                 ByteArray content, ByteArray signature, ByteArray key) {
        return create(sender, receiver, timestamp, 0, null,
                content, signature, key, null, null,
                null);
    }

    //
    //  file in message
    //

    public static Message create(String filename, ByteArray content,
                                 String sender, String receiver, long timestamp,
                                 ByteArray signature, ByteArray key) {
        return create(sender, receiver, timestamp, 0, null,
                content, signature, key, null, null,
                filename);
    }

    public static Message create(String filename, ByteArray content) {
        return create(null, null, 0, 0, null,
                content, null, null, null, null,
                filename);
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
        register(TYPE,      TypeValue.class);
        register(GROUP,     StringValue.class);

        register(CONTENT,   BinaryValue.class);
        register(SIGNATURE, BinaryValue.class);
        register(KEY,       BinaryValue.class);

        register(META,      BinaryValue.class);
        register(PROFILE,   BinaryValue.class);

        register(FILENAME,  StringValue.class);
    }
}
