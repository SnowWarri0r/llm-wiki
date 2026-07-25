---
name: skip-connection
type: concept
sources: [unet]
updated: 2026-07-24
---

# Skip Connection · 跨层连接 · 让早期信息绕过中间层

## 一句话

把较早层的特征直接送到较后层，中间不用逐层传递；U-Net 用 `concat` 补回空间细节，ResNet 用 `add` 让残差和梯度容易通过。

## 直觉

深层网络会不断改写信息。下采样尤其会丢掉精确位置。跨层连接给早期特征留一条直达后面的通道，避免所有信息都必须穿过瓶颈。

但“跳过去”之后怎么合并，有两种常见做法：

```text
ResNet：y = F(x) + x            # 同形状逐元素相加
U-Net：y = concat(up, skip)     # 沿通道拼接
```

## 数字例子 · add 和 concat 不是一回事

取两份两通道特征：

```text
深层特征 up   = [10, 20]
浅层特征 skip = [ 1,  2]
```

ResNet 式相加：

```text
[10,20] + [1,2] = [11,22]
```

两份信息已经混在同两个通道里。

U-Net 式拼接：

```text
concat([10,20],[1,2]) = [10,20,1,2]
```

后面的卷积能分别看到四个数，再决定如何组合。代价是通道从 2 变 4，计算和显存都增加。

## 尺寸为什么必须对齐

拼接要求宽高相同。原版 U-Net 中：

```text
编码器特征：64×64×512
解码器特征：56×56×512
```

先从编码器四周各裁：

```text
(64-56)/2 = 4 像素
```

变成 `56×56×512`，才能拼成 `56×56×1024`。

## 代码出处

- U-Net：`torch.cat([decoder, encoder_crop], dim=1)`
- ResNet：`out = F(x) + x`

## 链接

- [[unet]] · 横向跳连把定位细节送入解码器
- [[residual-connection]] · 用逐元素相加实现的另一类跨层连接
- [[transposed-convolution]] · 解码特征放大后再与 skip 对齐
