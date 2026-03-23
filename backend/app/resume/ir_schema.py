"""Intermediate Representation (IR) schema for parsed resumes.

Provides a format-agnostic, structured representation of resume content
that can be produced from any input format (PDF, DOCX, LaTeX, plain text).
"""

from __future__ import annotations

from pydantic import BaseModel


class ContactInfo(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    description: str | None = None
    bullets: list[str] = []
    tech_stack: list[str] = []
    metrics: list[str] = []


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    highlights: list[str] = []


class Project(BaseModel):
    name: str
    description: str | None = None
    tech_stack: list[str] = []
    url: str | None = None
    bullets: list[str] = []


class ResumeIR(BaseModel):
    contact: ContactInfo
    summary: str | None = None
    work: list[WorkExperience] = []
    education: list[Education] = []
    skills: list[str] = []
    skill_categories: dict[str, list[str]] = {}
    projects: list[Project] = []
    certifications: list[str] = []
    publications: list[str] = []
    languages: list[str] = []
    raw_text: str = ""
    section_confidence: dict[str, float] = {}
    parse_warnings: list[str] = []
