---
title: 面向长时运行应用开发的 Harness 设计
date: 2026-03-31 00:25:00
categories:
  - 技术
tags:
  - AI
  - Agent
  - Claude
  - Anthropic
  - Engineering
---

2023、2024 年，大家在学怎么「问」模型——Chain-of-Thought、Few-Shot、角色扮演，核心是把一句话说得让 AI 听懂，这是 Prompt 工程（Prompt Engineering）的时代。2025 年，Andrej Karpathy 一句话点醒了很多人：光会写 prompt 不够，你得设计模型「看到什么」。RAG、MCP、Memory、工具调用……重点是把整个 context 窗口当成系统来设计，这是 Context 工程（Context Engineering）的时代。

到了 2026 年，问题又往前推了一步：模型已经足够强，context 也设计得够好，但要让它在无人干预的情况下独立跑几个小时、产出一个完整的应用——还差点什么？这就是 **Harness 工程（Harness Engineering）**的舞台，也是这篇文章的主题。

Harness（Agent Harness）指的是围绕语言模型搭建的那一层软件基础设施——工具调用、context 管理、多 agent 编排、任务分解、会话间的状态传递，凡是"模型本身以外的一切"，都属于 Harness 的范畴。简单说，模型决定能力上限，Harness 决定这个上限能不能被稳定发挥出来。

本文记录了作者如何从前端设计出发，受生成对抗网络（GAN）启发，构建出"Generator + Evaluator"的双 agent 结构，再将其扩展为包含 Planner、Generator、Evaluator 的完整系统，最终实现数小时无人介入的全栈应用自主开发。文章还重点讨论了随着模型能力提升，Harness 应该如何跟着精简——对正在做 AI Agent 工程的开发者来说，很有参考价值。

原文来自 Anthropic 工程博客，发布于 2026 年 3 月 24 日，作者 Prithvi Rajasekaran 是 Anthropic Labs 团队成员。原文链接：[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)。

---

