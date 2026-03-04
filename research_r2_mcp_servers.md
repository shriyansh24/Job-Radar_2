# Research Report: MCP Server Landscape for JobRadar

**DATE:** 2026-03-02
**TO:** Senior Developers, JobRadar Agent Infrastructure Team
**FROM:** Research & Analysis Division
**SUBJECT:** Comprehensive Analysis of Model Context Protocol (MCP) Servers for a Multi-Agent Software Development System

## 1. Executive Summary

This report provides a comprehensive analysis of the Model Context Protocol (MCP) server landscape, tailored to the specific needs of the JobRadar multi-agent software development system. The objective is to guide the selection and implementation of a robust agent infrastructure that empowers a team of specialized software agents to build, test, and maintain the JobRadar application.

The analysis is structured into seven key categories reflecting the agent workflow: Filesystem & Code, Terminal & Process, Database, Web & APIs, Testing & Validation, Documentation & Context, and Communication & Coordination. For each identified MCP server, this report details its exact name, installation command, core capabilities, authentication model, execution environment, and maintenance status. Crucially, it also identifies which specialized agents within the JobRadar ecosystem—such as the `DeveloperAgent`, `BuildAgent`, `DataAgent`, and `TestingAgent`—would benefit most from each tool.

The report concludes with a strategic recommendation table, categorizing each server as either "Must-Have" for foundational functionality or "Optional" for enhanced capabilities. This framework is designed to enable a phased and strategic build-out of the agent toolchain, ensuring the JobRadar system is equipped with the necessary capabilities for autonomous software development.

## 2. Filesystem & Code Servers

This category covers servers that provide agents with the ability to read, write, analyze, and manage the source code and file structure of the JobRadar project. These are foundational for any agent tasked with development.

### 2.1. Filesystem Server: `@modelcontextprotocol/server-filesystem`

*   **Server Name:** `@modelcontextprotocol/server-filesystem`
*   **Install Command:** `npx -y @modelcontextprotocol/server-filesystem <allowed_dir_1> <allowed_dir_2>`
*   **Exposed Tools/Capabilities:** Provides a comprehensive suite of file operations, including `read_text_file`, `write_file`, `edit_file`, `move_file`, `list_directory`, `directory_tree`, and `search_files`. It also supports reading media files (`read_media_file`). All write/modify operations require explicit user approval.
*   **Auth Requirements:** None specified. Security is managed by restricting access to command-line specified directories.
*   **Local vs. Remote Execution:** Primarily local execution via `stdio`. Can be run within a Docker container for sandboxing.
*   **Stability/Maintenance Status:** A core reference implementation from the `modelcontextprotocol` group, indicating it is well-maintained and stable.
*   **Benefitting Agents (JobRadar):**
    *   **`DeveloperAgent`:** Essential for reading existing code, writing new files (e.g., components, API endpoints), and modifying code based on new requirements.
    *   **`BuildAgent`:** Required for managing build artifacts and project structure.
    *   **`DocumentationAgent`:** Needed to create or update `README.md` files and other documentation.

### 2.2. Git Version Control Server: `@modelcontextprotocol/server-git`

*   **Server Name:** `@modelcontextprotocol/server-git`
*   **Install Command:** `uvx mcp-server-git <repo_path>` or `pip install mcp-server-git` followed by `python -m mcp_server_git <repo_path>`
*   **Exposed Tools/Capabilities:** Exposes a wide range of Git commands as tools. Key capabilities include `git_status`, `git_add`, `git_commit`, `git_diff_staged`, `git_log`, `git_branch`, `git_checkout`, `git_push`, and `git_pull`.
*   **Auth Requirements:** None specified at the server level. Authentication for remote operations (e.g., `git_push`) relies on the underlying Git configuration of the host system (e.g., SSH keys, credential manager).
*   **Local vs. Remote Execution:** Local execution, operating on specified repository paths on the local filesystem.
*   **Stability/Maintenance Status:** Described as being in "early development," but it is a reference implementation from the official `modelcontextprotocol` repository, suggesting active development.
*   **Benefitting Agents (JobRadar):**
    *   **`DeveloperAgent`:** Critical for the entire development lifecycle: checking out branches, staging changes, committing code with descriptive messages, and pushing features for review.
    *   **`OrchestratorAgent`:** Can use this to tag releases or manage versioning across the project.

### 2.3. Code Intelligence Server: Code Index MCP

