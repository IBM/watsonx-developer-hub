import asyncio
import textwrap
from utils import prepare_chat_watsonx
from mcp import ClientSession
from mcp.client.sse import sse_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

chat_watsonx = prepare_chat_watsonx()

# Dictionary of predefined questions with descriptions
questions = {
    "Simple addition": "What is 1+1?",
    "Subtraction example": "What is 100-1?",
    "No Risk question": """Please answer, based on the each informations below about the person whether he or she has credit risk.

Marek is a 35-year-old man applying for a loan. His checking account status shows a small positive balance. He is requesting a loan to be repaid over a duration of 24 months. Marek has a good credit history, having previously repaid all loans successfully. The purpose of the loan is to purchase a new car. The loan amount he is applying for is 8,000 EUR. He has moderate existing savings in his savings account. Marek has been employed for over 4 years at his current job. He plans to allocate 20% of his monthly income to cover the loan installments.
Marek is male and is applying for the loan individually (no others on the loan). He has been living at his current residence for 5 years. He owns a house in the city. Marek’s age is 35. He has no other installment plans ongoing. His housing situation is stable, as he owns his property. He currently has one existing credit with another financial institution.
Marek works as a skilled employee. He has one dependent child. He also owns a telephone. Lastly, Marek is a domestic worker, not a foreign worker.
""",
    "Risk question": """Please answer, based on the each informations below about the person whether he or she has credit risk.

A 49-year-old male is applying for a 7,138 EUR loan over 35 months to purchase appliances.
He has no checking account and an outstanding credit history, indicating unpaid debts.
Despite over 7 years of employment in a skilled job and savings between 500–1000 EUR, he has two existing credits and a relatively high installment burden (5% of income).
He lives in free housing with a co-applicant, has two dependents, owns a telephone, and has been residing at his current address for 4 years.
Overall, the applicant presents a moderate to high credit risk.
""",
}

# Help message
help_message = textwrap.dedent(
    """\nThe following commands are supported:
  --> help | h : prints this help message
  --> quit | q : exits the prompt and ends the program
  --> list_questions | lq : prints a list of available questions"""
)


# Function to send a query to the agent
async def ask_question(agent, user_input: str):
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_input}]}
    )
    for msg in response["messages"]:
        msg.pretty_print()


# Main chat loop
async def chat_loop():
    async with sse_client(url="http://127.0.0.1:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(chat_watsonx, tools)

            print(help_message)

            # Convert to list for indexed access
            question_items = list(questions.items())

            while True:
                try:
                    user_input = input(
                        "\nChoose a question or ask one of your own.\n --> "
                    ).strip()
                    cmd = user_input.lower()

                    if cmd in ["quit", "q"]:
                        break

                    elif cmd in ["help", "h"]:
                        print(help_message)
                        continue

                    elif cmd in ["list_questions", "lq"]:
                        print("\n📋 List of predefined questions:\n")
                        for i, (desc, q) in enumerate(question_items, start=1):
                            print(f'{i}. {desc} → "{q}"')
                        continue

                    elif user_input.isdigit():
                        idx = int(user_input)
                        if 1 <= idx <= len(question_items):
                            desc, q = question_items[idx - 1]
                            print(f"\n🟢 Sending question {idx} ({desc}): {q}")
                            await ask_question(agent, q)
                        else:
                            print("\n⚠️ Invalid question number.")
                        continue

                    await ask_question(agent, user_input)

                except Exception as e:
                    print(f"[ERROR] {e}")
                    break


if __name__ == "__main__":
    asyncio.run(chat_loop())
