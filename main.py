from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Import calculator API routes
from app.operations.calculator import router as calculator_router

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def homepage():
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Hello World</h1>

        <input id="a" type="number" />
        <input id="b" type="number" />

        <button onclick="add()">Add</button>
        <button onclick="divide()">Divide</button>

        <div id="result"></div>

        <script>
            function add() {
                const a = parseFloat(document.getElementById('a').value);
                const b = parseFloat(document.getElementById('b').value);
                document.getElementById('result').innerText = "Result: " + (a + b);
            }

            function divide() {
                const a = parseFloat(document.getElementById('a').value);
                const b = parseFloat(document.getElementById('b').value);
                if (b === 0) {
                    document.getElementById('result').innerText = "Error: Cannot divide by zero!";
                } else {
                    document.getElementById('result').innerText = "Result: " + (a / b);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# Include calculator API routes (required for integration tests)
app.include_router(calculator_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
