import pytest

from app.projects.config import project_config
from app.projects.exceptions import MaxPositionsPerProjectLimitExceededException
from app.projects.models.project import Project, ProjectVisibility


@pytest.mark.unit
@pytest.mark.projects
class TestProjectModelLimits:
    def test_new_position_respects_limit(self) -> None:
        project = Project.create(
            owner_id=1,
            name="P",
            slug="p",
            small_description="s",
            full_description="d",
            visibility=ProjectVisibility.public,
            metadata={},
            tags=set(),
        )

        for i in range(project_config.MAX_POSITIONS_PER_PROJECT):
            project.new_position(
                title=f"Pos {i}",
                description="desc",
                required_skills={"python"},
                responsibilities=None,
                location_type=None,
                expected_load=None,
            )

        with pytest.raises(MaxPositionsPerProjectLimitExceededException):
            project.new_position(
                title="overflow",
                description="desc",
                required_skills={"python"},
                responsibilities=None,
                location_type=None,
                expected_load=None,
            )

