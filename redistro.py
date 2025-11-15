"""
Registro de personas (API REST + Tkinter)
- API REST con Flask para operaciones HTTP
- Interfaz Tkinter como cliente adicional
- Guardado automático en JSON
- Exporta JSON / XML / YAML
"""

import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import xml.etree.ElementTree as ET
from pathlib import Path
from flask import Flask, request, jsonify
import threading
import webbrowser

# Intento importar PyYAML (opcional para exportar YAML)
try:
    import yaml
    HAS_YAML = True
except Exception:
    yaml = None
    HAS_YAML = False

# Ruta del archivo persistente (en la misma carpeta del script)
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "personas.json"

# Lista en memoria
personas = []

# Configuración de Flask
app = Flask(__name__)
API_HOST = '127.0.0.1'
API_PORT = 5000

# -----------------------------
# GUARDADO / CARGA
# -----------------------------
def guardar_auto():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=4, ensure_ascii=False)
        print(f"[guardar_auto] guardado {len(personas)} registro(s) en {DATA_FILE}")
    except Exception as e:
        print(f"[guardar_auto] error al guardar: {e}")

def cargar_auto():
    global personas
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                personas = json.load(f)
            print(f"[cargar_auto] cargados {len(personas)} registro(s) desde {DATA_FILE}")
        else:
            personas = []
            print(f"[cargar_auto] no existe {DATA_FILE}, lista vacía")
    except Exception as e:
        personas = []
        print(f"[cargar_auto] error al cargar {DATA_FILE}: {e}")

# -----------------------------
# LÓGICA (Compartida para API y Tkinter)
# -----------------------------
def agregar_persona(nombre, control, especialidad):
    nombre = nombre.strip()
    control = control.strip()
    especialidad = especialidad.strip()
    if not nombre or not control or not especialidad:
        raise ValueError("Todos los campos son obligatorios")
    for p in personas:
        if p["control"] == control:
            raise ValueError(f"Ya existe un registro con el control {control}")
    nueva_persona = {"nombre": nombre, "control": control, "especialidad": especialidad}
    personas.append(nueva_persona)
    guardar_auto()
    return nueva_persona

def eliminar_persona_por_control(control):
    global personas
    inicial = len(personas)
    personas = [p for p in personas if p["control"] != control]
    if len(personas) < inicial:
        guardar_auto()
        return True
    return False

def buscar_personas(texto=""):
    if not texto:
        return personas.copy()
    
    texto = texto.lower().strip()
    return [
        p for p in personas
        if texto in p["nombre"].lower()
        or texto in p["control"].lower()
        or texto in p["especialidad"].lower()
    ]

def obtener_persona_por_control(control):
    for p in personas:
        if p["control"] == control:
            return p
    return None

def actualizar_persona(control_original, nuevo_nombre, nuevo_control, nueva_especialidad):
    nuevo_nombre = nuevo_nombre.strip()
    nuevo_control = nuevo_control.strip()
    nueva_especialidad = nueva_especialidad.strip()
    
    for p in personas:
        if p["control"] == control_original:
            if nuevo_control != control_original:
                for q in personas:
                    if q["control"] == nuevo_control:
                        raise ValueError("El nuevo número de control ya existe.")
            p["nombre"] = nuevo_nombre
            p["control"] = nuevo_control
            p["especialidad"] = nueva_especialidad
            guardar_auto()
            return p
    raise ValueError("No se encontró el registro.")

