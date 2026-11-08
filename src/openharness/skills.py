
import yaml
from pathlib import Path


class SkillManager:
    def __init__(self, skills_dir="skills"):
        self.skills_dir = Path(skills_dir)
        self.skills = {}

    def discover(self):
        self.skills.clear()

        if not self.skills_dir.exists():
            return []

        for skill_file in self.skills_dir.glob("*/SKILL.md"):
            content = skill_file.read_text(encoding="utf-8")

            if not content.startswith("---"):
                continue

            try:
                _, frontmatter, body = content.split("---", 2)
                metadata = yaml.safe_load(frontmatter) or {}

                name = metadata.get("name")
                description = metadata.get("description")

                if not name or not description:
                    continue

                if name != skill_file.parent.name:
                    continue

                self.skills[name] = {
                    "description": description,
                    "content": body.strip()
                }

            except (ValueError, yaml.YAMLError):
                continue

        return [
            {"name": name, "description": skill["description"]}
            for name, skill in self.skills.items()
        ]

    def get_catalog(self):
        return "\n".join(
            f"- {skill['name']}: {skill['description']}"
            for skill in self.discover()
        )

    def load_skill(self, name: str):
        name = name.lower()

        if name not in self.skills:
            matches = [
                skill_name
                for skill_name in self.skills
                if name in skill_name.lower()
            ]

            if len(matches) == 1:
                name = matches[0]
            else:
                raise ValueError(
                    f"Unknown or ambiguous skill: {name}. "
                    f"Available skills: {list(self.skills.keys())}"
                )

        skill = self.skills[name]

        return {
            "name": name,
            "instructions": skill["content"]
        }
