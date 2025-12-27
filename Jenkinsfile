pipeline {
    agent any

    parameters {
        string(name: 'CSV_URL', defaultValue: '', description: 'URL del CSV')
        string(name: 'MAPPING', defaultValue: '{}', description: 'Mapeo JSON')
        string(name: 'DEVICE_ID', defaultValue: '', description: 'ID del dispositivo')
        string(name: 'API_KEY', defaultValue: '', description: 'API Key del IoTAgent')
        password(name: 'AUTH_TOKEN', description: 'Token de seguridad')
    }

    stages {
        stage('1. Checkout') {
            steps {
                checkout scm
            }
        }

        stage('2. Create VirtualEnv & Install') {
            steps {
                echo 'Creando entorno virtual y cargando dependencias...'
                bat """
                :: Crear el entorno si no existe
                if not exist venv (
                    python -m venv venv
                )
                
                :: Activar e instalar requirements
                call venv\\Scripts\\activate && ^
                python -m pip install --upgrade pip && ^
                pip install -r requirements.txt
                """
            }
        }

        stage('3. Run ETL') {
            steps {
                echo "Ejecutando ETL en el entorno virtual..."
                
                withCredentials([string(credentialsId: 'github-token-tfm', variable: 'SECURE_TOKEN')]) {
                    bat """
                    :: Importante: Se activa el venv y se ejecuta en la misma sesión de comandos
                    call venv\\Scripts\\activate && ^
                    python main.py ^
                        --url "${params.CSV_URL}" ^
                        --mapping "${params.MAPPING}" ^
                        --device_id "${params.DEVICE_ID}" ^
                        --api_key "${params.API_KEY}" ^
                        --token "%SECURE_TOKEN%"
                    """
                }
            }
        }
    }

    post {
        failure {
            echo '❌ Error detectado. Revisa la instalación de dependencias o el código Python.'
        }
        always {
            echo 'Finalizando pipeline.'
            // No borramos el venv para que la siguiente ejecución sea más rápida (cache)
        }
    }
}