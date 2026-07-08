pipeline {
  agent any

  stages {
    stage('1. Checkout') {
      steps {
        checkout scm
      }
    }

    stage('2. Mostrar variables') {
      steps {
        script {
          echo "KEYCLOAK_URL=${env.KEYCLOAK_URL}"
          echo "ORION_BASE_URL=${env.ORION_BASE_URL}"
          echo "FIWARE_SERVICE=${env.FIWARE_SERVICE}"
          echo "FIWARE_SERVICEPATH=${env.FIWARE_SERVICEPATH}"
        }
        sh 'printenv | sort | grep -E "KEYCLOAK|ORION|FIWARE" || true'
      }
    }

    stage('3. Crear venv e instalar dependencias') {
      steps {
        echo 'Creando entorno virtual y cargando dependencias...'
        sh '''
          python --version
          if [ ! -d ".venv" ]; then
            python3 -m venv .venv
          fi
          . .venv/bin/activate
          python -m pip install --upgrade pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('4. Ejecutar ETL') {
    steps {
        withCredentials([
        usernamePassword(
            credentialsId: 'KEYCLOAK_CLIENT',
            usernameVariable: 'KEYCLOAK_CLIENT_ID',
            passwordVariable: 'KEYCLOAK_CLIENT_SECRET'
        ),
        usernamePassword(
            credentialsId: 'KEYCLOAK_USER',
            usernameVariable: 'KEYCLOAK_USER',
            passwordVariable: 'KEYCLOAK_PASSWORD'
        )
        ]) {
        echo "DATA_PATH=${params.DATA_PATH}"
        echo "DATASET_NAME=${params.DATASET_NAME}"
        sh """
            set +x

            echo "PWD: \$(pwd)"
            echo "Listing /"
            ls -la /
            echo "Listing /data"
            ls -la /data
            echo "Listing DATA_PATH..."
            ls -la "${params.DATA_PATH}" || echo "No se puede listar DATA_PATH"

            echo "Activando venv..."
            . .venv/bin/activate || echo "No se pudo activar .venv"

            echo "which python:"
            which python || echo "python no encontrado"

            echo "python --version:"
            python --version || echo "No se pudo obtener version de python"

            echo "Ejecutando main.py..."
            python main.py "${params.DATA_PATH}" "${params.DATASET_NAME}"
        """
        }
    }
    }
  }

  post {
    failure {
      echo 'Error detectado. Revisa la instalación de dependencias o el código Python.'
    }
    always {
      echo 'Finalizando pipeline.'
    }
  }
}