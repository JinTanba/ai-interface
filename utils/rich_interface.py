from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint
import asyncio
import sys
import inquirer

# 文字エンコーディングをUTF-8に設定（入力文字の多言語対応用）
sys.stdin.reconfigure(encoding='utf-8')
console = Console()

def ask_question(prompt_text: str) -> str:
    """リッチなプロンプトで質問を表示し、ユーザーからの入力を受け付けます"""
    return Prompt.ask(f"[bold cyan]{prompt_text}[/bold cyan]", console=console)

def get_model_and_mode(current_model: str = None) -> tuple[str, str]:
    """モデルとモードの選択を受け付けます"""
    model_choices = [
        ("o1", "o1"),
        ("o3-mini-high", "o3-mini-high"),
        ("o3", "o3")
    ]
    
    if current_model:
        model_choices.insert(0, (f"現在のモデルを維持（{current_model}）", current_model))
    
    mode_choices = [
        ("None", "None"),
        ("Deep search", "Deep search"),
        ("Search", "Search")
    ]
    
    questions = [
        inquirer.List('model',
                     message="Select model",
                     choices=[name for name, _ in model_choices]),
        inquirer.List('mode',
                     message="Select mode",
                     choices=[name for name, _ in mode_choices])
    ]
    
    answers = inquirer.prompt(questions)
    
    # 選択された値に対応するコードを取得
    model_code = next(code for name, code in model_choices if name == answers['model'])
    mode_code = next(code for name, code in mode_choices if name == answers['mode'])
    
    return model_code, mode_code

async def display_loading(text: str):
    """ローディング表示を行います"""
    with Progress(console=console) as progress:
        task = progress.add_task(f"[cyan]{text}", total=None)
        while True:
            await asyncio.sleep(0.1)
            progress.update(task, advance=0.1)

def display_response(text: str):
    """応答をパネル形式で表示します"""
    console.print(Panel(text, border_style="green"))

class StatusContext:
    """非同期コンテキストマネージャーとしてステータス表示を管理します"""
    def __init__(self, message: str):
        self.message = message
        self.console = console
        self.status = None

    async def __aenter__(self):
        self.status = self.console.status(f"[bold green]{self.message}[/bold green]")
        self.status.__enter__()
        return self.status

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.status:
            self.status.__exit__(exc_type, exc_val, exc_tb)