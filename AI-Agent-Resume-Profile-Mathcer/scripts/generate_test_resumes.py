from __future__ import annotations

import argparse
import random
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class RoleTemplate:
    title: str
    skills: List[str]
    project_focus: str


FIRST_NAMES = [
    "Aarav", "Vihaan", "Aditya", "Ishaan", "Kabir", "Rohan", "Arjun", "Nikhil", "Dev", "Karan",
    "Rahul", "Manav", "Ananya", "Aisha", "Riya", "Priya", "Sanya", "Neha", "Meera", "Diya",
    "Zoya", "Ira", "Sara", "Kavya", "Tara", "Aditi", "Siddharth", "Yash", "Harsh", "Nitin",
    "Bhavya", "Tanvi", "Pooja", "Sneha", "Varun", "Gaurav", "Mihir", "Pranav", "Shreya", "Naina",
    "Reyansh", "Ayaan", "Krish", "Parth", "Om", "Ritika", "Muskan", "Ishita", "Manya", "Lavanya",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Patel", "Mehta", "Reddy", "Nair", "Iyer", "Kapoor",
    "Bansal", "Saxena", "Agarwal", "Kumar", "Mishra", "Joshi", "Malhotra", "Chopra", "Das", "Menon",
]

LOCATIONS = [
    "Bengaluru", "Hyderabad", "Pune", "Delhi", "Mumbai", "Chennai", "Noida", "Gurugram", "Kolkata", "Ahmedabad",
]

EDUCATION_LINES = [
    "B.Tech in Computer Science, IIT Delhi, 2018",
    "B.E. in Information Technology, NIT Trichy, 2017",
    "B.Tech in Electronics and Communication, IIT Bombay, 2016",
    "M.Tech in Data Science, IIIT Hyderabad, 2019",
    "B.Sc. in Computer Science, Delhi University, 2018",
    "MCA, VIT Vellore, 2017",
]

CERTIFICATIONS = [
    "AWS Certified Developer – Associate",
    "Microsoft Certified: Azure Developer Associate",
    "Docker Certified Associate",
    "Kubernetes Application Developer (CKAD)",
    "Databricks Data Engineer Associate",
    "Google Professional Cloud Developer",
]

ROLE_TEMPLATES = [
    RoleTemplate(
        title="Full Stack Engineer",
        skills=["React", "TypeScript", "Node", "SQL", "Docker", "Azure"],
        project_focus="talent workflow platforms",
    ),
    RoleTemplate(
        title="AI Engineer",
        skills=["Python", "LLM", "LangChain", "LangGraph", "RAG", "SQL"],
        project_focus="retrieval-based AI assistants",
    ),
    RoleTemplate(
        title="Backend Engineer",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
        project_focus="distributed backend services",
    ),
    RoleTemplate(
        title="Data Engineer",
        skills=["Python", "Spark", "Airflow", "SQL", "AWS", "Azure"],
        project_focus="batch and streaming data pipelines",
    ),
    RoleTemplate(
        title="MLOps Engineer",
        skills=["Python", "Machine Learning", "Docker", "Kubernetes", "AWS", "Terraform"],
        project_focus="model serving and monitoring stacks",
    ),
]


def sanitize_filename(name: str, idx: int) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return f"cand_{idx:03d}_{slug}.txt"


def generate_candidate_name(index: int, rng: random.Random) -> str:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    last = LAST_NAMES[(index * 3 + rng.randint(0, len(LAST_NAMES) - 1)) % len(LAST_NAMES)]
    return f"{first} {last}"