*   **Server Name:** Code Index MCP
*   **Install Command:** Configuration typically involves pointing the MCP client to a running instance.
*   **Exposed Tools/Capabilities:** Provides intelligent code indexing and analysis using Tree-sitter for AST parsing. Tools include `set_project_path`, `refresh_index`, `build_deep_index` (full symbol index), `search_code_advanced`, and `get_file_summary` (analyzes file structure, functions, imports, and complexity).
*   **Auth Requirements:** None specified.
*   **Local vs. Remote Execution:** Runs locally, indexing the specified project path.
*   **Stability/Maintenance Status:** Appears to be a stable, community-provided server focused on a specific, powerful capability.
*   **Benefitting Agents (JobRadar):**
    *   **`DeveloperAgent`:** Can use `get_file_summary` and `search_code_advanced` to understand existing code before making changes, reducing errors and improving integration quality.
    *   **`CodeReviewAgent`:** Can analyze code complexity and structure to provide automated feedback.
    *   **`RefactorAgent`:** Essential for finding all references to a function or symbol before performing a refactor.

### 2.4. Code Validation Server: ESLint MCP Server

*   **Server Name:** ESLint MCP Server (`@eslint/mcp@latest`)
*   **Install Command:** `npx @eslint/mcp@latest`
*   **Exposed Tools/Capabilities:** Allows an LLM to directly use the ESLint CLI. Capabilities include checking for linting errors, automatically fixing issues, and displaying rule violations for specific files.
*   **Auth Requirements:** None.
*   **Local vs. Remote Execution:** Local execution within the project directory where `.eslintrc` is configured.
*   **Stability/Maintenance Status:** Maintained by the official ESLint team, indicating high stability and reliability.
*   **Benefitting Agents (JobRadar):**
    *   **`DeveloperAgent`:** Can use this tool to ensure any generated code adheres to the project's linting rules before committing, maintaining code quality automatically.
    *   **`TestingAgent` / `QAAgent`:** Can run this as part of a pre-commit or pre-push validation step.

## 3. Terminal & Process Servers

These servers grant agents controlled access to the system's shell, enabling them to run build scripts, execute tests, and manage system processes—a crucial capability for automating the development workflow.

### 3.1. Secure Shell Server: `mcp-server-shell` (by tumf)

*   **Server Name:** `mcp-server-shell`
*   **Install Command:** `pip install mcp-shell-server`
*   **Exposed Tools/Capabilities:** Provides a single `execute` tool to run whitelisted shell commands. It supports passing `stdin`, returns `stdout`, `stderr`, and `status`, and includes timeout controls.
*   **Auth Requirements:** None. Security is enforced via a mandatory `ALLOW_COMMANDS` environment variable, which acts as a strict whitelist (e.g., "pnpm,uv,npm,node").
*   **Local vs. Remote Execution:** Local execution only.
*   **Stability/Maintenance Status:** A focused, community-built server. Its security model (explicit whitelist) makes it a stable and predictable choice.
*   **Benefitting Agents (JobRadar):**
    *   **`BuildAgent`:** Essential for running commands like `pnpm install`, `pnpm build`, `uv install`, and `uv run` to manage dependencies and build the frontend and backend.
    *   **`TestingAgent`:** Required to execute the test suite via commands like `pytest` or `pnpm test`.
    *   **`DeveloperAgent`:** Can use this to run code formatters (e.g., `pnpm format`) or other project-specific scripts defined in `package.json` or `Makefile`.

### 3.2. Agent Delegation Server: Claude Code (as an MCP Server)

*   **Server Name:** Claude Code
*   **Install Command:** `claude mcp serve` (requires `@anthropic-ai/claude-code` to be globally installed).
*   **Exposed Tools/Capabilities:** Exposes its own native tools to other MCP clients. For JobRadar, the most relevant are `Bash` (execute shell commands), `Read`/`Write` (file I/O), and `dispatch_agent` (delegate to sub-agents).
*   **Auth Requirements:** None, but requires a one-time permissions acceptance (`claude --dangerously-skip-permissions`) before running in headless mode.
*   **Local vs. Remote Execution:** Runs as a local server process that other local agents can connect to.
*   **Stability/Maintenance Status:** An official feature from Anthropic, making it a stable and powerful option for agent orchestration.
*   **Benefitting Agents (JobRadar):**
    *   **`OrchestratorAgent`:** This is the primary beneficiary. It can connect to a `DeveloperAgent` running as a Claude Code server and use the `dispatch_agent` tool to delegate complex coding tasks, effectively creating a hierarchy of agents.
    *   All other agents can potentially be wrapped this way to expose their core functions to an orchestrator.

## 4. Database Servers

For JobRadar, direct interaction with its central `jobradar.db` SQLite database is critical for agents managing data, running analytics, or retrieving information to inform their tasks.

