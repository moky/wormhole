# WormHole
Network Modules


## Modules

|   Module   | Version |
|------------|---------|
| ByteArray  | 0.1.1   |
| TLV        | 0.1.3   |
| STUN       | 0.1.3   |
| TURN       | 0.1.3   |
| MTP        | 0.1.4   |
| StarTrek   | 0.2.0   |
| UDP        | 0.2.0   |
| TCP        | 0.2.0   |
| DMTP       | 0.2.0   |


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
