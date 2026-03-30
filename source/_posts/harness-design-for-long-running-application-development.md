---
title: Harness Design for Long-Running Application Development
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

> 原文：[Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
> 作者：Prithvi Rajasekaran（Anthropic Labs 团队成员）
> 发布日期：2026 年 3 月 24 日

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

**Planner**: Our previous long-running harness required the user to provide a detailed spec upfront. I wanted to automate that step, so I created a planner agent that took a simple 1-4 sentence prompt and expanded it into a full product spec. I prompted it to be ambitious about scope and to stay focused on product context and high level technical design rather than detailed technical implementation. This emphasis was due to the concern that if the planner tried to specify granular technical details upfront and got something wrong, the errors in the spec would cascade into the downstream implementation. It seemed smarter to constrain the agents on the deliverables to be produced and let them figure out the path as they worked. I also asked the planner to find opportunities to weave AI features into the product specs.

**Generator**: The one-feature-at-a-time approach from the earlier harness worked well for scope management. I applied a similar model here, instructing the generator to work in sprints, picking up one feature at a time from the spec. Each sprint implemented the app with a React, Vite, FastAPI, and SQLite (later PostgreSQL) stack, and the generator was instructed to self-evaluate its work at the end of each sprint before handing off to QA. It also had git for version control.

**Evaluator**: Applications from earlier harnesses often looked impressive but still had real bugs when you actually tried to use them. To catch these, the evaluator used the Playwright MCP to click through the running application the way a user would, testing UI features, API endpoints, and database states. It then graded each sprint against both the bugs it had found and a set of criteria modeled on the frontend experiment, adapted here to cover product depth, functionality, visual design, and code quality. Each criterion had a hard threshold, and if any one fell below it, the sprint failed and the generator got detailed feedback on what went wrong.

Before each sprint, the generator and evaluator negotiated a sprint contract: agreeing on what "done" looked like for that chunk of work before any code was written. This existed because the product spec was intentionally high-level, and I wanted a step to bridge the gap between user stories and testable implementation. The generator proposed what it would build and how success would be verified, and the evaluator reviewed that proposal to make sure the generator was building the right thing. The two iterated until they agreed.

Communication was handled via files: one agent would write a file, another agent would read it and respond either within that file or with a new file that the previous agent would read in turn. The generator then built against the agreed-upon contract before handing the work off to QA. This kept the work faithful to the spec without over-specifying implementation too early.

#### Running the harness

For the first version of this harness, I used Claude Opus 4.5, running user prompts against both the full harness and a single-agent system for comparison.

I wrote the following prompt to generate a retro video game maker:

> Create a 2D retro game maker with features including a level editor, sprite editor, entity behaviors, and a playable test mode.

| Harness | Duration | Cost |
|---------|----------|------|
| Solo | 20 min | $9 |
| Full harness | 6 hr | $200 |

The harness was over 20x more expensive, but the difference in output quality was immediately apparent.

The solo run produced an app with broken core gameplay—entities appeared on screen but nothing responded to input, and the wiring between entity definitions and the game runtime was broken. The harness run, starting from the same one-sentence prompt, expanded into a 16-feature spec spread across ten sprints, including a sprite animation system, behavior templates, sound effects and music, an AI-assisted sprite generator and level designer, and game export with shareable links. The app showed noticeably more polish, and crucially—the core gameplay actually worked.

Getting the evaluator to perform at this level took work. Out of the box, Claude is a poor QA agent. In early runs, it would identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway. The tuning loop was to read the evaluator's logs, find examples where its judgment diverged from mine, and update the QA's prompt to solve for those issues. It took several rounds before the evaluator was grading in a way I found reasonable.

#### Iterating on the harness

The first set of harness results was encouraging, but it was also bulky, slow, and expensive. Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing—both because they may be incorrect, and because they can quickly go stale as models improve. Our blog post [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) frames it as: "find the simplest solution possible, and only increase complexity when needed."

With the release of Opus 4.6—which "plans more carefully, sustains agentic tasks for longer, can operate more reliably in larger codebases, and has better code review and debugging skills to catch its own mistakes"—I moved to a more methodical approach, removing one component at a time and reviewing what impact it had.

**Removing the sprint construct**: I removed the sprint structure entirely. Given the improvements in Opus 4.6, the model could natively handle decomposition without this scaffolding. I kept both the planner and evaluator, and moved the evaluator to a single pass at the end of the run rather than grading per sprint.

The practical implication: the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo.

#### Results from the updated harness

To test the updated harness, I used this prompt to generate a Digital Audio Workstation (DAW):

> Build a fully featured DAW in the browser using the Web Audio API.

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

The QA agent still caught real gaps. Its first-round feedback noted that several core DAW features were display-only without interactive depth. After iterating, the final app had all the core pieces of a functional music production program: a working arrangement view, mixer, and transport running in the browser—with an integrated agent that could compose a short song snippet entirely through prompting.

### What comes next

As models continue to improve, we can roughly expect them to be capable of working for longer, and on more complex tasks. In some cases, that will mean the scaffold surrounding the model matters less over time, and developers can wait for the next model and see certain problems solve themselves. On the other hand, the better the models get, the more space there is to develop harnesses that can achieve complex tasks beyond what the model can do at baseline.

A few lessons worth carrying forward:

1. Always experiment with the model you're building against, read its traces on realistic problems, and tune its performance to achieve your desired outcomes.
2. When working on more complex tasks, there is sometimes headroom from decomposing the task and applying specialized agents to each aspect of the problem.
3. When a new model lands, re-examine the harness, stripping away pieces that are no longer load-bearing and adding new pieces for greater capability.

My conviction is that the space of interesting harness combinations doesn't shrink as models improve. Instead, it moves, and the interesting work for AI engineers is to keep finding the next novel combination.

---

## 中文翻译

作者：Prithvi Rajasekaran，Anthropic Labs 团队成员

在过去几个月里，我一直在研究两个相互关联的问题：让 Claude 产出高质量的前端设计，以及让它在无需人工干预的情况下构建完整的应用程序。这项工作起源于我们早期在[前端设计技能](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)和[长时运行编码 Agent Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 上的探索——通过提示工程和 Harness 设计，我和同事们将 Claude 的表现大幅提升，但两者最终都触碰到了天花板。

为了突破瓶颈，我开始寻找在两个截然不同领域都能奏效的 AI 工程新方法：一个领域依赖主观审美，另一个领域依赖可验证的正确性与可用性。受[生成对抗网络（GAN）](https://en.wikipedia.org/wiki/Generative_adversarial_network)的启发，我设计了一个包含生成器 Agent 和评估器 Agent 的多智能体结构。要让评估器可靠地、有品味地给输出打分，首先需要开发一套标准，将"这个设计好吗？"这类主观判断转化为具体的、可量化的维度。

随后，我将这些技术应用到长时运行的自主编程场景，延续了早期 Harness 工作中的两个经验：将构建任务拆解为可处理的小块，以及使用结构化的工件在会话之间传递上下文。最终成果是一个三 Agent 架构——规划器、生成器和评估器——能够在数小时的自主编程会话中产出丰富的全栈应用。

### 为什么朴素实现总是失效

我们此前已证明，Harness 设计对长时间运行的 Agentic 编程效果有重大影响。在早期[实验](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)中，我们使用初始化 Agent 将产品规格分解为任务列表，编程 Agent 逐一实现各功能，并在会话间传递工件以保留上下文。更广泛的开发者社区也汇聚了类似洞见，例如"Ralph Wiggum"方法使用 hooks 或脚本让 Agent 保持持续迭代循环。

但一些问题依然顽固存在。对于更复杂的任务，Agent 仍然容易随着时间推移而"跑偏"。在拆解这个问题时，我们观察到两种常见的失效模式。

**第一：上下文窗口填满时模型会失去连贯性**（参见我们关于[上下文工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)的文章）。部分模型还会表现出"上下文焦虑"——当它们认为自己接近上下文上限时，会提前草草收工。**上下文重置**——完全清空上下文窗口并启动新的 Agent，配合携带前一个 Agent 状态和后续步骤的结构化交接——可以同时解决这两个问题。

这与**压缩（compaction）**不同：压缩是将对话前半段就地摘要，让同一个 Agent 在缩短的历史上继续工作。压缩保留了连续性，但无法给 Agent 一张白纸，上下文焦虑仍可能持续。重置提供了白纸，代价是交接工件必须包含足够的状态，让下一个 Agent 能顺畅接手。在早期测试中，我们发现 Claude Sonnet 4.5 的上下文焦虑足够严重，仅靠压缩无法支撑强劲的长任务表现，因此上下文重置成为 Harness 设计的关键。这解决了核心问题，但也为每次 Harness 运行带来了编排复杂度、Token 开销和延迟。

**第二：自我评估问题**——这是我们此前未曾专门处理的。当 Agent 被要求评估自己的输出时，它们往往会自信地给出好评——即便在人类观察者看来，质量明显一般。这个问题在设计等主观任务中尤为突出，因为没有等效于软件测试的二元验证。一个布局是精致还是平庸，是一种判断，而 Agent 在给自己的工作打分时会系统性地偏向正面。

即便在有可验证结果的任务中，Agent 有时仍会表现出影响完成质量的糟糕判断。**将执行工作的 Agent 与评判工作的 Agent 分离**，被证明是解决这个问题的强力手段。分离本身并不能立即消除这种宽松倾向——评估器仍然是一个倾向于对 LLM 生成输出宽松的 LLM。但将一个独立的评估器调教得更加挑剔，远比让生成器批判自己的工作更容易实现。一旦外部反馈存在，生成器就有了具体的改进目标。

### 前端设计：让主观质量可量化

我从前端设计入手实验，因为自我评估问题在这里最为明显。在没有任何干预的情况下，Claude 通常倾向于生成安全、可预期的布局——技术上可用，但视觉上平淡无奇。

两个洞见塑造了我为前端设计构建的 Harness。第一，虽然审美不能完全化约为分数——个人品味始终各异——但可以通过编码了设计原则和偏好的评分标准来提升。"这个设计漂亮吗？"很难一致回答，但"这个设计符合我们的好设计原则吗？"给了 Claude 具体的评判依据。第二，将前端生成与前端评分分离，可以创造一个驱动生成器输出更强成果的反馈循环。

基于此，我写了四个评分维度，同时纳入生成器和评估器 Agent 的提示中：

- **设计质量**：设计是否感觉是一个连贯的整体，而非零件的拼凑？强劲的设计意味着颜色、排版、布局、图像等细节共同构建出独特的氛围和身份。
- **原创性**：是否有定制化决策的痕迹，还是模板布局、库默认值和 AI 生成模式的堆砌？人类设计师应该能认出刻意的创意选择。未修改的库存组件——或 AI 生成的典型特征，如白卡上的紫色渐变——在这里会失分。
- **工艺**：技术执行：排版层级、间距一致性、色彩和谐、对比度。这是能力检验而非创意检验。大多数合理实现默认会在这里表现良好；失败意味着基本功的缺失。
- **功能性**：独立于美学的可用性。用户能否理解界面的功能、找到主要操作、无需猜测地完成任务？

我将设计质量和原创性的权重置于工艺和功能性之上。Claude 默认在工艺和功能性上表现良好，所需技术能力对模型来说自然而然。但在设计和原创性上，Claude 的输出往往充其量是平淡的。这些标准明确惩罚了高度通用的"AI 糊弄"模式，通过加重设计和原创性的权重，推动模型承担更多审美风险。

我使用带有详细评分分解的少样本示例来校准评估器，确保评估器的判断与我的偏好一致，并减少迭代中的分数漂移。

我在 [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) 上构建了这个循环，编排逻辑保持简洁。生成器 Agent 首先根据用户提示创建 HTML/CSS/JS 前端；评估器获得了 Playwright MCP，能在对实时页面进行截图并仔细研究后，为每个标准打分并撰写详细评语。反馈作为下一轮迭代的输入流回生成器。每次生成运行 5 到 15 轮迭代，每轮迭代通常推动生成器朝更具辨识度的方向发展。由于评估器在主动导航页面而非对静态截图打分，每个周期需要真实的时间——完整运行可长达四小时。

迭代过程中有一个令人印象深刻的案例：我提示模型创建一个荷兰艺术博物馆的网站。到第九轮迭代时，它产出了一个精致的深色主题登陆页。然后，在第十轮，它彻底推翻了原有方案，将网站重新构想为一个空间体验：用 CSS 透视渲染的棋盘格地板的 3D 房间，艺术品随意悬挂在墙上，以门道而非滚动或点击在画廊间导航。这是我在单次生成中从未见过的创意飞跃。

### 扩展到全栈编程

带着这些发现，我将 GAN 启发的模式应用到全栈开发中。生成器-评估器循环自然映射到软件开发生命周期，代码审查和 QA 扮演着与设计评估器相同的结构角色。

#### 架构设计

在早期的[长时运行 Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 中，我们通过初始化 Agent、逐功能工作的编程 Agent 以及会话间的上下文重置，解决了连贯的多会话编程问题。Opus 4.5 在很大程度上自行消除了"上下文焦虑"行为，所以我能够完全去掉这个 Harness 中的上下文重置，Agent 在整个构建过程中作为一个连续会话运行，由 Claude Agent SDK 的自动压缩处理上下文增长。

三 Agent 系统包含以下角色：

**规划器（Planner）**：接受 1-4 句话的简短提示，将其展开为完整的产品规格。我提示它在范围上保持雄心，专注于产品背景和高层技术设计，而非细粒度的技术实现——避免规划器在早期指定错误的细节，导致错误级联进入下游实现。同时要求规划器寻找将 AI 功能编织进产品规格的机会。

**生成器（Generator）**：延续早期 Harness 的逐功能方法，指示生成器以冲刺（sprint）为单位工作，逐一从规格中选取功能实现。每个冲刺使用 React、Vite、FastAPI 和 SQLite（后改为 PostgreSQL）技术栈，生成器被要求在每个冲刺结束时自我评估工作，然后交接给 QA。

**评估器（Evaluator）**：使用 Playwright MCP 像用户一样点击运行中的应用程序，测试 UI 功能、API 端点和数据库状态。然后对照发现的错误和一套仿照前端实验的标准（适配为覆盖产品深度、功能性、视觉设计和代码质量）对每个冲刺打分。每个标准都有硬性门槛，任何一项低于门槛，冲刺失败，生成器会收到关于哪里出了问题的详细反馈。

每个冲刺前，生成器和评估器协商一份**冲刺契约**：在任何代码编写之前，就该工作块的"完成"标准达成一致。这弥合了用户故事与可测试实现之间的差距。通信通过文件处理：一个 Agent 写文件，另一个读取并在该文件内或用新文件回应。这在不过早指定实现细节的情况下，使工作忠实于规格。

#### 运行 Harness

使用以下提示生成复古游戏制作工具：

> 创建一个 2D 复古游戏制作器，功能包括关卡编辑器、精灵编辑器、实体行为和可玩的测试模式。

| Harness | 时长 | 费用 |
|---------|------|------|
| 单 Agent | 20 分钟 | $9 |
| 完整 Harness | 6 小时 | $200 |

Harness 贵了 20 倍以上，但输出质量差距立竿见影。单 Agent 版本的核心游戏玩法完全损坏——实体能显示但对输入没有任何响应；而 Harness 版本从同一句提示出发，扩展出了 16 个功能、横跨 10 个冲刺的规格，核心游戏真正可以运行。

让评估器达到这个水平需要大量调教。开箱即用的 Claude 是个糟糕的 QA Agent——早期运行中，它会识别出真实问题，然后说服自己这没什么大不了然后批准工作。调教循环是：阅读评估器日志，找到它的判断与我的判断偏离的例子，更新 QA 提示来解决这些问题。经过几轮这样的开发循环，评估器的评分才达到我认为合理的水准。

#### 迭代优化 Harness

Harness 的首批结果令人鼓舞，但也臃肿、缓慢且昂贵。Harness 中的每个组件都编码了一个关于模型自身无法完成某事的假设，而这些假设值得压力测试——因为它们可能是错误的，也可能随模型提升而迅速过时。《构建有效 Agent》中的核心原则是："找到最简单的可行方案，只在必要时才增加复杂度。"

随着 Opus 4.6 的发布（"更谨慎地规划、更持久地维持 Agentic 任务、在更大型代码库中更可靠地运行、更好地审查和调试代码"），我采用了更系统的方法：每次只移除一个组件，查看其对最终结果的影响。

**移除冲刺结构**：鉴于 Opus 4.6 的改进，模型可以原生处理任务分解，无需这种脚手架。我保留了规划器和评估器，将评估器改为在整次运行结束时单次评分，而非逐冲刺评分。

实际含义是：**评估器不是一个固定的是/否决策，它在任务超出当前模型独立可靠完成的范围时，才值得付出成本**。

#### 更新 Harness 的结果

测试更新后的 Harness，使用以下提示生成数字音频工作站（DAW）：

> 使用 Web Audio API 在浏览器中构建一个功能完整的 DAW。

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

QA Agent 仍然捕获了真实的差距——第一轮反馈指出若干核心 DAW 功能只有界面没有交互深度。经过迭代，最终应用具备了功能完整的音乐制作程序所需的所有核心部件：在浏览器中运行的编排视图、混音器和传输控制，集成 Agent 完全通过提示就能创作一段短曲。

### 展望未来

随着模型持续进步，我们大致可以预期它们能处理更长时间、更复杂的任务。在某些情况下，这意味着围绕模型的脚手架随时间变得不那么重要，开发者可以等待下一个模型让某些问题自行解决。另一方面，模型越好，开发能超越模型基线能力的复杂 Harness 的空间也越大。

几个值得铭记的经验：

1. **始终针对正在构建的模型进行实验**，阅读其在真实问题上的运行轨迹，调优以达到期望的结果。
2. **面对更复杂的任务时**，有时可以通过将任务分解并对问题的每个方面应用专项 Agent 来获得提升空间。
3. **每当新模型上线时，重新审视 Harness**——剥离那些不再承重的组件，增加新组件以达到此前不可能的更大能力。

我的信念是：**随着模型改进，有趣的 Harness 组合空间并不会缩小，而是会移动。对 AI 工程师来说，有趣的工作就是持续寻找下一个新颖的组合。**

---

*原文链接：https://www.anthropic.com/engineering/harness-design-long-running-apps*
