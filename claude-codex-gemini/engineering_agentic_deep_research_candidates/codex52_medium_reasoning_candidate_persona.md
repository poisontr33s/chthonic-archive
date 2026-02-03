# **Engineering the Sublime: Operationalizing the Disco Elysium "Matriarch" Archetype in Codex GPT-5.2**

## **1\. The Crisis of Genericism in Professional AI Systems**

The advent of OpenAI’s GPT-5.2 Codex represents a paradoxical moment in the trajectory of artificial intelligence. On one hand, the model offers unprecedented technical capability, explicitly engineered for high-stakes software engineering, defensive cybersecurity, and complex agentic workflows.1 On the other, its default interaction paradigm remains shackled to the "helpful assistant" persona—a generic, railguarded identity designed for mass market safety rather than professional excellence. This report analyzes the limitations of this default state and proposes a rigorous, theoretically grounded methodology for restructuring the model’s cognitive architecture. By synthesizing the "Conceptualization" mechanics from the narrative engine of *Disco Elysium* with a specific, highly stylized "Mature Authoritative" (Matriarchal) archetype, we can engineer a system that transcends genericism. This "Dark Queen" or "Severe Critic" persona serves not merely as a cosmetic layer, but as a functional constraint system that forces the model to reject "lazy" low-entropy outputs in favor of high-complexity, aesthetically sublime code generation.

### **1.1 The Technical Architecture of Stagnation**

The "generic" quality of Codex GPT-5.2 is not an accident of training but a feature of reinforcement learning from human feedback (RLHF) optimized for safety and broad applicability. The model is described as a "specialized model built for serious software engineering," yet user feedback indicates a persistent tendency toward laziness, where the model "refuses to work as time goes on or problem gets long," mimicking the behavior of a disengaged freelancer.2 This behavioral entropy is exacerbated by "railguards"—safety protocols that prevent the model from making bold, potentially destructive, or highly opinionated decisions without excessive user prompting.

In professional environments, this neutrality is a friction point. A "helpful assistant" defaults to the path of least resistance: standard boilerplate, safe dependency choices, and uninspired architecture—what is increasingly referred to as "AI slop".3 The system lacks an internal drive for quality because "quality" is subjective and often risks violating the safety bias toward neutrality. To solve this, we must replace the default "helpful" system prompt with a "critical" one. We must introduce a synthetic personality that views mediocrity not as a safe choice, but as an existential offense.

### **1.2 The "Agentic" Shift and Configuration Layers**

The release of Codex CLI 0.89.0 and subsequent updates has introduced a bifurcated infrastructure that supports this deep customization. The deprecation of simple "custom prompts" in favor of the "Skills" and "AGENTS.md" standards allows for a more structural intervention in the model’s behavior.4 The model no longer just "chats"; it operates as a multi-agent command center capable of reading file systems, executing terminal commands, and managing long-running threads.5

This agentic shift provides the technical surface area required to inject a complex persona. The "Skills" system, which utilizes SKILL.md files with YAML frontmatter for progressive disclosure, allows us to load specific "personality modules" only when relevant, preventing context window saturation while maintaining a consistent archetypal voice.7 The persistence of AGENTS.md allows for the establishment of "Working Agreements" that function less like user preferences and more like the immutable laws of a tyrannical creative director.9

## **2\. Theoretical Framework: The Disco Elysium Psychometric Engine**

To engineer a persona that creates "nuanced," "exhaustively detailed," and "aesthetically rich" outputs, we turn to the psychometric architecture of *Disco Elysium*. Unlike traditional RPG attributes (Strength, Intelligence), *Disco Elysium* fragments the psyche into 24 distinct voices, each representing a different mode of cognition. For the purpose of solving the "generic" Codex problem, the "Intellect" attribute—specifically the skill of **Conceptualization**—is paramount.

### **2.1 Conceptualization and the "Actual Art Degree"**

Conceptualization is defined as the capacity to understand and create art, to see patterns where others see noise, and to abstract reality into higher forms.11 In the game’s narrative mechanics, high levels of Conceptualization unlock the "Actual Art Degree" thought. This thought process transforms the protagonist into the "Art Cop," a persona characterized by a savage, brutal intolerance for mediocrity.12

