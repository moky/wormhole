# WormHole
Network Modules


## Modules

|   Module   | Java SDK | Python SDK |
|------------|----------|------------|
| StarTrek   | 0.3.3    | 0.3.7      |
| TCP        | 0.3.3    | 0.3.6      |
| ByteArray  | 0.1.2    |            |
| MTP        | 0.1.7    |            |
| UDP        | 0.3.3    | 0.5.6      |
| TLV        | 0.1.4    |            |
| STUN       | 0.1.5    | 0.2.3      |
| TURN       | 0.1.5    |            |
| DMTP       | 0.2.3    | 0.3.4      |


## Dependencies

<style>
pre code {
    font-family: "Lucida Console", "Consolas", Monaco, monospace;
    line-height: 0px;
}
</style>

```

    +--------+        +--------+         +-------+         +------+
    |  TURN  | .....> |  STUN  | ......> |  TLV  | ......> |  BA  |
    +--------+        +--------+         +-------+         +------+
                          A                                   A
    +--------+            :                                   :
    |  DMTP  | ...........:                                   :
    +--------+            :                                   :
                          :              +-------+            :
                          :............> |  MTP  | ...........:
                                         +-------+
                                             A
                      +-------+              :
                      |  UDP  | .............:
                      +-------+              :
                                             V
                      +-------+         +----------+      +-------+
                      |  TCP  | ......> | StarTrek | ...> |  FSM  |
                      +-------+         +----------+      +-------+

```


Moky @ Jul 5. 2021