# -----------------------------
# API REST ENDPOINTS
# -----------------------------
@app.route('/api/personas', methods=['GET'])
def api_obtener_personas():
    """Obtener todas las personas o buscar por parámetro"""
    try:
        busqueda = request.args.get('busqueda', '')
        resultado = buscar_personas(busqueda)
        return jsonify({
            "status": "success",
            "data": resultado,
            "count": len(resultado)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/personas/<control>', methods=['GET'])
def api_obtener_persona(control):
    """Obtener una persona por número de control"""
    try:
        persona = obtener_persona_por_control(control)
        if persona:
            return jsonify({
                "status": "success",
                "data": persona
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Persona no encontrada"
            }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/personas', methods=['POST'])
def api_agregar_persona():
    """Agregar una nueva persona"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Datos JSON requeridos"
            }), 400
        
        nombre = data.get('nombre', '').strip()
        control = data.get('control', '').strip()
        especialidad = data.get('especialidad', '').strip()
        
        if not nombre or not control or not especialidad:
            return jsonify({
                "status": "error",
                "message": "Todos los campos son obligatorios"
            }), 400
        
        nueva_persona = agregar_persona(nombre, control, especialidad)
        
        return jsonify({
            "status": "success",
            "message": "Persona agregada exitosamente",
            "data": nueva_persona
        }), 201
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error interno del servidor"
        }), 500

@app.route('/api/personas/<control>', methods=['PUT'])
def api_actualizar_persona(control):
    """Actualizar una persona existente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Datos JSON requeridos"
            }), 400
        
        nuevo_nombre = data.get('nombre', '').strip()
        nuevo_control = data.get('control', '').strip()
        nueva_especialidad = data.get('especialidad', '').strip()
        
        if not nuevo_nombre or not nuevo_control or not nueva_especialidad:
            return jsonify({
                "status": "error",
                "message": "Todos los campos son obligatorios"
            }), 400
        
        persona_actualizada = actualizar_persona(control, nuevo_nombre, nuevo_control, nueva_especialidad)
        
        return jsonify({
            "status": "success",
            "message": "Persona actualizada exitosamente",
            "data": persona_actualizada
        }), 200
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error interno del servidor"
        }), 500

@app.route('/api/personas/<control>', methods=['DELETE'])
def api_eliminar_persona(control):
    """Eliminar una persona por número de control"""
    try:
        if eliminar_persona_por_control(control):
            return jsonify({
                "status": "success",
                "message": "Persona eliminada exitosamente"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Persona no encontrada"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error interno del servidor"
        }), 500

