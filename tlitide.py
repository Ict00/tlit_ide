import threading
import time
import textual.widgets.text_area
from textual import on
from textual.app import App, ComposeResult, AutopilotCallbackType, ReturnType
from textual.widgets import TextArea, Header, Footer, DirectoryTree, Input
from textual.containers import Grid, Container
from textual.screen import *
from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.reactive import var
from rich.style import Style
from textual.widgets.text_area import TextAreaTheme
import os, sys

lit_theme = TextAreaTheme(
    name="lit_theme",

    cursor_style=Style(color="white", bgcolor="blue"),
    cursor_line_style=Style(bgcolor="black"),

    syntax_styles={
        "string": Style(color="green"),
        "number": Style(color="magenta"),
        "operator": Style(color="blue_violet"),
        "variable": Style(color="light_steel_blue"),
    }
)

tglyph_theme = TextAreaTheme(
    name="tglyph_theme",

    cursor_style=Style(color="white", bgcolor="blue"),
    cursor_line_style=Style(bgcolor="black"),

    syntax_styles={
        "string": Style(color="orange3"),
        "number": Style(color="dark_slate_gray2"),
        "operator": Style(color="green"),
        "variable": Style(color="green"),
        "keyword": Style(color="green"),
        "comment": Style(color="slate_blue3")
    }
)


CODES = {
    "new.tgl": open("new.tgl", "r").read() if os.path.isfile("new.tgl") else "NOTHING"
}

CURRENT = "new.tgl"


class NewFileScreen(Screen):
    BINDINGS = [
        ("escape", "quit_without")
    ]
    CSS = \
"""
NewFileScreen {
    align: center middle;
    background: rgba(0,0,0,0);
}

#newfile
{
    border: thick $panel-lighten-1;
    background: $panel;
    padding: 0 1;
    align: center middle;
    layout: grid;
    grid-gutter: 1 2;
    grid-rows: 1fr 3;
    grid-size: 1 2;
    width: 30%;
    height: 15%;
}

#file-c-label
{
    text-align: center;
    align: center top;
    dock: top;
}

#file-input 
{
    align-horizontal: center;
    text-align: center;
    dock: bottom;
}
"""

    def compose(self) -> ComposeResult:
        with Container(id="newfile"):
            yield textual.widgets.Label("Create a new file", id="file-c-label")
            yield textual.widgets.Input(placeholder="main.tgl", id="file-input")

    def action_quit_without(self):
        self.app.pop_screen()

    @on(Input.Submitted, "#file-input")
    def inp(self, _inp: Input):
        global CURRENT, CODES
        try:
            open(_inp.value, "x").close()
            CURRENT = _inp.value
            CODES[CURRENT] = ""
        except:
            pass
        self.app.pop_screen()
        self.app.exit(4)


class TLitIDE(App):
    CSS = \
