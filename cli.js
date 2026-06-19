#!/usr/bin/env node
const { execSync } = require("child_process");
const path = require("path");
const projectPath = process.argv[2] || ".";

function run(cmd) {
  try {
    execSync(cmd, { cwd: projectPath, stdio: "inherit" });
    process.exit(0);
  } catch {
    return false;
  }
}

// Try uv first, fallback to python
run(`uv run python -m src.installer "${projectPath}"`) ||
run(`python -m src.installer "${projectPath}"`) ||
run(`python3 -m src.installer "${projectPath}"`) ||
(() => { console.error("Failed to run token-saver installer"); process.exit(1); })();