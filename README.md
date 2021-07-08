# WormHole
Network Modules


## Modules

|   Module   | Version |
|------------|---------|
| ByteArray  | 0.1.0   |
| TLV        | 0.1.2   |
| STUN       | 0.1.2   |
| TURN       | 0.1.2   |
| MTP        | 0.1.3   |
| TCP        | 0.1.7   |
| UDP        | 0.1.1   |
| DMTP       | 0.1.2   |
| StarTrek   | 0.1.2   |


## Dependencies

<style>
pre code {
    font-family: "Lucida Console", "Consolas", Monaco, monospace;
    line-height: 0px;
}
</style>

```

    +--------+        +--------+        +-------+        +------+
    |  TURN  | .....> |  STUN  | .....> |  TLV  | .....> |  BA  |
    +--------+        +--------+        +-------+        +------+
                          ^                                 ^
                          :                                 :
                 .........:                        .........:
                 :                                 :
    +--------+   :    +-------+        +-------+   :
    |  DMTP  | ..:..> |  UDP  | .....> |  MTP  | ..:
    +--------+        +-------+   :    +-------+
                                  :
                                  :    +-------+        +-------+
                                  :..> |  TCP  | .....> |  FSM  |
                                       +-------+        +-------+
    +------------+
    |  StarTrek  |
    +------------+


```


Moky @ Jul 5. 2021
