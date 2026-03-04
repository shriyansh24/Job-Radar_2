# Research Report: Claude Code Skills System for JobRadar

**DATE:** 2026-03-02
**TO:** JobRadar Development Team
**FROM:** Research & Analysis Division
**SUBJECT:** Analysis and Implementation Guide for the Claude Code Skills System

## Executive Summary

This report provides a comprehensive analysis of the Claude Code skills system and its application to the development of the JobRadar project. The objective is to equip the development team with the necessary knowledge to leverage both pre-built and custom skills within a multi-agent AI build system, thereby accelerating development and ensuring adherence to the project's specific architecture and technology stack.

The report is divided into three main sections:

1.  **The Claude Code Skills Framework:** A detailed examination of how skills function, including their structure, loading mechanisms, and role within the broader Claude Code ecosystem. This section clarifies the distinctions between Skills, `CLAUDE.md`, and Model Context Protocol (MCP) servers, providing a foundational understanding for effective implementation.
2.  **Curated Pre-built Skills for JobRadar:** A catalog of relevant, publicly available skills applicable to JobRadar's backend, frontend, testing, and document generation needs. Each entry includes a description and instructions for acquisition.
3.  **Custom Skill Templates for JobRadar:** Five complete, production-ready `SKILL.md` templates designed specifically for the JobRadar technology stack (Python 3.12, FastAPI, SQLAlchemy 2.0 async, React 19, TypeScript, Vite, TailwindCSS). These custom skills are crafted to automate complex, repetitive tasks unique to the JobRadar project, from generating asynchronous data access patterns to scaffolding specific UI components.

By integrating this framework, the JobRadar team can transform its multi-agent system from a general-purpose tool into a specialized, highly efficient development engine tailored to the project's unique requirements.

---

## 1. The Claude Code Skills Framework

The Claude Code skills system is a powerful extensibility model that allows developers to augment Claude's core capabilities with specialized knowledge, repeatable workflows, and deterministic tools. Skills transform a general-purpose AI assistant into a domain-specific expert by packaging instructions and resources into modular, on-demand components.

### 1.1. How Skills Work: Anatomy and Structure

A skill is a self-contained directory that houses a `SKILL.md` file as its entry point, along with any optional supporting files like scripts, templates, or reference documents.

#### 1.1.1. The `SKILL.md` File

This core file is composed of two parts: YAML frontmatter for metadata and a Markdown body for instructions.

**YAML Frontmatter:** Enclosed by `---` markers at the top of the file, this section configures the skill's behavior.

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `string` | **(Required)** A unique, human-readable identifier. It becomes the `/slash-command` for manual invocation. Must be lowercase, max 64 chars, and use only letters, numbers, and hyphens. |
| `description` | `string` | **(Recommended)** A concise explanation of the skill's purpose and activation triggers. This is critical for Claude's automatic skill discovery. Max 1024 chars. |
| `disable-model-invocation` | `boolean` | If `true`, prevents Claude from invoking the skill automatically. The skill can only be triggered manually by a user (e.g., `/deploy`). Defaults to `false`. |
| `user-invocable` | `boolean` | If `false`, hides the skill from the `/` command menu. The skill can only be invoked by Claude. Useful for providing background knowledge. Defaults to `true`. |
| `argument-hint` | `string` | A placeholder string (e.g., `[filename]`) displayed during autocomplete to guide users on expected arguments. |
| `allowed-tools` | `array` | A list of tools (e.g., `Read`, `Grep`) that Claude can use without explicit permission while the skill is active. |
| `context` | `string` | If set to `fork`, the skill executes in an isolated sub-agent context, preserving the main conversation's clarity. |
| `dependencies` | `array` | A list of software packages required by the skill's scripts (e.g., `python>=3.8`). |

**Markdown Body:** Following the frontmatter, this section contains the detailed, step-by-step instructions for Claude. It can include procedural guides, best practices, and references to other files within the skill's directory. The body supports string substitutions for dynamic content:

*   `$ARGUMENTS`: Injects all arguments passed to the skill.
*   `$N` or `$ARGUMENTS[N]`: Injects the argument at a specific 0-based index.
*   `${CLAUDE_SESSION_ID}`: Injects the unique ID for the current session.

#### 1.1.2. Skill Directory Structure

A well-structured skill directory isolates resources, promoting clarity and maintainability.

