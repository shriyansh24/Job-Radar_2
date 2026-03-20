// Wrapper to start uvicorn from the correct directory
const { spawn } = require("child_process");
process.chdir(__dirname);
spawn("python", ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], {
  stdio: "inherit",
  cwd: __dirname,
});
