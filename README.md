# Generic Multi-Vertical ETL Engine (FIWARE)

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-FIWARE-green.svg)](https://www.fiware.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Descripción
Este proyecto consiste en un motor **ETL (Extract, Transform, Load)** genérico y configurable desarrollado en Python. Ha sido diseñado como parte de mi **Trabajo de Fin de Máster (TFM)** para facilitar la ingesta de datos desde diversas fuentes de Datos Abiertos (como el Ayuntamiento de Madrid) hacia una plataforma basada en **FIWARE Context Broker** a través de **IoTAgent JSON**.

La principal ventaja de esta herramienta es su capacidad **multi-vertical**: mediante archivos de configuración y mapeos dinámicos, puede procesar datos de calidad del aire, tráfico, meteorología o cualquier otro dominio sin modificar el código base.

## 🏗️ Arquitectura del Sistema
El pipeline está diseñado para ser ejecutado de forma automatizada mediante **Jenkins**, permitiendo una orquestación profesional y segura.

## 🚀 Características Principales
* **Extracción Dinámica:** Descarga automática de ficheros CSV mediante URLs parametrizadas.
* **Transformación Basada en Mapeo:** Conversión de columnas CSV a atributos JSON de FIWARE mediante un diccionario de mapeo.
* **Carga Segura:** Comunicación con la API de IoTAgent usando autenticación por Token y API_KEY.
* **Preparado para CI/CD:** Integración nativa con Jenkins mediante `Jenkinsfile`.

## 📁 Estructura del Proyecto
```text
├── main.py              # Orquestador principal y lógica de parámetros.
├── modules/
│   ├── extractor.py     # Gestión de peticiones HTTP y descarga de archivos.
│   ├── transformer.py   # Lógica de limpieza y mapeo de datos.
│   └── loader.py        # Cliente API para el IoTAgent.
├── configs/             # Archivos JSON/YAML con los parámetros de cada vertical.
├── Jenkinsfile          # Definición del pipeline de automatización.
└── requirements.txt     # Dependencias del proyecto.