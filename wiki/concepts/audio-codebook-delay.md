---
name: audio-codebook-delay
type: concept
sources: [personaplex]
updated: 2026-08-12
---

# Audio Codebook Delay · 先定语义，下一帧再补声学细节

## 一句话

同一段 80 毫秒声音里，第一层语义 token 按当前时刻生成，其余声学 token 故意向后错一帧。

## 直觉

像先写字幕草稿，再晚 80 毫秒决定具体语气、音高和质感。声学层拿得到已经确定的语义层，不必在同一个瞬间盲猜“说什么”和“怎么响”。

## 怎么排

设帧号为 `t`：

- agent 文字 token 与第 1 个语义音频 token 放在 `t`；
- 第 2–8 个声学 token 放在 `t+1`；
- 一帧是 `1 / 12.5 = 0.08` 秒，所以错开量是 80 毫秒。

## 数字例子

句子第 10 帧确定要说“好”：

1. `t=10` 先生成对应文字/语义码；
2. `t=11` 的深度模块已经看到这层语义，再补 7 层音色、韵律和细节码；
3. codec 收齐 8 层后还原这一小段波形。

代价是固定增加一帧等待；收益是声学细节不必与语义在同一帧互相猜。

## 链接

- [[personaplex]] · 来源
- [[temporal-depth-transformer]] · 帧内多 codebook 生成
- [[rvq-codec]] · 语义层和残差层