### 4.1. SQLite Interaction Server: `mcp-server-sqlite`

*   **Server Name:** `mcp-server-sqlite`
*   **Install Command:** `uvx mcp-server-sqlite --db-path ./data/jobradar.db` or `pip install mcp-server-sqlite`
*   **Exposed Tools/Capabilities:** Provides a rich set of tools for database interaction. Key tools include `list_tables`, `get_table_schema`, and `query` (for executing arbitrary SQL). Some implementations also offer higher-level CRUD tools (`create_record`, `read_records`).
*   **Auth Requirements:** None. Access is controlled by the file path to the SQLite database provided on startup.
*   **Local vs. Remote Execution:** Local execution, directly accessing the specified `.db` file.
*   **Stability/Maintenance Status:** The PyPI package is marked as "archived," but several active forks and alternative implementations exist (e.g., `jparkerweb/mcp-sqlite`, `sqlite-explorer-fastmcp-mcp-server`). The `sqlite-explorer` variant is notable for its focus on safe, read-only access.
*   **Benefitting Agents (JobRadar):**
    *   **`DataAgent`:** This is the primary tool for the `DataAgent` to perform its duties, such as cleaning data, running deduplication queries, and managing the job listings.
    *   **`AnalyticsAgent`:** Can execute complex SQL queries to generate the data needed for the frontend dashboard and analytics pages.
    *   **`DeveloperAgent`:** Can use `get_table_schema` to understand the database model when building new API endpoints.

## 5. Web & APIs Servers

These servers give agents the ability to interact with the web, whether for scraping, testing, or research. While JobRadar has a dedicated scraper architecture, these tools are invaluable for ad-hoc tasks and E2E validation.

### 5.1. Web Content Fetcher: `@modelcontextprotocol/server-fetch`

*   **Server Name:** `@modelcontextprotocol/server-fetch`
*   **Install Command:** `uvx mcp-server-fetch` or `pip install mcp-server-fetch`
*   **Exposed Tools/Capabilities:** Provides a core `fetch` tool that retrieves content from a URL and converts the HTML to clean Markdown, which is ideal for LLM consumption. It supports chunking (`max_length`, `start_index`) for large pages.
*   **Auth Requirements:** None.
*   **Local vs. Remote Execution:** Local execution.
*   **Stability/Maintenance Status:** A stable reference implementation from the official `modelcontextprotocol` repository.
*   **Benefitting Agents (JobRadar):**
    *   **`ResearchAgent`:** Can use this to fetch documentation, blog posts, or articles to inform development strategies or troubleshoot issues.
    *   **`ScraperAgent`:** While primary scraping uses dedicated libraries, this tool is useful for a quick check of a single URL or for fetching content from a newly discovered job board to analyze its structure.

### 5.2. Browser Automation Server: Playwright MCP Server

*   **Server Name:** Playwright MCP Server (`@playwright/mcp@latest`)
*   **Install Command:** `npx @playwright/mcp@latest` (requires `npx playwright install` to be run once).
*   **Exposed Tools/Capabilities:** Enables full browser automation via the Playwright framework. Instead of visual input, it provides the page's accessibility tree to the LLM, allowing it to navigate, click, type, and take snapshots in a structured way.
*   **Auth Requirements:** None.
*   **Local vs. Remote Execution:** Can run in local `stdio` mode or as a standalone remote HTTP server.
*   **Stability/Maintenance Status:** Officially maintained by Microsoft's Playwright team, ensuring high quality, stability, and integration with tools like GitHub Copilot.
*   **Benefitting Agents (JobRadar):**
    *   **`TestingAgent` / `QAAgent`:** A powerful tool for writing and executing end-to-end tests on the JobRadar frontend. The agent can be tasked to "verify the login flow" or "test the job filter functionality."
    *   **`ScraperAgent`:** Essential for scraping jobs from highly dynamic, JavaScript-heavy websites that are difficult to handle with simple HTTP requests.

## 6. Testing & Validation Servers

This category focuses on servers that provide specialized tools for quality assurance, from unit testing to static analysis, enabling agents to validate their own work.

### 6.1. Pytest Integration Server: `pytest-mcp-server`

