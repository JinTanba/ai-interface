import logging
import pprint

# Disable all logging messages with severity 'CRITICAL' and below
logging.disable(logging.CRITICAL)
import asyncio
import questionary
from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
from browser_use.browser.context import BrowserContext
from prompts.callGPT import get_prompt
from utils.rich_interface import ask_question
from playwright.async_api import Page
from utils.utils import pprint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompts.tranlate import tranlate_prompt

# ====【追加でインポートする】====
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

# Define your available options
MODELS = ["gpt-4o", "o1", "o1-pro", "o3-mini-high"]
MODES = ["usual","Search", "Deep Search"]

tranlate_chain = PromptTemplate(template=tranlate_prompt, input_variables=["text"]) \
    | ChatOpenAI(model="gpt-4o") \
    | StrOutputParser()

async def get_model_and_mode():
    """
    Asks the user to select a model and mode using pull-down menus
    navigable via the arrow keys.
    """
    chosen_model = await questionary.select(
        "Select a Model:",
        choices=MODELS
    ).ask_async()

    chosen_mode = await questionary.select(
        "Select a Mode:",
        choices=MODES
    ).ask_async()

    return chosen_model, chosen_mode

async def wait_for_res(page: Page, prev_ans: str):
    """
    Wait for the conversation element to stabilize on the page
    and return its final text, streaming the output in a style similar
    to `code2` once it's certain the answer is final.
    """

    same_count = 0
    last_text = ""

    while True:
        text = await page.locator('.group\\/conversation-turn').last.inner_text()
        # テキストが存在し、かつ前回の最終テキストと違うならチェック
        if text and text != prev_ans:
            # もし今回の text が前回チェックした last_text と同じなら「安定カウント」を増やす
            if text == last_text:
                same_count += 1
                # 一定回数以上同じ => 「これが最終版」とみなす
                if same_count >= 10:
                    # ====【ここで code2 に近い形のストリーミング出力】====
                    console = Console()
                    text_so_far = ""

                    # Liveコンテキストで継ぎ足しながら表示
                    with Live(console=console, refresh_per_second=4) as live:
                        # tranlate_chain をストリーム実行して翻訳結果を段階的に取得
                        for chunk in tranlate_chain.stream({"text": text}):
                            text_so_far += chunk
                            live.update(Markdown(text_so_far))

                    # ストリーミング完了後の最終テキスト表示
                    console.print(
                        "\n[bold green]Streaming complete! Here's the final text:[/bold green]\n"
                    )
                    console.print(Markdown(text_so_far))

                    return text
            else:
                # テキストが新しくなったらカウントをリセットし、last_text を更新
                same_count = 1
                last_text = text

        await asyncio.sleep(0.5)

async def callGPT(
    agent_cls,
    llm,
    context: BrowserContext,
    model: str,
    mode: str,
    prev_ans: str = ""
):
    """
    - Wait for user input
    - If 'c', change model/mode on the fly
    - Return the answer plus any updated model/mode/llm
    """
    prompt = ask_question("\nEnter your question: ")
    
    # Handle user quitting
    if prompt == "q":
        print("Exiting...")
        exit()

    # Handle user changing model/mode
    if prompt == "c":
        new_model, new_mode = await get_model_and_mode()
        # Update the ChatOpenAI object to use the new model
        model = new_model
        mode = new_mode
        page = await context.get_current_page()
        await page.goto(f"https://chatgpt.com/?model={model}")

        # Now ask for an actual prompt to send with the new model
        prompt = ask_question("\nEnter your question with the new settings: ")
        if prompt == "q":
            print("Exiting...")
            exit()

    # 翻訳チェーンで prompt を翻訳
    tranlated_prompt = tranlate_chain.invoke({"text": prompt})
    if "<translation>" in tranlated_prompt:
        extract_text_in_tag = tranlated_prompt.split("<translation>")[1].split("</translation>")[0]

    # Create the agent object and run it with the user prompt
    agent = agent_cls(
        task=get_prompt(prompt=extract_text_in_tag, model=model, mode=mode if mode != "usual" else ""),
        llm=llm,
        browser_context=context
    )
    print(f"you---->{model}")
    print(prompt)
    print(f"tranlated_prompt---->{extract_text_in_tag}")
    await agent.run()

    # wait_for_res 内で最終的な翻訳結果をストリーミング出力
    ans = await wait_for_res(await context.get_current_page(), prev_ans)
    return ans, model, mode, llm

async def main():
    # Create an LLM and Browser
    llm = ChatOpenAI(model="gpt-4o")
    browser_config = BrowserConfig(
        chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )
    browser = Browser(config=browser_config)
    
    # Prompt the user initially for model/mode
    selected_model, selected_mode = await get_model_and_mode()

    async with await browser.new_context() as context:
        prev_ans = ""
        page = await context.get_current_page()
        await page.goto(f"https://chatgpt.com/?model={selected_model}")
        
        while True:
            # Call GPT and check for any updates to model, mode, or llm
            ans, selected_model, selected_mode, llm = await callGPT(
                agent_cls=Agent,
                llm=llm,
                context=context,
                model=selected_model,
                mode=selected_mode,
                prev_ans=prev_ans
            )
            # Update prev_ans for the next iteration
            prev_ans = ans

        # Close the browser after finishing
    await context.browser.close()

if __name__ == "__main__":
    asyncio.run(main())
