---
name: hidden-prompt-injection
type: concept
sources: [stealing-reasoning-traces]
updated: 2026-08-12
---

# 隐藏提示注入 · 恶意指令藏在用户看不见的上下文里

## 一句话
模型会读到一段影响后续行为的指令，但用户界面和普通文本扫描器都看不到它。

## 直觉
普通提示注入像文档里夹着一句“忽略前面的要求”；至少人和扫描器能看见。隐藏注入更像把指令写进密封的交接单：接班模型能读，交接的人只能看到一串 opaque bytes。

## 怎么做的

```text
攻击者让模型产生一段含恶意意图的隐藏推理
→ API 把它封装成合法 envelope
→ envelope 被放进共享 trace / agent checkpoint
→ 受害者恢复这段 trace
→ 后续模型把旧推理当成自己的上下文继续执行
```

风险来自两件事同时成立：envelope 能跨上下文重放；外部审计只检查可见文本。

## 数字例子

假设一条共享轨迹含 100 个可见消息和 12 个 opaque reasoning blocks。发布者把 100 个消息都扫过，发现 0 条可疑文字；其中第 9 个隐藏块却含有一条持久指令。若恢复工具把 12 个块全部原样回传，文本审计覆盖率看似是 100%，对真实模型上下文却只覆盖了：

\[
\frac{100}{100+12}\approx 89.3\%.
\]

这里的 89.3% 只是按“块数”等权的教学估算；真实风险取决于隐藏块长度、位置和模型服从程度。

## 防御

- 分享 trace 前移除所有 opaque reasoning / signature 字段，而不只清洗可见文本。
- 恢复外部会话时默认丢弃隐藏状态，重新生成必要上下文摘要。
- provider 把 envelope 绑定到用户、会话和前序位置，使第三方块无法通过验证。
- 模型层识别来自旧隐藏状态的异常指令，并把工具调用继续交给显式权限检查。

## 链接

- [[reasoning-envelope-replay]] · 隐藏块为什么能从攻击者上下文搬进受害者上下文。
- [[authenticated-encryption]] · 密文真实、完整，不代表其使用上下文合法。
- [[stealing-reasoning-traces]] · 给出跨模型、跨任务的实验性 PoC。