*   **Server Name:** `pytest-mcp-server`
*   **Install Command:** Not directly installed as a running server; it's a Pytest plugin. The `TestingAgent` would use a shell server to run `pytest`. However, frameworks like `pytest-mcp` are used to test the agents themselves.
*   **Exposed Tools/Capabilities:** The `pytest-mcp` framework provides tools for evaluating agents and MCP servers. It offers assertions like `tool_was_called()` and `objective_succeeded()`, and reports on tool coverage, latency, and token usage.
*   **Auth Requirements:** N/A.
*   **Local vs. Remote Execution:** Local test execution.
*   **Stability/Maintenance Status:** Community-driven projects. `FastMCP` provides a robust pattern for in-memory testing of MCP servers, which is considered a best practice.
*   **Benefitting Agents (JobRadar):**
    *   **`OrchestratorAgent`:** Can use these frameworks to run meta-tests on the other agents, ensuring the tools are functioning correctly and the agents are meeting their objectives. This is crucial for maintaining a healthy multi-agent system.
    *   **`TestingAgent`:** While it uses the Terminal server to run application tests, its own logic and effectiveness can be validated using these specialized frameworks.

*(Note: ESLint MCP Server and Playwright MCP Server, detailed in other sections, are also critical components of the testing and validation toolchain.)*

## 7. Documentation & Context Servers

These servers provide agents with memory and external knowledge, allowing them to learn from past interactions and access up-to-date information beyond their training data.

### 7.1. Persistent Memory Server: `@modelcontextprotocol/server-memory`

*   **Server Name:** `@modelcontextprotocol/server-memory`
*   **Install Command:** `npx -y @modelcontextprotocol/server-memory`
*   **Exposed Tools/Capabilities:** Provides tools to manage a local knowledge graph. Agents can `create_entities`, `create_relations`, and `add_observations` to build a persistent memory. Tools like `read_graph` and `search_nodes` allow for retrieval of this stored context.
*   **Auth Requirements:** None. Data is stored in a local JSONL file.
*   **Local vs. Remote Execution:** Local execution.
*   **Stability/Maintenance Status:** A stable reference implementation from the official `modelcontextprotocol` repository.
*   **Benefitting Agents (JobRadar):**
    *   **`OrchestratorAgent`:** Can use this to store high-level project goals, architectural decisions, and user feedback across sessions.
    *   **`DeveloperAgent`:** Can be prompted to remember user preferences for coding style (e.g., "The user prefers functional components over class components in React") or specific implementation details.

### 7.2. Library Documentation Server: Context7 MCP

*   **Server Name:** Context7 MCP (`@upstash/context7-mcp`)
*   **Install Command:** `npx @upstash/context7-mcp`
*   **Exposed Tools/Capabilities:** Provides tools to fetch up-to-date, version-specific documentation for programming libraries and frameworks. The `query-docs` tool can retrieve relevant documentation snippets based on a natural language query.
*   **Auth Requirements:** An optional API key can be provided for higher rate limits.
*   **Local vs. Remote Execution:** The `npx` command runs a local client that communicates with the remote Context7 API backend.
*   **Stability/Maintenance Status:** Maintained by Upstash, a reputable developer tools company. The service is stable and actively maintained.
*   **Benefitting Agents (JobRadar):**
    *   **`DeveloperAgent`:** Extremely valuable for resolving issues related to library usage. When encountering an error with FastAPI or Recharts, the agent can use Context7 to look up the correct API usage for the specific version used in JobRadar, preventing hallucinations and reducing debugging time.

## 8. Communication & Coordination

Effective multi-agent systems require a mechanism for agents to delegate tasks and share information. While dedicated message queue servers can be built, the MCP standard itself provides a powerful pattern for coordination.

### 8.1. Inter-Agent Delegation

*   **Server Name:** N/A (Protocol Pattern)
*   **Install Command:** N/A
*   **Exposed Tools/Capabilities:** The core principle of MCP is that any agent can be exposed as an MCP server. This allows a primary agent (e.g., an `OrchestratorAgent`) to connect to specialized agents (`DeveloperAgent`, `TestingAgent`) and invoke their capabilities as "tools." For example, the `DeveloperAgent` could expose a high-level tool called `implement_feature(issue_description)`, which internally uses its own set of tools (filesystem, git, etc.).
*   **Auth Requirements:** Depends on the transport. Local `stdio` connections have no auth, while remote HTTP servers can implement bearer token or other schemes.
*   **Local vs. Remote Execution:** Supports both. For JobRadar's localhost-only architecture, local `stdio` connections are sufficient and secure.
*   **Stability/Maintenance Status:** This is the fundamental design pattern of MCP and is inherently stable.
*   **Benefitting Agents (JobRadar):**
    *   **`OrchestratorAgent`:** This pattern is the foundation of its existence. It allows the orchestrator to break down a high-level task like "Add a new 'Notes' field to jobs" and delegate parts of it to the appropriate agents: `DeveloperAgent` to modify the code, `DataAgent` to alter the database schema, and `TestingAgent` to validate the changes.

