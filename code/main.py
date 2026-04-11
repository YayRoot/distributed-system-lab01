from flask import Flask, request, jsonify
import sqlite3
import os
import ast
import operator
from db_manager import DatabaseManager

app = Flask(__name__)
db = DatabaseManager()

# ---5555555     db     55555555555555



ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

def safe_eval(expr):
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPS:
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("Division by zero")
            return ALLOWED_OPS[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPS:
            return ALLOWED_OPS[type(node.op)](_eval(node.operand))
        else:
            raise ValueError("Invalid expression")
    tree = ast.parse(expr.strip(), mode="eval")
    return _eval(tree)

 #              000000 API routes ------

@app.route("/api/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json(force=True)
        expression = (data or {}).get("expression", "").strip()
        if not expression:
            return jsonify({"error": "No expression provided"}), 400

        result = safe_eval(expression)

        if isinstance(result, float) and result.is_integer():
            result_str = str(int(result))
        else:
            result_str = str(round(result, 10)).rstrip("0").rstrip(".")

        row = db.add_calculation(
            expression, 
            result_str,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify(row)

    except ZeroDivisionError:
        return jsonify({"error": "Division by zero"}), 400
    except (ValueError, SyntaxError):
        return jsonify({"error": "Invalid expression"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        rows = db.get_history()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    try:
        db.clear_history(
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return jsonify({"message": "History cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """View all actions logged in the database"""
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = db.get_action_log(limit=limit)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get database statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#                Frontend

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Calculator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0f0f13;
    color: #e0e0e0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .wrapper {
    display: flex;
    gap: 24px;
    align-items: flex-start;
    flex-wrap: wrap;
    justify-content: center;
  }

  .signature {
    position: fixed;
    right: 24px;
    bottom: 18px;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #555b77;
    font-weight: 500;
    background: rgba(10, 10, 16, 0.9);
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid rgba(130, 170, 255, 0.18);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(8px);
    pointer-events: none;
  }

  .calc {
    background: #1a1a24;
    border-radius: 20px;
    padding: 24px;
    width: 320px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.6);
  }

  .display {
    background: #0f0f13;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    min-height: 90px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: flex-end;
    overflow: hidden;
  }

  .display .expr {
    font-size: 14px;
    color: #666;
    min-height: 20px;
    word-break: break-all;
    text-align: right;
  }

  .display .result {
    font-size: 36px;
    font-weight: 300;
    color: #fff;
    word-break: break-all;
    text-align: right;
  }

  .status {
    font-size: 12px;
    color: #e06c75;
    min-height: 16px;
    text-align: right;
    margin-bottom: 12px;
  }

  .buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
  }

  button {
    border: none;
    border-radius: 12px;
    font-size: 18px;
    height: 60px;
    cursor: pointer;
    transition: filter 0.1s, transform 0.1s;
    font-weight: 500;
  }

  button:active { filter: brightness(1.3); transform: scale(0.96); }

  .btn-num  { background: #252535; color: #e0e0e0; }
  .btn-op   { background: #2e2e50; color: #82aaff; }
  .btn-eq   { background: #5c7cfa; color: #fff; }
  .btn-clr  { background: #3a1f2e; color: #e06c75; }
  .btn-back { background: #2a2a3a; color: #c792ea; }
  .btn-sign { background: #2a2a3a; color: #c3e88d; }
  .btn-zero { grid-column: span 2; }

  .history {
    background: #1a1a24;
    border-radius: 20px;
    padding: 24px;
    width: 280px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.6);
    max-height: 580px;
    display: flex;
    flex-direction: column;
  }

  .history h2 {
    font-size: 14px;
    font-weight: 600;
    color: #82aaff;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 16px;
  }

  .history-list {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .history-list::-webkit-scrollbar { width: 4px; }
  .history-list::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }

  .history-item {
    background: #0f0f13;
    border-radius: 10px;
    padding: 10px 14px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .history-item:hover { background: #1f1f2e; }
  .history-item .h-expr { font-size: 12px; color: #666; }
  .history-item .h-result { font-size: 18px; color: #fff; font-weight: 300; }
  .history-item .h-time { font-size: 10px; color: #444; margin-top: 2px; }

  .empty { color: #444; font-size: 13px; text-align: center; padding: 20px 0; }

  .btn-clear-hist {
    margin-top: 14px;
    width: 100%;
    height: 40px;
    border-radius: 10px;
    background: #3a1f2e;
    color: #e06c75;
    font-size: 13px;
    border: none;
    cursor: pointer;
    transition: filter 0.15s;
  }
  .btn-clear-hist:hover { filter: brightness(1.2); }

 
 </style>
 </head>
 <body>
 <div class="wrapper">

  <!-- Calculator -->
  <div class="calc">
    <div class="display">
      <div class="expr" id="expr"></div>
      <div class="result" id="result">0</div>
    </div>
    <div class="status" id="status"></div>
    <div class="buttons">
      <button class="btn-clr"  onclick="clearAll()">C</button>
      <button class="btn-sign" onclick="toggleSign()">±</button>
      <button class="btn-back" onclick="backspace()">⌫</button>
      <button class="btn-op"   onclick="appendOp('/')">÷</button>

      <button class="btn-num" onclick="appendNum('7')">7</button>
      <button class="btn-num" onclick="appendNum('8')">8</button>
      <button class="btn-num" onclick="appendNum('9')">9</button>
      <button class="btn-op"  onclick="appendOp('*')">×</button>

      <button class="btn-num" onclick="appendNum('4')">4</button>
      <button class="btn-num" onclick="appendNum('5')">5</button>
      <button class="btn-num" onclick="appendNum('6')">6</button>
      <button class="btn-op"  onclick="appendOp('-')">−</button>

      <button class="btn-num" onclick="appendNum('1')">1</button>
      <button class="btn-num" onclick="appendNum('2')">2</button>
      <button class="btn-num" onclick="appendNum('3')">3</button>
      <button class="btn-op"  onclick="appendOp('+')">+</button>

      <button class="btn-num btn-zero" onclick="appendNum('0')">0</button>
      <button class="btn-num" onclick="appendDot()">.</button>
      <button class="btn-eq"  onclick="calculate()">=</button>
    </div>
  </div>

  <!-- History -->
  <div class="history">
    <h2>History</h2>
    <div class="history-list" id="historyList">
      <div class="empty">No calculations yet</div>
    </div>
    <button class="btn-clear-hist" onclick="clearHistory()">Clear History</button>
  </div>

  <div class="signature">made by Seraj</div>

 </div>

<script>
  let expression = "";
  let justCalculated = false;

  const exprEl   = document.getElementById("expr");
  const resultEl = document.getElementById("result");
  const statusEl = document.getElementById("status");
  const histEl   = document.getElementById("historyList");

  function setStatus(msg, isErr) {
    statusEl.textContent = msg;
    statusEl.style.color = isErr ? "#e06c75" : "#c3e88d";
  }

  function updateDisplay() {
    exprEl.textContent   = expression;
    resultEl.textContent = expression || "0";
  }

  function appendNum(n) {
    if (justCalculated) { expression = ""; justCalculated = false; }
    expression += n;
    updateDisplay();
  }

  function appendOp(op) {
    justCalculated = false;
    if (expression === "" && op === "-") { expression = "-"; updateDisplay(); return; }
    if (expression === "") return;
    const last = expression.slice(-1);
    if (["+","-","*","/"].includes(last)) expression = expression.slice(0,-1);
    expression += op;
    updateDisplay();
  }

  function appendDot() {
    if (justCalculated) { expression = "0"; justCalculated = false; }
    const parts = expression.split(/[+\\-*/]/);
    if (parts[parts.length-1].includes(".")) return;
    if (!parts[parts.length-1]) expression += "0";
    expression += ".";
    updateDisplay();
  }

  function clearAll() {
    expression = ""; justCalculated = false;
    resultEl.textContent = "0"; exprEl.textContent = ""; statusEl.textContent = "";
  }

  function backspace() {
    if (justCalculated) { clearAll(); return; }
    expression = expression.slice(0,-1);
    updateDisplay();
  }

  function toggleSign() {
    if (!expression || expression === "0") return;
    if (expression.startsWith("-")) expression = expression.slice(1);
    else expression = "-" + expression;
    updateDisplay();
  }

  async function calculate() {
    if (!expression) return;
    setStatus("", false);
    try {
      const resp = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expression })
      });
      const data = await resp.json();
      if (!resp.ok) { setStatus(data.error || "Error", true); return; }
      exprEl.textContent   = expression + " =";
      resultEl.textContent = data.result;
      expression = data.result;
      justCalculated = true;
      loadHistory();
    } catch(e) {
      setStatus("Could not reach server", true);
    }
  }

  async function loadHistory() {
    try {
      const resp = await fetch("/api/history");
      const data = await resp.json();
      if (!data.length) { histEl.innerHTML = '<div class="empty">No calculations yet</div>'; return; }
      histEl.innerHTML = data.map(h => `
        <div class="history-item" onclick="useHistory('${h.result}')">
          <div class="h-expr">${h.expression} =</div>
          <div class="h-result">${h.result}</div>
          <div class="h-time">${h.timestamp}</div>
        </div>
      `).join("");
    } catch(e) {}
  }

  function useHistory(val) {
    expression = val; justCalculated = false; updateDisplay();
  }

  async function clearHistory() {
    try {
      await fetch("/api/history", { method: "DELETE" });
      loadHistory();
    } catch(e) {}
  }

  document.addEventListener("keydown", e => {
    if (e.key >= "0" && e.key <= "9") appendNum(e.key);
    else if (e.key === "+") appendOp("+");
    else if (e.key === "-") appendOp("-");
    else if (e.key === "*") appendOp("*");
    else if (e.key === "/") { e.preventDefault(); appendOp("/"); }
    else if (e.key === ".") appendDot();
    else if (e.key === "Enter" || e.key === "=") calculate();
    else if (e.key === "Backspace") backspace();
    else if (e.key === "Escape") clearAll();
  });

  loadHistory();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)