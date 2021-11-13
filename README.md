# Bitcoin in Python
A simple implementation of bitcoin in Python.

Based on https://liuchengxu.gitbook.io/blockchain/

## TODO
- block 中嵌套 transaction 从数据库创建对象的时候怎么处理?

## Issues
- 是否应该弃用 tinydb 呢? 在字符串和字节序列间转来转去太折磨了..  
  替代方案: https://github.com/RaRe-Technologies/sqlitedict
  tinydb 的 doc_id 居然不支持字符串.. 看来只有迁移了..
- 我发现直接存 utxo 会有很多麻烦的地方, 不如存 unspent transactions..