## 9. Conclusion and Recommendations

To successfully build the JobRadar application using a multi-agent system, a well-curated set of tools is paramount. The following table provides a strategic recommendation for which MCP servers to prioritize, distinguishing between foundational "Must-Have" components and value-adding "Optional" enhancements.

| Category | Server Name | Recommendation | Justification for JobRadar |
| :--- | :--- | :--- | :--- |
| **Filesystem & Code** | `@modelcontextprotocol/server-filesystem` | **Must-Have** | Foundational for any agent that needs to read or write code and project files. |
| | `@modelcontextprotocol/server-git` | **Must-Have** | Essential for integrating the agents' work into a version-controlled workflow. |
| | Code Index MCP | **Optional** | Highly recommended. Enables agents to understand existing code, reducing bugs and rework. |
| | ESLint MCP Server | **Optional** | Highly recommended for maintaining code quality automatically as agents generate code. |
| **Terminal & Process** | `mcp-server-shell` (or similar) | **Must-Have** | Non-negotiable for running build scripts (`pnpm build`), tests (`pytest`), and managing dependencies (`uv install`). |
| **Database** | `mcp-server-sqlite` | **Must-Have** | Provides the necessary interface for the `DataAgent` and `AnalyticsAgent` to interact with the core `jobradar.db`. |
| **Web & APIs** | Playwright MCP Server | **Optional** | Crucial for enabling a `TestingAgent` to perform E2E tests and for a `ScraperAgent` to handle complex, dynamic websites. |
| | `@modelcontextprotocol/server-fetch` | **Optional** | A useful utility for ad-hoc research and simple page fetching, but not core to the primary scraping or development loop. |
| **Testing & Validation** | (See Playwright, ESLint, Terminal) | **Must-Have** | A combination of servers is required. The Terminal server is the must-have component to run test commands. |
| **Documentation & Context** | Context7 MCP | **Optional** | A significant productivity booster for the `DeveloperAgent`, reducing errors from outdated library knowledge. |
| | `@modelcontextprotocol/server-memory` | **Optional** | An advanced feature for creating a more intelligent and personalized system over time. Can be added in a later phase. |
| **Communication** | Inter-Agent Delegation (MCP Pattern) | **Must-Have** | This architectural pattern is the core of the multi-agent system, enabling task delegation and coordination. |

This tiered approach allows the infrastructure team to focus first on the essential servers required for basic agent operation, while providing a clear roadmap for incorporating more advanced capabilities to enhance agent intelligence, autonomy, and efficiency.