def years_to_dates(total_years: int) -> tuple[int, int]:
    current_year = datetime.now().year
    start_year = max(2010, current_year - total_years)
    midpoint = max(start_year + 1, current_year - max(1, total_years // 2))
    return start_year, midpoint


def write_resume(
    path: Path,
    name: str,
    role: RoleTemplate,
    years_exp: int,
    location: str,
    education_line: str,
    certification: str,
    rng: random.Random,
) -> None:
    start_year, midpoint = years_to_dates(years_exp)
    primary, secondary = role.skills[0], role.skills[1]
    tertiary = role.skills[2] if len(role.skills) > 2 else role.skills[0]
    skills_line = ", ".join(role.skills + rng.sample(["Git", "Linux", "SQL", "Docker", "Azure", "AWS"], k=2))
    skills_line = ", ".join(dict.fromkeys(skills_line.split(", ")))

    lines = [
        name,
        f"{role.title} | {location}",
        f"Email: {name.lower().replace(' ', '.')}@example.com | Phone: +91-98{rng.randint(10000000, 99999999)} | LinkedIn: linkedin.com/in/{name.lower().replace(' ', '-')}",
        "",
        "Summary",
        (
            f"Results-driven {role.title} with {years_exp}+ years of experience in {primary} and {secondary}. "
            f"Delivered business impact through {role.project_focus}, scalable systems, and strong stakeholder collaboration."
        ),
        "",
        "Skills",
        skills_line,
        "",
        "Experience",
        f"Senior {role.title} | NovaTech Systems | {midpoint} - Present",
        f"- Led architecture and delivery of {role.project_focus} using {primary}, {secondary}, and {tertiary}.",
        f"- Built production pipelines and improved performance by {rng.randint(25, 55)}% while mentoring a team of {rng.randint(2, 8)} engineers.",
        f"{role.title} | PixelBridge Labs | {start_year} - {midpoint}",
        f"- Implemented services with {primary}, {secondary}, and SQL; collaborated with product and analytics teams.",
        f"- Achieved {years_exp}+ years hands-on experience in {primary} across enterprise-grade systems.",
        "",
        "Projects",
        (
            f"Intelligent Talent Platform: Designed and deployed a {role.project_focus} solution with {primary}, "
            f"{secondary}, and Docker, supporting {rng.randint(50000, 200000)} monthly users."
        ),
        (
            "Observability and Reliability Upgrade: Introduced automated testing, CI/CD, and monitoring "
            f"to reduce incidents by {rng.randint(20, 45)}%."
        ),
        "",
        "Education",
        education_line,
        "",
        "Certifications",
        certification,
    ]

    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def generate_resumes(output_dir: Path, count: int, seed: int, overwrite: bool, clean: bool) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    if clean:
        for existing in output_dir.glob("*.txt"):
            existing.unlink()

    generated_files: List[Path] = []
    for idx in range(1, count + 1):
        name = generate_candidate_name(idx - 1, rng)
        role = ROLE_TEMPLATES[(idx - 1) % len(ROLE_TEMPLATES)]
        years_exp = 2 + ((idx - 1) % 10)
        location = LOCATIONS[(idx - 1) % len(LOCATIONS)]
        education_line = EDUCATION_LINES[(idx - 1) % len(EDUCATION_LINES)]
        certification = CERTIFICATIONS[(idx - 1) % len(CERTIFICATIONS)]
        file_path = output_dir / sanitize_filename(name, idx)

        if file_path.exists() and not overwrite:
            generated_files.append(file_path)
            continue

        write_resume(
            path=file_path,
            name=name,
            role=role,
            years_exp=years_exp,
            location=location,
            education_line=education_line,
            certification=certification,
            rng=rng,
        )
        generated_files.append(file_path)

    return generated_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic resumes for RAG testing")
    parser.add_argument("--output-dir", type=str, default="data/resumes", help="Directory to write generated resumes")
    parser.add_argument("--count", type=int, default=50, help="Number of sample resumes to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic output")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing resume files")
    parser.add_argument("--clean", action="store_true", help="Delete existing .txt resumes in output dir before generation")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.count < 1:
        parser.error("count must be >= 1")

    output_dir = Path(args.output_dir)
    files = generate_resumes(
        output_dir=output_dir,
        count=args.count,
        seed=args.seed,
        overwrite=args.overwrite,
        clean=args.clean,
    )

    print(f"Generated/available resumes: {len(files)}")
    print(f"Output directory: {output_dir.resolve().as_posix()}")


if __name__ == "__main__":
    main()
