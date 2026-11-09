
import time
import asyncio

from textual.app import App, ComposeResult
from textual import work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Input, Static
from rich.text import Text


class OpenHarnessTUI(App):

    TITLE = "OPENHARNESS 0.5"
    SUB_TITLE = "Autonomous AI Harness"

    CSS = """
        Screen {
            background: #101116;
        }

        Header {
            background: #191b23;
            color: #e5a45b;
        }

        Footer {
            background: #191b23;
        }

        #main {
            height: 1fr;
        }

        #sidebar {
            width: 28;
            background: #171920;
            border-right: solid #30333d;
            padding: 1;
        }

        #brand {
            color: #e5a45b;
            text-style: bold;
            margin-bottom: 2;
        }

        .section {
            color: #777f91;
            text-style: bold;
            margin-top: 1;
            margin-bottom: 1;
        }

        .item {
            color: #c4c6ce;
            padding-left: 1;
        }

        #content {
            width: 1fr;
            height: 1fr;
        }

        #chat-area {
            height: 1fr;
            padding: 1 3;
            background: #101116;
        }

        #conversation {
            height: 1fr;
            padding: 1;
            background: #101116;
            scrollbar-color: #555b69;
        }

        .message {
            width: 1fr;
            height: auto;
            margin-bottom: 1;
            padding: 0 1;
        }

        .message-content {
            width: 1fr;
            height: auto;
            color: #d5d7df;
        }

        #bottom {
            height: auto;
            background: #171920;
            border-top: solid #30333d;
            padding: 1 2;
        }

        #status {
            height: 1;
            color: #e5a45b;
            margin-bottom: 1;
        }

        #prompt {
            background: #20232b;
            color: white;
            border: tall #444956;
        }

        #prompt:focus {
            border: tall #d99a52;
        }

        #hint {
            color: #777f91;
            height: 1;
            margin-top: 1;
        }
    """

    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "Sidebar"),
        ("ctrl+l", "clear_screen", "Clear"),
        ("ctrl+q", "quit", "Quit"),
    ]

    SPINNER = ["◐", "◓", "◑", "◒"]

    def __init__(self, agent, messages):
        super().__init__()

        self.agent = agent
        self.messages = messages

        self.busy = False
        self.sidebar_visible = True

        self.spinner_index = 0
        self.started_at = 0
        self.current_activity = "Ready"

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main"):

            # Sidebar
            with Vertical(id="sidebar"):
                yield Static("◆ OPENHARNESS", id="brand")

                yield Static("SESSION", classes="section")
                yield Static("● Current session", classes="item")
            # Main content
            with Vertical(id="content"):

                with Vertical(id="chat-area"):
                    yield VerticalScroll(id="conversation")

                with Vertical(id="bottom"):
                    yield Static("● Ready", id="status")

                    yield Input(
                        placeholder="Ask OpenHarness anything...",
                        id="prompt"
                    )

                    yield Static(
                        "Enter: Send  ·  Ctrl+B: Sidebar  ·  Ctrl+L: Clear",
                        id="hint"
                    )

        yield Footer()

    async def on_mount(self):
        self.query_one("#prompt", Input).focus()

        self.set_interval(0.12, self.animate_status)
        self.set_interval(1, self.update_elapsed)

        await self.write_message(
            "OpenHarness",
            "Welcome! Your AI development assistant is ready."
        )

    def animate_status(self):
        if not self.busy:
            return

        self.spinner_index = (
            self.spinner_index + 1
        ) % len(self.SPINNER)

        spinner = self.SPINNER[self.spinner_index]

        elapsed = int(time.monotonic() - self.started_at)

        self.query_one("#status", Static).update(
            f"[bold #e5a45b]{spinner}[/bold #e5a45b] "
            f"{self.current_activity} "
            f"[dim]({elapsed}s)[/dim]"
        )

    def update_elapsed(self):
        if self.busy:
            elapsed = int(time.monotonic() - self.started_at)

            self.query_one("#hint", Static).update(
                f"OpenHarness is working... {elapsed}s elapsed"
            )

    async def on_input_submitted(self, event: Input.Submitted):
        prompt = event.value.strip()

        if not prompt or self.busy:
            return

        event.input.value = ""

        if prompt == "/exit":
            self.exit()
            return

        if prompt == "/clear":
            self.action_clear_screen()
            return

        if prompt == "/help":
            await self.write_message(
                "System",
                "Commands: `/help`, `/clear`, `/exit`"
            )
            return

        await self.write_message("You", prompt)

        self.run_agent(prompt)

    @work(exclusive=True, group="agent")
    async def run_agent(self, prompt: str):
        self.busy = True
        self.started_at = time.monotonic()
        self.current_activity = "Thinking"

        input_widget = self.query_one("#prompt", Input)
        input_widget.disabled = True

        try:
            response = await self.agent(
                prompt,
                self.messages
            )

            await self.typewriter(
                response or "(No response)",
                speed=0.01
            )

            self.query_one("#status", Static).update(
                "[bold green]● Ready[/bold green]"
            )

        except Exception as error:
            await self.write_message("Error", str(error))

            self.query_one("#status", Static).update(
                "[bold red]● Error[/bold red]"
            )

        finally:
            self.busy = False

            input_widget.disabled = False
            input_widget.focus()

            self.query_one("#hint", Static).update(
                "Enter: Send  ·  Ctrl+B: Sidebar  ·  Ctrl+L: Clear"
            )

    async def write_message(self, sender: str, content: str):
        conversation = self.query_one(
            "#conversation",
            VerticalScroll
        )

        if sender == "You":
            color = "#79b8ff"
        elif sender == "Error":
            color = "#ff6b6b"
        else:
            color = "#e5a45b"

        message = Vertical(classes="message")

        await conversation.mount(message)

        await message.mount(
            Static(
                f"[bold {color}]{sender}[/bold {color}]",
                markup=True
            )
        )

        if content:
            await message.mount(
                Static(
                    content,
                    classes="message-content",
                    markup=False
                )
            )

        conversation.scroll_end(animate=False)

    async def typewriter(self, text, speed=0.01):
        if not text:
            return

        conversation = self.query_one(
            "#conversation",
            VerticalScroll
        )

        # Create the assistant message in the conversation.
        message = Vertical(classes="message")

        await conversation.mount(message)

        await message.mount(
            Static(
                "[bold #e5a45b]OpenHarness[/bold #e5a45b]",
                markup=True
            )
        )

        # This widget is updated in place as text arrives.
        output = Static(
            "",
            classes="message-content",
            markup=False
        )

        await message.mount(output)

        current = Text()

        for char in text:
            current.append(char)
            output.update(current)

            conversation.scroll_end(animate=False)

            await asyncio.sleep(speed)

    def action_toggle_sidebar(self):
        sidebar = self.query_one("#sidebar")

        self.sidebar_visible = not self.sidebar_visible

        sidebar.styles.display = (
            "block" if self.sidebar_visible else "none"
        )

    def action_clear_screen(self):
        conversation = self.query_one(
            "#conversation",
            VerticalScroll
        )

        conversation.remove_children()

        # Preserve the system message.
        self.messages[:] = self.messages[:1]

        self.write_message(
            "System",
            "Conversation cleared."
        )

        self.add_activity("Conversation cleared")

    def add_activity(self, message: str):
        activity = self.query_one("#activity", Static)
        activity.update(message)
