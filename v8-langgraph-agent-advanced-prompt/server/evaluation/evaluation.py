###
### Based on https://docs.smith.langchain.com/evaluation/tutorials/agents
###
import os
from langsmith import Client
from dotenv import load_dotenv
from agent_core.agent_factory import AgentType, AgentFactory
from logger.cust_logger import logger, set_files_message_color, format_log_message
from evaluation.evaluator import final_answer_correct
import asyncio

load_dotenv()
env_var_key = "OPENAI_API_KEY"
model_path: str | None = os.getenv(env_var_key)
set_files_message_color("PURPLE")  # Set color for logging in this function

# Initialize the LangSmith Client
client = Client()


async def evaluate_message(input_message):
    language = "English"
    config = {"configurable": {"thread_id": "evaluation-test"}}
    agent = AgentFactory().create_agent(AgentType.ReActAgent)
    answer = await agent.invoke(input_message["question"], language, config)
    return {"response": answer}


test_cases = [
    {
        "question": "Hey",
        "response": "Hello! How can I assist you today?",
        "trajectory": [],
    },
    {
        "question": "rollout my app",
        "response": "I found the self-service action for rolling out an app. You can access it through this link: [Rollout app](https://demo.rely.io/self-service/action-details/rollout/action-details). You can run the self-service action from the web UI.",
        "trajectory": ["fetch_flow_tool"],
    },
]

dataset_name = "React Agent Baseline Evaluation v3"

if not client.has_dataset(dataset_name=dataset_name):
    dataset = client.create_dataset(dataset_name=dataset_name)
    client.create_examples(
        inputs=[{"question": ex["question"]} for ex in test_cases],
        outputs=[
            {"response": ex["response"], "trajectory": ex["trajectory"]}
            for ex in test_cases
        ],
        dataset_id=dataset.id,
    )


async def main():
    logger.info(format_log_message("Evaluation job started"))
    # Evaluation job and results
    experiment_results = await client.aevaluate(
        evaluate_message,
        data=dataset_name,
        evaluators=[final_answer_correct],
        experiment_prefix="react-agent-evaluation",
        num_repetitions=1,
        max_concurrency=4,
    )

    experiment_results.to_pandas()


if __name__ == "__main__":
    asyncio.run(main())