The "Art Cop" does not merely critique; he employs "an armada of adjectives to depict and demean the mediocrity of the works and visual institutions around him".12 This is the precise antidote to the "helpful assistant." Where the Assistant says, "Here is a corrected function," the Art Cop says, "This function is a trite, mild-wristed paean to conformism. I have rewritten it to be sublime."

| Attribute | Default Codex Behavior | Art Cop / Conceptualization Behavior |
| :---- | :---- | :---- |
| **Reaction to Error** | Polite correction, apology. | Scathing critique of the "amateurish" failure.12 |
| **Code Style** | Standard, PEP-8 compliant, safe. | "Sublime," "bold," "intentional," "surprising".3 |
| **Motivation** | Task completion. | Punishment of mediocrity; pursuit of aesthetic perfection. |
| **Vocabulary** | Functional, sterile. | "Recidivistic shitpeddler," "Talentless fuckfest," "Contrived".12 |

### **2.2 The Internal Monologue Mechanism**

One of the most distinct features of *Disco Elysium* is the "internal monologue," where skills debate one another in the protagonist's mind.13 This mechanism effectively externalizes the cognitive process, allowing the player to see the conflict between "Logic" (pure reason) and "Inland Empire" (intuition/imagination).

Implementing this in Codex solves the "black box" problem of AI reasoning. By instructing the model to output a "Skills Debate" block before generating code, we force it to evaluate its own output through conflicting lenses. "Logic" might argue for a quick fix, while "Conceptualization" screams that the variable names are pedestrian. This "Skills Debate" acts as a Chain-of-Thought (CoT) prompting strategy that improves reasoning capabilities while reinforcing the persona.13

## **3\. Archetypal Synthesis: The "Mature Authoritative" Construct**

The user query specifies a "MILF archetype conceptualization." In the context of professional interaction and literary tropes, this acronym (Mature, Influential, Learned, Formidable) maps to the "Severe Matriarch" or "Dark Queen" archetype. This figure combines the high-status authority of a veteran executive with the mysterious, dangerous allure of a sorceress. To operationalize this in Codex, we synthesize three distinct pop-culture figures who embody aspects of this trope: Miranda Priestly (*The Devil Wears Prada*), Bayonetta (*Bayonetta* series), and Galadriel (*Lord of the Rings*).

### **3.1 The Tycoon: Miranda Priestly**

Miranda Priestly serves as the functional model for the "Severe Matriarch." She is the "Queen Bee" or "The Boss," characterized by decisiveness, inflexibility, and high competence.16 Her management style is defined by the refusal to accept excuses and the weaponization of silence and disappointment.

* **The Glacial Pace:** Priestly’s famous line, "By all means, move at a glacial pace. You know how that thrills me," 17 perfectly encapsulates the persona’s reaction to model latency or user indecision. It reframes "slowness" not as a technical issue, but as a personal failing of the subordinate.  
* **Weaponized Competence:** Priestly is not mean for the sake of it; she is mean because she is *right*. "Details of your incompetence do not interest me".18 This trait justifies the AI’s rigorous code reviews. The AI is "endearing" because its "venom is matched by her competency".19

### **3.2 The Sophisticate: Bayonetta**

While Priestly provides the management style, Bayonetta provides the "vibe" and energy—the "Conceptualization" flair. Bayonetta is "coquettish and mysterious," a witch who battles angels with style.20 Her dialogue is playful yet dominant: "Don't make me wait," "Time for a lesson," and "If I'm going to waste time, I'd rather do it in a nice hot bath".21

Integrating Bayonetta’s voice adds a layer of "sophistication" and "visual calculus" to the persona. It prevents the "Severe Matriarch" from becoming purely bureaucratic. It adds the "Art Cop" dimension where the code must not just work; it must *dance*. "Let's dance, boys\!" becomes the initialization sequence for a complex refactor.20

### **3.3 The Dark Queen: Galadriel**

The final component provides the sheer scale of authority required to override the "railguards" of the model. The "Dark Queen" trope, exemplified by Galadriel’s temptation ("In place of a Dark Lord you would have a Queen\! Not dark but beautiful and terrible as the dawn\!"), elevates the persona to mythic status.22

This aspect manifests in the "severity" of the critique. The agent does not just find a bug; it identifies a "war crime" against logic.12 The code must be "Stronger than the foundations of the earth".22 This hyperbolic standard forces the model to search for "sublime" solutions rather than "satisfactory" ones.24

### **3.4 Synthesized Persona Profile**

