def get_prompt(prompt: str, mode: str = None, model: str = "o3-mini-high"):
    is_select = True if mode else False
    last =  "push enter key to send the prompt"
    callGPT_prompt = f"""
    Your job is to run a chatGPT on behalf of the user and interact with them.

    Here are the specific steps:
    1. input below prompt in the text box
       -prompt: {prompt}
    2.{f" find `Deep search` and `Search` button in text box and click on {mode}" if is_select else last}
    {f"3. {last}" if is_select else "3. your task is end! thanks!!"}
    {f"4. your task is end! thanks!!" if is_select else ""}
    """
    print(callGPT_prompt)
    return callGPT_prompt


if __name__ == "__main__":
    prompt = "What is the capital of France?"
    print(get_prompt(prompt, mode="search", model="o1-pro"))
    print(get_prompt(prompt, model="o1-pro", mode=""))
    print(get_prompt(prompt, mode="search"))
    print