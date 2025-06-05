"use client"; // Required for components using hooks like useEffect

import React from "react";
import { Markdown } from "~/components/deer-flow/markdown"; // Adjust path if necessary

const mermaidTestMarkdown = `
### 2.1 目标市场与应用场景

\`\`\`mermaid
pie title 全球高温Alpha淀粉酶市场份额概览
    "Novozymes" : 35
    "DuPont" : 25
    "DSM" : 10
    "Amano Enzyme" : 5
    "中国主要供应商" : 15
    "其他" : 10
\`\`\`

高温α-淀粉酶的核心功能是在高温下催化淀粉水解，主要应用场景包括:
- **淀粉加工**:液化与糖化工序，专利US8545907B2显示热稳定性淀粉酶可提升效率
- **生物燃料**:高温乙醇发酵的关键催化剂，占据30%市场份额
- **新兴应用**:烘焙食品保鲜（延长保质期）、造纸工业纤维改性

市场主要驱动因素包括生物燃料产业扩张、食品制造标准化和可持续生产技术需求。主要限制因素是超高温度（>100°C）下的酶稳定性技术瓶颈。

### 2.2 市场规模与增长潜力

\`\`\`mermaid
xychart-beta
    title "全球高温α-淀粉酶市场规模（百万美元）"
    x-axis [2023, 2030]
    y-axis "金额" 300 --> 400
    bar [331, 423]
\`\`\`

市场核心数据:
- **全球市场**:2023年3.31亿美元，预计2030年达4.23亿美元（CAGR 3.6%）
- **中国市场**:预计2023-2030年CAGR >5%（QYResearch）
- **价值链**:
  \`原材料 → 菌株开发 → 发酵生产 → 纯化制剂 → 终端应用\`

### 2.3 核心竞争者分析

\`\`\`mermaid
pie title 全球市场竞争格局
    "诺维信" : 35
    "杜邦" : 25
    "AB Enzymes" : 10
    "区域竞争者" : 30
\`\`\`

| 竞争者      | 核心技术优势                   | 市场策略               | 代表产品    |
|-------------|------------------------------|-----------------------|------------|
| 诺维信      | >85°C热稳定性（US20130059315A1） | 生物燃料领域主导       | Termamyl® SC|
| 杜邦        | 低pH耐热混合酶（US8815560B2）   | 淀粉加工解决方案       | -          |
| AB Enzymes  | 烘焙食品专用酶                 | 食品工业细分领域深耕   | -          |
| 山东隆达    | 成本优势                       | 区域市场渗透           | -          |

技术发展里程碑:
\`\`\`mermaid
gantt
    title 高温α-淀粉酶技术演进
    dateFormat  YYYY
    section 技术突破
    基因工程菌株        : 2013, 2016
    Termamyl® SC上市   : 2018, 2018
    低pH热稳定酶       : 2021, 2021
    古菌衍生酶         : 2023, 2023
\`\`\`
`;

export default function TestMermaidPage() {
    return (
        <div style={{ padding: "20px" }}>
            <h1>Mermaid Test</h1>
            <Markdown>{mermaidTestMarkdown}</Markdown>
        </div>
    );
} 