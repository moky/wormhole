# WormHole
Network Modules


## Modules

|   Module   | Java SDK | Python SDK |
|------------|----------|------------|
| StarTrek   | 0.2.2    | 0.2.6      |
| TCP        | 0.2.2    | 0.2.11     |
| ByteArray  | 0.1.2    |            |
| MTP        | 0.1.6    |            |
| UDP        | 0.2.2    | 0.4.15     |
| TLV        | 0.1.4    |            |
| STUN       | 0.1.5    | 0.2.3      |
| TURN       | 0.1.5    |            |
| DMTP       | 0.2.2    | 0.3.4      |


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
                          ^                                   ^
                          :                                   :
                 .........:                  .................:
                 :                           :
                 :    +-------+          +-------+
                 :..> |  UDP  | .......> |  MTP  |
                 :    +-------+   :      +-------+
                 :                :
    +--------+   :                :     +----------+      +-------+
    |  DMTP  | ..:                :...> | StarTrek | ...> |  FSM  |
    +--------+   :                      +----------+      +-------+
                 :                           ^
                 :    +-------+              :
                 :..> |  TCP  | .............:
                      +-------+

```


Moky @ Jul 5. 2021
