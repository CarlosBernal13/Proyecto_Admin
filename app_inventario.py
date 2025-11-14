from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "clave_super_secreta"  # Necesario para manejar sesiones

# --- Conexión a MongoDB ---
cliente = MongoClient("mongodb+srv://Carlosbernal:CarBer1998@cluster0.z31tlvd.mongodb.net/?appName=Cluster0")
db = cliente["Tienda"]
coleccion = db["productos"]
usuarios = db["usuarios"]
ventas=db["ventas"]

# --- LOGIN ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        pin = request.form['pin']
        
        user = usuarios.find_one({"usuario": usuario, "pin": pin})
        if user:
            session['usuario'] = usuario
            session['rol'] = user.get("rol", "cajero")
            flash(f"Bienvenido {usuario}", "success")
            return redirect('/inventario')
        else:
            flash("Usuario o PIN incorrectos", "danger")
    
    return render_template('login.html')

# --- INVENTARIO (solo si está logueado) ---
@app.route('/inventario')
def index():
    if 'usuario' not in session:
        return redirect('/')
    
    filtro = request.args.get('buscar', '')
    if filtro:
        productos = list(coleccion.find({
            "$or": [
                {"nombre": {"$regex": filtro, "$options": "i"}},
                {"codigo_barras": {"$regex": filtro, "$options": "i"}}
            ]
        }))
    else:
        productos = list(coleccion.find())
    return render_template('index.html', productos=productos, filtro=filtro, usuario=session['usuario'], rol=session['rol'])

# --- AGREGAR PRODUCTO ---
@app.route('/agregar', methods=['POST'])
def agregar():
    if 'usuario' not in session:
        return redirect('/')
    
    nuevo = {
        "codigo_barras": request.form['codigo'],
        "nombre": request.form['nombre'],
        "precio_venta": float(request.form['precio_v']),
        "precio_compra": float(request.form['precio_c']),
        "stock": int(request.form['stock'])
    }
    coleccion.insert_one(nuevo)
    flash("Producto agregado correctamente", "success")
    return redirect('/inventario')

# --- ELIMINAR PRODUCTO ---
@app.route('/eliminar/<id>')
def eliminar(id):
    if 'usuario' not in session:
        return redirect('/')
    coleccion.delete_one({"_id": ObjectId(id)})
    flash("Producto eliminado", "warning")
    return redirect('/inventario')

# --- EDITAR PRODUCTO ---
@app.route('/editar/<id>')
def editar(id):
    if 'usuario' not in session:
        return redirect('/')
    producto = coleccion.find_one({"_id": ObjectId(id)})
    return render_template('editar.html', producto=producto)

# --- ACTUALIZAR PRODUCTO ---
@app.route('/actualizar/<id>', methods=['POST'])
def actualizar(id):
    if 'usuario' not in session:
        return redirect('/')
    
    coleccion.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "codigo_barras": request.form['codigo'],
            "nombre": request.form['nombre'],
            "precio_venta": float(request.form['precio_v']),
            "precio_compra": float(request.form['precio_c']),
            "stock": int(request.form['stock'])
        }}
    )
    flash("Producto actualizado correctamente", "info")
    return redirect('/inventario')

# --- CERRAR SESIÓN ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
# --- HISTORIAL DE VENTAS ---
@app.route('/historial')
def historial():
    if 'usuario' not in session:
        return redirect('/')

    ventas_list = list(db["ventas"].find())

    # Calcular totales usando los nombres correctos
    total_ventas = sum(v.get("total_venta", 0) for v in ventas_list)
    total_ganancia = sum(v.get("ganancia_total", 0) for v in ventas_list)
    total_productos = sum(len(v.get("productos", [])) for v in ventas_list)

    return render_template('historial.html',
                           ventas=ventas_list,
                           total_ventas=total_ventas,
                           total_ganancia=total_ganancia,
                           total_productos=total_productos)


# --- Ejecutar el servidor ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
