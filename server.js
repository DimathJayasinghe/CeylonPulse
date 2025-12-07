const { spawn } = require("child_process");

function runPython(limit) {
  return new Promise((resolve, reject) => {
    const process = spawn("python3", ["web_news_scraper-/web_scraper.py"]);

    let result = "";

    process.stdout.on("data", data => {
      result += data.toString();
    });

    process.stderr.on("data", data => {
      console.error("Python Error:", data.toString());
    });

    process.on("close", () => {
      resolve(result.trim());
    });

    // send parameters to Python
    process.stdin.write(`${limit}`);
    process.stdin.end();
  });
}

runPython(1).then(output => {
  console.log("Result from Python:", output);
});