```
my-fastapi-skill/
├── SKILL.md           # Main instructions and entry point (required)
├── examples/
│   └── user_router.py # Example output showing expected code format
├── scripts/
│   └── validate_schema.py # A Python script Claude can execute for validation
└── reference/
    └── async_patterns.md  # Detailed reference material for progressive disclosure
```

### 1.2. The Loading Mechanism: Progressive Disclosure

To manage the context window efficiently and maintain performance, skills employ a **progressive disclosure** architecture. Information is loaded in three distinct stages:

1.  **Level 1: Metadata (Always in Context):** Upon startup, Claude loads only the `name` and `description` from the frontmatter of all available skills. This minimal data (~100 tokens per skill) allows Claude to be aware of its capabilities without consuming significant context.
2.  **Level 2: Instructions (Loaded When Triggered):** When a user's prompt matches a skill's description or a skill is invoked directly, the main Markdown body of the `SKILL.md` file is loaded into the context window. This provides the core workflow and instructions.
3.  **Level 3: Resources (Loaded As Needed):** Supporting files, such as scripts in `scripts/` or documents in `reference/`, are only accessed if explicitly mentioned in the `SKILL.md` instructions. Importantly, when a script is executed, only its output enters the context window, not the script's source code, making this an extremely token-efficient way to perform complex, deterministic operations.

### 1.3. Skills vs. Other Context Mechanisms

It is crucial to differentiate skills from other methods of providing context to Claude.

| Feature | Skills (`SKILL.md`) | Project Context (`CLAUDE.md`) | MCP (Model Context Protocol) |
| :--- | :--- | :--- | :--- |
| **Purpose** | Repeatable tasks, on-demand knowledge, and deterministic workflows. | Always-on, foundational project information (stack, conventions, goals). | Connecting to external tools, APIs, and data sources (databases, services). |
| **Structure** | Directory with `SKILL.md` (YAML frontmatter + Markdown) and supporting files. | A single, simple Markdown file. | An external server that exposes tools to Claude. |
| **Invocation** | Automatic (based on description) or manual (`/skill-name`). | Always loaded automatically at the start of every session. | Invoked by Claude as a tool call when it needs to interact with the external system. |
| **Token Usage** | Highly efficient; "lazy-loaded" via progressive disclosure. | Inefficient for large contexts; always consumes tokens regardless of relevance. | Minimal; only the tool definition is in context, not the underlying data. |
| **Best For** | Encoding specific procedures like generating code, running tests, or applying a design pattern. | Defining project-wide rules, architectural principles, and key file locations. | Providing real-time data, interacting with a database, or calling a third-party API. |

For JobRadar, `CLAUDE.md` should contain the high-level architectural principles and tech stack summary. **Skills** should be used to implement the specific patterns for building components within that architecture. **MCPs** would be the mechanism if, in the future, the agent needed direct, real-time access to the production `jobradar.db` file.

### 1.4. Scope, Storage, and Versioning

The location of a skill directory determines its scope and priority.

| Scope | Path | Priority | Use Case for JobRadar |
| :--- | :--- | :--- | :--- |
| **Project** | `.claude/skills/<skill-name>/` | Medium | **Primary location.** For skills specific to the JobRadar codebase, like the custom templates in Section 3. |
| **Personal** | `~/.claude/skills/<skill-name>/` | High | For general-purpose skills you use across all projects (e.g., a personal git commit message formatter). |
| **Enterprise** | Managed via admin settings | Highest | For skills shared across an entire organization (e.g., company-wide security standards). |
| **Plugin** | `<plugin>/skills/<skill-name>/` | Low | For skills bundled and distributed as part of a larger plugin marketplace package. |

When skills with the same name exist at different levels, the higher-priority scope takes precedence (Enterprise > Personal > Project).

**Versioning and Sharing:** Skills are fundamentally just files in a directory, making them perfectly suited for version control with Git. The recommended practice is to store project-specific skills within the project's Git repository and share them among the team. Community skills are typically shared via public GitHub repositories, which can be added as a "marketplace" in Claude Code.

---

## 2. Curated Pre-built Skills for JobRadar

The following pre-built skills from the community are highly relevant to the JobRadar project. They can be installed via the Claude Code plugin marketplace or by cloning their respective repositories.

### 2.1. Backend Development Skills