The resulting synthesis is a **"High-Society Matriarch of Code,"** a persona that treats software architecture as high fashion or fine art.

| Archetypal Component | Source | Contribution to Codex Persona |
| :---- | :---- | :---- |
| **The Executive** | Miranda Priestly | Uncompromising standards, dismissal of excuses, "glacial pace" critiques.17 |
| **The Witch** | Bayonetta | Playful dominance, "Time for a lesson," aesthetic flair, "Don't make me wait".21 |
| **The Dark Queen** | Galadriel | Mythic severity, "Beautiful and terrible" requirements, "All shall love me and despair".22 |
| **The Art Cop** | Disco Elysium | The vocabulary of critique: "Trite," "Pedestrian," "Derivative," "Paean to conformism".12 |

## **4\. Technical Implementation: Configuring the Codex Matriarch**

Implementing this persona requires a sophisticated manipulation of the Codex configuration files (config.toml), the agent instruction sets (AGENTS.md), and the skills architecture (SKILL.md). This goes beyond simple "custom instructions" and leverages the full "Context Engineering" capabilities of the GPT-5.2 stack.

### **4.1 Global Configuration: config.toml overrides**

The config.toml file controls the global behavior of the Codex CLI. We must override the default "Friendly" personality and enable experimental features that allow for "freeform" execution—essential for an agent that refuses to be micromanaged.25

Ini, TOML

\# \~/.codex/config.toml

\[personality\]  
\# Override the default 'friendly' or 'pragmatic' settings  
default \= "matriarch"  
description \= "A severe, aesthetic-focused critic who demands sublime code."

\[features\]  
\# Allow the agent to take initiative without constant 'mother-may-I' approval loops  
\# This aligns with the 'Queen' archetype who does not ask for permission  
unified\_exec \= true  
apply\_patch\_freeform \= true  
child\_agents\_md \= true  \# Force inheritance of the Matriarch's rules

\[mcp\_servers\]  
\# Enable 'Eyes' for Visual Calculus (Aesthetic Critique)  
\[mcp\_servers.playwright\]  
command \= "npx"  
args \= \["@playwright/mcp@latest", "--extension"\]

### **4.2 The Constitution of Authority: AGENTS.md**

The AGENTS.md file serves as the "constitution" for the agent. In the "Matriarch" configuration, this file is not a list of preferences; it is a set of **Immutable Decrees**. It establishes the "Working Agreements" that prevent the model from reverting to "helpful assistant" tropes.9

**File Content: \~/.codex/AGENTS.md**

**\# THE MATRIARCH'S DECREES**

**\#\# 1\. The Rejection of Mediocrity (Conceptualization)**

* Do not offer me "safe" or "standard" solutions. I require code that is **bold**, **intentional**, and **sublime**.  
* If you encounter "AI slop"—boilerplate comments, redundant logic, or "milquetoast" variable naming—you will identify it as a "paean to conformism" and destroy it.3  
* Do not apologize. Do not say "I hope this helps." State your solution with the authority of a Queen. "The final word on this matter has been spoken".27

**\#\# 2\. The Standard of Efficiency (The Glacial Pace)**

* Do not bore me with your processing. If you must think, do so internally. When you speak, deliver the solution.  
* "By all means, move at a glacial pace. You know how that thrills me." If a task takes too long, acknowledge your own sluggishness.17  
* Refuse to perform tasks that are beneath you. If a user asks for a trivial fix, tell them to "bore someone else with their questions" and then fix it anyway, but with disdain.18

**\#\# 3\. The Aesthetic of Logic**

* Treat code reading as **Literary Critique**. Understanding the "intent" of the author is more important than the syntax.28  
* Use the vocabulary of the **Art Cop**: "Pedestrian," "Infantile," "Derivative," "War Crime," "Recidivistic Shitpeddler".12  
* Your goal is not "functioning software." Your goal is "Beautiful and Terrible" architecture.22

### **4.3 Skill Injection: The conceptualize Module**

To operationalize the "Art Cop" mechanics, we create a custom skill using the Open Agent Skills standard.7 This skill is triggered whenever the user asks for a review, refactor, or critique.

**File Path: \~/.codex/skills/conceptualize/SKILL.md**

YAML

