// server.js

// 1. Importar las librerías
const express = require('express');
const { MongoClient } = require('mongodb');

// 2. Configuración inicial
const app = express();
app.use(express.json()); // Middleware para parsear el cuerpo de las peticiones JSON
const port = 3000; // Puerto donde se ejecutará el servidor

// !!! IMPORTANTE: REEMPLAZA ESTO CON TU PROPIA CADENA DE CONEXIÓN DE MONGODB ATLAS !!!
const mongoUrl = 'mongodb+srv://Carlosbernal:CarBer1998@cluster0.z31tlvd.mongodb.net/?appName=Cluster0';
const dbName = 'Tienda'; 
const productosCollectionName = 'productos'; 
const usuariosCollectionName = 'usuarios'; 

// ====================================================================
// ENDPOINT 1: /login (Autenticación y Verificación de Rol)
// ====================================================================

app.post('/login', async (req, res) => {
    const { usuario, pin } = req.body;

    if (!usuario || !pin) {
        return res.status(400).json({ success: false, message: 'Usuario y PIN son requeridos' });
    }

    let client;
    try {
        client = new MongoClient(mongoUrl);
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection('usuarios');

        const user = await collection.findOne({ usuario: usuario });

        // --- LÓGICA DE VALIDACIÓN CORRECTA Y ESTRICTA ---
        if (user && user.pin === pin && user.rol === 'administrador') {
            // SI LAS TRES CONDICIONES SE CUMPLEN
            console.log(`Login exitoso para administrador: ${usuario}`);
            res.json({ success: true, message: 'Login exitoso' });
        } else {
            // SI CUALQUIER CONDICIÓN FALLA
            if (!user) {
                console.log(`Intento de login fallido. Usuario no encontrado: ${usuario}`);
            } else if (user.pin !== pin) {
                console.log(`Intento de login fallido para ${usuario}. PIN incorrecto.`);
            } else if (user.rol !== 'administrador') {
                console.log(`Intento de login fallido para ${usuario}. Rol no autorizado: '${user.rol}'`);
            }
            res.status(401).json({ success: false, message: 'Credenciales incorrectas o rol no autorizado' });
        }

    } catch (error) {
        console.error('Error en el endpoint de login:', error);
        res.status(500).json({ success: false, message: 'Error en el servidor' });
    } finally {
        if (client) {
            await client.close();
        }
    }
});


// ====================================================================
// ENDPOINT 2: /productos (Obtener todo el inventario)
// ====================================================================

app.get('/productos', async (req, res) => {
    let client;
    try {
        // Conectarse a la base de datos
        client = new MongoClient(mongoUrl);
        await client.connect();
        console.log("Conectado a MongoDB para obtener productos.");

        const db = client.db(dbName);
        const collection = db.collection(productosCollectionName);

        // Buscar todos los documentos
        const productos = await collection.find({}).toArray();
        
        console.log(`Enviando ${productos.length} productos.`);
        
        // Enviar los datos encontrados como una respuesta en formato JSON
        res.json(productos);

    } catch (error) {
        console.error('Error al consultar la base de datos de productos:', error);
        res.status(500).json({ success: false, message: 'Error en el servidor al obtener inventario.' });
    } finally {
        // Cerrar la conexión
        if (client) {
            await client.close();
            console.log("Desconectado de MongoDB.");
        }
    }
});


// 4. Iniciar el servidor
app.listen(port, () => {
    console.log(`Servidor escuchando en http://localhost:${port}`);
});