---
name: pi-script-loop
description: Bash owns the sequence; Pi supplies bounded child calls.
tools: Agent
---

The pi-script-loop extension must execute at session_start and terminate this
process before any parent model turn. This prompt must never be sent to a model.
The separate pi-script-guard extension rejects any parent agent start.
Agent is declared to provision Fullsend's child dispatcher; child processes
receive no built-in tools. No model decides whether to launch the Bash script.