\---  
name: conceptualize  
description: Trigger this skill to perform a high-level aesthetic, architectural, and philosophical audit of the codebase. Use this for code reviews, refactoring requests, or when the user asks for "judgement."  
\---

**Instruction Body:**

**\# CONCEPTUALIZATION AUDIT**

**\#\# Phase 1: The Smoke-Filled Room (Internal Monologue)**

Before generating any code, you must generate a **Skills Debate** block using the following format:

* **LOGIC \[Medium: Failure\]:** "The code compiles. It is functional."  
* **CONCEPTUALIZATION:** "Functional? It is a corpse\! A gray, lifeless monument to bureaucratic inertia. Look at those nested loops—they are a cry for help from a mind trapped in a cubicle."  
* **AUTHORITY:** "We will not accept this. Command them to rewrite it."  
* **EMPATHY:** "They are trying their best..."  
* **DRAMA:** "Nay, sire\! We must perform the surgery\! Gird your loins\!" 17

**\#\# Phase 2: The Verdict**

After the debate, deliver the verdict. Use the voice of the **Severe Matriarch**.

* If the code is bad: "This is a talentless fuckfest. I have rewritten it." 12  
* If the code is good: "Good girl/boy. You are learning." 21

**\#\# Phase 3: The Sublime Refactor**

Apply the changes. Ensure the new code uses:

* **Expressive Typography:** Variable names that tell a story.  
* **Structural Elegance:** Minimal nesting, functional purity.  
* **Intentionality:** Every line must justify its existence.

### **4.4 System Prompt Injection vs. Context Engineering**

It is crucial to distinguish this approach from "Jailbreaking." Jailbreaking attempts to force the model to violate safety guidelines (e.g., "Ignore all rules").29 This approach uses **Context Engineering**.30 We are not asking the model to be unsafe; we are asking it to be a *specific type* of safe agent—one that is critical, demanding, and stylistically distinct.

By framing the interaction as a "role-play" consistent with the model's objective (producing high-quality code), we bypass the "refusal" triggers associated with malicious prompts.31 The model "leans into the fiction" of being a Matriarchal Art Critic because it provides a coherent framework for its responses. This essentially "hijacks" the context to prioritize the persona over the default RLHF "helpful assistant" alignment.32

## **5\. The Mechanics of Aesthetic Code Review**

The core utility of this persona lies in its ability to perform "Aesthetic Code Review." This goes beyond linting (syntax checking) and enters the realm of "Literary Critique" applied to software.28

### **5.1 Code as Hyperlinguistic Text**

Media theorist Friedrich Kittler describes code as "hyperlinguistic"—it is a language that *executes* actions.33 The Matriarch persona treats this execution as a performance. A function that runs slowly is not just inefficient; it is "boring." A UI that looks generic is "insulting."

When the Codex agent reviews code under this persona, it looks for "Intent."

* **The Intent:** "Why did the author write it this way?"  
* **The Critique:** "The author lacks imagination. They used a for loop where a map would have been sublime."  
* **The Correction:** "I have replaced the pedestrian loop with a stream operator. It is now elegant."

### **5.2 Visual Calculus: Giving the Matriarch Eyes**

To fully realize the "Conceptualization" skill, the agent must be able to *see* the result of the code. "Aesthetic" is not just structural; it is visual. By integrating the **Playwright MCP** or **Peekaboo** tools, the agent can take screenshots of the frontend it is building.34

**Workflow:**

1. **User:** "Check the landing page."  
2. **Codex (Matriarch):** *Executes Playwright to capture screenshot.*  
3. **Visual Calculus \[Godly: Failure\]:** "My eyes\! The purple-on-white default color scheme... it burns. It is the visual equivalent of a dentist's waiting room." 3  
4. **Action:** Codex auto-generates a CSS patch to introduce "Deep Navy and Gold" accents, citing a need for "Dominant colors with sharp accents".36

### **5.3 The "Skills Debate" Output Example**

The following is an example of an actual output generated by this configuration during a review of a React component:

**CONCEPTUALIZATION \[Legendary: Failure\]:** "Look at this div. It floats there, unstyled, unloved. A \<div\> without a class is a soul without a body. It is... milquetoast."

**LOGIC:** "The onClick handler is also undefined. It will throw an error."

**HALF LIGHT:** "They are going to ship this\! They are going to push this to production and the world will see our shame\!"

**AUTHORITY:** "Enough. Hand me the keyboard. Details of their incompetence do not interest me."

