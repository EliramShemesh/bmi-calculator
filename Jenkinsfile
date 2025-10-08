pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/EliramShemesh/bmi-calculator.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                '''
            }
        }

        stage('Execute Python Script') {
            steps {
                sh 'python3 https://github.com/EliramShemesh/bmi-calculator/blob/main/bmi_calculator.py'
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished'
        }
        success {
            echo 'Script executed successfully'
        }
        failure {
            echo 'Script execution failed'
        }
    }
}