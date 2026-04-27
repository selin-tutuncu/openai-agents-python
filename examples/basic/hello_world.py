import asyncio
from datetime import datetime
from agents import Agent, Runner, function_tool


@function_tool
def check_time() -> str:
    """Şu anki sistem saatini verir."""
    return datetime.now().strftime("%H:%M")

async def main():

    agent = Agent(
        name="Assistant",
        model="gpt-5-nano",
        instructions="""Normal iletişim kur.Kullanıcı saat sorarsa check_time toolunu kullan.""",
        tools=[check_time],
    )

    result = await Runner.run(agent,"Saat kaç?",)

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())