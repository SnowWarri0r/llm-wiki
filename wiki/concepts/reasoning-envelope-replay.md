---
name: reasoning-envelope-replay
type: concept
sources: [stealing-reasoning-traces]
updated: 2026-08-12
---

# 推理信封重放 · 合法密文被搬到了错误的对话

## 一句话
攻击者不改密文，只把一份仍能通过验证的推理块重新塞给另一次调用。

## 直觉
一张门票是真的，不代表它在任何影院、任何场次、任何人手里都该有效。重放攻击利用的正是这道差别：对象本身通过验真，但系统没有核对它属于谁、哪一场、排在第几步。

推理 API 为了保持无状态，会把隐藏推理装进 opaque envelope 交给客户端保管。后续请求把它传回，模型就能接着想。如果 envelope 只证明“这段内容由服务端签过”，没有证明“只能由这个用户在这段会话的这个位置使用”，它就可能被跨 session、跨 user 或跨 model 搬运。

## 怎么做的

```text
调用 A：强模型 → 返回 visible answer + opaque reasoning envelope E
搬运：客户端保留 E，不修改其中任何字节
调用 B：把 E 放进另一个兼容调用 → 目标模型接受并处理旧推理
```

三层兼容从窄到宽：

1. 跨 session：同一用户把 \(E\) 放进另一段会话。
2. 跨 user：另一账号也能提交 \(E\)。
3. 跨 model：同一 provider 的另一模型也能处理 \(E\)。

## 数字例子

把 envelope 想成四元组：

```text
E = (ciphertext, nonce, tag, key_id)
原上下文 = (user 17, session 42, model A, turn 8)
新上下文 = (user 29, session 91, model B, turn 2)
```

若验签只检查 \(E\) 的四个字段，两个上下文都会得到“有效”。若关联数据额外绑定 \((17,42,A,8)\)，第二组上下文至少有四处不匹配，重放会被拒绝。

## 防御

- 把用户、会话、模型与前序位置写进认证上下文。
- 服务端记录 envelope 是否已经消费，阻止同一块重复使用。
- 跨模型切换经过显式、受控的重新签发，而不是默认全家族通用。
- 轮换旧密钥并拒绝 legacy key ID，切断已经公开的历史块。

## 链接

- [[authenticated-encryption]] · 关联数据如何把合法密文绑定到合法上下文。
- [[stealing-reasoning-traces]] · 把重放与弱模型转录组合成推理提取。
- [[hidden-prompt-injection]] · 反方向风险：把带恶意意图的合法块交给受害者重放。

