---
name: addressable-kv-memory
type: concept
sources: [worldtrace]
updated: 2026-08-11
---

# Addressable KV Memory · 可寻址的 KV 记忆

## 一句话

**记忆在不在**与**模型能不能用 attention 找到它**是两回事；可寻址记忆要求历史内容还在、读取位置落在模型熟悉的范围内，而且多个记忆位置彼此可区分。

## 生活直觉

仓库里存着三箱货，不等于快递员能取到：

- 标签被撕掉：内容在，但没有地址；
- 三箱都写“最里面”：地址重合，无法区分；
- 标签使用从没培训过的新编码：人能看见，流程却不认识。

长视频 KV cache 也会这样。旧 Key 即使仍在显存，时间 RoPE 相对距离一旦超过训练范围，Query 就要在没学过的位置关系上检索。若又把多个旧摘要都截到同一个位置，它们还会发生地址碰撞。

## 三个条件

1. **Retention**：需要的信息没有被删掉或压坏；
2. **In-distribution address**：Query–Key 相对位置仍在训练见过的区间；
3. **Distinctness**：不同 memory slot 有不同地址，attention 能分开选择。

WorldTrace 的 slot-rank 位置解决后两项；Field / Landmark writer 解决第一项。只做任意一半都不够。

## 不是哪几件事

- 不是“KV cache 越大越好”：完整 cache 仍可能在超长 RoPE 距离上读不到；
- 不是普通数据库随机访问：地址是进入 attention 点积的位置相位，不是数组下标；
- 不是模型学到永久地图：WorldTrace 仍是有限槽位的视觉轨迹记忆。

## 链接

- [[worldtrace]] · 固定槽位怎样同时处理保存与寻址
- [[kv-cache]] · K/V 为什么会留在推理内存
- [[rotary-position-embedding]] · 时间地址怎样进入 Q/K 点积
- [[canonical-rope-keys]] · 内容换地址前为什么要先去掉旧相位
