"""StrictDoc configuration for the formal requirements and verifications.

Build the HTML export from the repository root with: strictdoc export docs
"""

from strictdoc.core.project_config import ProjectConfig


def create_config() -> ProjectConfig:
    return ProjectConfig(
        project_title="Buddyplan requirements",
        include_doc_paths=[
            "requirements/**",
            "verifications/**",
        ],
        grammars={
            "@requirement": "requirements/requirement.sgra",
            "@verification": "verifications/verification.sgra",
        },
    )
