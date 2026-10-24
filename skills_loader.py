import os
from pathlib import Path
from typing import Dict, Any, Union, List
import yaml
import json

from models import Evidence


def parse_skill_file(filepath: Path) -> Dict[str, Any]:
    """
    Parses YAML frontmatter and markdown body from SKILL.md.
    """
    content = filepath.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_raw = parts[1]
            body = parts[2].strip()
            frontmatter = yaml.safe_load(frontmatter_raw) or {}
            return {
                "name": frontmatter.get("name", "").strip(),
                "description": frontmatter.get("description", "").strip(),
                "metadata": frontmatter.get("metadata", {}),
                "body": body,
                "filepath": str(filepath),
            }
    return {
        "name": "",
        "description": "",
        "metadata": {},
        "body": content.strip(),
        "filepath": str(filepath),
    }


def load_skills(skills_dir: Union[str, Path] = "skills") -> Dict[str, Dict[str, str]]:
    """
    Loads skills with progressive disclosure:
    Validates name matches the folder name and description is non-empty.
    Stores only catalog metadata (name, description, filepath) in memory.
    The full body is loaded on demand.
    """
    base_path = Path(skills_dir)
    catalog: Dict[str, Dict[str, str]] = {}

    if not base_path.exists():
        return catalog

    for item in sorted(base_path.iterdir()):
        if item.is_dir():
            skill_md = item / "SKILL.md"
            if skill_md.exists() and skill_md.is_file():
                parsed = parse_skill_file(skill_md)
                folder_name = item.name
                skill_name = parsed["name"]
                description = parsed["description"]

                if not skill_name:
                    raise ValueError(f"Skill in {item} missing 'name' in frontmatter.")
                if skill_name != folder_name:
                    raise ValueError(
                        f"Skill name '{skill_name}' does not match folder '{folder_name}'."
                    )
                if not description:
                    raise ValueError(f"Skill '{skill_name}' must have a non-empty description.")

                # Progressive disclosure: keep only lightweight metadata in catalog
                catalog[skill_name] = {
                    "name": skill_name,
                    "description": description,
                    "filepath": str(skill_md),
                }

    return catalog


def route(evidence_type: str) -> str:
    """
    Deterministic routing mapping evidence types to skill names.
    No LLM routing used.
    """
    mapping = {
        "leakage": "explain-leakage",
        "duplicates": "explain-duplicates",
        "label_noise": "audit-labels",
        "correlation": "explain-correlation",
        "summary": "case-summary",
        "case_summary": "case-summary",
    }
    return mapping.get(evidence_type, "explain-leakage")


def get_skill_body(skill_info: Union[str, Dict[str, str]], skills_dir: str = "skills") -> str:
    """
    Retrieves the full body of a skill using progressive disclosure.
    """
    if isinstance(skill_info, str):
        # Could be skill name or file path
        if os.path.exists(skill_info):
            parsed = parse_skill_file(Path(skill_info))
            return parsed["body"]
        else:
            skill_path = Path(skills_dir) / skill_info / "SKILL.md"
            if skill_path.exists():
                return parse_skill_file(skill_path)["body"]
            raise FileNotFoundError(f"Skill {skill_info} not found at {skill_path}")
    elif isinstance(skill_info, dict) and "filepath" in skill_info:
        return parse_skill_file(Path(skill_info["filepath"]))["body"]
    elif isinstance(skill_info, dict) and "body" in skill_info:
        return skill_info["body"]
    raise ValueError(f"Invalid skill reference: {skill_info}")


def build_prompt(
    skill: Union[str, Dict[str, str]],
    evidence: Union[Evidence, Dict[str, Any], List[Union[Evidence, Dict[str, Any]]]],
    skills_dir: str = "skills",
) -> str:
    """
    Builds the complete prompt combining the skill instructions and evidence facts.
    Prompt = skill body + "\\n---\\nEvidence:\\n" + evidence JSON
    """
    body = get_skill_body(skill, skills_dir=skills_dir)

    if isinstance(evidence, Evidence):
        evidence_json = evidence.to_json()
    elif isinstance(evidence, list):
        ev_list = [
            e.to_dict() if isinstance(e, Evidence) else e
            for e in evidence
        ]
        evidence_json = json.dumps(ev_list, indent=2, default=str)
    elif isinstance(evidence, dict):
        evidence_json = json.dumps(evidence, indent=2, default=str)
    else:
        evidence_json = str(evidence)

    return f"{body}\n---\nEvidence:\n{evidence_json}"
