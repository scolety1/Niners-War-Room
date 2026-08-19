# Optimization tools

Use OR-Tools or PuLP only for explicit legal-slot/add-drop/trade-search constraints. OR-Tools is preferred for bounded integer constraints; PuLP is a simpler fallback. DFS optimizers are patterns only; never import salary/ownership assumptions into season-long decisions.
