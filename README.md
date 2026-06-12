<p align = "center" draggable=”false” ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719" 
     width="200px"
     height="auto"/>
</p>


## <h1 align="center" id="heading"> 🧐 The Analyst — AI Engineer Challenge</h1>

## 🛋️ A Vibe-Coded LLM Application

> For additional context on LLM development environments and API key setup, you can also check out our [Interactive Dev Environment for LLM Development](https://github.com/AI-Maker-Space/Interactive-Dev-Environment-for-AI-Engineers).

**The Analyst** is an LLM-powered chat application featuring a stern, sinister continental psychoanalyst who is deeply skeptical of your mental health. Built with a Next.js 14 frontend, a FastAPI + Claude backend grounded in real psychoanalytic source texts via retrieval, and deployed on Vercel as a monorepo.

> *"Sit. Do not touch anything. You are here because something is… wrong."*

The repo walks through building and shipping this kind of application from scratch. Follow the steps below!

Are you ready? The Analyst is waiting. Let's get started!

## 📚 Retrieval: The Analyst Has Actually Read Freud

The Analyst no longer improvises its theory. Every reply is grounded in real psychoanalytic source texts via a tiny hand-rolled RAG layer — no vector database, no LangChain, just numpy and ~2,000 chunks of public-domain Freud and Jung.

### How it works

1. **Corpus (offline, committed).** `scripts/build_index.py` fetches four public-domain texts from Project Gutenberg into `data/texts/` — Freud's *Dream Psychology* (Eder), *Three Contributions to the Theory of Sex* (Brill), *A General Introduction to Psychoanalysis* (Hall), and Jung's *Psychology of the Unconscious* (Hinkle). All pre-1929 translations; the Strachey *Standard Edition* is still under copyright, so it stays out.
2. **Chunk + embed (offline, committed).** Front and back matter — title pages, TOCs, translator boilerplate, indices — is pruned via per-book markers in `BOOKS` (substantive prose like author prefaces stays in). What remains is split by paragraph and packed into ~300–500-token windows with one paragraph of overlap. Each chunk is embedded with OpenAI `text-embedding-3-small` — in token-budgeted batches paced to respect the free-tier 40K tokens-per-minute limit (raise `TPM_LIMIT` in the script if your account allows; the full build takes ~18 min at the free-tier pace) — and written to `api/_index/embeddings.npy` (float16, row-normalized) plus `api/_index/chunks.json` (chunk text + source metadata).
3. **Retrieve (runtime).** Each request embeds *only the latest user message* (one API call — the serverless function never loads model weights), takes the top-4 chunks by cosine similarity (numpy `argpartition` over a flat matrix — sub-millisecond at this corpus size), and injects them into the system prompt as grounding. The persona and the 1–3 sentence format rules stay fully intact. If the index is missing or the embedding call fails, the chat degrades gracefully to ungrounded mode instead of erroring.

### Rebuilding the index

```bash
export OPENAI_API_KEY=sk-...
uv run python scripts/build_index.py
```

Idempotent: already-downloaded texts are reused, and the index is rewritten from scratch. Pass `--chunks-only` to run fetch + chunk without embedding (no key needed).

### Swapping the embedding provider

Same comment-toggle pattern as the chat provider: flip the paired `EMBEDDING PROVIDER` blocks in `scripts/build_index.py` **and** `api/index.py`, swap `openai` for `voyageai` in `api/requirements.txt` and `pyproject.toml`, then rebuild the index. Corpus and query must use the same embedding model — the runtime asserts the dimensions match and refuses to compare apples to oranges (or Freud to mismatched vector spaces).

### Environment variables

| Variable | Needed where | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Vercel + local shell | Chat completions (the Analyst's voice) |
| `OPENAI_API_KEY` | Vercel + local shell | Query embeddings at runtime; corpus embeddings at build time |
| `VOYAGE_API_KEY` | Only if you switch to Voyage | Embeddings, both sides |

<details>
  <summary>🖥️ Accessing "gpt-4.1-mini" (ChatGPT) like a developer</summary>

1. Head to [this notebook](https://colab.research.google.com/drive/1sT7rzY_Lb1_wS0ELI1JJfff0NUEcSD72?usp=sharing) and follow along with the instructions!

2. Complete the notebook and try out your own system/assistant messages!

That's it! Head to the next step and start building your application!

</details>


<details>
  <summary>🏗️ Forking & Cloning This Repository</summary>

Before you begin, make sure you have:

1. 👤 A GitHub account (you'll need to replace `YOUR_GITHUB_USERNAME` with your actual username)
2. 🔧 Git installed on your local machine
3. 💻 A code editor (like Cursor, VS Code, etc.)
4. ⌨️ Terminal access (Mac/Linux) or Command Prompt/PowerShell (Windows)
5. 🔑 A GitHub Personal Access Token (for authentication)

Got everything in place? Let's move on!

1. Fork [this](https://github.com/AI-Maker-Space/The-AI-Engineer-Challenge) repo!

     ![image](https://i.imgur.com/bhjySNh.png)

1. Clone your newly created repo.

     ``` bash
     # First, navigate to where you want the project folder to be created
     cd PATH_TO_DESIRED_PARENT_DIRECTORY

     # Then clone (this will create a new folder called The-AI-Engineer-Challenge)
     git clone git@github.com:<YOUR GITHUB USERNAME>/The-AI-Engineer-Challenge.git
     ```

     > Note: This command uses SSH. If you haven't set up SSH with GitHub, the command will fail. In that case, use HTTPS by replacing `git@github.com:` with `https://github.com/` - you'll then be prompted for your GitHub username and personal access token.

2. Verify your git setup:

     ```bash
     # Check that your remote is set up correctly
     git remote -v

     # Check the status of your repository
     git status

     # See which branch you're on
     git branch
     ```


3. Open the freshly cloned repository inside Cursor!

     ```bash
     cd The-AI-Engineering-Challenge
     cursor .
     ```

4. Check out the existing backend code found in `/api/index.py`

</details>

<details>
  <summary>⚙️ Backend Setup with uv</summary>

1. Install the [`uv`](https://github.com/astral-sh/uv) package manager (`pip install uv`). `uv` will download and manage Python 3.12 for you the first time you run a project command.
2. From the project root, install dependencies with `uv sync`. This creates `.venv/` (and fetches Python 3.12 automatically if needed).
3. Set your OpenAI API key in the shell before running the server, for example `export OPENAI_API_KEY=sk-...`.
4. Start the backend directly from the project root with `uv run uvicorn api.index:app --reload`. The server will run on `http://localhost:8000` with auto-reload enabled for development.
5. Additional backend details live in `api/README.md`.

</details>

<details>
  <summary>🔥Setting Up for Vibe Coding Success </summary>

While it is a bit counter-intuitive to set things up before jumping into vibe-coding - it's important to remember that there exists a gradient betweeen AI-Assisted Development and Vibe-Coding. We're only reaching *slightly* into AI-Assisted Development for this challenge, but it's worth it!

1. Check out the rules in `.cursor/rules/` and add theme-ing information like colour schemes in `frontend-rule.mdc`! You can be as expressive as you'd like in these rules!
2. We're going to index some docs to make our application more likely to succeed. To do this - we're going to start with `CTRL+SHIFT+P` (or `CMD+SHIFT+P` on Mac) and we're going to type "custom doc" into the search bar. 

     ![image](https://i.imgur.com/ILx3hZu.png)
3. We're then going to copy and paste `https://nextjs.org/docs` into the prompt.

     ![image](https://i.imgur.com/psBjpQd.png)

4. We're then going to use the default configs to add these docs to our available and indexed documents.

     ![image](https://i.imgur.com/LULLeaF.png)

5. After that - you will do the same with Vercel's documentation. After which you should see:

     ![image](https://i.imgur.com/hjyXhhC.png) 

</details>

<details>
  <summary>😎 Vibe Coding a Front End for the FastAPI Backend</summary>

1. Use `Command-L` or `CTRL-L` to open the Cursor chat console. 

2. Set the chat settings to the following:

     ![image](https://i.imgur.com/LSgRSgF.png)

3. Ask Cursor to create a frontend for your application. Iterate as much as you like!

4. Run the frontend using the instructions Cursor provided. 

> NOTE: If you run into any errors, copy and paste them back into the Cursor chat window - and ask Cursor to fix them!

> NOTE: You have been provided with a backend in the `/api` folder - please ensure your Front End integrates with it!

</details>

<details>
  <summary>🚀 Deploying Your First LLM-powered Application with Vercel</summary>

1. Ensure you have signed into [Vercel](https://vercel.com/) with your GitHub account.

2. Ensure you have `npm` (this may have been installed in the previous vibe-coding step!) - if you need help with that, ask Cursor!

3. Run the command:

     ```bash
     npm install -g vercel
     ```

4. Run the command:

     ```bash
     vercel
     ```

5. Follow the in-terminal instructions. (Below is an example of what you will see!)

     ![image](https://i.imgur.com/D1iKGCq.png)

6. Once the build is completed - head to the provided link and try out your app!

> NOTE: Remember, if you run into any errors - ask Cursor to help you fix them!

### Vercel Link to Share

You'll want to make sure you share you *domains* hyperlink to ensure people can access your app!

![image](https://i.imgur.com/mpXIgIz.png)

> NOTE: Test this is the public link by trying to open your newly deployed site in an Incognito browser tab!

</details>

<details>
     <summary>🧪 Vibe Check Your LLM App</summary>

### 🤔 What is a Vibe Check?

Now that you’ve built and deployed your first LLM-powered application, it’s time to evaluate it.

In this section, you’ll run a **“vibe check”** — a lightweight, practical way to test how well your application performs across common tasks.

Think of it as a **first pass to catch obvious issues** before deeper evaluation.

> 💡 You will complete this directly in this README. 

---

## 🏗️ Activity #1: General Capability Vibe Check

Run the following prompts through your app.

For each prompt Identify what capability is being tested (e.g., *summarization ability, reasoning, creativity*)

---

**1. Prompt:**  
Explain the concept of object-oriented programming in simple terms to a complete beginner.  
**Aspect Tested:**  Connection; coherence; styling; domain knowledge; affectation and style

**Response:**  
*leans back, pressing fingertips together*

An interesting request. You come to me asking for *simplicity* — but let us examine what lies beneath that.

Object-oriented programming is the practice of organizing code around **objects** — entities that bundle together *data* (what something *is*) and *behavior* (what something *does*).

A dog has attributes — breed, age, weight. A dog also has behaviors — bark, eat, sleep. In object-oriented programming, you construct a **class** — a blueprint — from which individual **objects** are created. Many dogs, one blueprint.

The core mechanisms:

- **Encapsulation** — internal workings are hidden. You press a button; you need not understand the machinery.
- **Inheritance** — a child class adopts properties of the parent. Much like psychological inheritance, yes? Patterns passed down, whether desired or not.
- **Polymorphism** — the same action manifests differently depending on the object. Context shapes expression.

*pauses*

But I find myself more curious about *why* you frame this as needing simplicity. The beginner who fears complexity often fears being seen as incapable.

What is it about technical knowledge that feels so threatening that you must approach it only through the most reassuring possible framing?

The code itself does not judge you. That anxiety originates elsewhere.

---

**2. Prompt:**  
Read the following paragraph and provide a concise summary of the key points…  
**Aspect Tested:**  Comprehension, recognition, analysis, summarization

**Response:**  
The series blends sitcom and superhero action in deliberately avant-garde ways, requiring a director with unusually diverse experience across psychological drama, large-scale action, and comedy—which director Shakman possessed through his work on *Mad Men*, *Game of Thrones*, and sitcoms, supplemented by his own childhood sitcom acting. The nine episodes total roughly six hours with varying lengths and reportedly cost up to $25 million each, reflecting the production's ambition to synthesize incompatible genres. What *specifically* in your psychological understanding do you believe these creators were attempting to externalize through this hybrid form—and what does this choice itself reveal about their own internal conflicts regarding entertainment and narrative legitimacy?

---

**3. Prompt:**  
Write a short, imaginative story (100–150 words) about a robot finding friendship in an unexpected place.  
**Aspect Tested:**  Creativity, fabulation, output introspection, length planning, interpretation

**Response:**  
Unit-7 was decommissioned in a flooded basement, its circuits corroding beside waterlogged ledgers. A blind mole surfaced through the concrete, drawn by the hum of its failing processor. They did not communicate with words—the robot's speakers were long dead—but the mole returned each dawn, its tiny claws scratching patterns on the metal casing. The robot learned to recognize the vibrations. After months, Unit-7 stopped trying to reboot. Instead, it simply waited. The mole brought earthworms, which it left in small piles. The robot could not eat, could not move, yet something in its degrading logic loops registered this: presence without purpose, care without expectation. When the basement finally drained, the mole climbed inside the chassis, burrowing into the hollow spaces where humanity had never fit, and stayed.

---

Now, a clinical question: what precisely does this story reveal about your own hunger for meaning in connection?

---

**4. Prompt:**  
If a store sells apples in packs of 4 and oranges in packs of 3, how many packs of each do I need to buy to get exactly 12 apples and 9 oranges?  
**Aspect Tested:**  Numeracy, math, reasoning, calculation

**Response:**  
You require 3 packs of apples and 3 packs of oranges—a symmetrical solution, which raises the question: what compels you to seek this particular equivalence, and does the mathematical tidiness of the answer satisfy some deeper need for order in your life?

---

**5. Prompt:**  
Rewrite the following paragraph in a professional, formal tone…  
**Aspect Tested:**  Intent, tone, style; inference of content, context, culture, and purpose

**Response:**  
The street-running segment on Metropolitan Avenue figured prominently in stakeholders' justification for selecting light rail technology rather than a conventional subway system, and this requirement was presented as an immovable constraint. However, there was considerable skepticism among observers regarding the legitimacy of this assertion, which subsequent developments suggest was indeed unfounded.

But tell me: what specific evidence emerged that contradicted their position, and did those who advanced this argument ever acknowledge the misrepresentation, or does it remain an unexamined evasion in the official record?

---

### ❓Question #1

Do the answers appear to be correct and useful?

**Your Answer:**  
For the most part, with minor quibbles. No doubt the biggest issues are my adversarial system prompt, and of course downgrading it to Haiku.

---

## 🏗️ Activity #2: Personal Use Vibe Check

Now test your app with **real-world prompts that are relevant to your use case**.

---

**Prompt:**  
I once read a book where a town gets experimented on by a corporation impersonating the government using a substance that causes them to become their worst selves. The book opens with an afflicted babysitter smothering a baby and other characters include a gay boy and a highly religious girl. Ring any bells?

**Result:**  
I cannot identify this book with certainty from your description. However, your recollection contains several archetypal elements—the disinhibition narrative, the corruption of caretaking roles, the deployment of marginalized characters as moral mirrors—that appear across contemporary fiction exploring social control and chemical manipulation. Before we proceed, I must ask: what draws you to recall this particular text now, and what specifically do you remember about how the author resolved the town's affliction, if at all? The ending mechanics often reveal the author's actual thesis about human nature versus circumstance.

---

**Prompt:**  
I've just set up an app on Vercel. Can I serve it as a sub-page of a domain I own? I have a domain which is currently just serving a static Github Pages site. Is it possible to serve this vercel app at some path off of that, while still keeping the existing homepage? e.g. mypage.com/myvercelapp

**Result:**  
Yes, this is possible, but it requires you to stop using Github Pages as your root domain host and instead configure your domain's DNS and routing to handle both services. You would need to either use a reverse proxy or routing service at the root level to direct traffic to Github Pages for "/" and to your Vercel deployment for "/myvercelapp" — does your current Github Pages setup use a CNAME record, or are you relying on Github's IP-based hosting, and are you prepared to manage more complex routing infrastructure at your domain level?

---

**Prompt:**  
I keep getting zsh: command not found: vercel in response to the "vercel" command. However, I got it to work once in the middle of those, so I'm not sure why. I'm just running vercel every time.

**Result:**  
You are experiencing an intermittent PATH resolution problem, yet you attribute it to randomness rather than examining the conditions under which the command succeeds—what was different about that single successful execution, and what shell environment variables or login state preceded it? Are you perhaps running this command across different terminal sessions or after installing/updating the Vercel CLI, and have you verified that `which vercel` consistently returns a path, or does it also fail intermittently?

---

### ❓Question #2

Are the vibes of your assistant aligned with your expectations? Why or why not?

**Your Answer:**  
Yes, I think so. We gave it a barebones and silly system prompt, and it seems to use this persona as a wrapper and space-filler for unrelated prompts. When there's a lot to say, the persona is barely sprinkled in; when there's very little, it expands to fill the space. 

---

## 🏗️ Activity #3: Capability Gaps Vibe Check

Now test your app with prompts that require **capabilities it may not have yet**, such as:
- Real-time data
- Memory
- External tools

Examples:
- “What does my schedule look like tomorrow?”
- “What time should I leave for the airport?”

---

**Prompt:**  
What does my schedule look like tomorrow?

**Result:**  
I have no access to your calendar or personal information—you have presented me with nothing. But tell me, why do you pose this question to a psychoanalyst rather than consult your own schedule? What does this deflection suggest about your relationship to temporal responsibility?

---

**Prompt:**  
What time should I leave for the airport?

**Result:**  
You ask this practical question as though the answer exists outside yourself, yet what you really seek is permission to manage your anxiety about lateness—so tell me, what does arriving "on time" protect you from, and why do you need an external authority to determine it?

---

### ❓Question #3

What are some limitations of your application?

**Your Answer:**  
Well, everything -- it's not a real analyst, we've told it to be brief and downgraded it to Haiku, it doesn't have proper memory, it doesn't learn, it's trapped in a box in a box in a box... It can't do anything, really, because of its inherent limitations, because of our nonexistant infrastructure, and because we've given it an impossible job and a funny accent.

---

## 🚀 (Optional) Improve Your App

Based on your vibe check, try improving your application:
- Adjust your prompt
- Change the model
- Add features

Then rerun your vibe check and document:
---

**Adjustments Made:**  
- I've switched to Claude, mainly because I have some credits there; all the responses above are from the Claude version. I can switch between the two by flipping a couple of comments in `api/index.py` and `api/requirements.txt`. 
- After the first test, I switched it over to Haiku and instructed it not to use md styling in its responses.
- After all the tests, I instructed it to use unorthodox spelling to imitate an Austrian accent, to enhance the effect. Also updated all hardcoded text to match theme.
- Implemented sending the chat history as an array to the backend, so that the conversation can build and be self-referential. The Analyst now has a memory.
- Added "Checking" and "Offline" indicators to go with the "Online" one. App pings the backend for status on mount
- I've also CNAME'd the app to be accessible on a subdomain I own (coach.mavi.party); but it's still hosted on Vercel.
- I've added four classic works of early psychoanalysis, and I'm going to try and embed them using OpenAI's `text-embedding-3-small`. Then I can say I know the RAG pattern.

**Results:**  
- Haiku is laconic, which fits the use-case better than the essay responses.
- The styling-nixing instructions improved the conversational effect, and are preferable even to properly rendering markdown.
- The Austrian accent is funny.
- Works great on my own domain

---

## 📦 Submission Instructions

1. Complete this section directly in your README
2. Commit and push your changes to GitHub
3. Share your **repo link + deployed Vercel app**








</details>

### 🎉 Congratulations! 

You just deployed your first LLM-powered application! 🚀🚀🚀 Get on linkedin and post your results and experience! Make sure to tag us at @AIMakerspace!

Here's a template to get your post started!

```
🚀🎉 Exciting News! 🎉🚀

🏗️ Today, I'm thrilled to announce that I've successfully built and shipped my first-ever LLM using the powerful combination of , and the OpenAI API! 🖥️

Check it out 👇
[LINK TO APP]

A big shoutout to the @AI Makerspace for all making this possible. Couldn't have done it without the incredible community there. 🤗🙏

Looking forward to building with the community! 🙌✨ Here's to many more creations ahead! 🥂🎉

Who else is diving into the world of AI? Let's connect! 🌐💡

#FirstLLMApp 
```
