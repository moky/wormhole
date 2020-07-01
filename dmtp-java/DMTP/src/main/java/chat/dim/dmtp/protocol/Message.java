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
import chat.dim.dmtp.values.*;
import chat.dim.tlv.Tag;

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
    private byte[] content = null;
    private byte[] signature = null;
    private byte[] key = null;

    // attachments
    private byte[] meta = null;
    private byte[] profile = null;

    // file in message
    private String filename = null;

    public Message(byte[] data) {
        super(data);
    }

    public Message(List<Field> fields) {
        super(fields);
    }

    //
    //  envelope
    //
    public String getSender() {
        return sender;
    }
    public String getReceiver() {
        return receiver;
    }
    public long getTimestamp() {
        return timestamp;
    }
    public int getType() {
        return type;
    }
    public String getGroup() {
        return group;
    }

    //
    //  body
    //
    public byte[] getContent() {
        return content;
    }
    public byte[] getSignature() {
        return signature;
    }
    public byte[] getKey() {
        return key;
    }

    //
    //  attachments
    //
    public byte[] getMeta() {
        return meta;
    }
    public byte[] getProfile() {
        return profile;
    }

    //
    //  file in message
    //
    public String getFilename() {
        return filename;
    }

    @Override
    protected void setField(Field field) {
        Tag tag = field.tag;
        //
        //  envelope
        //
        if (tag.equals(SENDER))
        {
            assert field.value instanceof StringValue : "sender ID error: " + field.value;
            sender = ((StringValue) field.value).string;
        }
        else if (tag.equals(RECEIVER))
        {
            assert field.value instanceof StringValue : "receiver ID error: " + field.value;
            receiver = ((StringValue) field.value).string;
        }
        else if (tag.equals(TIME))
        {
            assert field.value instanceof TimestampValue : "msg time error: " + field.value;
            timestamp = ((TimestampValue) field.value).value;
        }
        else if (tag.equals(TYPE))
        {
            assert field.value instanceof ByteValue : "msg type error: " + field.value;
            type = ((ByteValue) field.value).value;
        }
        else if (tag.equals(GROUP))
        {
            assert field.value instanceof StringValue : "group ID error: " + field.value;
            group = ((StringValue) field.value).string;
        }
        //
        //  body
        //
        else if (tag.equals(CONTENT))
        {
            assert field.value instanceof BinaryValue : "content data error: " + field.value;
            content = field.value.data;
        }
        else if (tag.equals(SIGNATURE))
        {
            assert field.value instanceof BinaryValue : "signature error: " + field.value;
            signature = field.value.data;
        }
        else if (tag.equals(KEY))
        {
            assert field.value instanceof BinaryValue : "symmetric key data error: " + field.value;
            key = field.value.data;
        }
        //
        //  attachments
        //
        else if (tag.equals(META))
        {
            assert field.value instanceof BinaryValue : "meta error: " + field.value;
            meta = field.value.data;
        }
        else if (tag.equals(PROFILE))
        {
            assert field.value instanceof BinaryValue : "profile error: " + field.value;
            profile = field.value.data;
        }
        //
        //  file in message
        //
        else if (tag.equals(FILENAME))
        {
            assert field.value instanceof StringValue : "filename error: " + field.value;
            filename = ((StringValue) field.value).string;
        }
        else
        {
            super.setField(field);
        }
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
        Message msg = new Message(fields);
        msg.setFields(fields);
        return msg;
    }

    public static Message create(String sender, String receiver, long timestamp,
                                 int type, String group,
                                 byte[] content, byte[] signature, byte[] key,
                                 byte[] meta, byte[] profile,
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
                                 byte[] content, byte[] signature, byte[] key,
                                 byte[] meta, byte[] profile) {
        return create(sender, receiver, timestamp, type, group,
                content, signature, key, meta, profile, null);
    }

    public static Message create(String sender, String receiver, long timestamp,
                                 byte[] content, byte[] signature, byte[] key) {
        return create(sender, receiver, timestamp, 0, null,
                content, signature, key, null, null, null);
    }

    //
    //  file in message
    //

    public static Message create(String filename, byte[] content,
                                 String sender, String receiver,
                                 byte[] signature, byte[] key) {
        return create(sender, receiver, 0, 0, null,
                content, signature, key, null, null, filename);
    }

    public static Message create(String filename, byte[] content) {
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
