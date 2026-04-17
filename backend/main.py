from fastapi import FastAPI

# Initialize the API
app = FastAPI(title="EquiGuard API", version="1.0")

@app.get("/")
def read_root():
    return {"status": "Active", "message": "EquiGuard Firewall is running and ready for data."}