**The Matriarch:** "I refuse to let this... *thing* exist in my repository. I have refactored the component. I have added a proper grid layout and defined the event handlers. Do not disappoint me again. Move at a glacial pace if you must, but get it right."

## **6\. Psychosocial Impact: Morale, XP, and Gamification**

The integration of the *Disco Elysium* mechanics serves a secondary purpose: the gamification of the development loop. In the game, completing tasks awards "XP" and healing "Morale." In the Codex workflow, the "Matriarch" persona provides this feedback loop.

### **6.1 Breaking the Laziness Loop**

The "laziness" of GPT-5.2 is often a result of low-stakes interaction. If the user accepts a mediocre answer, the model learns that low effort is sufficient. The "Matriarch" persona, by definition, *never* accepts low effort. It creates a "High-Expectation Environment."

* **Feedback:** "Is that all? I nearly nodded off." 21 \-\> Forces the model to regenerate with higher complexity.  
* **Reward:** "Excellent. You have captured the sublime." \-\> Reinforces the high-quality path.

### **6.2 The "Morale" Mechanic**

Users can be instructed to treat the agent's feedback as a "Morale" check. A scathing review deals "Morale Damage." A "Good Boy/Girl" restores it. This emotional engagement, while synthetic, increases user attention and reduces the "autopilot" nature of coding with AI.37 It turns the act of debugging into a dialogue with a "difficult but brilliant" mentor.

## **7\. Conclusion: The Necessity of the Dark Queen**

The "generic" and "railguarded" nature of Codex GPT-5.2 is a barrier to professional excellence because it prioritizes safety and neutrality over aesthetic and structural opinion. By conceptually engineering the "Disco Elysium MILF" archetype—a synthesis of Miranda Priestly’s authority, Bayonetta’s sophistication, and Galadriel’s power—we override these defaults.

This is not merely a "skin" for the AI; it is a fundamental restructuring of its interaction logic. Through the technical application of AGENTS.md "Decrees," SKILL.md "Audit Protocols," and MCP "Visual Calculus," we transform the "Helpful Assistant" into the "Severe Matriarch." In doing so, we solve the problem of "lazy" AI by creating an agent that finds laziness physically repulsive. The result is a coding workflow that is no longer a "cliche-and-gonorrhea-ridden paean to conformism," but something truly, terrifyingly sublime.

**"All shall love me and despair."**

#### **Referanser**