# References
1. [https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem)
2. [https://modelcontextprotocol.io/docs/develop/connect-local-servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)
3. [https://www.npmjs.com/package/@modelcontextprotocol/sdk](https://www.npmjs.com/package/@modelcontextprotocol/sdk)
4. [https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
5. [https://www.npmjs.com/package/@agent-infra/mcp-server-filesystem](https://www.npmjs.com/package/@agent-infra/mcp-server-filesystem)
6. [https://www.npmjs.com/package/@modelcontextprotocol/server-everything](https://www.npmjs.com/package/@modelcontextprotocol/server-everything)
7. [https://skywork.ai/skypage/en/Model-Context-Protocol-(MCP)-Server-Filesystem-A-Comprehensive-Guide-for-AI-Engineers/1971094888359784448](https://skywork.ai/skypage/en/Model-Context-Protocol-(MCP)-Server-Filesystem-A-Comprehensive-Guide-for-AI-Engineers/1971094888359784448)
8. [https://github.com/cyanheads/filesystem-mcp-server](https://github.com/cyanheads/filesystem-mcp-server)
9. [https://glama.ai/mcp/servers/@modelcontextprotocol/git](https://glama.ai/mcp/servers/@modelcontextprotocol/git)
10. [https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
11. [https://modelcontextprotocol.io/examples](https://modelcontextprotocol.io/examples)
12. [https://github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)
13. [https://mcpservers.org/servers/modelcontextprotocol/git](https://mcpservers.org/servers/modelcontextprotocol/git)
14. [https://www.npmjs.com/package/@mseep/git-mcp-server](https://www.npmjs.com/package/@mseep/git-mcp-server)
15. [https://mcp.so/server/git/modelcontextprotocol](https://mcp.so/server/git/modelcontextprotocol)
16. [https://github.com/modelcontextprotocol/servers/tree/main/src/git](https://github.com/modelcontextprotocol/servers/tree/main/src/git)
17. [MCP Server for AI Code Intelligence 2026 | Semantic Code Analysis for Claude Code, Codex & OpenCode | Code Pathfinder - Code Pathfinder](https://codepathfinder.dev/mcp)
18. [GitHub - angrysky56/ast-mcp-server: By transforming source code into a queryable Semantic Graph and a structured AST, this tool bridges the gap between 'reading text' and 'understanding structure.' For an AI assistant, it provides the 'spatial' awareness needed to navigate deep dependencies without getting lost in large files. - GitHub](https://github.com/angrysky56/ast-mcp-server)
19. [ast-grep MCP Server by ast-grep | PulseMCP - PulseMCP](https://www.pulsemcp.com/servers/ast-grep)
20. [GitHub - anortham/coa-codesearch-mcp: AI-powered code search and analysis for Claude Code with advanced type extraction across 25+ languages. Lightning-fast Lucene indexing, intelligent type parsing (Vue, Razor, C#, Python, Rust, Go, TypeScript+), and token-optimized responses. Built with .NET 9 + Tree-sitter. - GitHub](https://github.com/anortham/coa-codesearch-mcp)
21. [ast-grep MCP Server - GitHub](https://github.com/ast-grep/ast-grep-mcp)
22. [Code Index MCP | Awesome MCP Servers - MCP Servers](https://mcpservers.org/servers/johnhuang316/code-index-mcp)
23. [Code Analysis MCP Server by Johann-Peter Hartmann | PulseMCP - PulseMCP](https://www.pulsemcp.com/servers/johannhartmann-code-analysis)
24. [AST MCP Server - ast-grep/ast-grep-mcp - Playbooks](https://playbooks.com/mcp/ast-grep/ast-grep-mcp)
25. [https://cursor.directory/mcp/shell-command](https://cursor.directory/mcp/shell-command)
26. [https://www.pulsemcp.com/servers/rinardnick-terminal](https://www.pulsemcp.com/servers/rinardnick-terminal)
27. [https://github.com/tumf/mcp-shell-server](https://github.com/tumf/mcp-shell-server)
28. [https://playbooks.com/mcp/benyue1978-run-command](https://playbooks.com/mcp/benyue1978-run-command)
29. [https://github.com/MladenSU/cli-mcp-server](https://github.com/MladenSU/cli-mcp-server)
30. [https://www.pulsemcp.com/servers/kevinwatt-shell](https://www.pulsemcp.com/servers/kevinwatt-shell)
31. [https://www.pulsemcp.com/servers/ryaneggz-terminal-shell](https://www.pulsemcp.com/servers/ryaneggz-terminal-shell)
32. [https://playbooks.com/mcp/egoist-shell-command](https://playbooks.com/mcp/egoist-shell-command)
33. [https://github.com/modelcontextprotocol/servers/tree/main/src/fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
34. [https://pypi.org/project/mcp-server-fetch/](https://pypi.org/project/mcp-server-fetch/)
35. [https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/README.md](https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/README.md)
36. [https://playbooks.com/mcp/modelcontextprotocol-fetch](https://playbooks.com/mcp/modelcontextprotocol-fetch)
37. [https://www.pulsemcp.com/servers/modelcontextprotocol-fetch](https://www.pulsemcp.com/servers/modelcontextprotocol-fetch)
38. [https://mcpservers.org/servers/modelcontextprotocol/fetch](https://mcpservers.org/servers/modelcontextprotocol/fetch)
39. [https://github.com/jparkerweb/mcp-sqlite](https://github.com/jparkerweb/mcp-sqlite)
40. [https://mcpservers.org/servers/panasenco/mcp-sqlite](https://mcpservers.org/servers/panasenco/mcp-sqlite)
41. [https://www.pulsemcp.com/servers/modelcontextprotocol-sqlite](https://www.pulsemcp.com/servers/modelcontextprotocol-sqlite)
42. [https://pypi.org/project/mcp-server-sqlite/](https://pypi.org/project/mcp-server-sqlite/)
43. [https://n8n.io/workflows/3632-build-your-own-sqlite-mcp-server/](https://n8n.io/workflows/3632-build-your-own-sqlite-mcp-server/)
44. [https://github.com/hannesrudolph/sqlite-explorer-fastmcp-mcp-server](https://github.com/hannesrudolph/sqlite-explorer-fastmcp-mcp-server)
45. [Breaking Isolation: A Practical Guide to Building an MCP Server with SQLite - Medium](https://felix-pappe.medium.com/breaking-isolation-a-practical-guide-to-building-an-mcp-server-with-sqlite-68c800a25d42)
46. [https://googleapis.github.io/genai-toolbox/resources/sources/sqlite/](https://googleapis.github.io/genai-toolbox/resources/sources/sqlite/)
47. [https://github.com/microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)
48. [https://executeautomation.github.io/mcp-playwright/docs/intro](https://executeautomation.github.io/mcp-playwright/docs/intro)
49. [https://testomat.io/blog/playwright-mcp-modern-test-automation-from-zero-to-hero/](https://testomat.io/blog/playwright-mcp-modern-test-automation-from-zero-to-hero/)
50. [https://github.com/executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright)
51. [The complete Playwright end-to-end story: tools, AI, and real-world workflows - Microsoft 365 Developer Blog](https://developer.microsoft.com/blog/the-complete-playwright-end-to-end-story-tools-ai-and-real-world-workflows)
52. [https://executeautomation.github.io/mcp-playwright/docs/playwright-web/Examples](https://executeautomation.github.io/mcp-playwright/docs/playwright-web/Examples)
53. [https://developers.cloudflare.com/browser-rendering/playwright/playwright-mcp/](https://developers.cloudflare.com/browser-rendering/playwright/playwright-mcp/)
54. [Generative Automation Testing with Playwright MCP Server - Medium](https://adequatica.medium.com/generative-automation-testing-with-playwright-mcp-server-45e9b8f6f92a)
55. [https://mcp.so/server/pytest-mcp-server/tosin2013](https://mcp.so/server/pytest-mcp-server/tosin2013)
56. [https://mcpcat.io/guides/writing-unit-tests-mcp-servers/](https://mcpcat.io/guides/writing-unit-tests-mcp-servers/)
57. [https://github.com/tosin2013/pytest-mcp-server](https://github.com/tosin2013/pytest-mcp-server)
58. [https://github.com/IBM/mcp-context-forge/issues/261](https://github.com/IBM/mcp-context-forge/issues/261)
59. [https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers](https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers)
60. [https://gofastmcp.com/patterns/testing](https://gofastmcp.com/patterns/testing)
61. [https://pypi.org/project/pytest-mcp/](https://pypi.org/project/pytest-mcp/)
62. [https://pypi.org/project/mcp-testing-framework/](https://pypi.org/project/mcp-testing-framework/)
63. [https://www.npmjs.com/package/@modelcontextprotocol/server-memory](https://www.npmjs.com/package/@modelcontextprotocol/server-memory)
64. [https://github.com/modelcontextprotocol/servers/tree/main/src/memory](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
65. [https://playbooks.com/mcp/modelcontextprotocol/servers/memory](https://playbooks.com/mcp/modelcontextprotocol/servers/memory)
66. [https://mcp.so/server/memory/modelcontextprotocol](https://mcp.so/server/memory/modelcontextprotocol)
67. [https://www.promptfoo.dev/docs/integrations/mcp/](https://www.promptfoo.dev/docs/integrations/mcp/)
68. [https://www.grizzlypeaksoftware.com/articles?id=4Tyr7iByM6tvJI1WzshwsC](https://www.grizzlypeaksoftware.com/articles?id=4Tyr7iByM6tvJI1WzshwsC)
69. [https://github.com/upstash/context7](https://github.com/upstash/context7)
70. [https://smithery.ai/server/@upstash/context7-mcp](https://smithery.ai/server/@upstash/context7-mcp)
71. [https://playbooks.com/mcp/upstash/context7](https://playbooks.com/mcp/upstash/context7)
72. [https://hub.docker.com/r/mcp/context7](https://hub.docker.com/r/mcp/context7)
73. [https://www.npmjs.com/package/@upstash/context7-mcp](https://www.npmjs.com/package/@upstash/context7-mcp)
74. [https://upstash.com/blog/context7-mcp](https://upstash.com/blog/context7-mcp)
75. [https://lobehub.com/mcp/upstash-context7](https://lobehub.com/mcp/upstash-context7)
76. [https://apidog.com/blog/context7-mcp-server/](https://apidog.com/blog/context7-mcp-server/)
77. [https://registry.modelcontextprotocol.io/](https://registry.modelcontextprotocol.io/)
78. [https://github.com/modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry)
79. [https://modelcontextprotocol.info/tools/registry/](https://modelcontextprotocol.info/tools/registry/)
80. [https://registry.modelcontextprotocol.io/docs](https://registry.modelcontextprotocol.io/docs)
81. [http://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/](http://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/)
82. [https://modelcontextprotocol.info/tools/registry/faq/](https://modelcontextprotocol.info/tools/registry/faq/)
83. [Connect Claude Code to tools via MCP - Claude Code Docs - Claude Code Docs](https://code.claude.com/docs/en/mcp)
84. [Configuring MCP Tools in Claude Code - The Better Way - Scott Spence - Scott Spence](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
85. [Claude Code 🤝 FastMCP - FastMCP - FastMCP](https://gofastmcp.com/integrations/claude-code)
86. [Best MCP Servers for Claude Code - Top Tools & Integrations | MCPcat - MCPcat](https://mcpcat.io/guides/best-mcp-servers-for-claude-code/)
87. [Add MCP Servers to Claude Code with MCP Toolkit | Docker - Docker](https://www.docker.com/blog/add-mcp-servers-to-claude-code-with-mcp-toolkit/)
88. [Add MCP Servers to Claude Code - Setup & Configuration Guide | MCPcat - MCPcat](https://mcpcat.io/guides/adding-an-mcp-server-to-claude-code/)
89. [Claude Code MCP Server: Complete Setup Guide (2026) - KSRed](https://www.ksred.com/claude-code-as-an-mcp-server-an-interesting-capability-worth-understanding/)
90. [50+ Best MCP Servers for Claude Code in 2026 - ClaudeFAST](https://claudefa.st/blog/tools/mcp-extensions/best-addons)
91. [https://github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
92. [https://github.com/wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers)
93. [Top 10 MCP Servers for 2025 (Yes, GitHub's Included) - DEV Community](https://dev.to/fallon_jimmy/top-10-mcp-servers-for-2025-yes-githubs-included-15jg)
94. [GitHub Open Source MCP Projects - NocoBase](https://www.nocobase.com/en/blog/github-open-source-mcp-projects)
95. [List of most popular MCP github repos - Reddit](https://www.reddit.com/r/MCPservers/comments/1m6l1qr/list_of_most_popular_mcp_github_repos/)
96. [https://github.com/pedrojaques99/popular-mcp-servers](https://github.com/pedrojaques99/popular-mcp-servers)
97. [Top 10 most popular MCP servers on Github - Reddit](https://www.reddit.com/r/modelcontextprotocol/comments/1h8t98a/top_10_most_popular_mcp_servers_on_github/)
98. [https://github.com/tolkonepiu/best-of-mcp-servers](https://github.com/tolkonepiu/best-of-mcp-servers)
99. [https://www.nickyt.co/blog/build-your-first-or-next-mcp-server-with-the-typescript-mcp-template-3k3f/](https://www.nickyt.co/blog/build-your-first-or-next-mcp-server-with-the-typescript-mcp-template-3k3f/)
100. [Build your first (or next) MCP server with the TypeScript MCP Template - DEV Community](https://dev.to/nickytonline/build-your-first-or-next-mcp-server-with-the-typescript-mcp-template-3k3f)
101. [https://eslint.org/docs/latest/use/mcp](https://eslint.org/docs/latest/use/mcp)
102. [https://github.com/eslint/eslint/issues/20290](https://github.com/eslint/eslint/issues/20290)
103. [https://github.com/kirbah/mcp-typescript-starter](https://github.com/kirbah/mcp-typescript-starter)
104. [https://glama.ai/mcp/servers?query=how-to-use-eslint-and-typescript-for-code-validation](https://glama.ai/mcp/servers?query=how-to-use-eslint-and-typescript-for-code-validation)
105. [Extending LLM Capabilities: Build Your Own MCP Server - Medium](https://medium.com/@sk8teurjl/extending-llm-capabilities-build-your-own-mcp-server-721680c3bac6)
106. [https://lobehub.com/mcp/catpaladin-mcp-typescript-assistant](https://lobehub.com/mcp/catpaladin-mcp-typescript-assistant)
107. [Multi-agent communication through MCP - Reddit](https://www.reddit.com/r/mcp/comments/1j2wlea/multiagent_communication_through_mcp/)
108. [Publish–subscribe pattern - Wikipedia](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern)
109. [Messaging Patterns Explained: Pub-Sub vs. Message Queue - System Design Newsletter](https://blog.bytebytego.com/p/messaging-patterns-explained-pub)
110. [https://cloud.google.com/pubsub/docs/overview](https://cloud.google.com/pubsub/docs/overview)
111. [Message Queue vs. Pub/Sub - System Design School](https://systemdesignschool.io/blog/message-queue-vs-pub-sub)
112. [Pub/Sub vs. Message Queues | Baeldung - Baeldung](https://www.baeldung.com/pub-sub-vs-message-queues)
113. [https://github.com/vitaminR/agent-switchboard](https://github.com/vitaminR/agent-switchboard)
114. [How do you make a choice between message queue and pub/sub? - Reddit](https://www.reddit.com/r/ExperiencedDevs/comments/1f4v3lj/how_do_you_make_a_choice_between_message_queue/)