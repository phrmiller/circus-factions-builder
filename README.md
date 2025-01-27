# Circus Factions Builder

This repository contains the code for building Circus Factions (circusfactions.com).

The code is, essentially, just a simple Python static website generator script.

- It converts Markdown files (stored elsewhere) into HTML pages.
- It processes images (stored elsewhere).
- It throws in some CSS and JavaScript.
- It moves everything to a final site directory (stored elsewhere).

The entry point is `main.py`, which contains reasonably clear comments.

## Updates

2025-01-26. Added TailwindCSS, which meant adding Node, which meant adding complications to the develop and build environments -- but I think it all works now.

## Other Notes

Note to self: All other notes are in Obsidian; start with "Circus Factions / README".
