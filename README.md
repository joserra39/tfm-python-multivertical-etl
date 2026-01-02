# Generic Multi-Vertical ETL Engine (FIWARE)

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-FIWARE-green.svg)](https://www.fiware.org/)
[![Automation](https://img.shields.io/badge/CI/CD-Jenkins-orange.svg)](https://www.jenkins.io/)

## 📋 Descripción
Este proyecto es un motor **ETL (Extract, Transform, Load)** genérico diseñado para la ingesta automatizada de datos desde fuentes Open Data (CSV) hacia una infraestructura **FIWARE** mediante el **IoTAgent JSON**.

Desarrollado como pieza central de mi **TFM**, el sistema destaca por su arquitectura **multi-vertical**, permitiendo procesar diferentes tipos de datos (calidad del aire, tráfico, sensores IoT, etc.) sin modificar el código fuente, delegando toda la lógica específica a la configuración del Pipeline.

## 🏗️ Arquitectura y Automatización
El flujo de trabajo está completamente automatizado y aislado para garantizar la reproducibilidad y robustez:

1.  **Orquestación con Jenkins:** Se utiliza un `Jenkinsfile` que define todo el ciclo de vida del dato.
2.  **Aislamiento con Entorno Virtual (venv):** En cada ejecución, Jenkins gestiona un entorno virtual de Python para garantizar que las dependencias estén aisladas y no existan conflictos de librerías.
3.  **Configuración por Parámetros:** No existen valores "hardcoded". Toda la configuración (URLs, mapeos, tokens) se inyecta dinámicamente desde la interfaz de Jenkins.
4.  **Extracción Dinámica:** Descarga automática de ficheros CSV mediante URLs parametrizadas.
5.  **Transformación Basada en Mapeo:** Conversión de columnas CSV a atributos JSON de FIWARE mediante un diccionario de mapeo.
6.  **Carga Segura:** Comunicación con la API de IoTAgent usando autenticación por Token y API_KEY.

## 🚀 Configuración y Parámetros (Pipeline)
La flexibilidad del motor reside en los parámetros configurables definidos en el Pipeline de Jenkins:

| Parámetro | Descripción |
| :--- | :--- |
| `CSV_URL` | Enlace directo al recurso CSV (ej. Portal de Datos Abiertos de Madrid). |
| `MAPPING` | Estructura JSON que mapea las columnas del CSV a los atributos de FIWARE. |
| `DEVICE_ID` | Identificador único para el sensor en el Context Broker. |
| `API_KEY` | Clave de servicio para el IoTAgent. |
| `AUTH_TOKEN` | Token de seguridad (gestionado de forma segura mediante `withCredentials`). |

## 📁 Estructura del Repositorio
```text
├── modules/
│   ├── vertical
│   │   ├── extractor.py     # Gestión de peticiones HTTP y descarga de archivos.
│   │   ├── transformer.py   # Lógica de limpieza y mapeo de datos.
│   └── loader.py        # Cliente API para el IoTAgent.
├── Jenkinsfile          # Definición del pipeline (venv, seguridad y ejecución).
├── main.py              # Orquestador principal y lógica de parámetros.
└── requirements.txt     # Dependencias del proyecto.