@app.route('/api/exportar/<formato>', methods=['GET'])
def api_exportar(formato):
    """Exportar datos en diferentes formatos"""
    try:
        if formato == 'json':
            return jsonify({
                "status": "success",
                "data": personas
            }), 200
        elif formato == 'xml':
            root = ET.Element("personas")
            for p in personas:
                nodo = ET.SubElement(root, "persona")
                ET.SubElement(nodo, "nombre").text = p["nombre"]
                ET.SubElement(nodo, "control").text = p["control"]
                ET.SubElement(nodo, "especialidad").text = p["especialidad"]
            xml_str = ET.tostring(root, encoding='utf-8', method='xml').decode()
            return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}', 200, {'Content-Type': 'application/xml'}
        else:
            return jsonify({
                "status": "error",
                "message": "Formato no soportado. Use 'json' o 'xml'"
            }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Endpoint para verificar el estado del API"""
    return jsonify({
        "status": "success",
        "message": "API funcionando correctamente",
        "total_registros": len(personas),
        "version": "1.0"
    }), 200

# -----------------------------
# EXPORTAR (Para Tkinter)
# -----------------------------
def exportar_json(ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(personas, f, indent=4, ensure_ascii=False)

def exportar_xml(ruta):
    root = ET.Element("personas")
    for p in personas:
        nodo = ET.SubElement(root, "persona")
        ET.SubElement(nodo, "nombre").text = p["nombre"]
        ET.SubElement(nodo, "control").text = p["control"]
        ET.SubElement(nodo, "especialidad").text = p["especialidad"]
    ET.ElementTree(root).write(ruta, encoding="utf-8", xml_declaration=True)

def exportar_yaml(ruta):
    if not HAS_YAML:
        raise RuntimeError("PyYAML no instalado (pip install pyyaml)")
    with open(ruta, "w", encoding="utf-8") as f:
        yaml.safe_dump(personas, f, allow_unicode=True)

# -----------------------------
# INTERFAZ TKINTER
# -----------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Registro de Personas - Cliente + API")
        root.geometry("860x500")

        # Frame para controles de API
        api_frame = ttk.LabelFrame(root, text="Control del API REST")
        api_frame.pack(fill="x", padx=8, pady=6)
        
        ttk.Button(api_frame, text="Iniciar Servidor API", command=self.iniciar_api).pack(side="left", padx=4)
        ttk.Button(api_frame, text="Abrir Documentación API", command=self.abrir_documentacion).pack(side="left", padx=4)
        ttk.Label(api_frame, text=f"API: http://{API_HOST}:{API_PORT}/api").pack(side="left", padx=10)

        # Formulario
        frm = ttk.LabelFrame(root, text="Formulario")
        frm.pack(fill="x", padx=8, pady=6)

        ttk.Label(frm, text="Nombre:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.ent_nombre = ttk.Entry(frm, width=40)
        self.ent_nombre.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(frm, text="Número de control:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.ent_control = ttk.Entry(frm, width=40)
        self.ent_control.grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(frm, text="Especialidad:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.ent_especialidad = ttk.Entry(frm, width=40)
        self.ent_especialidad.grid(row=2, column=1, padx=4, pady=4)

        bf = ttk.Frame(frm)
        bf.grid(row=0, column=2, rowspan=3, padx=8, pady=4)
        ttk.Button(bf, text="Agregar", command=self.ui_agregar).pack(fill="x", pady=3)
        ttk.Button(bf, text="Actualizar", command=self.ui_actualizar).pack(fill="x", pady=3)
        ttk.Button(bf, text="Eliminar", command=self.ui_eliminar).pack(fill="x", pady=3)
        ttk.Button(bf, text="Limpiar", command=self.limpiar_campos).pack(fill="x", pady=3)

        # Búsqueda + exportar
        tools = ttk.Frame(root)
        tools.pack(fill="x", padx=8, pady=6)
        ttk.Label(tools, text="Buscar:").pack(side="left")
        self.ent_buscar = ttk.Entry(tools)
        self.ent_buscar.pack(side="left", padx=4)
        ttk.Button(tools, text="Buscar", command=self.ui_buscar).pack(side="left", padx=4)
        ttk.Button(tools, text="Mostrar todo", command=self.ui_mostrar_todo).pack(side="left", padx=4)
        ttk.Button(tools, text="Exportar JSON", command=self.ui_export_json).pack(side="right", padx=4)
        ttk.Button(tools, text="Exportar XML", command=self.ui_export_xml).pack(side="right", padx=4)
        ttk.Button(tools, text="Exportar YAML", command=self.ui_export_yaml).pack(side="right", padx=4)

        # Lista
        frm_list = ttk.LabelFrame(root, text="Registros")
        frm_list.pack(fill="both", expand=True, padx=8, pady=6)
        self.listbox = tk.Listbox(frm_list)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_seleccionar)
        scroll = ttk.Scrollbar(frm_list, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=scroll.set)
        self.txt_detalle = tk.Text(frm_list, width=35)
        self.txt_detalle.pack(side="left", fill="y", padx=6)

        self.ui_mostrar_todo()
        self.servidor_iniciado = False

    def iniciar_api(self):
        """Iniciar el servidor Flask en un hilo separado"""
        if not self.servidor_iniciado:
            def run_flask():
                app.run(host=API_HOST, port=API_PORT, debug=False, use_reloader=False)
            
            thread = threading.Thread(target=run_flask, daemon=True)
            thread.start()
            self.servidor_iniciado = True
            messagebox.showinfo("API Iniciada", f"Servidor API corriendo en:\nhttp://{API_HOST}:{API_PORT}/api")

    def abrir_documentacion(self):
        """Abrir documentación de la API en el navegador"""
        webbrowser.open(f"http://{API_HOST}:{API_PORT}/api/status")

    # Handlers
    def ui_agregar(self):
        try:
            agregar_persona(self.ent_nombre.get(), self.ent_control.get(), self.ent_especialidad.get())
            messagebox.showinfo("OK", "Registro agregado")
            self.ui_mostrar_todo()
            self.limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def ui_eliminar(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un registro")
            return
        texto = self.listbox.get(sel[0])
        control = texto.split(" - ")[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar el registro {control}?"):
            if eliminar_persona_por_control(control):
                self.ui_mostrar_todo()
                self.limpiar_campos()
            else:
                messagebox.showerror("Error", "No encontrado")

    def ui_buscar(self):
        self.refrescar_listbox(buscar_personas(self.ent_buscar.get()))

    def ui_mostrar_todo(self):
        self.refrescar_listbox(personas)

    def ui_actualizar(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un registro.")
            return
        texto = self.listbox.get(sel[0])
        original = texto.split(" - ")[1]
        try:
            actualizar_persona(original, self.ent_nombre.get(), self.ent_control.get(), self.ent_especialidad.get())
            messagebox.showinfo("OK", "Registro actualizado")
            self.ui_mostrar_todo()
            self.limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Export
    def ui_export_json(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".json")
        if ruta:
            exportar_json(ruta)
            messagebox.showinfo("OK", "Exportado JSON")

    def ui_export_xml(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".xml")
        if ruta:
            exportar_xml(ruta)
            messagebox.showinfo("OK", "Exportado XML")

    def ui_export_yaml(self):
        if not HAS_YAML:
            messagebox.showerror("Falta PyYAML", "Instale: pip install pyyaml")
            return
        ruta = filedialog.asksaveasfilename(defaultextension=".yaml")
        if ruta:
            exportar_yaml(ruta)
            messagebox.showinfo("OK", "Exportado YAML")

    # Aux
    def refrescar_listbox(self, data):
        self.listbox.delete(0, tk.END)
        for p in data:
            self.listbox.insert(tk.END, f"{p['nombre']} - {p['control']} - {p['especialidad']}")
        self.txt_detalle.delete("1.0", tk.END)
        self.txt_detalle.insert(tk.END, f"{len(data)} registro(s).")

    def limpiar_campos(self):
        self.ent_nombre.delete(0, tk.END)
        self.ent_control.delete(0, tk.END)
        self.ent_especialidad.delete(0, tk.END)
        self.ent_buscar.delete(0, tk.END)

    def on_seleccionar(self, event):
        sel = self.listbox.curselection()
        if sel:
            texto = self.listbox.get(sel[0])
            nombre, control, esp = texto.split(" - ", 2)
            self.ent_nombre.delete(0, tk.END); self.ent_nombre.insert(0, nombre)
            self.ent_control.delete(0, tk.END); self.ent_control.insert(0, control)
            self.ent_especialidad.delete(0, tk.END); self.ent_especialidad.insert(0, esp)
            self.txt_detalle.delete("1.0", tk.END)
            self.txt_detalle.insert(tk.END, f"Nombre: {nombre}\nControl: {control}\nEspecialidad: {esp}")

# -----------------------------
# MAIN
# -----------------------------
def main():
    cargar_auto()   # carga desde DATA_FILE
    root = tk.Tk()
    app = App(root)
    
    # Mostrar información sobre la API al iniciar
    messagebox.showinfo(
        "Sistema de Registro", 
        "Sistema de Registro de Personas\n\n"
        "Características:\n"
        "• Interfaz gráfica Tkinter\n"
        "• API REST con Flask\n"
        "• Endpoints para CRUD completo\n"
        "• Compatible con Postman\n\n"
        "Haga clic en 'Iniciar Servidor API' para activar los endpoints REST"
    )
    
    # Guardado automático al cerrar
    root.protocol("WM_DELETE_WINDOW", lambda: (guardar_auto(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()