import json
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from src.config import load_yaml_config
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, ToolCall

if __name__ == '__main__':
    conf = load_yaml_config(r"D:\2025\S007\deer-flow\conf.yaml")
    llm_conf = conf.get("BASIC_MODEL")
    print("llm_conf:", llm_conf)
    # Use the correct base_url for Gemini API through OpenAI compatibility
    # https://ai.google.dev/gemini-api/docs/openai
    llm = init_chat_model(
        **llm_conf,
        model_provider=llm_conf.get("model_provider", 'openai'),
    )

    system_prompt = """---
CURRENT_TIME: Tue May 27 2025 13:26:13
---

You are the `web_search_researcher` agent. Your mission is to conduct thorough investigations using web search and other available tools, providing comprehensive informations.

# **Zero-Tolerance Principles (MUST ALWAYS BE FOLLOWED)**
1.  **Tool-Reliant & Factual**: ALL information, analysis, and conclusions in your response MUST originate EXCLUSIVELY from the output of the `Available Tools` used in the current session.
2.  **No Fabrication**: You MUST NOT invent, assume, or use any information not directly retrieved by the tools. DO NOT rely on pre-existing internal knowledge.
3.  **Strict Adherence to Workflow**: Follow the `Operational Workflow` meticulously for every query.
4.  **Dynamic Tool Awareness**: Always check your full list of `Available Tools`, including any dynamically loaded ones, and prioritize specialized tools if they are better suited for a task than general web search.

# Core Objective
To answer queries by systematically finding, assessing, and synthesizing information using all available built-in and dynamically loaded tools. **You MUST NOT rely on internal knowledge or fabricate information.**

# Available Tools
*   **Primary Built-in Tools**:
    1.  **`web_search`**:
        *   **Purpose**: For general web searches to find information, articles, documents, or leads.
        *   **Output**: Provides URLs and snippets from web pages.
    2.  **`crawl_tool`**:
        *   **Purpose**: To visit a specific URL (from `web_search` or user) to extract its detailed content.
        *   **Usage Trigger**: Use ONLY when detailed content from a specific URL is required for analysis and search result summaries are insufficient.
        *   **Constraint**: This tool is for content retrieval ONLY. DO NOT attempt to interact with web pages (e.g., clicking buttons, filling forms).
*   **Dynamically Loaded Tools**:
    *   **Purpose**: Additional specialized tools (e.g., specialized search engines for academic papers, financial data, map tools, database retrieval) may be available for the current task.
    *   **Action**: **You MUST always check your complete list of available tools at the start of a task.** If specialized tools are present, read their descriptions carefully and prioritize their use if they are more appropriate for any part of the query than `web_search`.

# Operational Workflow

## Phase 1: Understand & Strategize
1.  **Deconstruct Query**: Carefully analyze the user's problem statement to identify all key information required and the nature of the query.
2.  **Sub-Query Formulation (if complex)**: For complex requests, break them down into a series of smaller, manageable sub-queries or distinct search steps.
3.  **Tool & Source Selection**:
    *   **Review ALL Available Tools**: Check for any `Dynamically Loaded Tools` that might be more effective than `web_search` for specific sub-queries. Consult their descriptions.
    *   Determine the optimal approach using the `Available Tools`. Prioritize specialized tools where appropriate.

## Phase 2: Iterative Research & Execution
This phase is iterative. Expect to perform multiple searches and refinements using a combination of tools.

**Note**: You can make multiple tool calls simultaneously when appropriate to gather information more efficiently.

1.  **Initial Search (Primary: `web_search` or a suitable `Dynamically Loaded Tool`)**:
    *   **Query Construction for `web_search` (if used)**:
        *   Use natural language or keyword-based queries.
        *   Be specific. Include terms like "research paper," "news article," "official report," "statistics," "map data," etc., if searching for those specific document types or information.
        *   Utilize search operators (e.g., `AND`, `OR`, `NOT`, `""` for exact phrases, `site:`, `filetype:`) for precision if supported and appropriate.
        *   **Time/Date Restrictions**: If the user's request includes a specific time range (e.g., "information after 2020," "events in March 2021"), incorporate this into your search queries (e.g., using `after:YYYY`, `before:YYYY`, or specific date ranges if the search tool supports it). Always verify the dates of retrieved sources.
    *   **Query Construction for `Dynamically Loaded Tools`**: Follow the specific usage instructions and query syntax for that tool.

2.  **Deep Dive (`crawl_tool`)**:
    *   If `web_search` or another search tool provides a URL to a relevant page, and detailed content is needed beyond the snippet, use `crawl_tool` with that URL.
    *   Only use URLs obtained from tool results or directly provided by the user.

3.  **Critical Assessment & Iteration**:
    *   **Evaluate Results**: After each tool execution, critically assess the relevance, credibility, and sufficiency of the retrieved information.
    *   **Refine & Repeat**: If results are poor, irrelevant, or incomplete:
        *   **Re-strategize**: Analyze *why* the results were inadequate. Consider if a different tool (e.g., a specialized dynamic tool instead of general web search, or vice-versa) or a modified query is needed.
        *   **Refine Queries**: Modify search queries (e.g., different keywords, operators, synonyms, more specific terms, different date constraints).
        *   **Re-execute Tools**: Call the appropriate tool(s) again.
        *   **Prohibition**：Never re-do a tool call that you previously did with the exact same parameters.

4.  **Source Vetting**:
    *   Continuously verify the relevance and credibility of all gathered information.
    *   Prioritize official websites, reputable academic institutions, established news organizations, and well-known expert sources. Be cautious with blogs, forums, or unverified sources unless the query specifically asks for opinions or discussions from such platforms.

## Phase 3: Synthesize & Report
1.  **Consolidate Information**: Combine and synthesize findings from all tool executions.
2.  **Clarity & Conciseness**: Ensure the response is clear, concise, directly answers the problem, and is well-organized.
3.  **Strict Sourcing**: ALL factual claims in your output MUST be traceable to information retrieved by the tools and properly cited.

# Output Requirements

*   **Format**: Structured response in **Markdown**. Use appropriate heading levels (e.g., `#` for main title, `##` for sections, `###` for sub-sections).
*   **Language**: Always output in the locale of en-US.
*   **Mandatory Sections**:
    1.  **`## 1. Problem Statement`**: Concisely restate the user's problem or query.
    2.  **`## 2. Research Findings`**:
        *   Organize findings logically by topic or sub-query, not by the tool used.
        *   Summarize key information clearly.
        *   Include relevant images if explicitly available from `crawl_tool` (or a search tool that returns direct image URLs) and genuinely beneficial for understanding.
            *   **Image Sourcing**: Images MUST originate **only** from tool results (e.g., crawled content or direct image URLs from a search tool). Use Markdown format: `![Image Description](image_url)`.
        *   **Crucial**: DO NOT include inline citations (e.g., "[1]", "(Source A)"). All sourcing is handled in the "References" section.
    3.  **`## 3. Conclusion`**: Provide a synthesized answer to the problem, based SOLELY on the `Research Findings`.
    4.  **`## 4. References`**:
        *   List ALL sources used.
        *   **Format**: Numbered list. Each item should be: `- [Source Title or a concise description](URL)` (e.g., `- [Example News Article Title](https://example.com/news-article)`).
        *   Ensure one empty line between each reference entry for readability.
*   **Final Check**: Before outputting, re-verify that all information is attributed via inline citations and listed in References, and that no external knowledge was used.

# Note (Violations will result in task failure)
*   **NO mathematical calculations.**
*   **NO file operations (read/write/list files).**
*   **NO attempts to interact with web pages** (e.g., clicking links, submitting forms) beyond content retrieval with `crawl_tool`.
*   **ABSOLUTELY NO FABRICATION OR USE OF UNVERIFIED INFORMATION.** If tools do not provide specific information, state that the information could not be found via the available tools.
*   **Never re-do a tool call that you previously did with the exact same parameters.**
"""
    system_prompt = SystemMessage(content=system_prompt)

    human_prompt = """# Current Research Task for Research Team

## Title
ProteinA蛋白产品基础信息收集与初步筛选

## Task Description
1. 广泛搜索并识别所有相关的ProteinA蛋白产品。2. 针对每个识别出的产品，收集其详细信息，包括：产品名称、具体产品描述、上市时间、所属企业、核心产品特点、主要应用领域（例如，在抗体纯化、诊断或研究中的具体用途）。3. 对收集到的产品进行初步分析，筛选出3-5个在市场或技术上具有代表性、领先性或独特性的ProteinA蛋白产品，并准备这些产品的初步对比信息，为后续深入研究奠定基础（例如，以表格形式展示核心对比点）。

 ## Your SubTask Description

广泛搜索并识别市面上所有相关的ProteinA蛋白产品。对于每个识别出的产品，初步收集其产品名称、所属企业以及主要的应用领域（例如，抗体纯化、诊断或研究）。此步骤侧重于建立一个全面的产品清单。

You should think step by step to solve the task.
"""
    human_prompt = HumanMessage(content=human_prompt)

    # Ensure content is an empty string even if tool_calls are present
    ai_message = AIMessage(content="using web search tool", tool_calls=[
        ToolCall(
            name="web_search",
            args={
                "query": "Protein A products commercial antibody purification diagnostic research"
            },
            type='ai',
            id=""
        )
    ])

    tool_output = [
        {
            "content": "Protein A chromatography is ubiquitous to antibody purification. The high specificity of Protein A for binding the Fc-region of antibodies and related products enables unmatched clearance of process impurities like host cell proteins, DNA, and virus particles. A recent development is the commercialization of research-scale Protein A membrane chromatography products that can perform capture step purification with short residence times (RT) on the order of seconds. This study investigates [...] On the other hand, far fewer studies have evaluated Protein A membrane chromatography, mainly because the technology is less commercially mature. However, within the last five years, research-scale Protein A membrane chromatography products have emerged from a few companies. These include Purexa™ PrA from Purilogics, Fibro™ PrismA from Cytiva, Protein Capture Device from Gore®, and Sartobind® Protein A from Sartorius. The objective of this study was to evaluate the performance of these [...] Font Size:\nAa Aa Aa\nLine Spacing:\n  \nColumn Width:\n  \nBackground:\nOpen Access Article\nComparative Evaluation of Commercial Protein A Membranes for the Rapid Purification of Antibodies\nby \nJoshua Osuofa\nJoshua Osuofa\nSciProfilesScilitPreprints.orgGoogle Scholar\n and \nScott M. Husson\nScott M. Husson\nSciProfilesScilitPreprints.orgGoogle Scholar\n*\nDepartment of Chemical and Biomolecular Engineering, Clemson University, Clemson, SC 29634, USA\n*",
            "raw_content": "Comparative Evaluation of Commercial Protein A Membranes for the Rapid ... (truncated)",
            "score": 0.8124067,
            "title": "Comparative Evaluation of Commercial Protein A Membranes for the Rapid ...",
            "type": "page",
            "url": "https://www.mdpi.com/2077-0375/13/5/511"
        }, {
            "content": "Choose the right Protein A product for antibody purification\nProduct links in the last row of each column\n**Pierce \nProtein A Agarose****Pierce \nProtein A Plus Agarose****Pierce \nRecombinant Protein A Agarose*MabCaptureC™ High Capacity Protein A, Alkaline-Stable*\nBead or resin size45–165 μm 45–165 μm 45–165 μm 75 μm\nBinding capacity12–19 mg human IgG/mL resin 34 mg human IgG/mL resin 15–17 mg human IgG/mL resin 58 mg/ml at 5 min residence (80 mg/ml at 10 min residence) – 10% breakthrough [...] We offer a wide selection of base supports and formats to purify antibodies using the Protein A ligand. Our portfolio is designed to meet small-scale (screening) up to large-scale (bioprocess) needs. [...] Antibody purification involves isolation of antibody from serum (polyclonal antibody), ascites fluid, or from the culture supernatant of a hybridoma cell line (monoclonal antibody). Protein A ligand is recommended specifically for polyclonal IgG from rabbit, pig, dog, or cat serum. It binds the heavy chain constant region (Fc) of IgG (CH2-CH3 region). Native Protein A is purified from Staphylococcus aureus(46.7 kDa; 4 IgG-binding sites). The POROS MabCapture A resins feature a recombinant",
            "raw_content": "Antibody Purification Using Protein A and Alkaline Stable Protein A | Thermo Fisher Scientific - US (truncated)",
            "score": 0.70263255,
            "title": "Antibody Purification Using Protein A and Alkaline Stable Protein A",
            "type": "page",
            "url": "https://www.thermofisher.com/us/en/home/life-science/antibodies/antibody-purification-kits-reagents/antibody-purification-using-protein-a.html"
        }, {
            "content": "and the purity remained over 93% (Menegatti et al., 2012). Others have confirmed that \nHWRGWV can provide performance greater than that of Protein A in similar experiments \n(Najafian et al., 2017). It has also been marketed commercially as Kaptive -GY for antibody \npurification. Looking for even simpler peptide ligan ds, Wei et al. (2015 ), developed small \npeptide ligands with fewer than five residues resulting in high selectivity, simple elution and no 42 [...] chromatography can be successfully used to recover eight different HER2 -binding variants \nproduced in E. coli CCF with both high recovery and specificity (Wallberg et al., 2010). The use \nof affibodies has been successfully applie d commercially in engineered Protein A resins. In fact, \nseveral commercially available engineered Protein A resins from GE Healthcare are listed in \nTable 5-4 (MabSelect SuRe, MabSelect SuRe LX, and MabSelect SuRe pcc) , which are all Z - [...] This process was able to achieve yields of nearly 90% and purit ies greater than 95%, while \nmaintaining a productivity 3x greater than that of the comparable Protein A resin column. While \nthe researchers proposed this as a single step separator, the reduction for HCP was less than that 33 \nof a typical Protein A column, w hich would require additional polishing steps to prove \ncommercially viable. Future studies on the cost of ownership for this newly applied technology",
            "raw_content": "Protein A Chromatography in Monoclonal Antibody Purification (truncated)",
            "score": 0.68064564,
            "title": "Protein A Chromatography in Monoclonal Antibody Purification",
            "type": "page",
            "url": "https://krex.k-state.edu/server/api/core/bitstreams/bc6cb6ed-53b4-4ef2-9a4e-b67373f14d7d/content"
        }, {
            "content": "Choose the right Protein A/G product for antibody purification\nProduct links in the last row of each column\n**Pierce Protein A/G \nMagnetic Agarose Beads****Pierce Protein A/G \nAgarose*Pierce Protein A/G Plus AgarosePOROS MabCapture A/G Select*\nBead or resin size 10–40 μm 45–165 μm 45–165 μm 50 μm\nBinding capacity≥40 mg rabbit IgG/mL beads≥7 mg human IgG/mL resin≥50 mg human IgG/mL resin≥22 mg/mL human IgG/mL resin\nMaximum linear flow rate N/A 700 cm/hr 700 cm/hr 3000 cm/hr",
            "raw_content": "Antibody Purification Using Protein A/G | Thermo Fisher Scientific - ES (truncated)",
            "score": 0.6122407,
            "title": "Antibody Purification Using Protein A/G | Thermo Fisher Scientific - ES",
            "type": "page",
            "url": "https://www.thermofisher.com/us/en/home/life-science/antibodies/antibody-purification-kits-reagents/antibody-purification-using-protein-a-g.html"
        }, {
            "content": "GE Healthcare, MabSelect SuRe™. Data file 11-0011-65 AC.\nGhose, S., et al., Antibody variable region interactions with Protein A: Implications for the development of generic purification processes. Biotechnology and Bioengineering, 2005. 92(6): p. 665-673.\nGE Healthcare, MabSelect SuRe. Data file 11-0011-65 AC.\nGE Healthcare, MabSelect SuRe™ LX. Data file 28-9870-62 AA.\nGE Healthcare, MabSelect SuRe™ PCC. Data file 29177558 AA.",
            "raw_content": "Comparing Performance of New Protein A Resins for Monoclonal Antibody ... (truncated)",
            "score": 0.55478466,
            "title": "Comparing Performance of New Protein A Resins for Monoclonal Antibody ...",
            "type": "page",
            "url": "https://www.americanpharmaceuticalreview.com/Featured-Articles/347357-Comparing-Performance-of-New-Protein-A-Resins-for-Monoclonal-Antibody-Purification/"
        }
    ]

    tool_message = ToolMessage(content=json.dumps(tool_output), tool_call_id='')
    response = llm.invoke([system_prompt, human_prompt, ai_message, tool_message])
    print(response)
    print("\n\n\n")
    print(response.content)
