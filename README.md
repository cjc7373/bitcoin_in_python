This repo is archived and I'm working on a Go version on [bitcoin_go](https://github.com/cjc7373/bitcoin_go).

# Bitcoin in Python
A simple implementation of bitcoin in Python.

Based on https://liuchengxu.gitbook.io/blockchain/
Which is a translation of https://github.com/Jeiwan/blockchain_go

## Issues
- 状态保存的问题, 我们同时需要维护内存中的状态和数据库中的状态
- 我们还要处理挖出一个块后因为某些原因回滚的情况, 此时如何更新 unspent_txs_set? 暂时先不考虑吧..

## History
- 是否应该弃用 tinydb 呢? 在字符串和字节序列间转来转去太折磨了..  
  替代方案: https://github.com/RaRe-Technologies/sqlitedict  
  tinydb 的 doc_id 居然不支持字符串.. 看来只有迁移了..
- 我发现直接存 utxo 会有很多麻烦的地方, 不如存 unspent transactions..