"""
Screen {
    layout: grid;
    background: $surface-darken-1;
    &:inline {
        height: 50vh;
    }
}

#tree-view {
    display: block;
    scrollbar-gutter: stable;
    overflow: auto;
    width: auto;
    height: 100%;
    dock: left;
}

CodeBrowser.-show-tree #tree-view {
    display: block;
    max-width: 50%;
}

#code {
    width: 100%;
    border: none;
}

#helper {
    width: 40%;
    border: none;
    dock: right;
}

#file-creator 
{
    layout: grid;
    grid-size: 1 2;
    width: 40%;
    height: 15vh;
    border: none;
    align: center bottom;
    dock: bottom;
}


"""
    BINDINGS = [
        ("f6", "run_paint", "Open Paint"),
        ("f5", "start_app", "Build & Start"),
        ("f4", "code_helper", "Call for help"),
        ("f3", "open_term", "Open terminal"),
        ("f2", "copy_cl", "Copy code to clipboard"),
        ("ctrl+s", "save_all", "Save all"),
        ("ctrl+n", "new_file", "Create new file"),
        ("q", "smart_quit", "Quit App"),
    ]

    def compose(self) -> ComposeResult:
        global lit_theme, CODES, CURRENT
        text = TextArea.code_editor(CODES[CURRENT], id="code", language="python", theme="vscode_dark")
        text.register_theme(lit_theme)
        text.register_theme(tglyph_theme)
        if os.path.splitext(CURRENT)[1] == ".tgl":
            text.theme = "tglyph_theme"
        else:
            text.theme = "lit_theme"

        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        yield Header(id="header")
        with Grid(id="main-container"):
            yield DirectoryTree(path, id="tree-view")
            yield text
        yield Footer()
        self.sub_title = CURRENT

    def action_run_paint(self):
        def paint():
            if os.name == 'nt':
                os.system("mspaint")
            else:
                if os.path.isfile("/usr/bin/krita"):
                    os.system("krita")
                else:
                    os.system("krita")

        threading.Thread(target=paint).start()

    def on_directory_tree_file_selected(
            self, event: DirectoryTree.FileSelected
    ) -> None:
        global CODES, CURRENT
        """Called when the user click a file in the directory tree."""
        event.stop()
        CODES[CURRENT] = self.query_one("#code", TextArea).text
        path = str(event.path)
        code = open(path, "r").read()

        if not CODES.__contains__(path):
            CODES[path] = code
        CURRENT = path
        self.query_one("#code", TextArea).text = CODES[CURRENT]
        if os.path.splitext(path)[1] == ".tgl":
            self.query_one("#code", TextArea).theme = "tglyph_theme"
        else:
            self.query_one("#code", TextArea).theme = "lit_theme"
        self.sub_title = CURRENT

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def action_new_file(self) -> None:
        self.action_save_all()
        self.push_screen(NewFileScreen())

    def action_code_helper(self) -> None:
        try:
            self.query_one("#helper", TextArea).remove()
        except:
            self.mount(TextArea.code_editor("", id="helper", theme="vscode_dark"))

    def action_copy_cl(self) -> None:
        global CODES, CURRENT
        CODES[CURRENT] = self.query_one("#code", TextArea).text
        self.copy_to_clipboard(CODES[CURRENT])

    def action_smart_quit(self) -> None:
        self.action_save_all()
        self.exit(0)

    def action_start_app(self) -> None:
        self.action_save_all()
        if os.path.splitext(CURRENT)[1] == ".tgl":
            self.exit(2)
        else:
            self.exit(1)

    def action_save_all(self) -> None:
        global CODES, CURRENT
        CODES[CURRENT] = self.query_one("#code", TextArea).text
        for i in list[str](CODES.keys()):
            try:
                open(i, "w").write(CODES[i])
            except:
                pass

    def action_open_term(self) -> None:
        self.action_save_all()
        self.exit(3)


if __name__ == "__main__":
    ran = True

    while ran:
        app = TLitIDE()
        res = app.run()
        if res == 0:
            ran = False
        elif res == 3:
            term_ran = True
            print("\x1b[2J\x1b[H", flush=True)
            print("\x1b[1m[!] To exit, enter ':q'.\x1b[0m", flush=True)
            while term_ran:
                inp = input(f"[\x1b[38;5;50m{os.getcwd()}\x1b[0m]\n> \x1b[1m")
                print(end='\x1b[0m', flush=True)
                if inp == ":q":
                    term_ran = False
                try:
                    os.system(inp)
                except:
                    print(f"\x1b[1;38;5;196m| Something went wrong:\x1b[0m\x1b[1m {inp}\x1b[0m")
            pass
        elif res == 2:
            try:
                print("\x1b[2J\x1b[H", end='', flush=True)
                if os.path.isfile("interpreter.py"):
                    os.system(f"python interpreter.py {CURRENT}")
                else:
                    print(f"\x1b[1;38;5;46m|\x1b[0m\x1b[1m No T^ interpreter found\x1b[0m")
            except SystemExit:
                pass
            finally:
                input()
        elif res == 1:
            try:
                print("\x1b[2J\x1b[H", end='', flush=True)
                if os.path.isfile("lit.py"):
                    os.system(f"python lit.py -d {CURRENT}")
                else:
                    print(f"\x1b[1;38;5;202m|\x1b[0m\x1b[1m No Lit compiler found\x1b[0m")
            except SystemExit:
                pass
            finally:
                input()
        elif res == 4:
            pass
        else:
            ran = False
