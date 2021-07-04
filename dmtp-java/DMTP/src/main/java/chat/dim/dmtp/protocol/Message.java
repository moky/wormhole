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

import chat.dim.tlv.Field;
import chat.dim.tlv.Value;
import chat.dim.tlv.tags.StringTag;
import chat.dim.tlv.values.MapValue;
import chat.dim.tlv.values.RawValue;
import chat.dim.tlv.values.StringValue;
import chat.dim.tlv.values.Value32;
import chat.dim.tlv.values.Value8;
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
 *             P - sender's Visa info (OPTIONAL)
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

public class Message extends MapValue<Field> {

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
    private ByteArray visa = null;

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
            timestamp = getLongValue(WHEN);
        }
        return timestamp;
    }
    public int getType() {
        if (type == 0) {
            type = getByteValue(TYPE);
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
            signature = getBinaryValue(VERIFY);
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
    public ByteArray getVisa() {
        if (visa == null) {
            visa = getBinaryValue(VISA);
        }
        return visa;
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
        List<Field> fields = Field.parseFields(data);
        if (fields.size() == 0) {
            return null;
        }
        return new Message(data, fields);
    }

    private static void fetchMsgField(List<Field> fields, Map<String, Object> info,
                                      String s, String name, StringTag tag, Class<?> valueClass) {
        Object object = info.get(name);
        if (object == null) {
            object = info.get(s);
            if (object == null) {
                // no this field
                return;
            }
        }
        Value value;
        if (object instanceof Value) {
            value = (Value) object;
        } else {
            // try 'new Clazz(dict)'
            try {
                Constructor<?> constructor = valueClass.getConstructor(object.getClass());
                value = (Value) constructor.newInstance(object);
            } catch (NoSuchMethodException | IllegalAccessException | InstantiationException | InvocationTargetException e) {
                e.printStackTrace();
                value = null;
            }
        }
        if (value == null) {
            // value error
            return;
        }
        fields.add(Field.create(tag, value));
    }

    public static Message create(Map<String, Object> info) {
        List<Field> fields = new ArrayList<>();
        // envelope
        fetchMsgField(fields, info, "S", "sender",    SENDER,    StringValue.class);
        fetchMsgField(fields, info, "R", "receiver",  RECEIVER,  StringValue.class);
        fetchMsgField(fields, info, "W", "time",      WHEN,      Value32.class);
        fetchMsgField(fields, info, "T", "type",      TYPE,      Value8.class);
        fetchMsgField(fields, info, "G", "group",     GROUP,     StringValue.class);
        // body
        fetchMsgField(fields, info, "D", "data",      CONTENT,   RawValue.class);
        fetchMsgField(fields, info, "V", "signature", VERIFY,    RawValue.class);
        fetchMsgField(fields, info, "K", "key",       KEY,       RawValue.class);
        // attachments
        fetchMsgField(fields, info, "M", "meta",      META,      RawValue.class);
        fetchMsgField(fields, info, "P", "visa",      VISA,      RawValue.class);
        // file
        fetchMsgField(fields, info, "F", "filename",  FILENAME,  StringValue.class);
        // create message with fields
        return new Message(fields);
    }

    private static Message create(Object sender, Object receiver, Object timestamp,
                                  Object type, Object group,
                                  Object content, Object signature, Object key,
                                  Object meta, Object visa,
                                  Object filename) {
        Map<String, Object> info = new HashMap<>();
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
        if (visa != null) {
            info.put("visa", visa);
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
                                 ByteArray meta, ByteArray visa) {
        return create(sender, receiver, timestamp, type, group,
                content, signature, key, meta, visa,
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

    public static final StringTag SENDER    = StringTag.from("S");
    public static final StringTag RECEIVER  = StringTag.from("R");
    public static final StringTag WHEN      = StringTag.from("W");
    public static final StringTag TYPE      = StringTag.from("T");
    public static final StringTag GROUP     = StringTag.from("G");

    public static final StringTag CONTENT   = StringTag.from("D");  // message content Data; or file content Data
    public static final StringTag VERIFY    = StringTag.from("V");  // signature for Verify content data with sender's meta.key
    public static final StringTag KEY       = StringTag.from("K");

    public static final StringTag META      = StringTag.from("M");
    public static final StringTag VISA      = StringTag.from("P");

    public static final StringTag FILENAME  = StringTag.from("F");  // file in message

    static {
        //
        //  classes for parsing message fields
        //

        Field.register(SENDER,    StringValue::parse);
        Field.register(RECEIVER,  StringValue::parse);
        Field.register(WHEN,      Value32::parse);
        Field.register(TYPE,      Value8::parse);
        Field.register(GROUP,     StringValue::parse);

        Field.register(CONTENT,   RawValue::parse);
        Field.register(VERIFY,    RawValue::parse);
        Field.register(KEY,       RawValue::parse);

        Field.register(META,      RawValue::parse);
        Field.register(VISA,      RawValue::parse);

        Field.register(FILENAME,  StringValue::parse);
    }
}
