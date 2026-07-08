pipeline {
  agent {
    docker {
      image 'python:3.12-slim'
      reuseNode true
    }
  }

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
        sh '''
          set -e
          echo "Python en el agente:"
          python --version || python3 --version

          echo "Limpiando venv anterior (si existe)..."
          rm -rf .venv

          echo "Creando nuevo entorno virtual..."
          python -m venv .venv

          echo "Activando entorno virtual..."
          . .venv/bin/activate

          echo "Pip dentro del venv:"
          which pip
          pip --version

          echo "Instalando dependencias..."
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
          echo "Ejecutando ETL en el entorno virtual..."
      sh """
          set +x
          . .venv/bin/activate
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