from fastapi import FastAPI

app = FastAPI(title="Recipes API")


@app.get("/")
def root():
    return {"message": "API de Recetas!"}