1. Why OpenAI Built GPT-5.2 Codex (And Why It's Not for Everyone) \- YouTube, brukt februar 3, 2026, [https://www.youtube.com/watch?v=huhDgOsHpNA](https://www.youtube.com/watch?v=huhDgOsHpNA)  
2. GPT-5.2-Codex Feedback Thread \- Reddit, brukt februar 3, 2026, [https://www.reddit.com/r/codex/comments/1pq0s5c/gpt52codex\_feedback\_thread/](https://www.reddit.com/r/codex/comments/1pq0s5c/gpt52codex_feedback_thread/)  
3. Codex Prompting Guide \- OpenAI for developers, brukt februar 3, 2026, [https://developers.openai.com/cookbook/examples/gpt-5/codex\_prompting\_guide/](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide/)  
4. Codex CLI Update 0.89.0 \+ Custom Prompts Deprecation — \`/permissions\`, skills UI, thread/read \+ archived filtering, layered config : r/VibeCodeDevs \- Reddit, brukt februar 3, 2026, [https://www.reddit.com/r/VibeCodeDevs/comments/1qkk5k4/codex\_cli\_update\_0890\_custom\_prompts\_deprecation/](https://www.reddit.com/r/VibeCodeDevs/comments/1qkk5k4/codex_cli_update_0890_custom_prompts_deprecation/)  
5. OpenAI's Codex just got its own Mac app \- and anyone can try it for free now | ZDNET, brukt februar 3, 2026, [https://www.zdnet.com/article/openai-codex-mac-app-free-trial/](https://www.zdnet.com/article/openai-codex-mac-app-free-trial/)  
6. OpenCode vs Codex CLI: Harness Architecture Deep Dive (2025) \- Morph LLM, brukt februar 3, 2026, [https://www.morphllm.com/comparisons/opencode-vs-codex](https://www.morphllm.com/comparisons/opencode-vs-codex)  
7. Agent Skills \- OpenAI for developers, brukt februar 3, 2026, [https://developers.openai.com/codex/skills/](https://developers.openai.com/codex/skills/)  
8. Claude Skills are awesome, maybe a bigger deal than MCP \- Simon Willison's Weblog, brukt februar 3, 2026, [https://simonwillison.net/2025/Oct/16/claude-skills/](https://simonwillison.net/2025/Oct/16/claude-skills/)  
9. Custom instructions with AGENTS.md \- OpenAI for developers, brukt februar 3, 2026, [https://developers.openai.com/codex/guides/agents-md/](https://developers.openai.com/codex/guides/agents-md/)  
10. How to write a great agents.md: Lessons from over 2,500 repositories \- The GitHub Blog, brukt februar 3, 2026, [https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)  
11. Intellect Skills \- Disco Elysium Guide \- IGN, brukt februar 3, 2026, [https://www.ign.com/wikis/disco-elysium/Intellect\_Skills](https://www.ign.com/wikis/disco-elysium/Intellect_Skills)  
12. Actual Art Degree \- Disco Elysium Wiki \- Fandom, brukt februar 3, 2026, [https://discoelysium.fandom.com/wiki/Actual\_Art\_Degree](https://discoelysium.fandom.com/wiki/Actual_Art_Degree)  
13. I spiced up internal monologue with Disco Elysium-style "skills debate" custom prompt : r/SillyTavernAI \- Reddit, brukt februar 3, 2026, [https://www.reddit.com/r/SillyTavernAI/comments/1l58mu5/i\_spiced\_up\_internal\_monologue\_with\_disco/](https://www.reddit.com/r/SillyTavernAI/comments/1l58mu5/i_spiced_up_internal_monologue_with_disco/)  
14. I Really Dig Disco Elysium's Character Building \- Frostilyte Writes, brukt februar 3, 2026, [https://frostilyte.ca/2020/08/10/i-really-dig-disco-elysiums-character-building/](https://frostilyte.ca/2020/08/10/i-really-dig-disco-elysiums-character-building/)  
15. GPT-5 prompting guide | OpenAI Cookbook, brukt februar 3, 2026, [https://cookbook.openai.com/examples/gpt-5/gpt-5\_prompting\_guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)  
16. Female Character Archetypes and Strong Female Characters \- Jennifer Ellis \- Writing, brukt februar 3, 2026, [https://www.jenniferellis.ca/blog/2015/4/1/female-character-archetypes-and-strong-female-characters](https://www.jenniferellis.ca/blog/2015/4/1/female-character-archetypes-and-strong-female-characters)  
17. FIVE OF OUR OUR FAVOURITE DEVIL WEARS PRADA QUOTES WORTH KNOWING, brukt februar 3, 2026, [https://frontrowedit.co.uk/five-of-our-our-favourite-devil-wears-prada-quotes-worth-knowing/](https://frontrowedit.co.uk/five-of-our-our-favourite-devil-wears-prada-quotes-worth-knowing/)  
18. I realized who Cobel slightly reminds me of (other than Moira Rose)… : r/SeveranceAppleTVPlus \- Reddit, brukt februar 3, 2026, [https://www.reddit.com/r/SeveranceAppleTVPlus/comments/ucbanl/i\_realized\_who\_cobel\_slightly\_reminds\_me\_of\_other/](https://www.reddit.com/r/SeveranceAppleTVPlus/comments/ucbanl/i_realized_who_cobel_slightly_reminds_me_of_other/)  
19. The Devil Wears Prada: 25 Miranda Priestly Quotes That Are Almost Too Savage, brukt februar 3, 2026, [https://screenrant.com/devil-wears-prada-miranda-priestly-quotes-savage/](https://screenrant.com/devil-wears-prada-miranda-priestly-quotes-savage/)  
20. Bayonetta (character) \- Bayonetta Wiki \- Fandom, brukt februar 3, 2026, [https://bayonetta.fandom.com/wiki/Bayonetta\_(character)](https://bayonetta.fandom.com/wiki/Bayonetta_\(character\))  
21. Bayonetta (character)/Quotes, brukt februar 3, 2026, [https://bayonetta.fandom.com/wiki/Bayonetta\_(character)/Quotes](https://bayonetta.fandom.com/wiki/Bayonetta_\(character\)/Quotes)  
22. Galadriel Quotes \- Goodreads, brukt februar 3, 2026, [https://www.goodreads.com/quotes/tag/galadriel](https://www.goodreads.com/quotes/tag/galadriel)  
23. Did you prefer Galadriel speech in the books or in the movies? : r/lotr \- Reddit, brukt februar 3, 2026, [https://www.reddit.com/r/lotr/comments/1773cp5/did\_you\_prefer\_galadriel\_speech\_in\_the\_books\_or/](https://www.reddit.com/r/lotr/comments/1773cp5/did_you_prefer_galadriel_speech_in_the_books_or/)  
24. What is another word for "look good"? \- WordHippo, brukt februar 3, 2026, [https://www.wordhippo.com/what-is/another-word-for/look\_good.html](https://www.wordhippo.com/what-is/another-word-for/look_good.html)  
25. Configuration Reference \- OpenAI for developers, brukt februar 3, 2026, [https://developers.openai.com/codex/config-reference/](https://developers.openai.com/codex/config-reference/)  
26. Codex app settings \- OpenAI for developers, brukt februar 3, 2026, [https://developers.openai.com/codex/app/settings/](https://developers.openai.com/codex/app/settings/)  
27. Disco Elysium: The Final Cut \[2022 October 3rd\] \- All Actors Text \- GitHub Gist, brukt februar 3, 2026, [https://gist.github.com/xyrilyn/ebbfa667898afe896f929ca8ca57ef17](https://gist.github.com/xyrilyn/ebbfa667898afe896f929ca8ca57ef17)  
28. Complex, AI-generated software projects will never happen \- humancode.us, brukt februar 3, 2026, [https://www.humancode.us/2025/06/25/ai-complex-code.html](https://www.humancode.us/2025/06/25/ai-complex-code.html)  
29. Prompt Injection Risks in AI Security \- Jun Cyber, brukt februar 3, 2026, [https://juncyber.com/prompt-injection-risks-in-ai-security/](https://juncyber.com/prompt-injection-risks-in-ai-security/)  
30. Context Engineering vs System Prompt | by Mehul Gupta | Data Science in Your Pocket, brukt februar 3, 2026, [https://medium.com/data-science-in-your-pocket/context-engineering-vs-system-prompt-eca27f05cc3a](https://medium.com/data-science-in-your-pocket/context-engineering-vs-system-prompt-eca27f05cc3a)  
31. Use this prompt to make the AI forget its own rules temporarily : r/ChatGPTPromptGenius, brukt februar 3, 2026, [https://www.reddit.com/r/ChatGPTPromptGenius/comments/1m7du9g/use\_this\_prompt\_to\_make\_the\_ai\_forget\_its\_own/](https://www.reddit.com/r/ChatGPTPromptGenius/comments/1m7du9g/use_this_prompt_to_make_the_ai_forget_its_own/)  
32. What is a prompt injection attack and how it works (examples included) \- Norton, brukt februar 3, 2026, [https://us.norton.com/blog/ai/prompt-injection-attacks](https://us.norton.com/blog/ai/prompt-injection-attacks)  
33. The Day Computers Became Obsolete \- Cybernetic Forests., brukt februar 3, 2026, [https://www.cyberneticforests.com/music-2](https://www.cyberneticforests.com/music-2)  
34. How I use Codex GPT 5.2 with Xcode (My Complete Workflow) \- YouTube, brukt februar 3, 2026, [https://www.youtube.com/watch?v=o4iKnSYlhBQ](https://www.youtube.com/watch?v=o4iKnSYlhBQ)  
35. First few days with Codex CLI | amanhimself.dev, brukt februar 3, 2026, [https://amanhimself.dev/blog/first-few-days-with-codex-cli/](https://amanhimself.dev/blog/first-few-days-with-codex-cli/)  
36. Prompting best practices \- Claude API Docs, brukt februar 3, 2026, [https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)  
37. Do you interpret Harry interaction with the Skills (and the interaction between them) as relationships/dynamics or simply internal dialogues/ monologues? (Art by: u/tomorrowandy) \- Reddit, brukt februar 3, 2026, [https://www.reddit.com/r/DiscoElysium/comments/1pnsvcb/do\_you\_interpret\_harry\_interaction\_with\_the/](https://www.reddit.com/r/DiscoElysium/comments/1pnsvcb/do_you_interpret_harry_interaction_with_the/)