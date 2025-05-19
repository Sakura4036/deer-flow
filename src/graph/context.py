from src.graph.types import Observation
from src.graph.types import State
from src.prompts.planner_model import StepType


class ContextManager:
    """管理传递给代理的上下文信息"""

    @staticmethod
    def get_relevant_observations(state: State, step_type: StepType, agent_type:str, threshold: float = 0.5) -> list[Observation]:
        """获取与当前步骤相关的观察结果"""
        observations = state.get("observations", [])

        # step可接受来源
        agent_type_observation_map = {
        }

        if step_type == StepType.RESEARCH:
            pass

        pass

    @staticmethod
    def format_context_for_agent(observations: list[Observation], agent_type: str) -> str:
        """根据代理类型格式化上下文信息"""

        # 根据不同代理类型定制格式  
        if agent_type == "researcher":
            return "## Previous Research Findings\n\n" + "\n\n".join([f"- {obs.content}" for obs in observations])
        elif agent_type == "coder":
            return "## Available Data\n\n" + "\n\n".join([f"```\n{obs.content}\n```" for obs in observations])
            # 其他代理类型...
