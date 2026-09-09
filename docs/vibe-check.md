# Vibe Check — evaluation notes

The original hands-on evaluation of The Analyst: five capability probes, three
open questions, and a running log of what changed as a result. Kept because the
answers are the honest ones — including where the app fell short.

Responses below are real output from the deployed app at the time of testing
(Claude, `claude-haiku-4-5`), before the retrieval layer landed.

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

## 🚀 What changed as a result

A running log of what the vibe check prompted, and what came of it.

**Adjustments made:**  
- I've switched to Claude, mainly because I have some credits there; all the responses above are from the Claude version. I can switch between the two by flipping a couple of comments in `api/index.py` and `api/requirements.txt`. 
- After the first test, I switched it over to Haiku and instructed it not to use md styling in its responses.
- After all the tests, I instructed it to use unorthodox spelling to imitate an Austrian accent, to enhance the effect. Also updated all hardcoded text to match theme.
- Implemented sending the chat history as an array to the backend, so that the conversation can build and be self-referential. The Analyst now has a memory.
- Added "Checking" and "Offline" indicators to go with the "Online" one. App pings the backend for status on mount
- I've also CNAME'd the app to be accessible on a subdomain I own (coach.mavi.party); but it's still hosted on Vercel.
- I've added nine classic public-domain works of early psychoanalysis (see `api/_index`), and I'm going to try and embed them using OpenAI's `text-embedding-3-small`. Then I can say I know the RAG pattern.
- I'm instructing Claude to follow TDD patterns from now on, as the project grows in scope.
- Adding query context, a similarity floor, rate limiting, session ending, a new endpoint for the Analyst's notes (`api/notes`) and one for API health (`api/health`), and a patient file in localStorage.
- I've significantly expanded the disclaimer because frankly the project is legitimately dangerous.
- I am no longer tracking adjustments made in this list

**Results:**  
- Haiku is laconic, which fits the use-case better than the essay responses.
- The styling-nixing instructions improved the conversational effect, and are preferable even to properly rendering markdown.
- The Austrian accent is funny.
- Works great on my own domain
- I've confirmed, via `api_health` and Vercel logging, that our corpus is in production. But so far it's not clear that it's having any sort of effect. Maybe I'll have to dig deep, give it some dream-meat or something to chew on.
- The case notes feature is genuinely really cool imo
- The session end as first implemented was dissonant within its own narrative. I'm adding an exit message.
