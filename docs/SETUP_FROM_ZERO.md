# Setup From Zero

**For everyone, before you open your own section.**

This assumes you have never written code, never used a terminal, and have never
touched git. If that's you, you're in the right place and nothing here is
obvious. If you've done some of this before, skim and skip ahead.

Set aside 60–90 minutes. Do it in one sitting if you can. **Getting stuck here
is normal and is not a sign of anything** — installing developer tools is
genuinely the worst part of programming, and it gets much better right after.

---

## Part 0: What these things even are

Five tools. Here's what each one is for, in plain terms.

| Tool | What it actually is |
|---|---|
| **Python** | The language our project is written in. Installing it gives your computer the ability to run our code. |
| **VS Code** | A text editor built for code. Like Word, but for programs. It also has a terminal built into it, which saves you learning a separate app. |
| **Terminal** | A window where you type commands instead of clicking buttons. It's how you tell the computer to run things. |
| **git** | Tracks every change to the code and lets five people work on it without overwriting each other. |
| **GitHub** | A website that stores the shared copy of our code. git is the tool, GitHub is the place. |

**A folder is a folder.** Our project is a folder on your computer with files
in it. The terminal is just a way of moving around folders by typing instead of
double-clicking. That's the whole idea.

---

## Part 1: Install Python

### On a Mac

Your Mac already has an old Python, but we need a current one.

1. Go to **python.org/downloads**
2. Click the big yellow button (it detects your Mac automatically)
3. Open the downloaded `.pkg` file and click through the installer
4. **Restart your computer.** Skipping this causes a confusing error later.

### On Windows

1. Go to **python.org/downloads**
2. Click the big yellow button
3. Run the downloaded `.exe`
4. **On the very first screen, check the box that says "Add python.exe to
   PATH".** It's at the bottom and easy to miss. If you don't check it, your
   computer won't be able to find Python and nothing else in this guide will
   work. If you already installed without it, run the installer again and
   choose Modify.
5. Then click Install Now
6. **Restart your computer.**

---

## Part 2: Install VS Code

1. Go to **code.visualstudio.com**
2. Download and install it
3. Open it. You'll see a mostly empty window with a sidebar. That's correct.

**Install the Python extension** (this gives you helpful colors and error
underlines):

1. Click the icon in the left sidebar that looks like four squares (Extensions)
2. Type `Python` in the search box
3. Install the first result, the one published by Microsoft

---

## Part 3: Open a terminal and find out where you are

This is the part that feels alien. It gets familiar fast.

In VS Code, press **Ctrl + `** (that's the backtick key, above Tab, left of the
1 key). Or use the menu: **Terminal → New Terminal**.

A panel opens at the bottom with some text and a blinking cursor. That's your
terminal. You type a command, press Enter, and it does something.

**Try three commands.** Type each one, press Enter, look at what comes back.

```
pwd
```

"Print working directory." It shows which folder you're currently standing in.
On Windows use `cd` by itself instead of `pwd`.

```
ls
```

"List." It shows the files and folders where you're standing. On Windows, use
`dir` instead.

```
cd Desktop
```

"Change directory." It moves you into a folder named Desktop. Now run `pwd`
again and you'll see you moved.

```
cd ..
```

Two dots means "go up one folder," back to where you were.

**That's the entire terminal skill you need for this project.** Where am I
(`pwd`), what's here (`ls`), move somewhere (`cd`). Everything else you'll be
copy-pasting.

---

## Part 4: Check Python is installed

In the terminal:

**Mac:**
```
python3 --version
```

**Windows:**
```
python --version
```

You should see something like `Python 3.12.4`. Any version starting with 3.11,
3.12, or 3.13 is fine.

> **Important for the rest of this project:** on Mac you type `python3` and
> `pip3`. On Windows you type `python` and `pip`. Our guides are written with
> `python` and `pip`. **Mac users: add the 3 every time.** This one difference
> causes more confusion than anything else on this list.

If you get "command not found" or "not recognized," Python either didn't
install or you skipped the restart. Restart first, then try again. If it still
fails on Windows, you almost certainly missed the "Add to PATH" checkbox.

---

## Part 5: Check git

```
git --version
```

**Mac:** if git isn't there, a popup appears offering to install developer
tools. Click Install and wait. That's the easiest path.

**Windows:** if it's missing, go to **git-scm.com/downloads**, install it, and
accept every default. Then close VS Code completely and reopen it, or the
terminal won't see git yet.

Then tell git who you are. Use your real name and the email on your GitHub
account:

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

This is what puts your name on your commits. Do it once, never again.

---

## Part 6: Get the project onto your computer

**Decide where it goes first.** Your Desktop is fine and easy to find.

```
cd Desktop
```

Now copy the project down from GitHub. Enrique will post the exact URL — use
his, not this placeholder:

```
git clone https://github.com/<enrique>/northstar-triage.git
```

You'll see a few lines about counting and unpacking objects. When it finishes,
there's a new folder on your Desktop called `northstar-triage`.

Move into it:

```
cd northstar-triage
```

**Every command for the rest of this project gets run from inside this
folder.** If a command fails with "file not found," the first thing to check is
whether you're standing in the right place. Run `pwd` and look.

**Open the project properly in VS Code:** File → Open Folder → pick
`northstar-triage`. The sidebar now shows all our files. Click any of them to
read it. Reopen the terminal (Ctrl + `) and notice it already starts you inside
the project folder. That's why we open the folder rather than individual files.

