from src.graph.types import Observation
from src.graph.types import State
from src.prompts.planner_model import StepType


class ContextManager:
    """Manages context information passed to agents, including filtering and formatting observations."""

    @staticmethod
    def get_relevant_observations(
        state: State,
        step_type: StepType,
        agent_type: str,
        threshold: float = 0.5,
        max_words: int = 64000,
    ) -> list[Observation]:
        """
        Get relevant observations for the current step and agent.
        Filters by agent_type/source, relevance_score, and trims to max_words.
        """
        observations = state.get("observations", [])

        # Map agent_type to allowed sources
        agent_type_observation_map = {
            "researcher": ["researcher", "literature_researcher", "patent_researcher"],
            "literature_researcher": ["researcher", "literature_researcher"],
            "patent_researcher": ["researcher", "patent_researcher"],
            "coder": ["coder"],
        }
        allowed_sources = agent_type_observation_map.get(agent_type, [])

        # Filter by source and relevance_score
        filtered = [
            obs for obs in observations
            if (not allowed_sources or obs["source"] in allowed_sources)
            and obs.get("relevance_score", 1.0) >= threshold
        ]

        # Sort by relevance_score descending
        filtered.sort(key=lambda x: x.get("relevance_score", 1.0), reverse=True)

        # Trim to max_words (approximate, by content length)
        total_words = 0
        result = []
        for obs in filtered:
            word_count = len(obs["content"].split())
            if total_words + word_count > max_words:
                break
            result.append(obs)
            total_words += word_count
        return result

    @staticmethod
    def format_context_for_agent(observations: list[Observation], agent_type: str) -> str:
        """Format context for agent based on agent_type."""
        if agent_type == "researcher":
            return "## Previous Research Findings\n\n" + "\n\n".join([f"- {obs['content']}" for obs in observations])
        elif agent_type == "coder":
            return "## Available Data\n\n" + "\n\n".join([f"```\n{obs['content']}\n```" for obs in observations])
        # Add more agent types as needed
        return "\n\n".join([obs['content'] for obs in observations])
