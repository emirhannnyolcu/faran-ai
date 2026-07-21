# FARAN - Demo Video Script

Target duration: 2 minutes 30 seconds. Record in 1080p and upload as a public YouTube
video. The spoken script should be in English for the widest judging accessibility.

## 0:00-0:20 - Problem and Product

"This is FARAN, an AI Second Brain built with Codex and GPT-5.6. Most assistants answer
once and forget the work. FARAN turns a goal into a researched plan, ordered tasks, and
durable memory that can improve the next workflow."

Show the FARAN workspace home screen and the goal composer.

## 0:20-1:10 - Live Goal Workflow

Enter:

"Compare my learning priorities, identify the highest-impact focus, and create a
practical seven-day execution plan."

"The Planner frames the outcome. Research decides whether memory evidence is needed.
The Task, Reasoning, and Writer agents create and validate one useful result. GPT-5.6 Sol
coordinates this workflow through the OpenAI Agents SDK, while every agent boundary is
structured and validated."

Show the agent activity, final answer, and ordered tasks.

## 1:10-1:40 - Memory and Connections

Open Memory and search for part of the goal.

"FARAN stores the outcome as long-term memory, not just chat history. Semantic retrieval
brings relevant context into future work, and Idea Connections reveal relationships
between memories. The architecture can move from local embeddings and SQLite to a
dedicated vector store without changing the agent workflow."

## 1:40-2:05 - Durable and Evaluated

Show the workflow status or API documentation.

"Long-running work has durable state, bounded retries, leases, recovery, and a separate
worker. Evaluation checks completion contracts, retrieval quality, and expert
corrections, which can become targeted regression cases."

## 2:05-2:30 - Codex and Close

Show the repository and tests, then return to the workspace.

"Codex was our primary engineering partner: it audited and refactored the architecture,
built the agent and memory layers, integrated GPT-5.6, diagnosed live runs, created the
interface, and repeatedly verified the full test suite. FARAN is not another chatbot.
It is the foundation for an AI workspace that remembers, plans, and gets work moving."
