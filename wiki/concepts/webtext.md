---
name: webtext
type: concept
sources: [gpt-2]
updated: 2026-05-21
---

# WebText · GPT-2 用的数据集

## 一句话
OpenAI 为 GPT-2 自建的 ~40GB 高质量网页数据集 —— 爬 Reddit 上至少 3 karma 的外链页面（"人筛过的网页"）。

## 直觉
GPT-1 用 BookCorpus（7000 本书），优点是干净，缺点是数量小。要 scale 到 1.5B 模型需要更多数据。

直接爬整个互联网（Common Crawl 那种）的问题：噪声大、SEO 垃圾多、低质量博客泛滥。OpenAI 想要<strong>高质量但量大</strong>的数据。

**Trick**：用 Reddit 当数据 filter。Reddit 用户点赞 = 一种 free 的人工标注。爬<strong>所有出现在 ≥ 3 karma 的 Reddit 帖子里</strong>的外链页面（45M unique outbound links），抓 HTML，提取文本。

**思想**：把"用户花时间点赞"当作"这页面值得读"的代理信号。免费的内容质量 reviewer。

## 数据规模
- 4500 万个 outbound link
- 去重后 800 万个文档
- ~40 GB 纯文本

跟同期数据集对比：
- BookCorpus: ~800 MB（小 50 倍）
- Wikipedia: ~6 GB（小 7 倍）
- C4 (T5 用的): ~750 GB（大 20 倍，但 2 年后）
- Pile: ~825 GB（大 20 倍，2020 年）
- RedPajama / Llama 训练数据: TB 级

WebText 在 2019 年是相当大的预训练数据集，但<strong>方法</strong>比规模影响更深远。

## 为什么"Reddit karma"作为信号能 work
- Reddit 用户群覆盖广泛话题（科技、新闻、教程、讨论）
- karma ≥ 3 是个低门槛，但能滤掉绝大多数刷量 / spam / 显然垃圾内容
- 链接到外站的帖子<strong>通常是"我觉得这值得分享"的语义</strong>，天然高质量
- 比 SEO 优化的"看起来权威实际无信息"的网页好

这本质是<strong>把人类注意力当作免费的数据标注</strong>。

## 它的局限
- Reddit 用户分布有偏（英语为主、男性为主、技术话题密集）→ 模型继承这种偏差
- karma 3 是个简陋启发式，无法过滤更隐蔽的低质量
- 没法外推到 TB 级数据 —— Reddit 链接总量就那么多

后续大模型用 C4（基于 Common Crawl + 启发式过滤）或更大的 Pile / RedPajama，karma-based 筛选这种小聪明退场。但<strong>"用社区信号筛数据质量"这个思路</strong>在后来的 Constitutional AI / RLHF 里又以不同形式出现。

## OpenAI 没开源 WebText
WebText 数据集本身一直没被公开 —— 因为里头有可能的版权内容 + Reddit ToS。开源社区做了 OpenWebText（基于同样思路自己重新爬一遍）作为复现。

这也开了"大模型训练数据不公开"的先例 —— 后来 Anthropic / Google 也都不公开他们的训练数据。

## 链接
- [[gpt-2]] · 使用方
- [[causal-language-model]] · WebText 的训练目标
