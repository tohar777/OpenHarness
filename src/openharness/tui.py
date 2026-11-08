
import time

from textual.app import App, ComposeResult
from textual import work
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, RichLog, Static
from rich.markdown import Markdown


class OpenHarnessTUI(App):

    TITLE = "OPENHARNESS"
    SUB_TITLE = "Autonomous AI Agent"

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

    #activity {
        height: 1fr;
        background: #171920;
        color: #aeb4c2;
        scrollbar-size: 1 1;
    }

    #content {
        width: 1fr;
        height: 1fr;
    }

    #conversation {
        height: 1fr;
        padding: 1 3;
        background: #101116;
        scrollbar-color: #555b69;
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

            with Vertical(id="sidebar"):
                yield Static("◆ OPENHARNESS", id="brand")

                yield Static("SESSION", classes="section")
                yield Static("● Current session", classes="item")

                yield Static("AGENT", classes="section")
                yield Static("◈ OpenRouter", classes="item")
                yield Static("◈ Tool calling", classes="item")

                yield Static("CAPABILITIES", classes="section")
                yield Static("◈ Web search", classes="item")
                yield Static("◈ Web fetch", classes="item")
                yield Static("◈ Filesystem", classes="item")
                yield Static("◈ MCP", classes="item")

                yield Static("ACTIVITY", classes="section")
                yield RichLog(
                    id="activity",
                    wrap=True,
                    markup=True,
                    highlight=True
                )

            with Vertical(id="content"):
                yield RichLog(
                    id="conversation",
                    wrap=True,
                    highlight=True,
                    markup=True
                )

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

    def on_mount(self):
        self.query_one("#prompt", Input).focus()

        self.set_interval(0.12, self.animate_status)
        self.set_interval(1, self.update_elapsed)

        self.write_message(
            "OpenHarness",
            "Welcome! Your AI development assistant is ready."
        )

        self.add_activity("System initialized")
        self.add_activity("Waiting for instructions")

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

    def add_activity(self, message: str):
        log = self.query_one("#activity", RichLog)

        timestamp = time.strftime("%H:%M:%S")

        log.write(
            f"[dim]{timestamp}[/dim] [#e5a45b]›[/#e5a45b] {message}"
        )

    def set_activity(self, message: str):
        self.current_activity = message
        self.add_activity(message)

    def on_input_submitted(self, event: Input.Submitted):
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
            self.write_message(
                "System",
                "Commands: `/help`, `/clear`, `/exit`"
            )
            return

        self.write_message("You", prompt)
        self.set_activity("New request received")

        self.run_agent(prompt)

    @work(exclusive=True, group="agent")
    async def run_agent(self, prompt: str):
        self.busy = True
        self.started_at = time.monotonic()
        self.current_activity = "Thinking"

        input_widget = self.query_one("#prompt", Input)
        input_widget.disabled = True

        self.set_activity("Agent started")

        try:
            response = await self.agent(prompt, self.messages)

            self.write_message(
                "OpenHarness",
                response or "(No response)"
            )

            self.set_activity("Response completed")
            self.query_one("#status", Static).update(
                "[bold green]● Ready[/bold green]"
            )

        except Exception as error:
            self.write_message("Error", str(error))
            self.set_activity(f"Error: {error}")

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

    def write_message(self, sender: str, content: str):
        log = self.query_one("#conversation", RichLog)

        log.write("")

        if sender == "You":
            color = "#79b8ff"
        elif sender == "Error":
            color = "#ff6b6b"
        else:
            color = "#e5a45b"

        log.write(f"[bold {color}]{sender}[/bold {color}]")
        log.write(Markdown(str(content)))
        log.write("")

    def action_toggle_sidebar(self):
        sidebar = self.query_one("#sidebar")

        self.sidebar_visible = not self.sidebar_visible

        sidebar.styles.display = (
            "block" if self.sidebar_visible else "none"
        )

    def action_clear_screen(self):
        self.query_one("#conversation", RichLog).clear()

        self.messages[:] = self.messages[:1]

        self.write_message(
            "System",
            "Conversation cleared."
        )

        self.add_activity("Conversation cleared")
