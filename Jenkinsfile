pipeline {
    agent any

    environment {
        ORION_ENDPOINT = 'http://orion:1026'
        FIWARE_SERVICE = 'madrid'
        // FIWARE_SERVICEPATH = '/airquality'

        AUTH_ENDPOINT = 'http://localhost:8082/realms/tfm'
        AUTH_CLIENT_ID = 'nginx-pep'
        AUTH_CLIENT_SECRET = credentials('keycloak-nginx-pep-secret')
        AUTH_USER = 'joserra'
        AUTH_PASSWORD = credentials('keycloak-user-password')
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
                @echo off
                if not exist venv (
                    python -m venv venv
                )
                call venv\\Scripts\\activate && python -m pip install --upgrade pip && pip install -r requirements.txt
                """
            }
        }

        stage('3. Run ETL') {
            steps {
                echo "Ejecutando ETL en el entorno virtual..."
                withCredentials([string(credentialsId: 'ID_DE_TU_CREDENCIAL', variable: 'SECURE_TOKEN')]) {
                    bat """
                    @echo off
                    call venv\\Scripts\\activate && python main.py --url "${params.CSV_URL}" --mapping "${params.MAPPING}" --device_id "${params.DEVICE_ID}" --api_key "${params.API_KEY}" --token "%SECURE_TOKEN%"
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