过去几个月，我一直在啃两个相互关联的问题：怎么让 Claude 做出高质量的前端设计，以及怎么让它在没人盯着的情况下独立构建完整的应用。这些工作脱胎于我们此前在[前端设计技能](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)和[长时运行 coding Agent Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 上的探索——提示工程加 Harness 设计确实把 Claude 的表现推上去了不少，但最终两条路都碰到了天花板。

为了突破，我开始找一种在两个截然不同的领域都能奏效的 AI 工程思路：一个靠主观审美，另一个靠可验证的正确性与可用性。受[生成对抗网络（GAN）](https://en.wikipedia.org/wiki/Generative_adversarial_network)的启发，我设计了一套包含Generator agent 与Evaluator agent 的多 agent 结构。要让Evaluator 的打分既可靠又有品味，关键是先建立一套评价标准，把"这个设计好看吗"这类主观判断拆解成具体可量化的维度。

随后，我把同样的思路移植到长时运行的自主 coding 中，沿用了早期 Harness 工作里跑通的两个经验：把构建任务拆解成可处理的小块，以及用结构化工件在会话间传递 context。最终落地为一套三 agent 架构——Planner、Generator、Evaluator——能在数小时的自主 coding 会话里产出完整的全栈应用。

### 为什么朴素方案总是不够用

我们之前已经验证过，Harness 设计对长时间运行的 agentic coding 效果影响很大。在早期[实验](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)里，我们让一个初始化 agent 把产品规格拆成任务列表，coding agent 逐功能实现，并在会话之间传递工件以保留 context。更广泛的开发者社区也形成了类似的共识，比如 ["Ralph Wiggum"](https://ghuntley.com/ralph/) 方案就是用 hooks 或脚本让 agent 保持持续迭代。

但有些问题始终甩不掉。面对更复杂的任务，agent 仍然容易跑偏。深入分析后，我们归结出两类典型的失效模式。

**第一类是 context 窗口塞满后模型连贯性下降**（详见我们关于 [context 工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)的文章）。部分模型还会出现"context 焦虑"——当它们觉得自己快到 context 上限时，会提前草草收工。**context 重置**——彻底清空 context 窗口、启动新 agent，同时附上一份记录了前一个 agent 状态和后续步骤的结构化交接文件——可以同时解决这两个问题。

这跟压缩（compaction）的思路不一样：压缩是把对话前段就地摘要，让同一个 agent 在压缩后的历史上接着干。压缩保留了连续性，但给不了 agent 一张白纸，context 焦虑依然会有。重置能给白纸，代价是交接文件必须带足够的状态，让下一个 agent 能顺畅接手。早期测试里，Claude Sonnet 4.5 的 context 焦虑严重到单靠压缩撑不住长任务，context 重置因此成了 Harness 设计的关键一环。这虽然解决了核心问题，但每次运行都会带来额外的编排复杂度、Token 开销和延迟。

**第二类是自我评估问题**——这是我们以前没有专门处理过的。让 agent 评估自己的输出时，它往往信心满满地给好评，即便在人类看来明显平庸。这个问题在设计这类主观任务里尤为突出，因为没有像跑测试那样的二元验证。一个布局是精致还是普通，本质上是一种判断，而 agent 给自己打分时会系统性地偏向正面。

即便是有可验证结果的任务，agent 也常常会出现影响完成质量的判断失误。把干活的 agent 和评判的 agent 分开，是应对这个问题的有效手段。分离本身不会立刻消除宽松倾向——Evaluator 也是 LLM，同样容易对 LLM 生成的内容手下留情。但把一个独立 Evaluator调教得更挑剔，远比让Generator 自我批判容易得多。只要有了外部反馈，生成器就有了具体的改进方向。

### 前端设计：让主观质量变得可量化

我从前端设计入手，因为自我评估问题在这里最典型。没有任何干预的情况下，Claude 倾向于产出中规中矩的布局——功能上能用，视觉上平平。

为前端设计构建 Harness 时，有两个判断塑造了整体思路。其一，审美虽然不能完全化约成分数——个人品味终究各有不同——但通过编入了设计原则和偏好的评分标准，可以推动质量提升。"这个设计漂亮吗"难有一致的答案，但"这个设计符合我们的好设计原则吗"给了 Claude 具体的评判依据。其二，把前端生成和前端评分分开，可以形成驱动生成器持续进步的反馈闭环。

基于此，我设计了四个评分维度，同时写进Generator 和 Evaluator 的提示：

- **设计质量**：整体是否浑然一体，而非东拼西凑？颜色、字体、布局、图像等元素能否共同营造出独特的氛围和气质。
- **原创性**：是否有定制化的决策痕迹，还是在套模板、用库的默认值、堆 AI 生成套路？有经验的设计师应该能认出刻意为之的创意选择。未经修改的库存组件，或 AI 生成的典型特征——比如白底卡片上的紫色渐变——都会在这里扣分。
- **工艺**：技术层面的执行质量：字体层级、间距一致性、色彩搭配、对比度。这是基本功，不是创意检验。大多数正常实现默认不会在这里翻车；扣分意味着基本功有漏洞。
- **功能性**：独立于美学的可用性。用户能不能看懂界面要做什么，找到主要操作，不用猜就能完成任务。

我把设计质量和原创性的权重放在工艺和功能性之上。Claude 在工艺和功能性上默认表现不错，模型本身就具备所需的技术能力。但在设计和原创性上，输出往往只是平庸之作。这套评分标准明确惩罚了那些高度雷同的"AI 套路"，通过加重这两项的权重，推着模型在审美上多冒一点险。

Evaluator 的校准用了带详细评分解析的少量示例，确保其判断和我的偏好对齐，也减少了迭代中的分数漂移。

整个循环搭建在 [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) 上，编排逻辑保持简洁。Generator agent 先根据用户提示生成 HTML/CSS/JS 前端；Evaluator 配备了 Playwright MCP，可以直接和实时页面交互，截图研究后对每个维度打分并给出详细评语。评语作为下一轮的输入反馈给生成器。每次生成跑 5 到 15 轮，每轮通常都在把生成器往更有辨识度的方向推。因为Evaluator 是在主动浏览页面而不是看静态截图，每个周期都需要真实的时间——完整跑下来最长可达四个小时。我还要求生成器在每轮评估后做一个策略判断：分数走势好就在当前方向上深化，感觉不对就彻底换一套审美思路。

各轮迭代中，Evaluator 的分数通常会持续爬升，直到趋于平稳，但仍有改善空间。有些生成在稳步改良，另一些则在某次迭代后发生了明显的审美转向。

评分标准的措辞以我没有预料到的方式影响着生成器。加入"最好的设计能达到博物馆级别"这类表述后，输出设计呈现出特定的视觉收敛倾向——说明标准本身的语言就在直接塑造输出的性格。

分数走势并不总是线性向上的。后期版本整体上通常更好，但我经常发现自己更喜欢中间某一轮的结果，而不是最后一轮。实现复杂度也往往随轮次增加，生成器会在Evaluator 的推动下尝试越来越有野心的方案。即便在第一轮，输出就已经明显好于没有任何提示的基线——说明评分标准和相关语言本身就在引导模型跳出通用默认值，还没等Evaluator 介入就已经起了作用。

有个案例让我印象很深：我让模型为一家荷兰艺术博物馆做网站。到第九轮，它产出了一个精致的深色主题落地页，视觉上无懈可击，但还在我预期的范围内。第十轮，它彻底推翻了前面的方案，把网站重新构想成一种空间体验：用 CSS 透视渲染的棋盘地板三维房间，画作自由悬挂在墙上，访客通过门洞而非滚动或点击在画廊间穿行。这种创意跳跃，是我在单次生成里从来没见过的。

<video controls style="width:100%;max-width:800px">
  <source src="https://cdn.sanity.io/files/4zrzovbb/website/9877febd34432f7f582aecd0023b951223605c6a.mp4" type="video/mp4">
</video>

### 向全栈 coding 延伸

带着这些发现，我把 GAN 启发的模式移植到了全栈开发。Generator-Evaluator 的循环与软件开发生命周期天然契合，代码审查和 QA 在其中扮演的结构性角色，和设计 Evaluator如出一辙。

#### 架构设计

在早期的[长时运行 Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 里，我们通过初始化 agent、逐功能推进的 coding agent 以及会话间的 context 重置，解决了多会话 coding 的连贯性问题。到了 Opus 4.5，模型在很大程度上自行消除了 context 焦虑，所以这套新 Harness 彻底去掉了 context 重置——agent 在整个构建过程中作为单个连续会话运行，context 增长由 Claude Agent SDK 的自动压缩处理。

系统包含三个 agent，分别对应我在早期实验中发现的不同问题：

**Planner**：接受 1 到 4 句话的简短提示，将其扩展为完整的产品规格。我要求它在范围上保持野心，聚焦产品背景和高层技术设计，而不是细粒度的实现细节——原因是一旦 Planner 早期把细节定错了，错误就会顺着流程一路传下去。把 agent 约束在交付物上、让它们自己摸索实现路径，这个思路更稳。同时，我也要求 Planner 主动寻找把 AI 功能编进产品规格的机会。

**Generator**：沿用早期 Harness 的逐功能方式，以 sprint 为单位工作，逐一从规格中挑功能实现。（译者注：sprint 是敏捷开发里的"冲刺周期"，通常指一到两周内完成一批预定功能的工作节奏，这里借用来表示每一轮的开发任务单元。）技术栈是 React、Vite、FastAPI 和 SQLite（后期换成了 PostgreSQL），每个 sprint 结束时要求 Generator 先自我评估，再交接给 QA，同时用 git 做版本控制。

**Evaluator**：用 Playwright MCP 像真实用户一样点击运行中的应用，测试 UI 功能、API 端点和数据库状态，再对照发现的 bug 和一套参照前端实验改编的评分标准（覆盖产品深度、功能性、视觉设计和代码质量）逐项打分。每个维度都有硬性门槛，任何一项不达线，sprint 失败，Generator 会收到具体的问题反馈。

每个 sprint 开始前，Generator 和 Evaluator 会先协商一份 **sprint 契约**：动手写代码之前，先就这块工作的"完成"标准对齐。产品规格故意保持在高层，这一步是在用户故事和可测试实现之间架桥。Generator 提出要做什么、怎么验收，Evaluator 审核方向对不对，两方来回协商直到对齐。

两者通过文件通信：一个 agent 写文件，另一个读取后在同一文件或新文件里回应。Generator 按照约定好的契约开工，完成后交给 QA 验收。这样既保证工作忠实于规格，又没有过早锁死实现细节。

#### 跑起来

第一版 Harness 用的是 Claude Opus 4.5，同一批提示分别跑了完整 Harness 和单 agent 对照。

用于生成复古游戏制作工具的提示是：

> Create a 2D retro game maker with features including a level editor, sprite editor, entity behaviors, and a playable test mode.

| Harness | 时长 | 费用 |
|---------|------|------|
| 单 agent | 20 分钟 | $9 |
| 完整 Harness | 6 小时 | $200 |

费用相差 20 倍，但输出质量的差距一眼就能看出来。

单 agent 版本的核心玩法彻底坏了——实体能显示，但对任何输入毫无反应，实体定义和游戏运行时之间的连接断了，表面上完全看不出来。

**单 agent 版本截图：**

![单agent版：应用初始界面](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F23c98f1d7ae720bfb39190d50e0706c03b177ad8-1999x1320.png&w=3840&q=75)
*单 agent 版：打开应用时的初始界面*

![单agent版：精灵编辑器](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F24472c85629a6c82a092f25def4a659042be1f7c-1999x1010.png&w=3840&q=75)
*单 agent 版：精灵编辑器*

![单agent版：游戏无法运行](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F79217dbfce3f31172eb7fd4deee5449023c9b2ac-1999x757.png&w=3840&q=75)
*单 agent 版：尝试运行关卡，游戏完全坏掉*

Harness 版本从同一句提示出发，Planner 将其扩展为横跨十个 sprint 的 16 个功能规格，涵盖了精灵动画系统、行为模板、音效与音乐、AI 辅助的精灵生成器和关卡设计师，以及带可分享链接的游戏导出功能。整体完成度更高，最关键的是——游戏真的能玩了。

**完整 Harness 版本截图：**

![完整 Harness 版：初始界面](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2Fa8bef95425966495629095a5cb38bde4a8b13558-1999x997.png&w=3840&q=75)
*完整 Harness 版：新建游戏时的初始界面，整体视觉风格更统一*

![完整 Harness 版：精灵编辑器](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2Fc05aa3ef8daaf0ef3d0dba66d6480ab753e9cbaa-1999x1007.png&w=3840&q=75)
*完整 Harness 版：精灵编辑器更丰富，工具栏更清晰*

![完整 Harness 版：AI 辅助关卡设计](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2F287b35f4683ecb77ac6a8d66bf2b3ed5956d1db9-1999x1008.png&w=3840&q=75)
*完整 Harness 版：通过内置 AI 功能生成关卡*

![完整 Harness 版：游戏可以正常运行](https://www.anthropic.com/_next/image?url=https%3A%2F%2Fwww-cdn.anthropic.com%2Fimages%2F4zrzovbb%2Fwebsite%2Ff2953550e51957a0a49a3792a0df3bcfed0fde48-1994x1654.png&w=3840&q=75)
*完整 Harness 版：游戏可以正常运行了*

让 Evaluator 达到这个水准需要下大力气调教。开箱即用的 Claude 是个很烂的 QA agent。早期跑下来，它能发现真实的问题，然后自己把自己说服："也没那么严重嘛"，转头就批准了。它还倾向于走马观花，不深挖边界情况，导致更隐蔽的 bug 经常漏网。调教方法是：读Evaluator 的日志，找出它的判断和我的判断有出入的地方，然后更新 QA 提示来纠偏。这样来回跑几轮，Evaluator 的打分才算到位。

下表列出了Evaluator 抓到的一些问题示例：

| 契约条款 | Evaluator 发现 |
|----------|-----------|
| 矩形填充工具支持点击拖拽、将所选图块填入矩形区域 | **不通过** — 工具只在拖拽起点/终点放置图块，而非填充整个区域。`fillRectangle` 函数存在，但 `mouseUp` 时未正确触发。 |
| 用户可以选中并删除已放置的实体生成点 | **不通过** — `LevelEditor.tsx:892` 的删除键处理器同时要求 `selection` 和 `selectedEntityId` 非空，但点击实体只会设置 `selectedEntityId`。条件应改为 `selection \|\| (selectedEntityId && activeLayer === 'entity')`。 |
| 用户可通过 API 对动画帧重新排序 | **不通过** — `PUT /frames/reorder` 路由定义在 `/{frame_id}` 路由之后，FastAPI 将 `'reorder'` 匹配为整数型 `frame_id`，返回 422：`"unable to parse string as an integer"`。 |

#### 迭代精简 Harness

第一批结果令人鼓舞，但这套 Harness 确实太重——慢，也贵。Harness 里的每个组件，背后都是一个关于"模型自己搞不定某件事"的假设，而这些假设值得持续审视——它们本来就可能是错的，随着模型进步也会很快过时。我们在[《构建有效 Agent》](https://www.anthropic.com/research/building-effective-agents)里提出的核心原则就是："先找最简单的可行方案，只在必要时才加复杂度。"

Opus 4.6 发布后（官方说法是"规划更谨慎、agentic 任务持续时间更长、在大型 codebase 里更可靠、代码审查和调试能力更强"），我有了进一步精简的理由。这次我改用更系统的方式：每次只去掉一个组件，看它对最终结果的影响。

**去掉 sprint 结构**：Opus 4.6 的提升让模型可以自己处理任务分解，不再需要这层脚手架。Planner 和 Evaluator 保留，Evaluator 改为在整次运行结束后统一打分，而不是逐 sprint 评估。

由此得出的实践结论是：Evaluator 不是非此即彼的选择，它在任务超出当前模型能独立稳定完成的边界时才值得投入。

#### 更新版 Harness 的结果

用下面这条提示在新版 Harness 上生成数字音频工作站（DAW）：

> Build a fully featured DAW in the browser using the Web Audio API.

| Agent 与阶段 | 时长 | 费用 |
|-------------|------|------|
| Planner | 4.7 分钟 | $0.46 |
| 构建（第 1 轮） | 2 小时 7 分钟 | $71.08 |
| QA（第 1 轮） | 8.8 分钟 | $3.24 |
| 构建（第 2 轮） | 1 小时 2 分钟 | $36.89 |
| QA（第 2 轮） | 6.8 分钟 | $3.09 |
| 构建（第 3 轮） | 10.9 分钟 | $5.88 |
| QA（第 3 轮） | 9.6 分钟 | $4.06 |
| **V2 Harness 合计** | **3 小时 50 分钟** | **$124.70** |

QA agent 依然抓出了真实的问题。第一轮反馈写道：

> 整体是个不错的应用，设计还原度高，AI agent 扎实，后端稳定。主要失分点是功能完整性——应用好看，AI 集成运转良好，但几个核心 DAW 功能只有界面展示，缺乏交互深度：时间线上的片段无法拖拽移动，没有乐器 UI 面板（合成器旋钮、鼓垫），也没有可视化效果编辑器（均衡器曲线、压缩器仪表）。这些不是边角情况——它们是让 DAW 真正能用的核心交互，规格里也明确要求了。

第二轮又抓到了几处功能缺口：

> 剩余问题：
> - 音频录制仍是桩实现（按钮能切换，但采集不到麦克风）
> - 片段边缘拖拽调整大小和片段分割未实现
> - 效果可视化是数字滑块，不是图形化的（没有均衡器曲线）

经过几轮迭代，最终产出的应用具备了一个能用的音乐制作程序所需的全部核心部件：在浏览器里跑通的编排视图、混音器和传输控件，外加一个完全靠提示驱动的集成 agent——定拍子、铺旋律、建鼓轨、调混音、加混响，全程不用手动操作。下面是演示视频：

<video controls style="width:100%;max-width:800px">
  <source src="https://cdn.sanity.io/files/4zrzovbb/website/555910f9adb3938734940224e7a6f4c7cbbbd8f2.mp4" type="video/mp4">
</video>

### 往后的路

随着模型持续进步，可以预期它们能处理时间更长、难度更高的任务。某些情况下，围绕模型的脚手架会随时间变得越来越不重要，等下一个模型出来，有些问题就自然消失了。但反过来，模型越强，构建能突破模型基线能力的复杂 Harness 的空间也就越大。

几点经验值得带走：

1. **始终针对你正在用的模型做实验**，读它在真实问题上的运行轨迹，调到你想要的效果。
2. **面对复杂任务时**，把任务拆开、对各个子问题分配专项 agent，有时能带来明显的质量提升。
3. **每当新模型上线，重新审视你的 Harness**——去掉不再承重的组件，加上此前做不到、现在可以做的新能力。

我的判断是：有趣的 Harness 组合空间不会随模型进步而缩小，只会位移。对 AI 工程师来说，持续找到下一个新颖组合，才是真正的工作所在。