---

## Part 7: Install what the project needs

Our project uses a few libraries other people wrote. This downloads them:

**Mac:**
```
pip3 install -r requirements.txt
```

**Windows:**
```
pip install -r requirements.txt
```

You'll see a wall of scrolling text. That's normal. It ends with something like
`Successfully installed langchain-openai-1.5.1 ...`.

If you get a permissions error or a message about an "externally managed
environment," add this to the end and run it again:

```
--break-system-packages
```

---

## Part 8: Run it

The moment of truth:

**Mac:**
```
python3 main.py --mock
```

**Windows:**
```
python main.py --mock
```

You should see 12 tickets scroll past, each labeled AUTO or HUMAN, then a
summary with an automation rate.

**If you see that, you are fully set up.** Everything from here is editing text
files and re-running that command.

`--mock` means "use fake responses instead of calling the real AI." It's free,
instant, and needs no key. Use it constantly.

---

## Part 9: Your practice commit (do this before any real work)

You're going to make one tiny change and push it through the entire git
workflow. Nothing here can break anything. The point is to have already done it
once before it matters.

**Step 1 — make your own branch.** Replace `yourname`:

```
git checkout -b yourname/practice
```

You should see `Switched to a new branch 'yourname/practice'`. A branch is your
own private copy of the project. Nothing you do here affects anyone else until
it gets merged.

**Step 2 — make a change.** In the VS Code sidebar, click `TEAM.md`. Find your
name and fill in the blank next to it. One sentence, anything you like.

**Step 3 — save.** Ctrl+S (Cmd+S on Mac). VS Code does not auto-save.
Unsaved files are a classic source of "why isn't my change working."

**Step 4 — see what git noticed:**

```
git status
```

It should list `TEAM.md` under "modified." git is watching every file and it
noticed you touched that one.

**Step 5 — stage and commit:**

```
git add TEAM.md
git commit -m "Add my line to TEAM.md"
```

`add` means "include this in what I'm about to save." `commit` means "save it,
with a note about what I did."

**Step 6 — push it to GitHub:**

```
git push -u origin yourname/practice
```

The `-u origin yourname/practice` part is only needed the first time you push a
new branch. After that, plain `git push` works.

**Step 7 — open a pull request.** Go to the repo on github.com. A yellow banner
appears near the top: *"yourname/practice had recent pushes."* Click **Compare &
pull request**, then **Create pull request**. Then tell the group chat.

That's it. That's the entire workflow you'll use for every piece of real work.
You just did the scary part with nothing at stake.

**Step 8 — go back to main and get everyone's changes:**

```
git checkout main
git pull
```

Do this every single time before starting new work.

---

## Part 10: Your rhythm from now on

Every time you sit down to work:

```
git checkout main
git pull
git checkout -b yourname/what-im-doing
```

...do your work, then:

```
git add .
git commit -m "what I did"
git push -u origin yourname/what-im-doing
```

...then open the pull request on github.com and tell the chat.

Print this. Tape it to your monitor. You'll internalize it in about a week.

---

## Errors you will hit, and what they mean

**`command not found: python3`** / **`'python' is not recognized`**
Python isn't installed, or you skipped the restart, or (Windows) you missed the
"Add to PATH" checkbox. Restart first.

**`No such file or directory: main.py`**
You're standing in the wrong folder. Run `pwd` (Mac) or `cd` (Windows). You need
to be inside `northstar-triage`.

**`ModuleNotFoundError: No module named 'pydantic'`**
Part 7 didn't finish. Run the `pip install -r requirements.txt` line again and
read the end of the output for an error.

**`fatal: not a git repository`**
Same problem as above — you're outside the project folder. `cd` into it.

**`error: pathspec 'main' did not match`**
You typo'd a branch name. Run `git branch` to see the branches that exist.

**`Permission denied (publickey)`** or a login prompt on push
GitHub needs to know it's you. The simplest fix is installing **GitHub
Desktop**, signing in there once, and letting it handle credentials for you.
Then your terminal pushes will work.

**`Your branch is behind 'origin/main'`**
Someone merged something since you last pulled. Run `git pull`.

**Nothing happens when I run the file**
Check you saved (Ctrl+S). VS Code shows a filled dot in the file's tab when
there are unsaved changes.

---

## When you're stuck

Post in the group chat with all three of these:

1. What you were trying to do
2. The **exact command** you typed
3. The **entire** error message, copy-pasted, not just the last line

The lines above the final error usually name the file and line number, which is
where the actual answer is. A screenshot of the whole terminal is fine too.

Nobody on this team has done this before. Asking after fifteen minutes of being
stuck is the correct move, not a last resort.
