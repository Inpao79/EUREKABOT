# Importar librerías necesarias para construir nuestra API.
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse 
from fastapi.staticfiles import StaticFiles
import pandas as pd  
import nltk  
from nltk.tokenize import word_tokenize  
from nltk.corpus import wordnet  

# Importar librerías necesarias para el manejo de plantillas HTML
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os

# Configuración de NLTK
nltk.data.path.append(r"C:\Users\Ana Karina Vargas\AppData\Local\Programs\Python\Python312\Lib\site-packages\nltk")
nltk.download('punkt', quiet=True)  
nltk.download('wordnet', quiet=True)  

# Función para cargar los experimentos desde un archivo CSV
def load_experimentos(): 
    try:
        df = pd.read_csv('Dataset/experimentos.csv', usecols=['nombre', 'descripcion'], encoding='utf-8', on_bad_lines='skip')
        df.fillna('', inplace=True)
        return df.to_dict('records')  
    except FileNotFoundError:
        return []  

# Cargar experimentos al iniciar la API
experimentos_list = load_experimentos()

# Función para obtener sinónimos de una palabra
def get_synonyms(word):
    synsets = wordnet.synsets(word)
    return {lemma.name() for syn in synsets for lemma in syn.lemmas()} if synsets else set()

# Inicializar FastAPI
app = FastAPI(title="Mis experimentos", version="1.0.0")
# Montar la carpeta 'static' para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Asegúrate de que la ruta de templates es correcta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta de inicio
@app.get("/", tags=['Home'])
def home():
    return HTMLResponse('<h1>Bienvenido a la API de experimentos</h1>')

# Ruta para obtener la lista completa de experimentos
@app.get("/experimentos", tags=['Experimentos'])
def get_experimentos():
    if experimentos_list:
        return experimentos_list
    raise HTTPException(status_code=500, detail="No hay datos de los experimentos disponibles")

# Ruta para obtener un experimento por su nombre
@app.get("/experimentos/{nombre}", tags=['Experimentos'])
def get_experimento_por_nombre(nombre: str):
    experimento = next((m for m in experimentos_list if m['nombre'].lower() == nombre.lower()), None)
    if experimento:
        return experimento
    raise HTTPException(status_code=404, detail="Experimento no encontrado")

# Chatbot que busca experimentos por palabras clave
@app.get("/chatbot", tags=['Chatbot'])
def chatbot(query: str = Query(None, title="Consulta", description="Palabras clave para buscar experimentos")):
    if not query:
        raise HTTPException(status_code=400, detail="El parámetro 'query' es obligatorio")

    query_words = word_tokenize(query.lower())
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)
    
    results = [m for m in experimentos_list if any(s in m['nombre'].lower() for s in synonyms)]

    return JSONResponse(content={
        "Respuesta": "Aquí tienes algunos experimentos relacionados" if results else "No se encontraron experimentos con ese nombre",
        "experimentos": results
    })
    
@app.get("/buscar")
def buscar_experimentos(query: str = Query(..., title="Palabra clave")):
    query = query.lower()
    resultados = [exp for exp in experimentos_list if query in exp['nombre'].lower() or query in exp['descripcion'].lower()]
    
    if not resultados:
        return JSONResponse(content={"respuesta": "No encontré experimentos relacionados."}, status_code=404)

    return JSONResponse(content={"experimentos": resultados})

    resultados = []
    for exp in experimentos_list:
        nombre = exp['nombre'].lower().strip()
        descripcion = exp['descripcion'].lower().strip()

        # Busca la palabra clave en el nombre o la descripción
        if query_lower in descripcion or query_lower in nombre:
            resultados.append(exp)

    if resultados:
        response_text = "\n".join(
            [f"📌 **{exp['nombre']}**: {exp['descripcion']}" for exp in resultados]
        )
        print(f"✅ Experimentos encontrados:\n{response_text}")
        return {"respuesta": response_text}

    print("❌ No se encontraron experimentos.")
    return {"respuesta": "No encontré experimentos relacionados."}  


