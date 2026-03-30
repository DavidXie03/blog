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

这篇文章来自 Anthropic 工程博客，原文发布于 2026 年 3 月 24 日，作者 Prithvi Rajasekaran 是 Anthropic Labs 团队成员。文章记录了他在过去数月里解决两个相互关联问题的经历：如何让 Claude 产出高质量的前端设计，以及如何让它在没有人工干预的情况下构建完整的应用程序。他从生成对抗网络（GAN）中获得灵感，设计了"生成器 + 评估器"的多智能体结构，并最终将其扩展为一套包含规划器、生成器和评估器的三 Agent 架构，实现了数小时无人介入的全栈应用自主开发。文章还着重讨论了随着模型能力提升，Harness 设计应如何随之精简演化——这对当下从事 AI Agent 工程的开发者颇具参考价值。原文链接：[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)。

---

## 译文

过去几个月，我一直在研究两个相互关联的问题：让 Claude 产出高质量的前端设计，以及让它在无需人工干预的情况下构建完整的应用程序。这项工作源于我们早期在[前端设计技能](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)和[长时运行编码 Agent Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 上的探索——通过提示工程与 Harness 设计，我们将 Claude 的表现大幅提升，但两者最终都碰到了天花板。

为了突破，我开始寻找在两个差异悬殊的领域都能生效的 AI 工程新路径：一个领域靠主观审美，另一个靠可验证的正确性与可用性。受[生成对抗网络（GAN）](https://en.wikipedia.org/wiki/Generative_adversarial_network)的启发，我设计了一套包含生成器 Agent 与评估器 Agent 的多智能体结构。要让评估器打分既可靠又有品味，前提是先建立一套标准，将"这个设计好看吗"这类主观判断转化为具体可量化的维度。

随后，我把这些思路移植到长时运行的自主编程中，沿用了早期 Harness 工作的两个经验：将构建任务拆解为可处理的小块，以及用结构化工件在会话间传递上下文。最终落地成一套三 Agent 架构——规划器、生成器、评估器——能在数小时的自主编程会话中产出完整的全栈应用。

### 为什么简单实现总是失效

我们此前已证明，Harness 设计对长时间运行的 Agentic 编程效果影响显著。在早期[实验](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)中，我们用一个初始化 Agent 将产品规格拆解为任务列表，编程 Agent 逐功能实现，并在会话间传递工件以保留上下文。更广泛的开发者社区也形成了类似共识，比如"Ralph Wiggum"方法用 hooks 或脚本让 Agent 保持持续迭代。

但有些问题始终顽固。面对更复杂的任务，Agent 仍然容易随着时间推移偏离轨道。深入拆解后，我们归纳出两类常见的失效模式。

**其一是上下文窗口填满后模型的连贯性下降**（详见我们关于[上下文工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)的文章）。部分模型还会出现"上下文焦虑"——当它们判断自己快到上下文上限时，会提前草草收场。**上下文重置**——完全清空上下文窗口、启动新 Agent，同时配合一份携带前一个 Agent 状态和后续步骤的结构化交接文件——可以同时解决这两个问题。

这与**压缩（compaction）**的思路不同：压缩是将对话前段就地摘要，让同一个 Agent 在压缩后的历史上继续工作。压缩保留了延续性，但给不了 Agent 一张白纸，上下文焦虑依然可能存在。重置能提供白纸，代价是交接文件必须携带足够的状态，让下一个 Agent 能顺畅接手。早期测试中，Claude Sonnet 4.5 的上下文焦虑严重到单靠压缩无法支撑长任务表现，上下文重置因此成为 Harness 设计的关键。这虽解决了核心问题，但也为每次运行带来了编排复杂度、额外的 Token 开销和延迟。

**其二是自我评估问题**——这是我们此前未专门处理过的。让 Agent 评估自己的输出时，它往往会信心满满地给出好评，即便在人类看来质量明显平庸。这个问题在设计等主观任务中尤为突出，因为没有像软件测试那样的二元验证。一个布局是精致还是普通，本质上是一种判断，而 Agent 给自己打分时会系统性地偏向正面。

即便是有可验证结果的任务，Agent 也时常表现出影响完成质量的判断失误。**将执行工作的 Agent 与评判工作的 Agent 分开**，被证明是应对这一问题的有效手段。分离本身不能立刻消除宽松倾向——评估器也是 LLM，同样倾向于对 LLM 生成的内容宽容。但将一个独立评估器调教得更加挑剔，远比让生成器批判自己的工作容易得多。一旦外部反馈存在，生成器就有了具体的改进抓手。

### 前端设计：把主观质量变得可量化

我从前端设计入手，因为自我评估问题在这里最为突出。没有任何干预的情况下，Claude 倾向于产出安全、中规中矩的布局——功能上说得过去，视觉上乏善可陈。

有两个认识塑造了我为前端设计构建的 Harness。第一，审美虽然不能完全化约为分数——个人品味终究各异——但通过编码了设计原则和偏好的评分标准，可以推动质量提升。"这个设计漂亮吗"难以一致作答，但"这个设计符合我们的好设计原则吗"给了 Claude 具体的评判依据。第二，将前端生成与前端评分分离，可以形成驱动生成器不断进步的反馈闭环。

基于此，我设计了四个评分维度，同时写入生成器和评估器的提示：

- **设计质量**：整体是否浑然一体，而非零件拼凑？颜色、字体、布局、图像等元素能否共同营造出独特的氛围与气质。
- **原创性**：是否有定制化的决策痕迹，还是模板套用、库默认值与 AI 生成模式的堆叠？人类设计师应当能认出刻意为之的创意选择。未经修改的库存组件，或 AI 生成的典型特征——比如白卡上的紫色渐变——都会在这里丢分。
- **工艺**：技术层面的执行质量：字体层级、间距一致性、色彩和谐度、对比度。这是能力的基本盘，而非创意检验。大多数合理实现默认不会在这里出问题；失分意味着基本功缺失。
- **功能性**：独立于美学的可用性。用户能否看懂界面要做什么，找到主要操作，不用瞎猜就能完成任务。

我将设计质量与原创性的权重置于工艺和功能性之上。Claude 在工艺和功能性上默认表现良好，所需技术能力对模型来说是自然具备的。但在设计和原创性上，输出往往不过是平庸之作。这些评分标准明确惩罚了那些高度雷同的"AI 糊弄"模式，通过加重这两项的权重，推动模型在审美上多冒一点险。

评估器的校准用了带详细评分解析的少量示例，确保其判断与我的偏好对齐，也减少了迭代中的分数漂移。

整个循环搭建在 [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) 上，编排逻辑保持简洁。生成器 Agent 首先根据用户提示生成 HTML/CSS/JS 前端；评估器配备了 Playwright MCP，可以直接与实时页面交互，截图研究后再对每个维度打分并给出详细评语。评语作为下一轮迭代的输入反馈给生成器。每次生成运行 5 到 15 轮，每轮通常推着生成器往更有辨识度的方向走。由于评估器是在主动浏览页面而非评判静态截图，每个周期都需要真实的时间——完整跑下来最长可达四小时。我还要求生成器在每轮评估后做一个策略判断：如果分数走势良好，就在当前方向上深化；如果效果不对，就彻底换一套审美。

各轮迭代中，评估器的评分通常会持续提升，直至趋于平稳，仍有改善空间。有些生成在渐进改良，另一些则在迭代间发生了明显的审美转向。

评分标准的措辞以我未曾预料的方式影响着生成器。加入"最好的设计达到博物馆级别"这类表述后，设计呈现出特定的视觉收敛倾向，说明标准本身的语言直接塑造了输出的性格。

分数走势并不总是线性向上的。后期版本整体上通常更好，但我经常发现自己更偏爱中间某一轮的结果而非最后一轮。实现复杂度也往往随轮次增加，生成器会在评估器的推动下尝试越来越有野心的方案。即便在第一轮，输出就已经明显好于没有任何提示的基线，说明评分标准和相关语言本身就在引导模型离开通用默认值，还未等评估器反馈介入便已奏效。

有一个案例令人印象深刻：我提示模型为一家荷兰艺术博物馆创建网站。到第九轮，它产出了一个精致的深色主题落地页，视觉上无懈可击，但仍在我预期的范围之内。第十轮，它彻底推翻了既有方案，将网站重新构想为一种空间体验：用 CSS 透视渲染的棋盘地板三维房间，画作自由悬挂在墙上，以门洞而非滚动或点击的方式在画廊间穿行。这种创意跳跃，是我在单次生成中从未见过的。

### 向全栈编程延伸

带着这些发现，我将 GAN 启发的模式移植到了全栈开发中。生成器-评估器的循环与软件开发生命周期天然契合，代码审查和 QA 扮演的结构性角色与设计评估器如出一辙。

#### 架构设计

在早期的[长时运行 Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 中，我们通过初始化 Agent、逐功能推进的编程 Agent 以及会话间的上下文重置，解决了多会话编程的连贯性问题。Opus 4.5 在很大程度上自行消除了上下文焦虑，因此这套新的 Harness 彻底去掉了上下文重置——Agent 在整个构建过程中作为一个连续会话运行，上下文增长由 Claude Agent SDK 的自动压缩处理。

三 Agent 系统的角色分工如下：

**规划器（Planner）**：接受 1 到 4 句话的简短提示，将其扩展为完整的产品规格。我要求它在范围上保持野心，专注于产品背景和高层技术设计，而非细粒度的实现细节——原因是一旦规划器在早期把细节指定错了，错误就会顺着流程级联进入下游实现。约束 Agent 在交付物上，让它们自己摸索实现路径，这个思路更稳。同时，我也要求规划器主动寻找将 AI 功能编织进产品规格的机会。

**生成器（Generator）**：沿用早期 Harness 的逐功能方式，以冲刺（sprint）为单位工作，逐一从规格中选取功能实现。每个冲刺使用 React、Vite、FastAPI 和 SQLite（后期换成了 PostgreSQL）技术栈，每轮冲刺结束时要求生成器先自我评估再交接给 QA，同时用 git 做版本控制。

**评估器（Evaluator）**：用 Playwright MCP 像真实用户一样点击运行中的应用，测试 UI 功能、API 端点和数据库状态，再对照发现的 bug 和一套仿照前端实验改编的标准（覆盖产品深度、功能性、视觉设计和代码质量）逐项打分。每个维度都有硬性门槛，任何一项不达线，冲刺失败，生成器会收到具体的问题反馈。

每个冲刺开始前，生成器和评估器会先协商一份**冲刺契约**：在动手写代码之前，就这一块工作的"完成"标准达成共识。产品规格有意保持高层，这个步骤是在用户故事和可测试实现之间架一座桥。生成器提出要做什么、用什么方式验收，评估器审核提案是否方向正确，两方反复协商直至对齐。

通信通过文件完成：一个 Agent 写文件，另一个读取后在同一文件或新文件中回应。生成器依照约定好的契约开工，完成后交给 QA 验收。这样既保证了工作忠实于规格，又没有过早锁死实现细节。

#### 跑起来

第一版 Harness 使用 Claude Opus 4.5，同一批提示分别跑完整 Harness 和单 Agent 对照。

用于生成复古游戏制作工具的提示是：

> Create a 2D retro game maker with features including a level editor, sprite editor, entity behaviors, and a playable test mode.

| Harness | 时长 | 费用 |
|---------|------|------|
| 单 Agent | 20 分钟 | $9 |
| 完整 Harness | 6 小时 | $200 |

费用超出 20 倍，但输出质量的差距一眼就看出来了。

单 Agent 版本的核心玩法彻底坏了——实体能显示出来，但对任何输入毫无反应，实体定义和游戏运行时之间的连线断了，表面上看不出任何提示。Harness 版本从同一句提示出发，规划器将其扩展为横跨十个冲刺的 16 个功能规格，涵盖了精灵动画系统、行为模板、音效与音乐、AI 辅助的精灵生成器和关卡设计师，以及带可分享链接的游戏导出功能。整体完成度更高，最关键的是——游戏真的能玩了。

让评估器达到这个水准需要下大力气调教。开箱即用的 Claude 是个糟糕的 QA Agent。早期运行里，它能识别出真实的问题，然后自己说服自己"这也没什么大不了"，转头就批准了。调教的方法是：读评估器的日志，找出它的判断和我的判断出现偏差的例子，更新 QA 提示来纠正。经过几轮这样的循环，评估器的打分才到了我能接受的水准。

#### 迭代精简 Harness

第一批结果令人鼓舞，但这套 Harness 也太笨重、太慢、太贵。Harness 里的每个组件，背后都是一个关于"模型自己做不到某件事"的假设，而这些假设值得持续检验——因为它们本来就可能是错的，而且随着模型进步很快就会过时。我们在[《构建有效 Agent》](https://www.anthropic.com/research/building-effective-agents)中提出的核心原则正是："找到最简单的可行方案，只在必要时才增加复杂度。"

Opus 4.6 发布后（官方表述是"规划更谨慎、Agentic 任务持续时间更长、在大型代码库中运行更可靠、代码审查和调试能力更强"），这给了我进一步精简的理由。我换成了更系统的方式：每次只移除一个组件，观察它对最终结果的影响。

**去掉冲刺结构**：Opus 4.6 的提升让模型可以自行处理任务分解，不再需要这层脚手架。规划器和评估器保留，评估器改为在整次运行结束后一次性打分，而非逐冲刺评估。

由此得出的实践结论是：**评估器不是一道非此即彼的选择题，它在任务超出当前模型独立稳定完成的边界时才值得投入成本。**

#### 更新版 Harness 的结果

用以下提示在更新版 Harness 上生成数字音频工作站（DAW）：

> Build a fully featured DAW in the browser using the Web Audio API.

| Agent 与阶段 | 时长 | 费用 |
|--------------|------|------|
| 规划器 | 4.7 分钟 | $0.46 |
| 构建（第 1 轮） | 2 小时 7 分钟 | $71.08 |
| QA（第 1 轮） | 8.8 分钟 | $3.24 |
| 构建（第 2 轮） | 1 小时 2 分钟 | $36.89 |
| QA（第 2 轮） | 6.8 分钟 | $3.09 |
| 构建（第 3 轮） | 10.9 分钟 | $5.88 |
| QA（第 3 轮） | 9.6 分钟 | $4.06 |
| **V2 Harness 合计** | **3 小时 50 分钟** | **$124.70** |

QA Agent 依然揪出了真实的问题。第一轮反馈指出，若干核心 DAW 功能只有界面但没有交互深度——这些不是边角情况，而是让 DAW 能用的核心交互。经过几轮迭代，最终产出的应用具备了一个可用音乐制作程序所需的全部核心部件：在浏览器里跑通的编排视图、混音器和传输控件，以及一个可以完全通过提示驱动的集成 Agent——定拍子、铺旋律、建鼓轨、调混音、加混响，从头到尾不用手动操作。

### 往后的路

随着模型持续进步，大致可以预期它们能处理时间更长、难度更高的任务。在某些情况下，围绕模型的脚手架会随时间变得越来越不重要，等下一个模型出来，有些问题就自然解决了。但另一方面，模型越强，构建能突破模型基线能力的复杂 Harness 的空间也就越大。

几点值得带走的经验：

1. **始终针对你正在使用的模型做实验**，读它在真实问题上的运行轨迹，调优到你想要的结果。
2. **面对复杂任务时**，把任务拆解、对各个子问题分配专项 Agent，有时能带来明显的质量提升。
3. **每当新模型上线，重新审视你的 Harness**——剥掉不再承重的组件，加上此前做不到、现在可以做到的新能力。

我的判断是：**有趣的 Harness 组合空间不会随模型进步而收窄，只会位移。对 AI 工程师来说，持续找到下一个新颖组合，才是真正的工作所在。**

---

## 原文（English Original）

Written by Prithvi Rajasekaran, a member of our [Labs](https://www.anthropic.com/news/introducing-anthropic-labs) team.

Over the past several months I've been working on two interconnected problems: getting Claude to produce high-quality frontend designs, and getting it to build complete applications without human intervention. This work originated with earlier efforts on our [frontend design skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md) and [long-running coding agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), where my colleagues and I were able to improve Claude's performance well above baseline through prompt engineering and harness design—but both eventually hit ceilings.

To break through, I sought out novel AI engineering approaches that held across two quite different domains, one defined by subjective taste, the other by verifiable correctness and usability. Taking inspiration from [Generative Adversarial Networks](https://en.wikipedia.org/wiki/Generative_adversarial_network) (GANs), I designed a multi-agent structure with a generator and evaluator agent. Building an evaluator that graded outputs reliably—and with taste—meant first developing a set of criteria that could turn subjective judgments like "is this design good?" into concrete, gradable terms.

I then applied these techniques to long-running autonomous coding, carrying over two lessons from our earlier harness work: decomposing the build into tractable chunks, and using structured artifacts to hand off context between sessions. The final result was a three-agent architecture—planner, generator, and evaluator—that produced rich full-stack applications over multi-hour autonomous coding sessions.

### Why naive implementations fall short

We've previously shown that harness design has a substantial impact on the effectiveness of long running agentic coding. In an earlier [experiment](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), we used an initializer agent to decompose a product spec into a task list, and a coding agent that implemented the tasks one feature at a time before handing off artifacts to carry context across sessions. The broader developer community has converged on similar insights, with approaches like the "Ralph Wiggum" method using hooks or scripts to keep agents in continuous iteration cycles.

But some problems remained persistent. For more complex tasks, the agent still tends to go off the rails over time. While decomposing this issue, we observed two common failure modes with agents executing these sorts of tasks.

First is that models tend to lose coherence on lengthy tasks as the context window fills (see our post on [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). Some models also exhibit "context anxiety," in which they begin wrapping up work prematurely as they approach what they believe is their context limit. Context resets—clearing the context window entirely and starting a fresh agent, combined with a structured handoff that carries the previous agent's state and the next steps—addresses both these issues.

This differs from compaction, where earlier parts of the conversation are summarized in place so the same agent can keep going on a shortened history. While compaction preserves continuity, it doesn't give the agent a clean slate, which means context anxiety can still persist. A reset provides a clean slate, at the cost of the handoff artifact having enough state for the next agent to pick up the work cleanly. In our earlier testing, we found Claude Sonnet 4.5 exhibited context anxiety strongly enough that compaction alone wasn't sufficient to enable strong long task performance, so context resets became essential to the harness design. This solves the core issue, but adds orchestration complexity, token overhead, and latency to each harness run.

A second issue, which we haven't previously addressed, is self-evaluation. When asked to evaluate work they've produced, agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre. This problem is particularly pronounced for subjective tasks like design, where there is no binary check equivalent to a verifiable software test. Whether a layout feels polished or generic is a judgment call, and agents reliably skew positive when grading their own work.

However, even on tasks that do have verifiable outcomes, agents still sometimes exhibit poor judgment that impedes their performance while completing the task. Separating the agent doing the work from the agent judging it proves to be a strong lever to address this issue. The separation doesn't immediately eliminate that leniency on its own; the evaluator is still an LLM that is inclined to be generous towards LLM-generated outputs. But tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work, and once that external feedback exists, the generator has something concrete to iterate against.

### Frontend design: making subjective quality gradable

I started by experimenting on frontend design, where the self-evaluation issue was most visible. Absent any intervention, Claude normally gravitates toward safe, predictable layouts that are technically functional but visually unremarkable.

Two insights shaped the harness I built for frontend design. First, while aesthetics can't be fully reduced to a score—and individual tastes will always vary—they can be improved with grading criteria that encode design principles and preferences. "Is this design beautiful?" is hard to answer consistently, but "does this follow our principles for good design?" gives Claude something concrete to grade against. Second, by separating frontend generation from frontend grading, we can create a feedback loop that drives the generator toward stronger outputs.

With this in mind, I wrote four grading criteria that I gave to both the generator and evaluator agents in their prompts:

- **Design quality**: Does the design feel like a coherent whole rather than a collection of parts? Strong work here means the colors, typography, layout, imagery, and other details combine to create a distinct mood and identity.
- **Originality**: Is there evidence of custom decisions, or is this template layouts, library defaults, and AI-generated patterns? A human designer should recognize deliberate creative choices. Unmodified stock components—or telltale signs of AI generation like purple gradients over white cards—fail here.
- **Craft**: Technical execution: typography hierarchy, spacing consistency, color harmony, contrast ratios. This is a competence check rather than a creativity check. Most reasonable implementations do fine here by default; failing means broken fundamentals.
- **Functionality**: Usability independent of aesthetics. Can users understand what the interface does, find primary actions, and complete tasks without guessing?

I emphasized design quality and originality over craft and functionality. Claude already scored well on craft and functionality by default, as the required technical competence tended to come naturally to the model. But on design and originality, Claude often produced outputs that were bland at best. The criteria explicitly penalized highly generic "AI slop" patterns, and by weighting design and originality more heavily it pushed the model toward more aesthetic risk-taking.

I calibrated the evaluator using few-shot examples with detailed score breakdowns. This ensured the evaluator's judgment aligned with my preferences, and reduced score drift across iterations.

I built the loop on the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview), which kept the orchestration straightforward. A generator agent first created an HTML/CSS/JS frontend based on a user prompt. I gave the evaluator the Playwright MCP, which let it interact with the live page directly before scoring each criterion and writing a detailed critique. In practice, the evaluator would navigate the page on its own, screenshotting and carefully studying the implementation before producing its assessment. That feedback flowed back to the generator as input for the next iteration. I ran 5 to 15 iterations per generation, with each iteration typically pushing the generator in a more distinctive direction as it responded to the evaluator's critique. Because the evaluator was actively navigating the page rather than scoring a static screenshot, each cycle took real wall-clock time. Full runs stretched up to four hours. I also instructed the generator to make a strategic decision after each evaluation: refine the current direction if scores were trending well, or pivot to an entirely different aesthetic if the approach wasn't working.

Across runs, the evaluator's assessments improved over iterations before plateauing, with headroom still remaining. Some generations refined incrementally. Others took sharp aesthetic turns between iterations.

The wording of the criteria steered the generator in ways I didn't fully anticipate. Including phrases like "the best designs are museum quality" pushed designs toward a particular visual convergence, suggesting that the prompting associated with the criteria directly shaped the character of the output.

While scores generally improved over iterations, the pattern was not always cleanly linear. Later implementations tended to be better as a whole, but I regularly saw cases where I preferred a middle iteration over the last one. Implementation complexity also tended to increase across rounds, with the generator reaching for more ambitious solutions in response to the evaluator's feedback. Even on the first iteration, outputs were noticeably better than a baseline with no prompting at all, suggesting the criteria and associated language themselves steered the model away from generic defaults before any evaluator feedback led to further refinement.

In one notable example, I prompted the model to create a website for a Dutch art museum. By the ninth iteration, it had produced a clean, dark-themed landing page for a fictional museum. The page was visually polished but largely in line with my expectations. Then, on the tenth cycle, it scrapped the approach entirely and reimagined the site as a spatial experience: a 3D room with a checkered floor rendered in CSS perspective, artwork hung on the walls in free-form positions, and doorway-based navigation between gallery rooms instead of scroll or click. It was the kind of creative leap that I hadn't seen before from a single-pass generation.

### Scaling to full-stack coding

With these findings in hand, I applied this GAN-inspired pattern to full-stack development. The generator-evaluator loop maps naturally onto the software development lifecycle, where code review and QA serve the same structural role as the design evaluator.

#### The architecture

In our earlier [long-running harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), we had solved for coherent multi-session coding with an initializer agent, a coding agent that worked one feature at a time, and context resets between sessions. Context resets were a key unlock: the harness used Sonnet 4.5, which exhibited the "context anxiety" tendency mentioned earlier. Creating a harness that worked well across context resets was key to keeping the model on task. Opus 4.5 largely removed that behavior on its own, so I was able to drop context resets from this harness entirely. The agents were run as one continuous session across the whole build, with the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)'s automatic compaction handling context growth along the way.

For this work I built on the foundation from the original harness with a three-agent system, with each agent addressing a specific gap I'd observed in prior runs. The system contained the following agent personas:

**Planner**: Our previous long-running harness required the user to provide a detailed spec upfront. I wanted to automate that step, so I created a planner agent that took a simple 1-4 sentence prompt and expanded it into a full product spec. I prompted it to be ambitious about scope and to stay focused on product context and high level technical design rather than detailed technical implementation. This emphasis was due to the concern that if the planner tried to specify granular technical details upfront and got something wrong, the errors in the spec would cascade into the downstream implementation. It seemed smarter to constrain the agents on the deliverables to be produced and let them figure out the path as they worked. I also asked the planner to find opportunities to weave AI features into the product specs. (See example in the Appendix at the bottom.)

**Generator**: The one-feature-at-a-time approach from the earlier harness worked well for scope management. I applied a similar model here, instructing the generator to work in sprints, picking up one feature at a time from the spec. Each sprint implemented the app with a React, Vite, FastAPI, and SQLite (later PostgreSQL) stack, and the generator was instructed to self-evaluate its work at the end of each sprint before handing off to QA. It also had git for version control.

**Evaluator**: Applications from earlier harnesses often looked impressive but still had real bugs when you actually tried to use them. To catch these, the evaluator used the Playwright MCP to click through the running application the way a user would, testing UI features, API endpoints, and database states. It then graded each sprint against both the bugs it had found and a set of criteria modeled on the frontend experiment, adapted here to cover product depth, functionality, visual design, and code quality. Each criterion had a hard threshold, and if any one fell below it, the sprint failed and the generator got detailed feedback on what went wrong.

Before each sprint, the generator and evaluator negotiated a sprint contract: agreeing on what "done" looked like for that chunk of work before any code was written. This existed because the product spec was intentionally high-level, and I wanted a step to bridge the gap between user stories and testable implementation. The generator proposed what it would build and how success would be verified, and the evaluator reviewed that proposal to make sure the generator was building the right thing. The two iterated until they agreed.

Communication was handled via files: one agent would write a file, another agent would read it and respond either within that file or with a new file that the previous agent would read in turn. The generator then built against the agreed-upon contract before handing the work off to QA. This kept the work faithful to the spec without over-specifying implementation too early.

#### Running the harness

For the first version of this harness, I used Claude Opus 4.5, running user prompts against both the full harness and a single-agent system for comparison. I used Opus 4.5 since this was our best coding model when I began these experiments.

I wrote the following prompt to generate a retro video game maker:

> Create a 2D retro game maker with features including a level editor, sprite editor, entity behaviors, and a playable test mode.

| Harness | Duration | Cost |
|---------|----------|------|
| Solo | 20 min | $9 |
| Full harness | 6 hr | $200 |

The harness was over 20x more expensive, but the difference in output quality was immediately apparent.

I was expecting an interface where I could construct a level and its component parts (sprites, entities, tile layout) then hit play to actually play the level. I started by opening the solo run's output, and the initial application seemed in line with those expectations.

As I clicked through, however, issues started to emerge. The layout wasted space, with fixed-height panels leaving most of the viewport empty. The workflow was rigid. Trying to populate a level prompted me to create sprites and entities first, but nothing in the UI guided me toward that sequence. More to the point, the actual game was broken. My entities appeared on screen but nothing responded to input. Digging into the code revealed that the wiring between entity definitions and the game runtime was broken, with no surface indication of where.

After evaluating the solo run, I turned my attention to the harness run. This run started from the same one-sentence prompt, but the planner step expanded that prompt into a 16-feature spec spread across ten sprints. It went well beyond what the solo run attempted. In addition to the core editors and play mode, the spec called for a sprite animation system, behavior templates, sound effects and music, an AI-assisted sprite generator and level designer, and game export with shareable links. I gave the planner access to our frontend design skill, which it read and used to create a visual design language for the app as part of the spec. For each sprint, the generator and evaluator negotiated a contract defining the specific implementation details for the sprint, and the testable behaviors that would be tested to verify completion.

The app immediately showed more polish and smoothness than the solo run. The canvas used the full viewport, the panels were sized sensibly, and the interface had a consistent visual identity that tracked the design direction from the spec. Some of the clunkiness I'd seen in the solo run did remain—the workflow still didn't make it clear that you should build sprites and entities before trying to populate a level, and I had to figure that out by poking around. This read as a gap in the base model's product intuition rather than something the harness was designed to address, though it did suggest a place where targeted iteration inside the harness could help to further improve output quality.

Working through the editors, the new run's advantages over solo became more apparent. The sprite editor was richer and more fully featured, with cleaner tool palettes, a better color picker, and more usable zoom controls.

Because I'd asked the planner to weave AI features into its specs, the app also came with a built-in Claude integration that let me generate different parts of the game through prompting. This significantly sped up the workflow.

The biggest difference was in play mode. I was actually able to move my entity and play the game. The physics had some rough edges—my character jumped onto a platform but ended up overlapping with it, which felt intuitively wrong—but the core thing worked, which the solo run did not manage.

Getting the evaluator to perform at this level took work. Out of the box, Claude is a poor QA agent. In early runs, I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway. It also tended to test superficially, rather than probing edge cases, so more subtle bugs often slipped through. The tuning loop was to read the evaluator's logs, find examples where its judgment diverged from mine, and update the QAs prompt to solve for those issues. It took several rounds of this development loop before the evaluator was grading in a way that I found reasonable. Even then, the harness output showed the limits of the model's QAing capabilities: small layout issues, interactions that felt unintuitive in places, and undiscovered bugs in more deeply nested features that the evaluator hadn't exercised thoroughly.

#### Iterating on the harness

The first set of harness results was encouraging, but it was also bulky, slow, and expensive. The logical next step was to find ways to simplify the harness without degrading its performance. This was partly common sense and partly a function of a more general principle: every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing, both because they may be incorrect, and because they can quickly go stale as models improve. Our blog post [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) frames the underlying idea as "find the simplest solution possible, and only increase complexity when needed," and it's a pattern that shows up consistently for anyone maintaining an agent harness.

In my first attempt to simplify, I cut the harness back radically and tried a few creative new ideas, but I wasn't able to replicate the performance of the original. It also became difficult to tell which pieces of the harness design were actually load-bearing, and in what ways. Based on that experience, I moved to a more methodical approach, removing one component at a time and reviewing what impact it had on the final result.

As I was going through these iteration cycles, we also released Opus 4.6, which provided further motivation to reduce harness complexity. There was good reason to expect 4.6 would need less scaffolding than 4.5 did. From our [launch blog](https://www.anthropic.com/news/claude-opus-4-6): "[Opus 4.6] plans more carefully, sustains agentic tasks for longer, can operate more reliably in larger codebases, and has better code review and debugging skills to catch its own mistakes." It also improved substantially on long-context retrieval. These were all capabilities the harness had been built to supplement.

**Removing the sprint construct**: I started by removing the sprint construct entirely. The sprint structure had helped to decompose work into chunks for the model to work coherently. Given the improvements in Opus 4.6, there was good reason to believe that the model could natively handle the job without this sort of decomposition.

I kept both the planner and evaluator, as each continued to add obvious value. Without the planner, the generator under-scoped: given the raw prompt, it would start building without first speccing its work, and end up creating a less feature-rich application than the planner did.

With the sprint construct removed, I moved the evaluator to a single pass at the end of the run rather than grading per sprint. Since the model was much more capable, it changed how load-bearing the evaluator was for certain runs, with its usefulness depending on where the task sat relative to what the model could do reliably on its own. On 4.5, that boundary was close: our builds were at the edge of what the generator could do well solo, and the evaluator caught meaningful issues across the build. On 4.6, the model's raw capability increased, so the boundary moved outward. Tasks that used to need the evaluator's check to be implemented coherently were now often within what the generator handled well on its own, and for tasks within that boundary, the evaluator became unnecessary overhead. But for the parts of the build that were still at the edge of the generator's capabilities, the evaluator continued to give real lift.

The practical implication is that the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo.

Alongside the structural simplification, I also added prompting to improve how the harness built AI features into each app, specifically getting the generator to build a proper agent that could drive the app's own functionality through tools. That took real iteration, since the relevant knowledge is recent enough that Claude's training data covers it thinly. But with enough tuning, the generator was building agents correctly.

#### Results from the updated harness

To put the updated harness to the test, I used the following prompt to generate a Digital Audio Workstation (DAW), a music production program for composing, recording, and mixing songs:

> Build a fully featured DAW in the browser using the Web Audio API.

The run was still lengthy and expensive, at about 4 hours and $124 in token costs.

| Agent & Phase | Duration | Cost |
|---------------|----------|------|
| Planner | 4.7 min | $0.46 |
| Build (Round 1) | 2 hr 7 min | $71.08 |
| QA (Round 1) | 8.8 min | $3.24 |
| Build (Round 2) | 1 hr 2 min | $36.89 |
| QA (Round 2) | 6.8 min | $3.09 |
| Build (Round 3) | 10.9 min | $5.88 |
| QA (Round 3) | 9.6 min | $4.06 |
| **Total V2 Harness** | **3 hr 50 min** | **$124.70** |

Most of the time went to the builder, which ran coherently for over two hours without the sprint decomposition that Opus 4.5 had needed.

As with the previous harness, the planner expanded the one-line prompt into a full spec. From the logs, I could see the generator model did a good job planning the app and the agent design, wiring the agent up, and testing it before handing off to QA.

That being said, the QA agent still caught real gaps. In its first-round feedback, it noted:

> This is a strong app with excellent design fidelity, solid AI agent, and good backend. The main failure point is Feature Completeness — while the app looks impressive and the AI integration works well, several core DAW features are display-only without interactive depth: clips can't be dragged/moved on the timeline, there are no instrument UI panels (synth knobs, drum pads), and no visual effect editors (EQ curves, compressor meters). These aren't edge cases — they're the core interactions that make a DAW usable, and the spec explicitly calls for them.

In its second round feedback, it again caught several functionality gaps:

> Remaining gaps:
> - Audio recording is still stub-only (button toggles but no mic capture)
> - Clip resize by edge drag and clip split not implemented
> - Effect visualizations are numeric sliders, not graphical (no EQ curve)

The generator was still liable to miss details or stub features when left to its own devices, and the QA still added value in catching those last mile issues for the generator to fix.

The final app had all the core pieces of a functional music production program: a working arrangement view, mixer, and transport running in the browser. Beyond that, I was able to put together a short song snippet entirely through prompting: the agent set the tempo and key, laid down a melody, built a drum track, adjusted mixer levels, and added reverb. The core primitives for song composition were present, and the agent could drive them autonomously, using tools to create a simple production from end to end.

### What comes next

As models continue to improve, we can roughly expect them to be capable of working for longer, and on more complex tasks. In some cases, that will mean the scaffold surrounding the model matters less over time, and developers can wait for the next model and see certain problems solve themselves. On the other hand, the better the models get, the more space there is to develop harnesses that can achieve complex tasks beyond what the model can do at baseline.

With this in mind, there are a few lessons from this work worth carrying forward. It is always good practice to experiment with the model you're building against, read its traces on realistic problems, and tune its performance to achieve your desired outcomes. When working on more complex tasks, there is sometimes headroom from decomposing the task and applying specialized agents to each aspect of the problem. And when a new model lands, it is generally good practice to re-examine a harness, stripping away pieces that are no longer load-bearing to performance and adding new pieces to achieve greater capability that may not have been possible before.

From this work, my conviction is that the space of interesting harness combinations doesn't shrink as models improve. Instead, it moves, and the interesting work for AI engineers is to keep finding the next novel combination.