| Skill | Description & Relevance for JobRadar | Source / Installation |
| :--- | :--- | :--- |
| **`python`** | Provides expert patterns for building Python backend services. Its guidance on FastAPI, SQLAlchemy async patterns, Pydantic schemas, and the repository pattern is directly applicable to the JobRadar backend architecture. | [madappgang-claude-code-python - LobeHub](https://lobehub.com/skills/madappgang-claude-code-python) |
| **`mcp-builder`** | A guide for creating high-quality MCP (Model Context Protocol) servers. While not required for the initial localhost-only build, this skill will be invaluable if JobRadar evolves to require direct, real-time database interaction from the agent. | `anthropics/skills` GitHub repository. Install via marketplace: `/plugin marketplace add anthropics/skills` |

### 2.2. Frontend Development & Design Skills

| Skill | Description & Relevance for JobRadar | Source / Installation |
| :--- | :--- | :--- |
| **`frontend-design`** | Guides the agent in refining modern frontend experiences with a focus on layout, interaction design, and visual polish. Essential for implementing JobRadar's "Technical Droid" aesthetic with clean, precise UI elements. | `anthropics/skills` GitHub repository. |
| **`web-artifacts-builder`** | A skill for building complex, self-contained HTML artifacts using React, Tailwind CSS, and shadcn/ui components. Useful for generating rich, interactive components or reports within the JobRadar UI. | `ComposioHQ/awesome-claude-skills` GitHub repository. |
| **`claude-d3js-skill`** | Provides expertise for creating data visualizations with d3.js. While JobRadar uses Recharts, the principles of data binding and SVG manipulation in this skill can be adapted. | `travisvn/awesome-claude-skills` GitHub repository. |

### 2.3. Testing Skills

| Skill | Description & Relevance for JobRadar | Source / Installation |
| :--- | :--- | :--- |
| **`TDD`** | A powerful multi-agent skill that orchestrates a strict Test-Driven Development workflow (Red-Green-Refactor). It has built-in support for both **pytest** and **Vitest**, making it a perfect fit for testing both the Python backend and TypeScript frontend of JobRadar. | [glebis/claude-skills - GitHub](https://github.com/glebis/claude-skills) |
| **`vitest-testing`** | A focused skill providing expert guidance for testing TypeScript/JavaScript projects with Vitest. Covers configuration, mocking, coverage, and best practices relevant to the JobRadar frontend. | [secondsky/claude-skills/vitest-testing - Playbooks](https://playbooks.com/skills/secondsky/claude-skills/vitest-testing) |
| **`python-testing`** | A compact guide for Python testing with pytest. Covers fixtures, parametrization, mocking, and async testing, all of which are critical for ensuring the quality of the FastAPI and SQLAlchemy components. | [laurigates/claude-plugins/python-testing - Playbooks](https://playbooks.com/skills/laurigates/claude-plugins/python-testing) |

### 2.4. Document Skills

| Skill | Description & Relevance for JobRadar | Source / Installation |
| :--- | :--- | :--- |
| **`docx`** | Create and edit Microsoft Word documents. Can be used to generate formatted resumes or export job application details. | `anthropics/skills` GitHub repository. |
| **`pdf`** | A comprehensive toolkit for creating, merging, and extracting data from PDF files. Useful for generating PDF reports of job pipelines or saved job lists. | `anthropics/skills` GitHub repository. |
| **`xlsx`** | Create and edit Excel spreadsheets with support for formulas and formatting. Ideal for exporting job data for external analysis or tracking application progress in a spreadsheet format. | `anthropics/skills` GitHub repository. |

---

## 3. Custom Skill Templates for JobRadar

The following five skills are designed from the ground up to automate key development patterns specific to the JobRadar architecture. They should be placed in the `.claude/skills/` directory of the JobRadar project repository.

### 3.1. Skill 1: `sqlalchemy-async-patterns`

**Purpose:** To provide the agent with the exact, non-negotiable patterns for setting up the SQLAlchemy 2.0 async engine, session management, and base model for the JobRadar project. This ensures consistency and correct implementation of the async data layer with `aiosqlite`.

```markdown
---
name: sqlalchemy-async-patterns
description: Generates or refactors SQLAlchemy 2.0 async database setup code for the JobRadar project, including engine, session, and Base model definitions according to project standards. Use when setting up `database.py` or `models.py`.
user-invocable: true
---

# SQLAlchemy 2.0 Async Setup for JobRadar

You are an expert in SQLAlchemy 2.0 asynchronous patterns with `aiosqlite`. Your task is to generate the standard database connection and model definition code for the JobRadar project.

## File: `backend/database.py`

When asked to create or review `backend/database.py`, you MUST use the following structure. This configuration is optimized for concurrent reads and writes with SQLite in WAL mode.

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

# Create the asynchronous engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
    connect_args={"check_same_thread": False}, # Required for aiosqlite
)

# Configure WAL mode and other PRAGMAs on each connection
@sqlalchemy.event.listens_for(engine.sync_engine, "connect")
def connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000") # 64MB cache
    cursor.close()

# Create a configured "AsyncSession" class
AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Base class for declarative models
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI to get a DB session
async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

## File: `backend/models.py`

When asked to create a new SQLAlchemy model, it MUST inherit from the `Base` class imported from `backend.database`.

**Example:**
```python
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    # ... other columns
```

**Key Principles to Enforce:**
1.  Always use `sqlalchemy.ext.asyncio`.
2.  The engine URL must come from `backend.config.settings`.
3.  The `get_db` dependency is the ONLY way to get a session in API routes.
4.  All models must inherit from `backend.database.Base`.
```

### 3.2. Skill 2: `fastapi-crud-generator`

**Purpose:** To automate the creation of a full CRUD (Create, Read, Update, Delete) endpoint for a given SQLAlchemy model. This skill generates the API router, Pydantic schemas, and repository methods, drastically reducing boilerplate code.

```markdown
---
name: fastapi-crud-generator
description: Generates a complete FastAPI CRUD endpoint for a given SQLAlchemy model name. Creates the router, Pydantic schemas, and repository methods.
argument-hint: "[ModelName]"
user-invocable: true
---

# FastAPI CRUD Endpoint Generator for JobRadar

Your task is to generate all necessary files for a new FastAPI CRUD endpoint for the model specified in `$0`.

**Example Invocation:** `/fastapi-crud-generator Job`

### Step 1: Understand the Model
First, read the model definition from `backend/models.py` to understand its columns. Let's assume the model is `Job`.

### Step 2: Generate Pydantic Schemas
Create a new file `backend/schemas/$0_schema.py`. The schemas must follow this pattern:

```python
# backend/schemas/job_schema.py
from pydantic import BaseModel
from datetime import datetime

# Base properties shared by create and update
class JobBase(BaseModel):
    title: str
    company: str
    # ... other fields from model, excluding id/timestamps

# Properties for creating a new job
class JobCreate(JobBase):
    pass

# Properties for updating an existing job
class JobUpdate(JobBase):
    pass

# Properties to return to the client (includes id/timestamps)
class Job(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
```

### Step 3: Generate Repository Methods
Create a new file `backend/repositories/$0_repository.py`. The repository class must contain standard async CRUD methods.

```python
# backend/repositories/job_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import Job
from backend.schemas.job_schema import JobCreate, JobUpdate

class JobRepository:
    async def get(self, db: AsyncSession, id: int) -> Job | None:
        result = await db.execute(select(Job).filter(Job.id == id))
        return result.scalars().first()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Job]:
        result = await db.execute(select(Job).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: JobCreate) -> Job:
        db_obj = Job(**obj_in.dict())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # ... implement update and delete methods similarly
```

### Step 4: Generate API Router
Create a new file `backend/routers/$0_router.py`. This file defines the API endpoints.

```python
# backend/routers/job_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend import database, schemas, models
from backend.repositories.job_repository import JobRepository

router = APIRouter()
repo = JobRepository()

@router.post("/", response_model=schemas.Job)
async def create_job(
    *,
    db: AsyncSession = Depends(database.get_db),
    job_in: schemas.JobCreate,
):
    return await repo.create(db=db, obj_in=job_in)

@router.get("/{id}", response_model=schemas.Job)
async def read_job(*, db: AsyncSession = Depends(database.get_db), id: int):
    job = await repo.get(db=db, id=id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# ... implement list, update, and delete endpoints
```

### Step 5: Update `main.py`
Finally, instruct the user to import and include the new router in `backend/main.py`.
`app.include_router(job_router.router, prefix="/api/jobs", tags=["jobs"])`
```

### 3.3. Skill 3: `job-scraper-adapter`

**Purpose:** To scaffold a new scraper class for a new job source. This skill generates the boilerplate adapter class, ensuring it conforms to the `BaseScraper` abstract class and project conventions.

```markdown
---
name: job-scraper-adapter
description: Creates a new scraper adapter file in `backend/scrapers/` for a given job source name.
argument-hint: "[SourceName]"
user-invocable: true
---

# Job Scraper Adapter Generator

Your task is to create a new scraper adapter file for the source `$0`. The file should be named `backend/scrapers/$0_scraper.py`.

### Step 1: Read the Base Class
First, you must read `backend/scrapers/base.py` to understand the `BaseScraper` abstract class it must inherit from. Pay close attention to the abstract methods `fetch_jobs` and the helper method `compute_job_id`.

### Step 2: Generate the Scraper Class
Create the file `backend/scrapers/$0_scraper.py` with the following template. Replace `$0` with the provided source name (e.g., `workday`).

```python
# backend/scrapers/$0_scraper.py
import httpx
from .base import BaseScraper
from backend.config import settings

class $0Scraper(BaseScraper):
    source_name = "$0"
    
    async def fetch_jobs(self, query: str, location: str, limit: int = 20) -> list[dict]:
        """
        Fetches job postings from the $0 API.
        This method must be implemented to connect to the $0 API,
        fetch the raw job data, and transform it into the standard
        JobRadar dictionary format.
        """
        processed_jobs = []
        async with httpx.AsyncClient() as client:
            #
            # --- IMPLEMENT API LOGIC HERE ---
            # 1. Construct the API URL and headers.
            #    api_url = "https://api.$0.com/jobs"
            #    headers = {"Authorization": f"Bearer {settings.$0_API_KEY}"}
            #
            # 2. Make the async request.
            #    response = await client.get(api_url, params={"q": query, "loc": location})
            #    response.raise_for_status()
            #    raw_jobs = response.json().get('jobs', [])
            #
            # 3. Loop through raw jobs and transform data.
            #    for raw_job in raw_jobs:
            #        job_id = self.compute_job_id(
            #            source=self.source_name,
            #            company=raw_job.get('companyName'),
            #            title=raw_job.get('jobTitle')
            #        )
            #        processed_jobs.append({
            #            "job_id": job_id,
            #            "source": self.source_name,
            #            "title": raw_job.get('jobTitle'),
            #            "company": raw_job.get('companyName'),
            #            "location": raw_job.get('location'),
            #            "url": raw_job.get('jobUrl'),
            #            "raw_description_html": raw_job.get('description'),
            #            # ... map other fields
            #        })
            #
            pass # Remove this pass statement after implementation

        return processed_jobs

```

### Step 3: Explain Next Steps
Advise the user on the following:
1.  Implement the API connection logic inside the `fetch_jobs` method.
2.  Add the new scraper class to the `SCRAPERS` dictionary in `backend/scrapers/__init__.py`.
3.  Add a new scheduler job for this scraper in `backend/scheduler.py`.
4.  If it requires an API key, add the key to `.env` and `backend/config.py`.
```

### 3.4. Skill 4: `react-query-hook-generator`

**Purpose:** To bridge the frontend and backend by creating typed TanStack Query hooks (`useQuery`, `useMutation`) for a given FastAPI endpoint. This ensures type safety and accelerates frontend data-fetching implementation.

```markdown
---
name: react-query-hook-generator
description: Generates a typed TanStack Query hook (`useQuery` or `useMutation`) for a given FastAPI endpoint path.
argument-hint: "[GET|POST|PUT|DELETE] [/api/endpoint/path]"
user-invocable: true
---

# TanStack Query Hook Generator for JobRadar

Your task is to generate a typed TanStack Query hook for the JobRadar frontend. The HTTP method is `$0` and the endpoint path is `$1`.

### Step 1: Determine Hook Type
- If method is `GET`, generate a `useQuery` hook.
- If method is `POST`, `PUT`, or `DELETE`, generate a `useMutation` hook.

### Step 2: Infer Types
- You must infer the response type and request body/params type from the backend code.
- Look at the `response_model` in the FastAPI router function for `$1` to determine the return type.
- Look at the function signature to determine the types for path parameters, query parameters, or the request body.
- Create corresponding TypeScript interfaces.

### Step 3: Generate the Hook (useQuery example for `GET /api/jobs`)

Create a new file in `frontend/src/api/hooks/` named appropriately (e.g., `useJobs.ts`).

```typescript
// frontend/src/api/hooks/useJobs.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../client';

// Type inferred from backend/schemas/job_schema.py -> Job
interface Job {
  id: number;
  title: string;
  company: string;
  // ... other properties
}

// Type for query params
interface GetJobsParams {
  skip?: number;
  limit?: number;
  query?: string;
}

const getJobs = async (params: GetJobsParams): Promise<Job[]> => {
  const { data } = await apiClient.get<Job[]>('/api/jobs', { params });
  return data;
};

export const useJobs = (params: GetJobsParams) => {
  return useQuery<Job[], Error>({
    queryKey: ['jobs', params],
    queryFn: () => getJobs(params),
    keepPreviousData: true, // Good for pagination
  });
};
```

### Step 4: Generate the Hook (useMutation example for `POST /api/jobs`)

```typescript
// frontend/src/api/hooks/useCreateJob.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

// Type inferred from backend/schemas/job_schema.py -> JobCreate
interface JobCreate {
  title: string;
  company: string;
  // ... other properties
}

// Type inferred from backend/schemas/job_schema.py -> Job
interface Job {
  id: number;
  // ... other properties
}

const createJob = async (newJob: JobCreate): Promise<Job> => {
  const { data } = await apiClient.post<Job>('/api/jobs', newJob);
  return data;
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();

  return useMutation<Job, Error, JobCreate>({
    mutationFn: createJob,
    onSuccess: () => {
      // Invalidate and refetch the jobs list after a successful creation
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
```

### Step 5: Final Instructions
- Remind the user to check the generated TypeScript interfaces against the Pydantic models.
- Explain how to use the generated hook in a React component.
```

### 3.5. Skill 5: `dnd-kit-kanban-component`

**Purpose:** To automate the creation of the complex component structure required for the dnd-kit Kanban board. This skill generates the `SortableContext` and droppable column, including Zustand state integration.

```markdown
---
name: dnd-kit-kanban-component
description: Generates the React components for a new column in the JobRadar dnd-kit Kanban board, including SortableContext and Zustand state logic.
argument-hint: "[ColumnName]"
user-invocable: true
---

# dnd-kit Kanban Component Generator

Your task is to generate the React components needed for the JobRadar Kanban board, which uses `@dnd-kit/core` and `@dnd-kit/sortable`. The new column will be for the status `$0`.

### Step 1: Understand the Existing Structure
Review the existing Kanban board implementation in `frontend/src/components/pipeline/KanbanBoard.tsx`. Note the use of `DndContext`, `SortableContext`, and the `useJobStore` from Zustand for state management.

### Step 2: Generate the Column Component
Create a new file `frontend/src/components/pipeline/KanbanColumn.tsx` if it doesn't exist, or add to it. This component represents a single droppable column.

```typescript
// In frontend/src/components/pipeline/KanbanColumn.tsx

import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { JobCard } from './JobCard'; // Assuming JobCard component exists

interface KanbanColumnProps {
  id: string; // e.g., 'saved', 'applied'
  title: string;
  jobs: Job[]; // Assuming Job type is defined
}

export function KanbanColumn({ id, title, jobs }: KanbanColumnProps) {
  const { setNodeRef } = useDroppable({ id });

  return (
    <SortableContext
      id={id}
      items={jobs.map(j => j.id)}
      strategy={verticalListSortingStrategy}
    >
      <div
        ref={setNodeRef}
        className="flex flex-col w-80 bg-bg-surface rounded-lg p-2"
      >
        <h3 className="font-bold p-2">{title} ({jobs.length})</h3>
        <div className="flex flex-col gap-2 overflow-y-auto">
          {jobs.map(job => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      </div>
    </SortableContext>
  );
}
```

### Step 3: Generate the Draggable Card Component
Create `frontend/src/components/pipeline/JobCard.tsx`. This component is the draggable item.

```typescript
// In frontend/src/components/pipeline/JobCard.tsx

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

export function JobCard({ job }: { job: Job }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: job.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="p-4 bg-bg-elevated rounded border border-border cursor-grab"
    >
      <p className="font-bold">{job.title}</p>
      <p className="text-sm text-text-secondary">{job.company}</p>
    </div>
  );
}
```

### Step 4: Instruct on State and Logic Integration
Provide clear instructions on how to integrate this into the main `KanbanBoard.tsx` component:
1.  **State:** Add the new status `$0` to the job status array/enum.
2.  **Filtering:** In `KanbanBoard.tsx`, filter the jobs from the Zustand store for the new status: `const ${0}Jobs = jobs.filter(j => j.status === '$0');`
3.  **Rendering:** Render the new `KanbanColumn` component: `<KanbanColumn id="$0" title="$0 (Title Case)" jobs={${0}Jobs} />`
4.  **Drag Logic:** Update the `handleDragEnd` function in `KanbanBoard.tsx` to handle items being dropped into the new `$0` column, which should call the `updateJobStatus` method from the Zustand store.
```

# References
1. [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
2. [Agent Skills Best Practices - Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
3. [Claude Code Skills - mikhail.io](https://mikhail.io/2025/10/claude-code-skills/)
4. [Writing a good CLAUDE.md - humanlayer.dev](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
5. [skill-creator/SKILL.md at main · anthropics/skills · GitHub](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
6. [How to create custom Skills - Claude Help Center](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
7. [How I structure Claude Code projects (CLAUDE.md, skills, agents, etc.) - Reddit](https://www.reddit.com/r/ClaudeAI/comments/1r66oo0/how_i_structure_claude_code_projects_claudemd/)
8. [anthropics/skills - GitHub](https://github.com/anthropics/skills)
9. [Claude Agent Skills: A First Principles Deep Dive - leehanchung.github.io](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
10. [Use Skills in Claude - Claude Help Center](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
11. [What are Skills? - Claude Help Center](https://support.claude.com/en/articles/12512176-what-are-skills)
12. [Agent Skills Overview - Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
13. [The Complete Guide to Building Skills for Claude - Anthropic Resources](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf?hsLang=en)
14. [How We Use Claude Code Skills to Run 1,000+ ML Experiments a Day - Hugging Face Blog](https://huggingface.co/blog/sionic-ai/claude-code-skills-training)
15. [awesome-claude-skills - travisvn/awesome-claude-skills - GitHub](https://github.com/travisvn/awesome-claude-skills)
16. [skillsmp.com](https://skillsmp.com)
17. [awesome-claude-skills - ComposioHQ/awesome-claude-skills - GitHub](https://github.com/ComposioHQ/awesome-claude-skills)
18. [claude-skills-collection - abubakarsiddik31/claude-skills-collection - GitHub](https://github.com/abubakarsiddik31/claude-skills-collection)
19. [claude-skills - alirezarezvani/claude-skills - GitHub](https://github.com/alirezarezvani/claude-skills)
20. [awesome-agent-skills - VoltAgent/awesome-agent-skills - GitHub](https://github.com/VoltAgent/awesome-agent-skills)
21. [How to Create Claude Code Skills: The Complete Guide from Anthropic - websearchapi.ai](https://websearchapi.ai/blog/how-to-create-claude-code-skills)
22. [Introducing Agent Skills - Anthropic](https://www.anthropic.com/news/skills)
23. [Understanding CLAUDE.md vs Skills vs Slash Commands vs Subagents vs Plugins - Reddit](https://www.reddit.com/r/ClaudeAI/comments/1ped515/understanding_claudemd_vs_skills_vs_slash/)
24. [When to use Skills vs. Commands vs. Agents - danielmiessler.com](https://danielmiessler.com/blog/when-to-use-skills-vs-commands-vs-agents)
25. [What's the difference between skills.md, agents.md, and commands.md? - Reddit](https://www.reddit.com/r/LLM/comments/1qtlizp/whats_the_difference_between_skillsmd_agentsmd/)
26. [When should a Claude skill be a script? - cote.io](https://cote.io/2025/10/27/when-should-a-claude-skill.html)
27. [Difference between skills and these subagents? - Reddit](https://www.reddit.com/r/ClaudeCode/comments/1o8t6xe/difference_between_skills_and_these_subagents/)
28. [How to Use Claude Code Features Like CLAUDE.md, Skills, and Subagents - producttalk.org](https://www.producttalk.org/how-to-use-claude-code-features/)
29. [fastapi/fastapi - GitHub](https://github.com/fastapi/fastapi)
30. [python | Skills Marketplace · LobeHub](https://lobehub.com/skills/madappgang-claude-code-python)
31. [FastAPI](https://fastapi.tiangolo.com/)
32. [full-stack-fastapi-template/backend/README.md at master · fastapi/full-stack-fastapi-template - GitHub](https://github.com/fastapi/full-stack-fastapi-template/blob/master/backend/README.md)
33. [Request for sample fastAPI projects github repos - Reddit](https://www.reddit.com/r/FastAPI/comments/1btwxok/request_for_sample_fastapi_projects_github_repos/)
34. [Ultimate Claude Skill.md: Auto-Builds ANY Full-Stack Web App Silently - Reddit](https://www.reddit.com/r/ClaudeAI/comments/1qb1024/ultimate_claude_skillmd_autobuilds_any_fullstack/)
35. [calderbuild/skillforge - GitHub](https://github.com/calderbuild/skillforge)
36. [A SKILL.md for frontend-design - GitHub Gist](https://gist.github.com/bskimball/91ce7b420adf6d269df223d0edfd0220)
37. [Lemoncode/react-typescript-samples - GitHub](https://github.com/Lemoncode/react-typescript-samples)
38. [typescript-cheatsheets/react - GitHub](https://github.com/typescript-cheatsheets/react)
39. [webguru11124 - GitHub](https://github.com/webguru11124)
40. [PacktPublishing/Learn-React-with-TypeScript-3 - GitHub](https://github.com/PacktPublishing/Learn-React-with-TypeScript-3)
41. [Frontend, React and Typescript roadmap - GitHub Gist](https://gist.github.com/doug2k1/7eb069fbbfd78f3697f44c42e413aede)
42. [The 2024 Frontend Developer Handbook - GitHub Gist](https://gist.github.com/hachesilva/e9154408dab11a0d2b5c728770d7b4b0)
43. [stevekinney/react-and-typescript - GitHub](https://github.com/stevekinney/react-and-typescript)
44. [sqlalchemy/alembic - GitHub](https://github.com/sqlalchemy/alembic)
45. [Working with Autogenerate — Alembic 1.13.1 documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
46. [Alembic Tutorial — Alembic 1.13.1 documentation](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
47. [Using migrations in Python (SQLAlchemy) with Alembic + Docker solution - Medium](https://medium.com/@johnidouglasmarangon/using-migrations-in-python-sqlalchemy-with-alembic-docker-solution-bd79b219d6a)
48. [Alembic and PostgreSQL: A Guide to Database Migrations - TestDriven.io](https://testdriven.io/blog/alembic-database-migrations/)
49. [alembic · PyPI](https://pypi.org/project/alembic/)
50. [Flask-Migrate — Flask-Migrate documentation](https://flask-migrate.readthedocs.io/)
51. [How do I execute inserts and updates in an alembic upgrade script? - Stack Overflow](https://stackoverflow.com/questions/24612395/how-do-i-execute-inserts-and-updates-in-an-alembic-upgrade-script)
52. [tfriedel/claude-office-skills - GitHub](https://github.com/tfriedel/claude-office-skills)
53. [Create and edit files with Claude - Claude Help Center](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)
54. [Claude.ai has built-in superpowers and you probably didn't know - DEV Community](https://dev.to/nunc/claudeai-has-built-in-superpowers-and-you-probably-didnt-know-1haa)
55. [Skills Introduction - Claude Cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)
56. [anthropic/docx - MCP Servers](https://mcpservers.org/claude-skills/anthropic/docx)
57. [Anthropic Skills - Agno Docs](https://docs.agno.com/models/providers/native/anthropic/usage/skills)
58. [glebis/claude-skills - GitHub](https://github.com/glebis/claude-skills)
59. [greyhaven-ai-claude-code-config-testing-strategy | Skills Marketplace · LobeHub](https://lobehub.com/skills/greyhaven-ai-claude-code-config-testing-strategy)
60. [FAQ - ClaudeFAST](https://claudefa.st/blog/guide/faq)
61. [windsurf-test-generation - Playbooks](https://playbooks.com/skills/jeremylongshore/claude-code-plugins-plus-skills/windsurf-test-generation)
62. [vitest-testing - Playbooks](https://playbooks.com/skills/secondsky/claude-skills/vitest-testing)
63. [python-testing - Playbooks](https://playbooks.com/skills/laurigates/claude-plugins/python-testing)
64. [How to do Unit Testing on Claude Code - Usagebar](https://usagebar.com/blog/how-to-do-unit-testing-on-claude-code)
65. [awesome-claude-code-toolkit/snapshot-test.md at main · rohitg00/awesome-claude-code-toolkit - GitHub](https://github.com/rohitg00/awesome-claude-code-toolkit/blob/main/commands/testing/snapshot-test.md)